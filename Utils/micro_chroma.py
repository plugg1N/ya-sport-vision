import json
import asyncio

import chromadb
from chromadb.utils import embedding_functions

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


# alp = "abcdefghijklmnopqrstuvwxyz1234567890"


def get_rag_answer(name: str, query:str,) -> list[str]:
    # name = generate_name()
    collect = new_collection(name)
    results = collect.query(
        query_texts=[query], # Chroma will embed this for you
        n_results=3 # how many results to return
    )
    ### TODO приделать BM25+
    answer = results["documents"][0]
    if len(results["documents"]) != 1:
        for res in results["documents"][1:]:
            answer.append(res)
    return answer


def new_collection(name: str):
    collection = client.get_or_create_collection(name, embedding_function=sentence_transformer_ef, metadata={"hnsw":"l2"})
    return collection


def minus_collection(name: str):
    client.delete_collection(name=name)


async def gen_answer(name, query):
    answer = await asyncio.get_running_loop().run_in_executor(None, get_rag_answer, name, query)
    return " ".join(answer)


async def load_stt(stt_text: str, key: str):
    # name = generate_name()
    temp = stt_text.split("\n")
    collect = new_collection(key)
    texts = []
    for t in temp:
        if len(t) < 500:
            texts.append(t)
        else:
            first_i = 0
            last_i = min(first_i+500, len(t))
            while last_i < len(t):
                texts.append(t[first_i:last_i])
                first_i = last_i
                last_i = min(first_i+500, len(t))
            if t[first_i:last_i] not in texts:
                texts.append(t[first_i:last_i])
    collect.add(
        documents=texts,
        ids=[f"id{i}" for i, _ in enumerate(texts)]
    )
    print(f"<log> stt {key} loaded")


async def get_command():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                            value_serializer=lambda x: json.dumps(x).encode("utf-8"))

    consumer = AIOKafkaConsumer(
        "get_rag",
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    await producer.start()
    await consumer.start()
    try:
        async for message in consumer:
            print(message.value, "cons")
            data: dict = message.value
            answer_topic = "give_rag"
            if data["command"] == "question":
                ans = await gen_answer(data["id"], data["query"])
                print(ans)
                await producer.send_and_wait(answer_topic, {"ans": ans, "id": data["id"]})
            elif data["command"] == "load_stt":
                stt_text = "\n".join(list(filter(lambda x: x is not None, data["stt"])))
                await load_stt(stt_text, data["id"])
            elif data["command"] == "del_collect":
                await asyncio.get_running_loop().run_in_executor(None, minus_collection, data["id"])
            else:
                if answer_topic != "":
                    await producer.send_and_wait(answer_topic, {"error": "Unknown command"})
    finally:
        await producer.stop()
        await consumer.stop()


if __name__ == '__main__':
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-large")
    client = chromadb.PersistentClient(path="/home/ubuntu/ya-sport-vision/chroma_db")
    asyncio.run(get_command())


