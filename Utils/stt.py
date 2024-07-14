import torch

from io import BytesIO
from typing import List, Tuple

import warnings

import numpy as np
from pyannote.audio import Pipeline
from pydub import AudioSegment

import torch
import subprocess
import locale
from nemo.collections.asr.models import EncDecCTCModel

from nemo.collections.asr.modules.audio_preprocessing import (
    AudioToMelSpectrogramPreprocessor as NeMoAudioToMelSpectrogramPreprocessor)
import torchaudio
from nemo.collections.asr.parts.preprocessing.features import FilterbankFeaturesTA as NeMoFilterbankFeaturesTA

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



class GigaAMCTC:
    def __init__(self):
        locale.getpreferredencoding = lambda: "UTF-8"

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        config_path = "../CTC-config"

        model = EncDecCTCModel.from_config_file(f"{config_path}/ctc_model_config.yaml")
        ckpt = torch.load(f"{config_path}/ctc_model_weights.ckpt", map_location="cpu")
        model.load_state_dict(ckpt, strict=False)
        model.eval()

        self.model = model.to(device)


    def return_model(self):
        return self.model

    def audiosegment_to_numpy(self, audiosegment: AudioSegment) -> np.ndarray:
        """Convert AudioSegment to numpy array."""
        samples = np.array(audiosegment.get_array_of_samples())
        if audiosegment.channels == 2:
            samples = samples.reshape((-1, 2))

        samples = samples.astype(np.float32, order="C") / 32768.0
        return samples


    def segment_audio(
        self,
        audio_path: str,
        pipeline: Pipeline,
        max_duration: float = 1002.0,
        min_duration: float = 15.0,
        new_chunk_threshold: float = 0.2,
    ) -> Tuple[List[np.ndarray], List[List[float]]]:
        # Prepare audio for pyannote vad pipeline
        audio = AudioSegment.from_wav(audio_path)
        audio_bytes = BytesIO()
        audio.export(audio_bytes, format="wav")
        audio_bytes.seek(0)

        # Process audio with pipeline to obtain segments with speech activity
        sad_segments = pipeline({"uri": "filename", "audio": audio_bytes})

        segments = []
        curr_duration = 0
        curr_start = 0
        curr_end = 0
        boundaries = []

        # Concat segments from pipeline into chunks for asr according to max/min duration
        for segment in sad_segments.get_timeline().support():
            start = max(0, segment.start)
            end = min(len(audio) / 1000, segment.end)
            if (
                curr_duration > min_duration and start - curr_end > new_chunk_threshold
            ) or (curr_duration + (end - curr_end) > max_duration):
                audio_segment = self.audiosegment_to_numpy(
                    audio[curr_start * 1000 : curr_end * 1000]
                )
                segments.append(audio_segment)
                boundaries.append([curr_start, curr_end])
                curr_start = start

            curr_end = end
            curr_duration = curr_end - curr_start

        if curr_duration != 0:
            audio_segment = self.audiosegment_to_numpy(
                audio[curr_start * 1000 : curr_end * 1000]
            )
            segments.append(audio_segment)
            boundaries.append([curr_start, curr_end])

        return segments, boundaries



    # Any audio to mono channel and 16Khz
    def normalize_audio(self, audio_path: str) -> str:
        filename = audio_path.split(".")[0]

        subprocess.run(f'ffmpeg -i {audio_path} -ac 1 -ar 16000 {filename}.wav', shell=True)
        return f'{filename}.wav'


    # Run transcribation
    def speech_to_text(self, audio_path: str) -> str:
        torch.cuda.empty_cache()

        HF_TOKEN = "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"

        warnings.simplefilter("ignore")
        pipeline = Pipeline.from_pretrained(
        "pyannote/voice-activity-detection", use_auth_token=HF_TOKEN)
        pipeline = pipeline.to(torch.device(self.device))

        segments, _ = self.segment_audio(audio_path, pipeline)

        # Transcribing segments
        BATCH_SIZE = 2
        return self.model.transcribe(segments, batch_size=BATCH_SIZE)


