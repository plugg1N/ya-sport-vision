import asyncio
import json
import os
from dotenv import load_dotenv

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from typing import List

from glob import glob
from stt import YaSpeechKit
from audio_dp import AudioDispatcher

load_dotenv()

token: str = os.getenv("YA_SPEECH_KIT")

# Initialize FastAPI app
stt = YaSpeechKit(token)
adp = AudioDispatcher()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'

def process_file(file_path: str):
    adp.split_into_batches(file_name=file_path, overlap_s=1, chunk_length=210)

    chunk_paths = glob('./segments/*')
    try:
        for path in chunk_paths:
            text_chank = ""
            for text_part in stt.speech_to_text(path):
                text_chank += text_part
            yield text_chank
    except Exception as e:
        print(e)
    finally:
        os.system('rm -rf segments')


async def consume_kafka_messages():
    global producer, consumer

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    consumer = AIOKafkaConsumer(
        "stt_get",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )


    await producer.start()
    await consumer.start()
    try:
        async for msg in consumer:
            answer_topic = "stt_give"
            data = msg.value
            file_path = data.get("path")
            if file_path:
                result = []
                for chunk in process_file(file_path):
                    await producer.send_and_wait(answer_topic, {"result": chunk})
                    result.append(chunk)
                await producer.send_and_wait("get_rag", {"command": "load_stt", "stt": result, "id": data["id"]})
                await producer.send_and_wait(answer_topic, {"result": "STOP"})
            else:
                await producer.send_and_wait(answer_topic, {"error": "Invalid file path"})
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(consume_kafka_messages())
