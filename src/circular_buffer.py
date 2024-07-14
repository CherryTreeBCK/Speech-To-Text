import pyaudio
import numpy as np
import wave
import collections

RATE = 44100
CHUNK_FACTOR = 5
CHUNK = int(RATE / CHUNK_FACTOR)  # RATE / number of updates per second
DURATION = 5  # IN SECONDS
DEQUE_LEN = DURATION * RATE
OUTPUT_FILENAME = "output.wav"

audio_dq = collections.deque(maxlen=DEQUE_LEN)

def soundplot(stream):
    data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    audio_dq.extend(data)
    return audio_dq

if __name__ == "__main__":
    p = pyaudio.PyAudio()

    # List all audio input devices
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"{i}: {dev['name']}")

    stream = p.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("Recording...")
    for i in range(int(RATE / CHUNK * DURATION)):
        audio_dq = soundplot(stream)
    
    print("Finished recording")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save to WAV file
    wf = wave.open(OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(np.array(audio_dq).tobytes())
    wf.close()

    print(f"Audio saved to {OUTPUT_FILENAME}")
