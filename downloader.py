from Utils.youtube_sub import YoutubeTranscribe # YT subtitle getter
from Utils.stt import Whisper                   # Our stt
from Utils.audio_dp import AudioDispatcher      # Batch splitter


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=pqaBWcsBGyA'

    stt = Whisper('base')
    yt = YoutubeTranscribe()
    adp = AudioDispatcher()

    # adp.split_into_batches(link=url)
    print(stt.speech_to_text('audio.mp3'))

    # try:
    #     print(yt.process_url(link=url))

    # except:
    #     adp.split_into_batches(link=url)
    #     print(stt.speech_to_text('audio.mp3'))



