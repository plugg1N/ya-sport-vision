from youtube_transcript_api import YouTubeTranscriptApi
import re


# Extracting an id from url
def extracting_id(*, video_url: str) -> str:
    return video_url.partition("v=")[2]


# Extracting subtitles via api
def extracting_text(*, video_id: str) -> str:
    batch = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru'])
    extracting_data = []
    for i in range(len(batch)):
        extracting_data.append(batch[i]['text'])

    return ' '.join(extracting_data)


# Removing brackets and the text in them
def text_processing(*, text: str) -> str:
    clean_text = re.sub(r'\[.*?\]', '', text)
    return clean_text


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=M90JoLZgIlc'

    print(text_processing(text=extracting_text(video_id=extracting_id(video_url=url))))
