import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, TypeAdapter
from fastapi.responses import StreamingResponse
import uvicorn

from glob import glob
from audio_dp import AudioDispatcher
#, dl_get_audio
# from sum_pipe import init_model, gen_answer, create_summary, gen_conspect

from first_tv_sport_pars_video import search_videos_first_tv, get_video_first_tv
from match_tv_pars import search_video_match_tv, get_video_match_tv
from search_youtube import search_youtube

# llm = init_model()
app = FastAPI()
adp = AudioDispatcher()


class Summary_text(BaseModel):
    for_summary_text: str
    id: str
    part_mode: bool = True


class Video(BaseModel):
    title: str
    link: str


class User_question(BaseModel):
    prompt: str
    id: str


class Stt_request(BaseModel):
    file_path: str
    id: str


origins = [
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)



async def process_file(file_path: str) -> str:
    adp.split_into_batches(file_name=file_path, overlap_s=1, chunk_length=210)
    filenames = glob('./segments/*')
    full_text = ''

    for filename in filenames:
        trans = stt.speech_to_text(filename)
        for batch in trans:
            full_text += batch

    os.system('rm -rf segments')
    return full_text



@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/search_video/")
async def search_videos(query: str):
    tasks = []
    tasks.append(asyncio.create_task(search_videos_first_tv(query)))
    tasks.append(asyncio.create_task(search_video_match_tv(query)))
    tasks.append(asyncio.create_task(search_youtube(question=query, limit=10)))
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
    list_of_videos = list(Video.model_validate(video_dict) for video_dict in results)
    return {"results": list_of_videos}


@app.post("/video")
async def get_video(video: Video) ->dict[str, str]:
    #try:
        if "matchtv.ru" in video.link:
            path = await get_video_match_tv(video.link)
        elif "www.sport1tv.ru" in video.link:
            path = await get_video_first_tv(str(video.link))
        elif "youtube.com" in video.link:
            path = await asyncio.get_running_loop().run_in_executor(None, dl_get_audio, video.link)
        else:
            return {"error": "Invalid video"}
        return {"path": path}
   # except Exception as e:
        #return {"error": str(e)}


@app.post("/stt")
async def gen_sub(on_stt: Stt_request):
    async def stream_stt():
        data = {"path": on_stt.file_path, "id": on_stt.id}
        data["answer_topic"] = "stt_give"
        data["mode"] = "yandex"
        producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                                    value_serializer=lambda x: json.dumps(x).encode("utf-8"))

        consumer = AIOKafkaConsumer(
            "stt_give",
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        answer = ""
        await producer.start()
        await consumer.start()
        try:
            await producer.send_and_wait("stt_get", data)
            print(data)
            async for mes in consumer:
                answer = mes.value["result"]
                if answer == "STOP":
                    break
                elif answer == "Invalid file path":
                    yield "Invalid file path"
                    break
                # print(answer)
                yield answer
            await consumer.stop()
        except Exception as e:
            print(e)
            await consumer.stop()
            yield ""
        finally:
            await producer.stop()
    return StreamingResponse(stream_stt(), media_type='text/event-stream')


@app.post("/sum")
async def get_summary(for_sum: Summary_text):
    answer_topic = "llm_summary"
    data = for_sum.model_dump()
    if for_sum.part_mode:
        data["command"] = "part_summary"
    else:
        data["command"] = "summary"
    data["answer_topic"] = answer_topic
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                            value_serializer=lambda x: json.dumps(x).encode("utf-8"))

    consumer = AIOKafkaConsumer(
        answer_topic,
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    answer = ""
    await producer.start()
    await consumer.start()
    try:
        await producer.send_and_wait("llm_question", data)
        # print("back", data)
        async for mes in consumer:
            print(mes.value)
            answer = mes.value
            # print(type(answer))
            # print(answer.keys())
            if "error" in answer.keys():
                print("text")
                return {"ans": answer["error"]}
            # print(answer)
            return {"ans": answer["ans"]}
    except Exception as e:
        return {"ans": e}

    finally:
        await producer.stop()
        await consumer.stop()


@app.post("/llm_question")
async def gen_answer_llm(user_input: User_question):
    # answer = await asyncio.get_running_loop().run_in_executor(None, gen_answer, user_input.prompt, llm)
    answer_topic = "llm_answer"
    data = user_input.model_dump()
    data["command"] = "question"
    data["answer_topic"] = answer_topic
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                            value_serializer=lambda x: json.dumps(x).encode("utf-8"))

    consumer = AIOKafkaConsumer(
        answer_topic,
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    answer = ""
    await producer.start()
    await consumer.start()
    try:
        await producer.send_and_wait("llm_question", data)
        # print("back", data)
        async for mes in consumer:
            # print(mes.value)
            answer = mes.value
            # print(answer)
            if "error" in answer.keys():
                return {"ans": answer["error"]}
            return {"ans": answer["ans"]}
    except Exception as e:
        return {"ans": e}

    finally:
        await producer.stop()
        await consumer.stop()


@app.post("/test_stream")
async def stream_test(temp: Stt_request):
    async def random_gen():
        tep = [i for i in range(10)]
        for i in tep:
            yield str(i)+temp.id
    return StreamingResponse(random_gen(), media_type='text/event-stream')




@app.delete("/collection/{collection_id}")
async def delete_collection(collection_id: str):
    data ={"command": "del_collect", "id": collection_id}
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                            value_serializer=lambda x: json.dumps(x).encode("utf-8"))
    await producer.start()
    try:
        await producer.send_and_wait("llm_question", data)
        # print("back", data)
        return {"ok": True, "error": None}
    except Exception as e:
        return {"error": e, "ok": False}
    finally:
        await producer.stop()


# @app.get("/auto_karma/{path_to_video:path}")
# async def generate_karma(path_to_video: str):
#     ans = await gen_sub(path_to_video)
#     answer = await asyncio.get_running_loop().run_in_executor(None, gen_conspect, ans, llm)
#     return {"ans", answer}


if __name__ == "__main__":
    uvicorn.run("back:app", host="127.0.0.1", port=8000, reload=False, log_level="debug")
