# Speech To Text Overlay Program


## gui.py
Simple graphic program that displays the provided text

## google-speech-gui.py
Using Google's sophisticated speech-to-text API and gui.py, we can transcribe 
audio in real time from the computer's audio. This is extremely helpful when 
subtitles aren't naturally included.

## whisper-gui.py
The issue with Google's API is that it requires a Google Account, a 
decent amount of local setup, and a constant internet connection. The goal of 
using Whisper is to have real-time, local transcription without any setup!


# To-Do:
- Circular buffer works for stereo audio when saving to a file, but does not work
when using whisper circular. This is likely due to the fact that stereo audio is 
treated as a single channel in circular buffer, causing the program to think it
is twice as long as it actually is (since it's the same audio right after itself).
    - Double check sampling rates, make more modular.
- Change whisper-gui.py to use a numpy buffer
    - Use circular buffer, overwrite the buffer such that it always has the last 5 seconds of audio.
    - Currently, whisper-gui has a delay due to the 5 second temp file buffer. Real time is the goal.
    - Using hugging face 
- Circular buffer initializer should use chunk factor instead of chunk size because we do not know the rate.


