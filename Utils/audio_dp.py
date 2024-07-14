import yt_dlp as youtube_dl
from pytube import YouTube
import subprocess


class AudioDispatcher:
    # Download a video from YouTube using yt_dl
    def dl_get_audio(self, *, link: str) -> None:
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


    # Download a video from YouTube using yt_dl
    def tube_get_audio(self, *, link: str) -> None:
        youtube_video = YouTube(link)
        stream_number = 0
        streaminfo = youtube_video.streams.filter(file_extension='mp4')

        for s in streaminfo:
            if 'itag="22"' in str(s):
                stream_number = 22
            elif 'itag="18"' in str(s):
                stream_number = 18

        stream = youtube_video.streams.get_by_itag(stream_number)
        stream.download(filename='video.mp4', timeout=12000)

        subprocess.run(f'ffmpeg -loglevel error -i "video.mp4" "audio.mp3"',shell=True)



    def split_into_batches(self, *, file_name: str, overlap_s: int, chunk_length: int = 20) -> None:
        subprocess.run(f'./chunking {file_name} {overlap_s} {chunk_length}', shell=True)

