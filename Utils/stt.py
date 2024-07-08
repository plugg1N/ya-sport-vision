from transformers import AutoModelForCTC, Wav2Vec2Processor
from typing import List, Any
import whisper
import librosa
import torch


class Whisper:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = whisper.load_model(self.model_name, device='cuda')
        print('Model loaded')


    def speech_to_text(self, /, path: str) -> str:
        result = self.model.transcribe(f'{path}')
        return result["text"]