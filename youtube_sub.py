from youtube_transcript_api import YouTubeTranscriptApi
import re


class YoutubeTranscribe:
    # Extracting an id from url
    def __extracting_id(self, *, video_url: str) -> str:
        return video_url.partition("v=")[2]


    # Extracting subtitles via api
    def __extracting_text(self, *, video_id: str) -> str:
        batch = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru'])
        extracting_data = []
        for i in range(len(batch)):
            extracting_data.append(batch[i]['text'])

        return ' '.join(extracting_data)


    # Removing brackets and the text in them
    def __text_processing(self, *, text: str) -> str:
        clean_text = re.sub(r'\[.*?\]', '', text)
        return clean_text
    

    # Get subtitles of the video
    def process_url(self, *, link: str) -> str:
        return self.__text_processing(text=self.__extracting_text(video_id=self.__extracting_id(video_url=link)))
