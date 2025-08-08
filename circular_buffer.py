import pyaudiowpatch as pyaudio
import numpy as np
import librosa
from pydub import AudioSegment

class ComputerAudioStream:
    """Opens a recording stream and keeps the last few seconds of audio data."""
    def __init__(self, chunk_factor, duration):
        self._chunk_factor = chunk_factor
        self._duration = duration
        self._rate = 48000
        self._channels = 2
        self._buff = np.zeros(int(5 * self._rate * self._channels), dtype=np.int16)  # Buffer size for 5 seconds
        self.closed = True
        self._write_index = 0

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
        self._chunk = int(self._rate / self._chunk_factor)
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
        num_samples = data.shape[0]

        # Write new data to the buffer
        self._buff[self._write_index:self._write_index + num_samples] = data

        # Update the write index, wrapping around if necessary
        self._write_index = (self._write_index + num_samples) % self._buff.size

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

    def get_current_buffer(self, duration=5):
        """Returns the last `duration` seconds of audio data."""
        num_samples = int(self._rate * self._channels * duration)
        if num_samples > self._buff.size:
            num_samples = self._buff.size

        # Get the data starting from the write index
        if self._write_index >= num_samples:
            data = self._buff[self._write_index - num_samples:self._write_index]
        else:
            data = np.concatenate((self._buff[self._write_index - num_samples:], self._buff[:self._write_index]))

        return data

    def get_current_buffer_resample(self, duration=5, target_sr=16000):
        data = self.get_current_buffer(duration=duration)

        # Use librosa to resample the audio
        if self._channels > 1:
            data = data.reshape(-1, self._channels).mean(axis=1)
        data_float32 = data.astype(np.float32) / 32768.0  # Convert to float32

        # In-place resampling
        resampled_data = librosa.resample(data_float32, orig_sr=self._rate, target_sr=target_sr)

        return resampled_data


# Example usage:
if __name__ == "__main__":
    CHUNK_FACTOR = 5  # How many chunks a second
    DURATION = 5  # Seconds

    with ComputerAudioStream(chunk_factor=CHUNK_FACTOR, duration=DURATION) as stream:
        import time
        print("Recording audio...")
        time.sleep(DURATION)
        print("Recording stopped.")

        # Save the last DURATION seconds of audio to an MP3 file
        data = stream.get_current_buffer()

        print(data.shape)

        # Convert the numpy array to an AudioSegment
        audio_segment_og = AudioSegment(
            data.tobytes(),
            frame_rate=stream._rate,
            sample_width=data.dtype.itemsize,
            channels=stream._channels
        )
        
        print("Using librosa to resample the audio...")
        
        # Use librosa to resample the audio
        resampled_data = stream.get_current_buffer_resample(target_sr=16000)
        resampled_data_int16 = (resampled_data * 32768).astype(np.int16)  # Convert back to int16

        # Convert the resampled numpy array to an AudioSegment
        audio_segment_resample = AudioSegment(
            resampled_data_int16.tobytes(),
            frame_rate=16000,
            sample_width=resampled_data_int16.dtype.itemsize,
            channels=1
        )
        print("Audio resampled successfully.")

        # Export the audio segment as an MP3 file
        audio_segment_og.export("output_original.mp3", format="mp3")
        audio_segment_resample.export("output_resample.mp3", format="mp3")
