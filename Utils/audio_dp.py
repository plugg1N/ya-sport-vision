import yt_dlp as youtube_dl
from pydub import AudioSegment
import subprocess
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
    def split_into_batches(self, link: str, *, overlap_ms: int, batches_am: int = 20) -> None:
        self.__get_audio(link=link)

        if not os.path.exists('segments'):
            os.mkdir('./segments')

        if not os.path.exists('temp00'):
            os.mkdir('./temp00')
            
        audio = AudioSegment.from_file('audio.mp3')

        chunk_size = int(librosa.get_duration(path='audio.mp3')) * 1000 // batches_am  # in milliseconds
        overlap = overlap_ms                                                           # in milliseconds

        start, end = 0, chunk_size

        num_chunks = (len(audio) - overlap) // (chunk_size - overlap)

        for i in range(num_chunks):
            start = i * (chunk_size - overlap)
            end = start + chunk_size

            chunk = audio[start:end]

            full_path = os.path.join('temp00', f"chunk_{i}.wav")
            new_path = os.path.join('segments', f"chunk_{i}.wav")

            chunk.export(full_path, format="wav")
            subprocess.run(f'ffmpeg -i "{full_path}" -ac 1 -ar 16000 "{new_path}"', shell=True)

        subprocess.run(f'rm -rf temp00/', shell=True)
