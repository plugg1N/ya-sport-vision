import yt_dlp as youtube_dl
from pydub import AudioSegment
import librosa
import os


class AudioDispatcher:
    # Download a video from YouTube
    def __get_audio(self, *, link: str) -> None:
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


    # Split into batches
    def split_into_batches(self, *, link: str) -> None:
        self.__get_audio(link=link)
        os.mkdir('segments')

        audio = AudioSegment.from_file('audio.mp3')

        chunk_size = int(librosa.get_duration(path='audio.mp3')) * 100  # in milliseconds
        overlap = 2000                                           # in milliseconds

        start, end = 0, chunk_size

        num_chunks = (len(audio) - overlap) // (chunk_size - overlap)

        for i in range(num_chunks):
            start = i * (chunk_size - overlap)
            end = start + chunk_size

            chunk = audio[start:end]
            chunk.export(os.path.join('segments', f"chunk_{i}.wav"), format="wav")