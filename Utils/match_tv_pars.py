from time import time
from datetime import datetime, timedelta
import asyncio
import aiofiles
import os

from bs4 import BeautifulSoup
import httpx
import subprocess


start = time()


async def get_video_link(page_link: str) -> str:
    try:
        cookies = {
            'spbc_uuid': 'b6bc2c3a-14ba-4ec1-b98c-a51f4cb7ea60',
            'spbc_uuid_recreated': '1',
            'redirect2beta': '0',
            '___dmpkit___': 'bee60fb6-3013-418d-aecf-6fc2a8e65153',
            'gpmd_sex': '1',
            'gpmd_age': '41',
            'khl_sex': '5',
            'khl_age': '29',
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://video.matchtv.ru',
            'Connection': 'keep-alive',
            'Referer': 'https://video.matchtv.ru/',
            # 'Cookie': 'spbc_uuid=b6bc2c3a-14ba-4ec1-b98c-a51f4cb7ea60; spbc_uuid_recreated=1; redirect2beta=0; ___dmpkit___=bee60fb6-3013-418d-aecf-6fc2a8e65153; gpmd_sex=1; gpmd_age=41; khl_sex=5; khl_age=29',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'If-Modified-Since': 'Thu, 11 Jul 2024 10:40:43 GMT',
        }

        params = {
            'sr': '14',
            'type_id': '',
            'width': '100%',
            'height': '100%',
            'lang': 'ru',
            'skin_name': 'matchtv',
            'ref': page_link,
            'uid': 'PVBQLWZV-JTRI-AX1D-ERJ3-SUVBHDW4QTUE',
            'locale': 'ru',
        }

        async with httpx.AsyncClient(headers=headers, cookies=cookies) as session:
            # print(page_link)
            resp1 = await session.get(page_link)
            iframe_video = resp1.text.split('itemprop="url embedUrl"')[1].split(">")[0].split(' href="')[1][:-2]
            # print(resp1.text)
            # print(iframe_video)
            resp2 = await session.get(iframe_video)
            # print(resp2.text)
            url = resp2.text.split("config=")[-1].split("?sr")[0]
            # print(url)
            # print("=" * 20)
            resp3 = await session.get(url, params=params)
            link = resp3.text.split("<video><![CDATA[")[1].split("]")[0]
            # print(link)
            # print("="*20)
            resp4 = await session.get(link)
            # print(resp4.text)
            link2 = resp4.text.split("<track")[1].split("<![CDATA[")[1].split("]")[0]

            resp5 = await session.get(link2)
            download_link = list(filter(lambda x: "https://" in x, resp5.text.split("\n")))[0]
        return download_link
    except Exception as e:
        print(e)
        return "error"


async def search_video_match_tv(name: str):
    domen = "https://matchtv.ru"
    cookies = {
        'spbc_uuid': 'b6bc2c3a-14ba-4ec1-b98c-a51f4cb7ea60',
        'spbc_uuid_recreated': '1',
        'redirect2beta': '0',
        '___dmpkit___': 'bee60fb6-3013-418d-aecf-6fc2a8e65153',
        'spb_abtests_index_n': '464',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        # 'Cookie': 'spbc_uuid=b6bc2c3a-14ba-4ec1-b98c-a51f4cb7ea60; spbc_uuid_recreated=1; redirect2beta=0; ___dmpkit___=bee60fb6-3013-418d-aecf-6fc2a8e65153; spb_abtests_index_n=464',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=1',
    }

    async with httpx.AsyncClient(headers=headers, cookies=cookies) as session:
        resp = await session.get(f"https://matchtv.ru/search/broadcasts?q={name}", timeout=30.0)
        soup = await asyncio.get_running_loop().run_in_executor(None, BeautifulSoup, resp.text, 'lxml')
        ans = list()
        for block in soup.findAll("div", class_="grid-column-4 grid-column-md-6 grid-column-sm-6 grid-column-xs-12 cards-loader__item"):
            if datetime.strptime(block.find("time").get("datetime"), "%Y-%m-%d %H:%M") > (datetime.now() + timedelta(hours=3.0)):
                # print(datetime.strptime(block.find("time").get("datetime"), "%Y-%m-%d %H:%M"))
                continue
            if "Бесплатно" not in block.find("div", class_="card-item__cost").text:
                continue
            ans.append([block.find("div", class_="card-item__title").text, domen+block.find("a").get("href")])
        return ans


