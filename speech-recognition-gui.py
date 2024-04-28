import queue
import re
from threading import Thread
from google.cloud import speech
import pyaudio
from gui import GUI

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

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
            input_device_index=1,
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
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
        enable_automatic_punctuation=True,
        model='latest_long'
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    with MicrophoneStream(RATE, CHUNK) as stream:
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

