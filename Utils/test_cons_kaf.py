from aiokafka import AIOKafkaConsumer

import asyncio
import json


async def consume():
    consumer = AIOKafkaConsumer(
        "llm_question",
        bootstrap_servers='localhost:9092',
        auto_offset_reset="earliest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    await consumer.start()
    try:
        async for msg in consumer:
                print("consumed: ", msg.topic, msg.partition, msg.offset,
                      msg.key, msg.value, msg.timestamp)
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()

asyncio.run(consume())
