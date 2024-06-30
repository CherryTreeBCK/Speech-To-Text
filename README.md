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
- Change whisper-gui.py to use a numpy buffer instead of a temp file
    - Use circular buffer, overwrite the buffer such that it always has the last 5 seconds of audio.
    - Currently, whisper-gui has a delay due to the 5 second temp file buffer. Real time is the goal.
