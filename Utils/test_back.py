import asyncio

from fastapi import FastAPI
from pydantic import BaseModel, TypeAdapter
import uvicorn
from typing import List

from stt import GigaAMCTC
from glob import glob
from audio_dp import AudioDispatcher
from sum_pipe import init_model, gen_answer, create_summary, gen_conspect

from first_tv_sport_pars_video import search_videos_first_tv, get_video_first_tv
from match_tv_pars import search_video_match_tv, get_video_match_tv



llm = init_model()
app = FastAPI()
stt = GigaAMCTC()
adp = AudioDispatcher()


class Summary_text(BaseModel):
    for_summary_text: str


class Video(BaseModel):
    title: str
    link: str

class User_question(BaseModel):
    prompt: str
    id: str


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/search_video/")
async def search_videos(query: str):
    tasks = []
    tasks.append(asyncio.create_task(search_videos_first_tv(query)))
    tasks.append(asyncio.create_task(search_video_match_tv(query)))
    temp = await asyncio.gather(*tasks)
    results = list()
    for data in temp:
        for item in data:
            if len(item) == 2:
                results.append({"title": item[0], "link": item[1]})
            elif len(item) == 5:
                results.append({"id": item[0],
                            "title": item[1],
                            "duration": item[2],
                            "prewiew": item[3],
                            "link": item[4]})
    # return {"ans": results}
    # ta = TypeAdapter(Video)
    # list_of_videos = ta.validate_python(results)
    list_of_videos = list(Video.model_validate(video_dict) for video_dict in results)
    # print(type[list_of_videos])
    return {"results": list_of_videos}


@app.get("/video")
async def get_video(video: Video) -> str:
    if "matchtv.ru" in video.link:
        path = await get_video_match_tv(video.link)
    elif "www.sport1tv.ru" in video.link:
        path = await get_video_first_tv(video.link)
    elif "youtube.com" in video.link:
        # TODO Ютуб скачка
        path = video.link
    else:
        return {"error": "Invalid video"}
    return {"path": path}


@app.get("/stt/{file_path:path}")
async def gen_sub(file_path: str) -> List:
    adp.split_into_batches(file_name=file_path, overlap_s=1, chunk_length=210)

    filenames = glob('../segments/*')
    text = []

    for filename in filenames:
        text.append(stt.speech_to_text(filename))


    return text


@app.post("/sum")
async def get_summary(for_sum: Summary_text):
    answer = await asyncio.get_running_loop().run_in_executor(None, create_summary, for_sum.for_summary_text, llm)
    return {"ans": answer}


@app.get("/llm_question")
async def gen_answer_llm(user_input: User_question):
    answer = await asyncio.get_running_loop().run_in_executor(None, gen_answer, user_input.prompt, llm)
    return {"ans": answer}


@app.get("/auto_karma/{path_to_video:path}")
async def generate_karma(path_to_video: str):
    ans = await gen_sub(path_to_video)
    answer = await asyncio.get_running_loop().run_in_executor(None, gen_conspect, ans, llm)
    return {"ans", answer}


if __name__ == "__main__":
    uvicorn.run("test_back:app", host="0.0.0.0", port=88, reload=True, log_level="debug")
