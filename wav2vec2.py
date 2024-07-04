from typing import List, Any

from transformers import AutoModelForCTC, Wav2Vec2Processor
import librosa
import torch


# Analise audio file
def librosa_audio(*, audio_file: str) -> list[Any]:
    audio, _ = librosa.load(audio_file, sr=16000)
    audio = list(audio)
    return audio


# Use wav2vec2 model to translate
def speech_to_text(*, audio_file: str) -> str:
    with torch.no_grad():
        input_values = torch.tensor(librosa_audio(audio_file=audio_file)).unsqueeze(0)  #, device="cuda
        logins_model = model(input_values).logits
    pred_ids = torch.argmax(logins_model, dim=-1)
    batch = processor.batch_decode(pred_ids)[0]
    return batch


if __name__ == '__main__':
    model = AutoModelForCTC.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-russian")  # .to("cuda")
    processor = Wav2Vec2Processor.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-russian")  # , device="cuda"

    filename = 'input_audio.wav'

    print(speech_to_text(audio_file=filename))
