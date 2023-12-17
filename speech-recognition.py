import queue
import re
import sys
from threading import Thread
from google.cloud import speech
import pyaudio
import sounddevice as sd

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream:
    """Opens a loopback recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate=RATE, chunk=CHUNK, device=4):  # Adjust the device index as needed
        self._rate = rate
        self._chunk = chunk
        self._device = device
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        # Define the callback function for the SoundDevice stream
        def callback(indata, frames, time, status):
            # Convert the numpy array (indata) to bytes and put it in the buffer
            self._buff.put(indata.tobytes())

        # Open the SoundDevice stream for loopback
        self._audio_stream = sd.InputStream(
            device=8, 
            channels=1, 
            samplerate=self._rate,
            callback=callback
        )
        self._audio_stream.start()
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)

    def generator(self):
        """Generates audio chunks from the stream."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

def listen_print_loop(responses):
    """Iterates through server responses and prints the transcription."""
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        if result.is_final:
            # gui.update_text(transcript.lstrip() + '\r')
            print(transcript.lstrip() + '\r')
            num_chars_printed = 0

            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break
        else:
            # gui.update_text(transcript.lstrip() + '\r')
            print(transcript.lstrip() + '\r')
            num_chars_printed = len(transcript)

def main():
    """Main function to start the speech recognition and GUI."""
    language_code = "en-US"  # a BCP-47 language tag
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model='latest_long'
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    # gui = GUI()
    # gui_thread = Thread(target=gui.run)
    # gui_thread.start()

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)
        listen_print_loop(responses)

if __name__ == "__main__":
    main()
