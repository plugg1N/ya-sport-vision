import yt_dlp as youtube_dl
import whisper
import os

# Generate .mp3 file from .mp4 file
def get_audio(link: str) -> None:
    ydl_opts = {
        'format': 'bestaudio/best',
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
    result = model.transcribe(f'{dest_name}.mp3')
    return result["text"]



if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=M90JoLZgIlc'
    
