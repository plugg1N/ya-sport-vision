from io import BytesIO
from typing import List
import os
from typing import List, Tuple
import numpy as np
from pyannote.audio import Pipeline
from pydub import AudioSegment
import torch
import locale
from nemo.collections.asr.models import EncDecCTCModel


from speechkit import model_repository, configure_credentials, creds
from speechkit.stt import AudioProcessingType


class YaSpeechKit:
    def __init__(self, api_key: str):
        configure_credentials(yandex_credentials=creds.YandexCredentials(
            api_key=api_key)
        )
        print('<log> Speech kit initialized.')



    def speech_to_text(self, audio_path: str):
        model = model_repository.recognition_model()

        model.model = 'general'
        model.language = 'ru-RU'
        model.audio_processing_type = AudioProcessingType.Full


        result = model.transcribe_file(audio_path)
        for _, res in enumerate(result):
            if res.has_utterances():
                for utterance in res.utterances:
                    yield str(utterance)




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
        max_duration: float = 300.0,
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


    # Run transcribation
    def speech_to_text(self, audio_path: str) -> str:
        torch.cuda.empty_cache()

        HF_TOKEN = "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"

        pipeline = Pipeline.from_pretrained(
        "pyannote/voice-activity-detection", use_auth_token=HF_TOKEN)
        pipeline = pipeline.to(torch.device(self.device))

        segments, _ = self.segment_audio(audio_path, pipeline)

        # Transcribing segments
        BATCH_SIZE = 2
        return self.model.transcribe(segments, batch_size=BATCH_SIZE)




if __name__ == '__main__':
#    print(GigaAMCTC().speech_to_text('./segments/chunk_3.wav'))
    print(YaSpeechKit('AQVN3NvPmtiUySQUR27b_CLg_6swX-6PBCE1sPdm').speech_to_text('./chunk_1.wav'))
