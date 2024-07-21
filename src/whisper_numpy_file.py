import os
import psutil
import time
import numpy as np
from faster_whisper import WhisperModel
from scipy.io import wavfile
from scipy.signal import resample

# Setting the environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Model size
model_size = 'small'

# Initialize the model
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# Function to print system utilization
def print_system_utilization():
    # Get CPU utilization
    cpu_usage = psutil.cpu_percent(interval=1)
    # Get memory utilization
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    
    # Get the memory usage of the current process in MB
    process = psutil.Process(os.getpid())
    memory_usage_mb = process.memory_info().rss / (1024 * 1024)
    
    print(f"CPU Usage: {cpu_usage}%")
    print(f"Memory Usage: {memory_usage}%")
    print(f"Memory Usage of the program: {memory_usage_mb:.2f} MB")

def load_and_resample_wav(file_path, target_sample_rate=16000):
    # Read the WAV file
    sample_rate, data = wavfile.read(file_path)

    # If stereo, convert to mono by averaging the channels
    if len(data.shape) == 2:
        data = data.mean(axis=1)

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

    return sample_rate, data


# load the file and resample it to 16000
filepath = 'output.wav'
sample_rate, data = load_and_resample_wav(filepath)
print(f"Sample Rate: {sample_rate}")
print(f"Data Type: {data.dtype}")
print(f"Shape of Data: {data.shape}")
# Start transcribing and monitor system utilization
segments, info = model.transcribe(data, beam_size=5)

# Language confidence
print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

# Print the transcription
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

# Print system utilization after the transcription is done
print_system_utilization()
