from pytube import YouTube

url = 'https://www.youtube.com/watch?v=FByWlLb14gI'

def youtube_video_downloader(video_url):

    youtube_video = YouTube(video_url)
    stream_number = 0
    streaminfo = youtube_video.streams.filter(file_extension='mp4')

    for s in streaminfo:
        if 'itag="22"' in str(s):
            stream_number = 22
        elif 'itag="18"' in str(s):
            stream_number = 18
    
    stream = youtube_video.streams.get_by_itag(stream_number)
    stream.download('E:/',filename='downloadedvideo.mp4',timeout=12000)

youtube_video_downloader(url)