import yt_dlp as youtube_dl
from pytube import YouTube
import re
import subprocess
import asyncio


class AudioDispatcher:
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


def dl_get_audio(link: str) -> str:
        video_id_match = re.search(r"(?:v=|\/|\.be\/|\/embed\/|\/live\/)([0-9A-Za-z_-]{11})", link)
        if not video_id_match:
            raise ValueError("Invalid YouTube URL")
        video_id = video_id_match.group(1)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'./audio_{video_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': '~/cookies.txt',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'timeout': 6000,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        return f'./audio_{video_id}.mp3'


def get_audio(link: str) -> str:
    try:
        path = dl_get_audio(link)
    except Exception as e:
        print(e)
        path = get_audio(link)
    finally:
        return path


if __name__ == '__main__':
    adp = AudioDispatcher()

    test_link = "https://www.youtube.com/live/M90JoLZgIlc?si=rmbzRZ_jkjbBcQCe"
    audio_path = get_audio(link=test_link)
    print(f"Audio downloaded and extracted using dl_get_audio. Saved to {audio_path}")
