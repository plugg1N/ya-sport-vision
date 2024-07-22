from Utils.youtube_sub import YoutubeTranscribe # YT subtitle gette0
from Utils.audio_dp import AudioDispatcher      # Batch splitter

import warnings
warnings.simplefilter("ignore")


if __name__ == '__main__':
    adp = AudioDispatcher()
    adp.dl_get_audio(link='https://www.youtube.com/watch?v=gz79_r7v9mc')