async def download_video(download_link: str) -> str:
    cookies = {
        'spbc_uuid': 'b6bc2c3a-14ba-4ec1-b98c-a51f4cb7ea60',
        'spbc_uuid_recreated': '1',
        'redirect2beta': '0',
        '___dmpkit___': 'bee60fb6-3013-418d-aecf-6fc2a8e65153',
        'spb_abtests_index_n': '464',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        # 'Cookie': 'spbc_uuid=b6bc2c3a-14ba-4ec1-b98c-a51f4cb7ea60; spbc_uuid_recreated=1; redirect2beta=0; ___dmpkit___=bee60fb6-3013-418d-aecf-6fc2a8e65153; spb_abtests_index_n=464',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=1',
    }
    async with httpx.AsyncClient(headers=headers, cookies=cookies) as session:
        resp = await session.get(download_link)
        links = list(filter(lambda x: ".ts" in x ,resp.text.split("#EXT-X-DISCONTINUITY")[1].split("\n")))
        name = download_link.split("/")[-2]
        path = "./videos/"
        # print(path)
        paths = await a_download_video(links, session, name, path)
        # for p in paths:
        #     print(p)
        await concat_video(paths, name, path)
        return f"{path}{name}.mp4"


async def get_video_match_tv(link: str):
    try:
        return await download_video(await get_video_link(link))
    except Exception as e:
        # print(e)
        return "error"


async def a_get_video_part(link: str, index: int, session, name_video: str, path_to_video: str, retry=5):
    try:
        # print(link)
        response = await session.get(
            link,
            timeout=30.0,
            follow_redirects=True
        )
        # print(response.status_code)
        if response.status_code == 200:
            # path = r"{}1tv_video_{}_seg{}.ts".format(path_to_video, name_video, index)
            path = f"{path_to_video}{index}_{name_video}"
            # print(path, link)
            async with aiofiles.open(path, "wb") as f:
                await f.write(response.read())
            # await get_audio(f"videos\\1tv_video_{video_id}_seg{index}")
            return path
    except httpx.PoolTimeout and httpx.RemoteProtocolError:
        # print(e)
        if retry == 0:
            print("Код сдох")
            return "error"
        print(retry, index)
        await asyncio.sleep(10)
        await a_get_video_part(link, index, session, name_video, path_to_video, retry-1)
    except Exception as e:
        print(e)
        return "error"
    #     print(e)
    #     print("Всё легло")


async def a_download_video(links: list[str], session, name_video: str, path_to_video: str):
    tasks = []
    prev_numb = 0
    # print(last_index)
    for parts_of_calls in range(0, len(links) + 1, 80):
        if parts_of_calls == 0:
            continue
        tasks.extend(asyncio.create_task(a_get_video_part(links[index_of_part], index_of_part, session, name_video[:3], path_to_video)) for index_of_part in
                        range(prev_numb+1, parts_of_calls+1))
        await asyncio.sleep(10)
        # print(parts_of_calls)
        prev_numb = parts_of_calls
    if prev_numb < len(links):
        tasks.extend(asyncio.create_task(a_get_video_part(links[index_of_part], index_of_part, session, name_video[:3], path_to_video)) for index_of_part in
                        range(prev_numb + 1, len(links)))
    ans = await asyncio.gather(*tasks)
    # for temp in ans:
    #     print(temp)
    paths = list(filter(lambda x: x != "error", ans))
    return paths


async def concat_video(list_of_videos: list[str], video_name: str, path_to_video: str) -> str:
    videos = "|".join(list(sorted(list_of_videos)))
    name_video = "{}{}.mp4".format(path_to_video, video_name)
    subprocess.run('ffmpeg -loglevel error -i "concat:{}" -vcodec copy -acodec copy {}'.format(videos, name_video), shell=True)
    for video in list_of_videos:
        # print(video)
        os.remove(video)


async def main():
    ans = await search_video_match_tv("Швеция")
    print(len(ans))
    if len(ans) > 0:
        # for line in ans:
        #     print(line)
        download_link = await get_video_link(ans[2][1])
        if download_link != "":
            an = await download_video(download_link)
            print(an)
            # subprocess.run(f"ffmpeg -loglevel error -i {download_link} -c copy -bsf:a aac_adtstoasc ./videos/out2.mp4")


if __name__ == '__main__':
    asyncio.run(main())
    # subprocess.run(f"ffmpeg -loglevel error -i {download_link} -c copy -bsf:a aac_adtstoasc ./videos/output1.mp4")
    print(time() - start)

