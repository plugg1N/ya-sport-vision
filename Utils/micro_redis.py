import asyncio
import json

import redis

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

class RedisInterface:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.ttl: int = 100


    # Set a life time for chat
    def set_ttl(self, ttl: int):
        self.ttl = ttl


    # Add a message to history of user-chat
    def add_message(self, chat_id, message):
        if self.client.llen(chat_id) >= 5:
            self.client.lpop(chat_id)

        # Add the new message
        self.client.rpush(chat_id, message)
        self.client.expire(chat_id, self.ttl)


    # Read history of messages sent in by user
    def read_history(self, chat_id):
        return self.client.lrange(chat_id, 0, -1)


def get_llm_history(key):
    chat_history = redis_interface.read_history(key)
    print(chat_history)
    if len(chat_history) == 0:
        return None
    return "\n".join([mes for mes in chat_history])


def put_llm_history(key, prompt, answer):
    message = f"{prompt}{answer}<end_of_turn>"
    redis_interface.add_message(key, message)


def get_prev_summary(key):
    print([key])
    prev_summary = redis_interface.read_history(key)
    if len(prev_summary) == 0:
        return ""
    return prev_summary[-1]


def put_prev_summary(key, summary):
    redis_interface.add_message(key, summary)


async def get_command():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                            value_serializer=lambda x: json.dumps(x).encode("utf-8"))

    consumer = AIOKafkaConsumer(
        "redis_get",
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    await producer.start()
    await consumer.start()
    try:
        async for message in consumer:
            # print(message.value, "cons")
            data = message.value
            answer_topic = ""
            if "answer_topic" in data.keys():
                answer_topic = data["answer_topic"]
            if data["command"] == "get_llm_history":
                ans = await asyncio.get_running_loop().run_in_executor(None, get_llm_history, data["id"])
                # print(ans)
                await producer.send_and_wait(answer_topic, {"ans": ans, "id": data["id"]})
                # print("ready")
            elif data["command"] == "put_llm_history":
                await asyncio.get_running_loop().run_in_executor(None, put_llm_history, data["id"], data["prompt"], data["ans"])

            elif data["command"] == "get_llm_summary":
                    ans = await asyncio.get_running_loop().run_in_executor(None, get_prev_summary, data["id"]+"sum")
                    # print(ans)
                    await producer.send_and_wait(answer_topic, {"ans": ans, "id": data["id"]})
                # print("ready")
            elif data["command"] == "put_llm_summary":
                await asyncio.get_running_loop().run_in_executor(None, put_prev_summary, data["id"]+"sum", data["text"])
            else:
                await producer.send_and_wait(answer_topic, {"error": "Unknown command"})
    finally:
        await producer.stop()
        await consumer.stop()

if __name__ == "__main__":
    redis_interface = RedisInterface()
    asyncio.run(get_command())

    # Add messages to chat history (including Russian messages)
    # redis_interface.add_message('123456789', "Привет")
    # redis_interface.add_message('123456789', "Как дела?")
    # redis_interface.add_message('123456789', "До свидания")

    # # Read chat history
    # chat_history = redis_interface.read_history('123456789')
    # for message in chat_history:
        # print(message)
