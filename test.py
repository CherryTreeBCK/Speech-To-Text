import os
import psutil
import time
from faster_whisper import WhisperModel

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

# Start transcribing and monitor system utilization
segments, info = model.transcribe("Rev.mp3", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

# Print system utilization after the transcription is done
print_system_utilization()
