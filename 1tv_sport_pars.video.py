import asyncio
import time
import subprocess

import aiofiles
import requests
import httpx
from bs4 import BeautifulSoup

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


async def get_audio(filename: str) -> None:
    subprocess.run(f'ffmpeg -loglevel error -i "{filename}.ts" "{filename}.mp3"', shell=True)


def get_video_part(index: int):
    try:
        response = requests.get(
            url=f"https://v1-dtln.1internet.tv/video/multibitrate/video/2023/12/16/b1d626ed-d910-4f3f-ad6c-7ea468e9195c_HD-news-2023_12_17-18_10_17_,350,950,3800,8000,.mp4.urlset/seg-{index}-f4-v1-a1.ts",
            headers=headers
        )
        if response.ok:
            with open(f"videos\\video_{index}.ts", "wb") as f:
                f.write(response.content)
            print(f"Часть {index} готова")
    except:
        print(f"Часть {index} пропущена")
        time.sleep(3)


def download_video():
    response = requests.get(url='https://v1-dtln.1internet.tv/video/multibitrate/video/2023/12/16/b1d626ed-d910-4f3f-ad6c-7ea468e9195c_HD-news-2023_12_17-18_10_17_,350,950,3800,8000,.mp4.urlset/index-f3-v1-a1.m3u8',
                            headers=headers)
    if response.ok:
        last_index = int(response.text.split("\n")[-3].split("-")[1])
        for index in range(1, last_index):
            get_video_part(index)
        return "success"

    else:
        return f"Error {response.status_code}"


async def a_get_video_part(link: str, index: int, session, video_id: str, retry=5):
    try:
        response = await session.get(
            f'{link}_,350,950,3800,8000,.mp4.urlset/seg-{index}-f1-v1-a1.ts',
            timeout=30.0
        )
        if response.status_code == 200:
            async with aiofiles.open(f"videos\\1tv_video_{video_id}_seg{index}.ts", "wb") as f:
                await f.write(response.read())
            await get_audio(f"videos\\1tv_video_{video_id}_seg{index}")
            return "success"
    except httpx.PoolTimeout and httpx.RemoteProtocolError:
        if retry == 0:
            # print("Код сдох")
            return "error"
        # print(retry, index)
        await asyncio.sleep(10)
        await a_get_video_part(link, index, session, video_id, retry-1)
    # except Exception as e:
    #     print(e)
    #     print("Всё легло")


async def a_download_video(link: str, session, video_id):
    response = await session.get(
        f'{link}_,350,950,3800,8000,.mp4.urlset/index-f1-v1-a1.m3u8',
        headers=headers,
    )
    if response.status_code == 200:
        last_index = int(response.text.split("\n")[-3].split("-")[1])
        tasks = []
        prev_numb = 0
        # print(last_index)
        for parts_of_calls in range(0, last_index+1, 80):
            if parts_of_calls == 0:
                continue
            tasks.extend(asyncio.create_task(a_get_video_part(link, index_of_part, session, video_id)) for index_of_part in
                         range(prev_numb+1, parts_of_calls+1))
            await asyncio.sleep(10)
            prev_numb = parts_of_calls
        if prev_numb < last_index:
            tasks.extend(asyncio.create_task(a_get_video_part(link, index_of_part, session, video_id)) for index_of_part in
                         range(prev_numb + 1, last_index + 1))
        ans = sum(map(lambda x: x == "success", await asyncio.gather(*tasks)))
        return "success", ans, len(tasks)


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
    back_of_link = ans[lists_of_uids_of_videos.index(int(video_id))]["mbr"][-1]["src"].split("/video/multibitrate/video/")[-1]
    back_of_link = "_".join(back_of_link.split("_")[:-1:])
    link = f"https://v1-dtln.1internet.tv/video/multibitrate/video/{back_of_link}"
    return link


async def get_video(url: str) -> tuple[str, int, str]:
    async with httpx.AsyncClient(headers=headers) as session:
        video_id = await get_video_id(session, url)
        link = await get_video_url(session, video_id)
        status = await a_download_video(link, session, video_id)
        return status[0], status[1], video_id


async def main():
    start = time.time()
    url = "https://www.1tv.ru/-/jjxqzo"
    print(await get_video(url))
    print(time.time() - start)


if __name__ == "__main__":
    asyncio.run(main())
# "https://v1-dtln.1internet.tv/video/multibitrate/video/2023/12/15/0bd9440f-7a65-4cb5-b399-132177de4aae_HD-news-2023_12_16-18_10_17_350.mp4.urlset/seg-1-f1-v1-a1.ts"
