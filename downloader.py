import yt_dlp as youtube_dl
# import whisper
from pydub import AudioSegment
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


# Use whisper to translate
def audio_to_text(*, dest_name: str, model_name: str) -> str:
    model = whisper.load_model(model_name)
    result = model.transcribe(f'{dest_name}')
    return result["text"]


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=hWTvOa3vifU'

    get_audio(url)
    split_into_batches('audio.mp3')
