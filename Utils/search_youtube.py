from youtubesearchpython import VideosSearch


def time_to_minutes(*, time: str) -> int:
    time_list = time.split(':')
    if len(time_list) == 3:
        hours, minutes, seconds = map(int, time_list)
        total_minutes = hours * 60 + minutes
    elif len(time_list) == 2:
        minutes, sec = map(int, time_list)
        total_minutes = minutes
    else:
        total_minutes = 0
    return total_minutes


async def search_youtube(*, question: str, limit: int) -> list[list[str]]:
    videos_search = VideosSearch(question + "профессиональный спорт ролная запись игры", limit=limit)
    video = videos_search.result()
    search = []
    ret_search = []
    for word in video['result']:
        duration = word['duration']
        if time_to_minutes(time=duration) > 20:
            search.append(word['id'])
            search.append(word['title'])
            search.append(word['duration'])
            search.append(word['thumbnails'][0]['url'])
            search.append(word['link'])
            ret_search.append(search)
            search = []
    return ret_search
