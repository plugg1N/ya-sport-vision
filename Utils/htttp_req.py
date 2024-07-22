import httpx as htttpx

url = 'http://0.0.0.0:80/search_video/?query=Россия и Швеция 2022'

res = htttpx.get(url, timeout=None)

print(res.text)
