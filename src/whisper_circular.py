from circular_buffer import ComputerAudioStream
from faster_whisper import WhisperModel
import time
import os

##########################################################
# Whisper Section
##########################################################

# Setting the environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Model size
model_size = 'small'

# Initialize the model
model = WhisperModel(model_size, device="cpu", compute_type="int8")

##########################################################
# Circular buffer logic
##########################################################
CHUNK_FACTOR = 10 # How many chunks a second
DURATION = 5 # Seconds

with ComputerAudioStream(chunk_factor=CHUNK_FACTOR, duration=DURATION) as stream:
    while True:
        data = stream.get_current_buffer_resample(target_sr=16000)
        print(f"data shape: {data.shape}")
        
        # Start transcribing and monitor system utilization
        segments, info = model.transcribe(data, beam_size=5)

        # Language confidence
        if info.language_probability > 0.9:
            print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

            # Print the transcription
            
            for segment in segments:
                print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        