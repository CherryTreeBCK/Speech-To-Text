# Speech Recognition
import queue
import re
from threading import Thread
from google.cloud import speech
import pyaudiowpatch as pyaudio
from gui import GUI

# Audio recording parameters
CHUNK_SIZE = 512
RATE = 48000

class ComputerAudioStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        try:
            # Attempt to get default WASAPI host API information
            self.wasapi_info = self._audio_interface.get_host_api_info_by_type(pyaudio.paWASAPI)
            
        except OSError:
            print("WASAPI not available. Exiting...")
            exit()
        
        # Find default output device that supports loopback recording
        default_speakers = self.get_default_speakers()
        # Get the audio stream of the default speakers
        self._audio_stream = self.get_audio_stream(default_speakers)
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue
        
    def get_default_speakers(self):
        default_speakers = self._audio_interface.get_device_info_by_index(self.wasapi_info["defaultOutputDevice"])
        if not default_speakers["isLoopbackDevice"]:
            for loopback in self._audio_interface.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                print("No loopback device found. Exiting...")
                exit()
                
        return default_speakers
        
    def get_audio_stream(self, default_speakers):
        return self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=default_speakers["maxInputChannels"],
            rate=int(default_speakers["defaultSampleRate"]),
            frames_per_buffer=CHUNK_SIZE,
            input=True,
            input_device_index=default_speakers["index"],
            stream_callback=self._fill_buffer,
        )
        

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield chunk

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
            input_device_index=0,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield chunk

def speech_recognition_thread(gui_queue):
    def listen_print_loop(responses):
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if result.is_final:
                gui_queue.put(transcript.lstrip())
                num_chars_printed = 0

                if re.search(r"\b(exit|quit)\b", transcript, re.I):
                    print("Exiting..")
                    break
            else:
                overwrite_chars = ' ' * (num_chars_printed - len(transcript))
                gui_queue.put(transcript.lstrip() + overwrite_chars)
                num_chars_printed = len(transcript)

    # Speech recognition setup
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding='LINEAR16',                  # Audio encoding type
        language_code='en-US',                # Language of the audio
        sample_rate_hertz=RATE,              # Sample rate in Hertz
        audio_channel_count=2,                # Number of audio channels
        enable_automatic_punctuation=True,    # Automatic punctuation
        model='latest_long'                   # Latest long
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
    
    # Uncomment this line if you prefer to use a microphone rather
    # than system audio
    # with MicrophoneStream(RATE, CHUNK_SIZE) as stream:
    with ComputerAudioStream(RATE, CHUNK_SIZE) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
        responses = client.streaming_recognize(streaming_config, requests)
        listen_print_loop(responses)
        

def main():
    gui = GUI()
    Thread(target=speech_recognition_thread, args=(gui.queue,), daemon=True).start()
    gui.run()

if __name__ == "__main__":
    main()