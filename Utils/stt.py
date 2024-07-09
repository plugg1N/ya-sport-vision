import whisper
import torch

import torch
import subprocess
import locale
from nemo.collections.asr.models import EncDecCTCModel

import torchaudio
from nemo.collections.asr.modules.audio_preprocessing import (
    AudioToMelSpectrogramPreprocessor as NeMoAudioToMelSpectrogramPreprocessor)
from nemo.collections.asr.parts.preprocessing.features import (
    FilterbankFeaturesTA as NeMoFilterbankFeaturesTA)


class FilterbankFeaturesTA(NeMoFilterbankFeaturesTA):
    def __init__(self, mel_scale: str = "htk", wkwargs=None, **kwargs):
        if "window_size" in kwargs:
            del kwargs["window_size"]
        if "window_stride" in kwargs:
            del kwargs["window_stride"]

        super().__init__(**kwargs)

        self._mel_spec_extractor: torchaudio.transforms.MelSpectrogram = (
            torchaudio.transforms.MelSpectrogram(
                sample_rate=self._sample_rate,
                win_length=self.win_length,
                hop_length=self.hop_length,
                n_mels=kwargs["nfilt"],
                window_fn=self.torch_windows[kwargs["window"]],
                mel_scale=mel_scale,
                norm=kwargs["mel_norm"],
                n_fft=kwargs["n_fft"],
                f_max=kwargs.get("highfreq", None),
                f_min=kwargs.get("lowfreq", 0),
                wkwargs=wkwargs,
            )
        )


class AudioToMelSpectrogramPreprocessor(NeMoAudioToMelSpectrogramPreprocessor):
    def __init__(self, mel_scale: str = "htk", **kwargs):
        super().__init__(**kwargs)
        kwargs["nfilt"] = kwargs["features"]
        del kwargs["features"]
        self.featurizer = (
            FilterbankFeaturesTA(  # Deprecated arguments; kept for config compatibility
                mel_scale=mel_scale,
                **kwargs,
            )
        )




class Whisper:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = whisper.load_model(self.model_name, device='cuda')
        print('Model loaded')


    # Transcribe
    def speech_to_text(self, path: str) -> str:
        result = self.model.transcribe(f'{path}')
        return result["text"]
    


class GigaAMCTC:
    def __init__(self):
        locale.getpreferredencoding = lambda: "UTF-8"

        device = "cuda" if torch.cuda.is_available() else "cpu"
        config_path = 'CTC-config'

        model = EncDecCTCModel.from_config_file(f"{config_path}/ctc_model_config.yaml")
        ckpt = torch.load(f"{config_path}/ctc_model_weights.ckpt", map_location="cpu")
        model.load_state_dict(ckpt, strict=False)
        model.eval()

        self.model = model.to(device)


    # Any audio to mono channel and 96Khz
    def __normalize_audio(self, audio_path: str) -> str:
        filename = audio_path.split(".")[0]

        subprocess.run(f'ffmpeg -i {audio_path} -ac 1 -ar 16000 {filename}.wav', shell=True)
        return f'{filename}.wav'


    # Run transcribation
    def speech_to_text(self, audio_path: str) -> str:
        path = self.__normalize_audio(audio_path)

        torch.cuda.empty_cache()
        return self.model.transcribe([path])


stt = GigaAMCTC()
print(stt.speech_to_text('videoplayback.m4a'))