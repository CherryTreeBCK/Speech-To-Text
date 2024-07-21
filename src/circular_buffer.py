import pyaudiowpatch as pyaudio
import numpy as np
import collections
from scipy.signal import resample
from pydub import AudioSegment

class ComputerAudioStream:
    """Opens a recording stream and keeps the last few seconds of audio data."""
    def __init__(self, chunk, duration):
        self._chunk = chunk
        self._duration = duration
        self._buff = collections.deque()  # Buffer initialized empty
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        try:
            self.wasapi_info = self._audio_interface.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("WASAPI not available. Exiting...")
            exit()
        
        default_speakers = self.get_default_speakers()
        self._rate = int(default_speakers["defaultSampleRate"])
        self._channels = default_speakers["maxInputChannels"]
        self._buff = collections.deque(maxlen=int(self._duration * self._rate * self._channels))
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
            channels=self._channels,
            rate=self._rate,
            frames_per_buffer=self._chunk,
            input=True,
            input_device_index=default_speakers["index"],
            stream_callback=self._fill_buffer,
        )

    def get_current_buffer(self, duration=None):
        """Returns the current contents of the buffer. If duration is specified, returns the last `duration` seconds of audio."""
        if duration is None:
            return np.array(self._buff)
        
        num_samples = int(duration * self._rate * self._channels)
        if num_samples > len(self._buff):
            num_samples = len(self._buff)
        
        return np.array(self._buff)[-num_samples:]
        
    def get_current_buffer_resample(self, duration=None, target_sample_rate=16000):
        sample_rate = self._rate
        data = self.get_current_buffer(duration=duration)

        # Reshape data to two channels if stereo
        if self._channels > 1:
            data = data.reshape(-1, self._channels)
            data = data.mean(axis=1)  # Convert to mono by averaging channels
            
        data = data.flatten()

        # Convert to float32
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0  # int16 range is -32768 to 32767
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0  # int32 range is -2147483648 to 2147483647
        else:
            data = data.astype(np.float32)

        # Resample the data to the target sample rate
        if sample_rate != target_sample_rate:
            number_of_samples = round(len(data) * float(target_sample_rate) / sample_rate)
            data = resample(data, number_of_samples)
            sample_rate = target_sample_rate

        return data

# Example usage:
if __name__ == "__main__":
    CHUNK_FACTOR = 5 # How many chunks a second
    DURATION = 5 # Seconds
    OUTPUT_FILENAME = "output.mp3"

    with ComputerAudioStream(chunk=int(48000 / CHUNK_FACTOR), duration=DURATION) as stream:
        import time
        for _ in range(int(stream._rate / stream._chunk * DURATION)):
            time.sleep(stream._chunk / stream._rate)
            audio_chunk = stream.get_current_buffer_resample()
            print(f"Full buffer: {audio_chunk}")
            short_chunk = stream.get_current_buffer(5)  # Last 5 seconds
            print(f"Last 5 seconds: {short_chunk}")

        # Save the last DURATION seconds of audio to an MP3 file
        final_audio = stream.get_current_buffer(5)
        
        print(final_audio.shape)
        
        # Convert the numpy array to an AudioSegment
        audio_segment = AudioSegment(
            final_audio.tobytes(),
            frame_rate=stream._rate,
            sample_width=final_audio.dtype.itemsize,
            channels=stream._channels
        )

        # Export the audio segment as an MP3 file
        audio_segment.export(OUTPUT_FILENAME, format="mp3")

        print(f"Audio saved to {OUTPUT_FILENAME}")
