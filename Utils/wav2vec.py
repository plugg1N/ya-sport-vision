from transformers import AutoModelForCTC, Wav2Vec2Processor
from typing import List, Any
import librosa
import torch


class Wav2Vec:
    def __init__(self):
        self.model = AutoModelForCTC.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-russian")  # .to("cuda")
        self.processor = Wav2Vec2Processor.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-russian")  # , device="cuda"


    # Analise audio file
    def _librosa_audio(self, *, audio_file: str) -> list[Any]:
        audio, _ = librosa.load(audio_file, sr=16000)
        audio = list(audio)
        return audio


    # Use wav2vec2 model to translate
    def speech_to_text(self, *, audio_file: str) -> str:
        with torch.no_grad():
            input_values = torch.tensor(self._librosa_audio(audio_file=audio_file)).unsqueeze(0)  #, device="cuda
            logins_model = self.model(input_values).logits
        pred_ids = torch.argmax(logins_model, dim=-1)
        batch = self.processor.batch_decode(pred_ids)[0]
        return batch
