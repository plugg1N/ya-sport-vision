import redis



class RedisInterface:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.ttl: int = 100


    # Set a life time for chat
    def set_ttl(self, ttl: int):
        self.ttl = ttl


    # Add a message to history of user-chat
    def add_message(self, chat_id, message):
        self.client.rpush(chat_id, message)
        self.client.expire(chat_id, self.ttl)


    # Read history of messages sent in by user
    def read_history(self, chat_id):
        return self.client.lrange(chat_id, 0, -1)


if __name__ == "__main__":
    redis_interface = RedisInterface()

    # Add messages to chat history (including Russian messages)
    redis_interface.add_message('123456789', "Привет")
    redis_interface.add_message('123456789', "Как дела?")
    redis_interface.add_message('123456789', "До свидания")

    # Read chat history
    chat_history = redis_interface.read_history('123456789')
    for message in chat_history:
        print(message)

