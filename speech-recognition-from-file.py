from _spinner_helper import Spinner
import pyaudiowpatch as pyaudio
import time
import wave
import os

DURATION = 5.0
CHUNK_SIZE = 512
CURRENT_FILENAME = "recording_{}.wav"
CURRENT_INDEX = 1
chunks = []

from google.cloud import speech
from pydub import AudioSegment

def transcribe_file(speech_file: str) -> speech.RecognizeResponse:
    """Transcribe the given audio file."""
    client = speech.SpeechClient()

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding = 'LINEAR16',
        language_code = 'en-US',
        sample_rate_hertz = 48000,
        audio_channel_count = 2,
    )

    response = client.recognize(config=config, audio=audio)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print(f"Transcript: {result.alternatives[0].transcript}")

    return response

def record_audio():
    global CURRENT_FILENAME, CURRENT_INDEX
    filename = CURRENT_FILENAME.format(CURRENT_INDEX)
    CURRENT_INDEX += 1

    with pyaudio.PyAudio() as p, Spinner() as spinner:
        """
        Create PyAudio instance via context manager.
        Spinner is a helper class, for `pretty` output
        """
        try:
            # Get default WASAPI info
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            spinner.print("Looks like WASAPI is not available on the system. Exiting...")
            spinner.stop()
            exit()
        
        # Get default WASAPI speakers
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                """
                Try to find loopback device with same name(and [Loopback suffix]).
                Unfortunately, this is the most adequate way at the moment.
                """
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                spinner.print("Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available devices.\nExiting...\n")
                spinner.stop()
                exit()
                
        #spinner.print(f"Recording from: ({default_speakers['index']}){default_speakers['name']}")
        
        wave_file = wave.open(filename, 'wb')
        
        wave_file.setnchannels(default_speakers["maxInputChannels"])
        wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(int(default_speakers["defaultSampleRate"]))
        
        def callback(in_data, frame_count, time_info, status):
            """Write frames and return PA flag"""
            wave_file.writeframes(in_data)
            return (in_data, pyaudio.paContinue)
        
        with p.open(format=pyaudio.paInt16,
                channels=default_speakers["maxInputChannels"],
                rate=int(default_speakers["defaultSampleRate"]),
                frames_per_buffer=CHUNK_SIZE,
                input=True,
                input_device_index=default_speakers["index"],
                stream_callback=callback
        ) as stream:
            """
            Opena PA stream via context manager.
            After leaving the context, everything will
            be correctly closed(Stream, PyAudio manager)            
            """
            # spinner.print(f"The next {DURATION} seconds will be written to {filename}")
            time.sleep(DURATION) # Blocking execution while playing
        
        wave_file.close()
        
        return filename
    
# Load the audio file

# Export each chunk as a separate WAV file
for i, chunk in enumerate(chunks):
    chunk.export(f"chunk_{i}.wav", format="wav")

# Record audio and transcribe in order
filenames = []
for _ in range(5):  # Record 3 times
    filename = record_audio()
    song = AudioSegment.from_file(filename, format="wav")
    filenames.append(filename)
    transcribe_file(filename)

for filename in filenames:
    os.remove(filename)