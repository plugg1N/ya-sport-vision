from Utils.youtube_sub import YoutubeTranscribe
from Utils.wav2vec import Wav2Vec
from Utils.audio_dp import AudioDispatcher


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=hn3zaQJd_hk'

    stt = Wav2Vec()
    yt = YoutubeTranscribe()
    adp = AudioDispatcher()

    try:
        yt.process_url(link=url)

    except:
        adp.split_into_batches(link=url)
        stt.speech_to_text('audio.mp3')

