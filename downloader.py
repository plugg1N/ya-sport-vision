from Utils.youtube_sub import YoutubeTranscribe # YT subtitle getter
from Utils.stt import Whisper                   # Our stt
from Utils.audio_dp import AudioDispatcher      # Batch splitter


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=hn3zaQJd_hk'

    stt = Whisper()
    yt = YoutubeTranscribe()
    adp = AudioDispatcher()

    try:
        print(yt.process_url(link=url))

    except:
        adp.split_into_batches(link=url)
        print(stt.speech_to_text('audio.mp3', model_name='base'))

