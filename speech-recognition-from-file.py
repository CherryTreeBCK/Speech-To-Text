# Import necessary libraries
from _spinner_helper import Spinner  # Custom module for creating a spinner effect
import pyaudiowpatch as pyaudio      # Modified PyAudio for specific audio handling
import time                          # Time library for timing operations
import wave                          # Module to read and write WAV files
import os                            # Operating system interface module

# Constants for audio recording
DURATION = 5.0                       # Duration of each audio recording in seconds
CHUNK_SIZE = 512                     # Size of each audio chunk to read
CURRENT_FILENAME = "recording_{}.wav"  # Template for audio file naming
CURRENT_INDEX = 1                    # Index to keep track of audio files created

# Import Google Cloud client library for speech recognition
from google.cloud import speech       
from pydub import AudioSegment        # Library to manipulate audio with simple high-level interface

def transcribe_file(speech_file: str) -> speech.RecognizeResponse:
    """Transcribe the given audio file using Google Cloud Speech-to-Text."""
    client = speech.SpeechClient()    # Create a client for interacting with the API

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()   # Read the audio file content

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding='LINEAR16',                  # Audio encoding type
        language_code='en-US',                # Language of the audio
        sample_rate_hertz=48000,              # Sample rate in Hertz
        audio_channel_count=2,                # Number of audio channels
        enable_automatic_punctuation=True,    # Automatic punctuation
        model='latest_long'                   # Latest long
    )

    response = client.recognize(config=config, audio=audio)

    # Print the transcripts for the entire audio file
    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")

    return response

def record_audio():
    """Record audio from the default system microphone for a set duration."""
    global CURRENT_FILENAME, CURRENT_INDEX
    filename = CURRENT_FILENAME.format(CURRENT_INDEX)
    CURRENT_INDEX += 1

    with pyaudio.PyAudio() as p, Spinner() as spinner:
        try:
            # Attempt to get default WASAPI host API information
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            spinner.print("WASAPI not available. Exiting...")
            spinner.stop()
            exit()
        
        # Find default output device that supports loopback recording
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                spinner.print("No loopback device found. Exiting...")
                spinner.stop()
                exit()
                
        # Create a wave file for recording
        wave_file = wave.open(filename, 'wb')
        wave_file.setnchannels(default_speakers["maxInputChannels"])
        wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(int(default_speakers["defaultSampleRate"]))
        
        # Callback function to write data to the wave file
        def callback(in_data, frame_count, time_info, status):
            wave_file.writeframes(in_data)
            return (in_data, pyaudio.paContinue)
        
        # Open a PyAudio stream for recording
        with p.open(format=pyaudio.paInt16,
                    channels=default_speakers["maxInputChannels"],
                    rate=int(default_speakers["defaultSampleRate"]),
                    frames_per_buffer=CHUNK_SIZE,
                    input=True,
                    input_device_index=default_speakers["index"],
                    stream_callback=callback) as stream:
            time.sleep(DURATION)  # Record for the set duration
        
        wave_file.close()   # Close the wave file after recording
        
        return filename
    
# This part of the code is commented out because it seems to be unused in the provided context.
# It shows how you would export audio chunks if they were manipulated within the script.
# for i, chunk in enumerate(chunks):
#     chunk.export(f"chunk_{i}.wav", format="wav")

# Main execution block: record and transcribe audio files, then clean up
filenames = []
for _ in range(5):  # Record 5 times
    filename = record_audio()
    song = AudioSegment.from_file(filename, format="wav")
    filenames.append(filename)
    transcribe_file(filename)

# Remove the recorded audio files after processing
for filename in filenames:
    os.remove(filename)
