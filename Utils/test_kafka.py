from aiokafka import AIOKafkaProducer

import asyncio
import json


async def send_one():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                                value_serializer=lambda x: json.dumps(x).encode("utf-8"))
    await producer.start()
    try:
        await producer.send_and_wait("llm_question", {"test": "Super message"})
        print("test")
    finally:
        await producer.stop()


asyncio.run(send_one())
