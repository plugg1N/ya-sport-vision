import yt_dlp as youtube_dl
from youtube_sub import YoutubeTranscribe
# import whisper
from pydub import AudioSegment
from wav2vec import Wav2Vec
import librosa
import os


# Split an audio into separate batches
def split_into_batches(path: str) -> None:
    audio = AudioSegment.from_file(path)

    chunk_size = int(librosa.get_duration(path=path)) * 100  # in milliseconds
    overlap = 2000                                           # in milliseconds

    start, end = 0, chunk_size

    num_chunks = (len(audio) - overlap) // (chunk_size - overlap)

    for i in range(num_chunks):
        start = i * (chunk_size - overlap)
        end = start + chunk_size

        chunk = audio[start:end]
        chunk.export(os.path.join('segments', f"chunk_{i}.wav"), format="wav")


# Generate .mp3 file from .mp4 file
def get_audio(link: str) -> None:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': './audio',

        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])




if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=hn3zaQJd_hk'
    stt = Wav2Vec()
    yt = YoutubeTranscribe()

    try:
        yt.process_url(link=url)

    except:
        get_audio(link=url)
        

