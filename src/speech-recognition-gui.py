import queue
import re
from threading import Thread
import torch
from transformers import pipeline
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
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny",
        chunk_length_s=30,
        device=device,
    )

    def listen_print_loop(audio_generator):
        for chunk in audio_generator:
            prediction = pipe(chunk, return_timestamps=True)["chunks"]
            transcript = " ".join([pred["text"] for pred in prediction])
            gui_queue.put(transcript)
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break

    # Uncomment this line if you prefer to use a microphone rather than system audio
    # with MicrophoneStream(RATE, CHUNK_SIZE) as stream:
    with ComputerAudioStream(RATE, CHUNK_SIZE) as stream:
        audio_generator = stream.generator()
        listen_print_loop(audio_generator)

def main():
    gui = GUI()
    Thread(target=speech_recognition_thread, args=(gui.queue,), daemon=True).start()
    gui.run()

if __name__ == "__main__":
    main()
