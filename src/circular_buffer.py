import pyaudiowpatch as pyaudio
import numpy as np
import collections
import wave

class ComputerAudioStream:
    """Opens a recording stream and keeps the last few seconds of audio data."""
    def __init__(self, rate, chunk, duration):
        self._rate = rate
        self._chunk = chunk
        self._deque_len = duration * rate
        self._buff = collections.deque(maxlen=self._deque_len)
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        try:
            self.wasapi_info = self._audio_interface.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("WASAPI not available. Exiting...")
            exit()
        
        default_speakers = self.get_default_speakers()
        self._audio_stream = self.get_audio_stream(default_speakers)
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        data = np.frombuffer(in_data, dtype=np.int16)
        self._buff.extend(data)
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
            frames_per_buffer=self._chunk,
            input=True,
            input_device_index=default_speakers["index"],
            stream_callback=self._fill_buffer,
        )

    def get_current_buffer(self, duration=None):
        """Returns the current contents of the buffer. If duration is specified, returns the last `duration` seconds of audio."""
        if duration is None:
            return np.array(self._buff)
        
        num_samples = int(duration * self._rate)
        if num_samples > len(self._buff):
            num_samples = len(self._buff)
        
        return np.array(self._buff)[-num_samples:]

# Example usage:
if __name__ == "__main__":
    RATE = 44100
    CHUNK_FACTOR = 5
    CHUNK = int(RATE / CHUNK_FACTOR)
    DURATION = 5
    OUTPUT_FILENAME = "output.wav"

    with ComputerAudioStream(RATE, CHUNK, DURATION) as stream:
        import time
        for _ in range(int(RATE / CHUNK * DURATION)):
            time.sleep(CHUNK / RATE)
            audio_chunk = stream.get_current_buffer()
            print(f"Full buffer: {audio_chunk}")
            short_chunk = stream.get_current_buffer(2)  # Last 2 seconds
            print(f"Last 2 seconds: {short_chunk}")

        # Save the last DURATION seconds of audio to a WAV file
        final_audio = stream.get_current_buffer()
        wf = wave.open(OUTPUT_FILENAME, 'wb')
        wf.setnchannels(1)  # Assuming mono audio for simplicity
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(final_audio.tobytes())
        wf.close()

        print(f"Audio saved to {OUTPUT_FILENAME}")
