from pytube import YouTube
import subprocess
import whisper
import os

# Generate .mp3 file from .mp4 file
def get_audio(*, filename: str, output_filename: str) -> None:
    subprocess.run(f'ffmpeg -loglevel error -i "{filename}.mp4" "{output_filename}.mp3"',shell=True)


# Use whisper to translate
def audio_to_text(*, dest_name: str, model_name: str) -> str:
    model = whisper.load_model(model_name)
    result = model.transcribe(f'{dest_name}.mp3')
    return result["text"]


# Download video from YouTube 
def youtube_video_downloader(*, video_url: str, output_filename: str):
    youtube_video = YouTube(video_url)
    stream_number = 0
    streaminfo = youtube_video.streams.filter(file_extension='mp4')

    for s in streaminfo:
        if 'itag="22"' in str(s):
            stream_number = 22
        elif 'itag="18"' in str(s):
            stream_number = 18

    stream = youtube_video.streams.get_by_itag(stream_number)
    stream.download(filename=f'{output_filename}.mp4',timeout=12000)



if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=1aA1WGON49E'

    youtube_video_downloader(video_url=url, output_filename='#1')
    get_audio(filename='#1', output_filename='#1_audio')
    os.remove('#1.mp4')
    print(audio_to_text(model_name='medium', dest_name='#1_audio'))
