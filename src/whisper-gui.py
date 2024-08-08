from threading import Thread
from gui import GUI
from faster_whisper import WhisperModel
import os
from circular_buffer import ComputerAudioStream  # Import the circular buffer class

#######################
# Whisper Setup
#######################
# Setting the environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Model size
model_size = 'small'
# Initialize the model
model = WhisperModel(model_size, device="cpu", compute_type="int8")
LANG_THRESHOLD = 0.9 # Helps ensure the confidence is high

def speech_recognition_thread(gui_queue):
    CHUNK_FACTOR = 20  # How many chunks a second
    DURATION =  5 # Seconds

    with ComputerAudioStream(chunk_factor=CHUNK_FACTOR, duration=DURATION) as stream:
        while True:
            # Get the current buffer, resampled to 16kHz
            data = stream.get_current_buffer_resample(target_sr=16000)
            # print(f"data shape: {data.shape}")

            # Transcribe the audio data using the Whisper model
            segments, info = model.transcribe(data, beam_size=5)

            # Check if the detected language probability is above the threshold
            if info.language_probability > LANG_THRESHOLD:
                print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

                # Send the transcription segments to the GUI queue
                for segment in segments:
                    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
                    gui_queue.put(segment.text)

def main():
    gui = GUI()
    Thread(target=speech_recognition_thread, args=(gui.queue,), daemon=True).start()
    gui.run()

if __name__ == "__main__":
    main()
