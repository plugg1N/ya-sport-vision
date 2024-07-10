from youtubesearchpython import VideosSearch


def search_youtube(*, question: str, limit: int) -> list[list]:
    videos_search = VideosSearch(question, limit=limit)
    video = videos_search.result()
    search = []
    ret_search = []

    for word in video['result']:
        search.append(word['id'])
        search.append(word['title'])
        search.append(word['duration'])
        search.append(word['thumbnails'][0]['url'])
        search.append(word['link'])

        ret_search.append(search)
        search = []

    return ret_search
