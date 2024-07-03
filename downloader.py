import yt_dlp as youtube_dl
import whisper
import os

# Generate .mp3 file from .mp4 file
def get_audio() -> None:
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    yt_url = "https://www.youtube.com/watch?v=M90JoLZgIlc"

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt_url])


# Use whisper to translate
def audio_to_text(*, dest_name: str, model_name: str) -> str:
    model = whisper.load_model(model_name)
    result = model.transcribe(f'{dest_name}.mp3')
    return result["text"]



if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=M90JoLZgIlc'


    # get_audio()
    # youtube_video_downloader(video_url=url, output_filename='#1')
    # print('Video loaded')
    # get_audio(filename='#1', output_filename='#1_audio')
    audio_to_text(dest_name='hello', model_name='base')
    # print('Audio received')
    # os.remove('#1.mp4')
    # print(audio_to_text(model_name='medium', dest_name='#1_audio'))
