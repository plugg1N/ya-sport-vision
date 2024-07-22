import logging
import asyncio
import time
import subprocess
from datetime import datetime
import os

import aiofiles
import httpx
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Accept': '*/*',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

async def get_audio(filename: str) -> None:
    subprocess.run(f'ffmpeg -loglevel error -i "{filename}.ts" "{filename}.mp3"', shell=True)

async def concat_video(list_of_videos: list[str], video_id: str, path_to_video: str) -> str:
    videos = "|".join(list(sorted(list_of_videos)))
    name_video = r"{}\1tv_video_{}.mp4".format(path_to_video, video_id)
    subprocess.run('ffmpeg -i "concat:{}" -vcodec copy -acodec copy {}'.format(videos, name_video), shell=True)
    return name_video

async def a_get_video_part(link: str, index: int, session, video_id: str, path_to_video: str, retry=5):
    try:
        response = await session.get(
            f'{link}_,350,950,3800,8000,.mp4.urlset/seg-{index}-f1-v1-a1.ts',
            timeout=30.0
        )
        if response.status_code == 200:
            path = r"{}1tv_video_{}_seg{}.ts".format(path_to_video, video_id, index)
            dir_name = os.path.dirname(path)
            os.makedirs(dir_name, exist_ok=True)

            async with aiofiles.open(path, "wb") as f:
                await f.write(response.read())
            return path
    except (httpx.PoolTimeout, httpx.RemoteProtocolError):
        if retry == 0:
            return None
        await asyncio.sleep(10)
        return await a_get_video_part(link, index, session, video_id, path_to_video, retry-1)
    except Exception as e:
        return None

async def a_download_video(link: str, session, video_id: str, path_to_video: str):
    response = await session.get(
        f'{link}_,350,950,3800,8000,.mp4.urlset/index-f1-v1-a1.m3u8',
        headers=headers,
    )
    if response.status_code == 200:
        last_index = int(response.text.split("\n")[-3].split("-")[1])
        tasks = []
        prev_numb = 0
        for parts_of_calls in range(0, last_index+1, 80):
            if parts_of_calls == 0:
                continue
            tasks.extend(asyncio.create_task(a_get_video_part(link, index_of_part, session, video_id, path_to_video)) for index_of_part in
                         range(prev_numb+1, parts_of_calls+1))
            await asyncio.sleep(10)
            prev_numb = parts_of_calls
        if prev_numb < last_index:
            tasks.extend(asyncio.create_task(a_get_video_part(link, index_of_part, session, video_id, path_to_video)) for index_of_part in
                         range(prev_numb + 1, last_index + 1))
        ans = await asyncio.gather(*tasks)
        res = len(ans) - sum(1 for x in ans if x is None)
        paths = [x for x in ans if x is not None]
        return "success", res, paths
    return "error", 0, []


async def get_video_id(session, url: str) -> str:
    response = await session.get(
        url, follow_redirects=True
    )
    soup = await asyncio.get_running_loop().run_in_executor(None, BeautifulSoup, response.text, 'lxml')
    popup = soup.find(class_="popup hidden")
    content_id = popup.find(class_="content").get("data-content-id")
    return content_id


async def get_video_url(session, video_id: str) -> str:
    params = {
        'admin': 'false',
        'single': 'false',
        'sort': 'none',
        'video_id': video_id,
    }
    # print(params)
    response = await session.get('https://www.sport1tv.ru/playlist', params=params, follow_redirects=True)
    ans = response.json()
    lists_of_uids_of_videos = [data["uid"] for data in ans]
    temp = ans[lists_of_uids_of_videos.index(int(video_id))].get("mbr", "error")
    if temp == "error":
        return "error"
    back_of_link = temp[-1]["src"].split("/video/multibitrate/video/")[-1]
    back_of_link = "_".join(back_of_link.split("_")[:-1:])
    link = f"https://v1-dtln.1internet.tv/video/multibitrate/video/{back_of_link}"
    return link


async def get_video_first_tv(url: str, path_to_video="./videos") -> str | None:
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Accept': '*/*',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    # 'Referer': 'https://www.sport1tv.ru/',
    # 'Origin': 'https://www.sport1tv.ru',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    }
    async with httpx.AsyncClient(headers=headers) as session:
        video_id = await get_video_id(session, url)
        link = await get_video_url(session, video_id)
        if link == "error":
            return None
        status = await a_download_video(link, session, video_id, path_to_video)
        path_to_video = await concat_video(status[2], video_id, path_to_video)
        # return status[0], status[1], path_to_video
        return path_to_video


async def search_videos_first_tv(name: str) -> list[list[str, str]] | None:
    domen = "https://www.sport1tv.ru"

    async with httpx.AsyncClient(headers=headers) as session:
        response = await session.get(
            'https://www.sport1tv.ru/search.js?from=1995-01-01&amp;limit=10&amp;offset=0&amp;project_id=110887&amp;q=text%3A{} Полная видеозапись игры&amp;to={}'.format(name, datetime.now().strftime('%Y-%m-%d')),
            headers=headers,
            follow_redirects=True
        )
        logging.info(f"Status code: { response.status_code}")
        if response.status_code < 400:
            ans = response.text
            data = ans.split('append("')[-1].split('");')[0].split(r'href=\"')[1:]
            results: list[list[str, str]] = [[line.split(r'th-color-text-article\">')[-1].split('<')[0].replace(u'\xa0', u' '), domen+line.split('"')[0][:-1]] for line in data]
            return results
        else:
            print(response.status_code)
    return None


async def main():
    start = time.time()
    print(await search_videos_first_tv("Швеция"))
    print(time.time() - start)

if __name__ == "__main__":
    asyncio.run(get_video_first_tv('https://www.sport1tv.ru/sport/kubok-pervogo-kanala-po-hokkeyu/kubok-2020/tovarisheskiy-match-svyaz-pokoleniy-kubok-pervogo-kanala-po-hokkeyu'))
