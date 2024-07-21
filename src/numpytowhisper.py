import sys
import pyaudio
import numpy as np
from . import load_model
from .transcribe import transcribe
from .utils import write_txt

import whisper

RATE = 16000
CHUNK_SIZE = 16000*5
FORMAT = pyaudio.paInt16
FORMATOUT = pyaudio.paInt16

def test():
    model = whisper.load_model("base")
    
    p = pyaudio.PyAudio()
    
    streamIn = p.open(
        format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE
    )
    while True:
        data = streamIn.read(CHUNK_SIZE)
        audio = np.frombuffer(data, np.int16).astype(np.float32)*(1/32768.0)

        # load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio("output.wav")
        audio = whisper.pad_or_trim(audio)

        # make log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # detect the spoken language
        _, probs = model.detect_language(mel)
        print(f"Detected language: {max(probs, key=probs.get)}")

        # decode the audio
        options = whisper.DecodingOptions(fp16=False)
        result = whisper.decode(model, mel, options)

        # print the recognized text
        print(result.text)
