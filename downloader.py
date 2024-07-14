from Utils.youtube_sub import YoutubeTranscribe # YT subtitle gette0
from Utils.stt_test import GigaAMCTC                 # STT
from Utils.audio_dp import AudioDispatcher      # Batch splitter

from Utils.preprocessors.audio_to_mel import AudioToMelSpectrogramPreprocessor
from Utils.preprocessors.filterbank_features import FilterbankFeaturesTA

import warnings
warnings.simplefilter("ignore")


if __name__ == '__main__':
    print(GigaAMCTC().speech_to_text('Utils/segments/chunk_1.wav'))
