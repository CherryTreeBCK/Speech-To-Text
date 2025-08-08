from threading import Thread
from gui import GUI
from faster_whisper import WhisperModel
import os
from circular_buffer import ComputerAudioStream  # Import the circular buffer class
from googletrans import Translator
import re
import config

translator = Translator()
#######################
# Whisper Setup
#######################
# Setting the environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Model size
model_size = 'tiny'
TRANSLATE = config.TRANSLATE
# Initialize the model
model = WhisperModel(model_size, device="cpu", compute_type="int8")
LANG_THRESHOLD = 0.9 # Helps ensure the confidence is high

def speech_recognition_thread(gui_queue):
    CHUNK_FACTOR = 10 # How many chunks a second
    DURATION = 3 # Seconds

    with ComputerAudioStream(chunk_factor=CHUNK_FACTOR, duration=DURATION) as stream:
        while True:
            # Get the current buffer, resampled to 16kHz
            data = stream.get_current_buffer_resample(target_sr=16000)
            # print(f"data shape: {data.shape}")

            # Transcribe the audio data using the Whisper model
            segments, info = model.transcribe(
                data,
                beam_size=5,
                condition_on_previous_text=True,
            )

            if info.language_probability > LANG_THRESHOLD:
                print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

                for segment in segments:
                    cleaned_text = segment.text.strip(",. ").strip()
                    if cleaned_text == "":
                        continue
                    if not re.search(r'[가-힣a-zA-Z0-9]', cleaned_text):
                        continue

                    if TRANSLATE and info.language != config.LANGUAGE:
                        try:
                            translation = translator.translate(segment.text, src=info.language, dest=config.LANGUAGE)
                            translated_text = translation.text
                        except Exception as e:
                            print(f"Translation failed: {e}")
                            translated_text = "(Translation Error)"
                        display_text = translated_text
                    else:
                        display_text = segment.text

                    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {display_text}")
                    gui_queue.put(display_text)

def main():
    gui = GUI()
    Thread(target=speech_recognition_thread, args=(gui.queue,), daemon=True).start()
    gui.run()

if __name__ == "__main__":
    main()
