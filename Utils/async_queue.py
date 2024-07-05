import os
import asyncio
import aiofiles
from typing import Any
from stt import Whisper


class AsyncFileProcessor:
    def __init__(self, *, model: Any, path: str, num_consumers: int = 3):
        self.directory = path
        self.queue = asyncio.Queue()
        self.num_consumers = num_consumers
        self.model = model


    async def __producer(self):
        for filename in os.listdir(self.directory):
            await self.queue.put(filename)


    async def __consumer(self):
        while True:
            filename = await self.queue.get()

            if filename is None:  # None is used to signal that there are no more files
                break

            file_path = os.path.join(self.directory, filename)
            text = await asyncio.to_thread(self.model.speech_to_text, file_path)  # Use to_thread to run sync function
            print(f'#{filename}: {text}')

            self.queue.task_done()


    async def run(self):
        producer_task = asyncio.create_task(self.__producer())
        consumer_tasks = [asyncio.create_task(self.__consumer()) for _ in range(self.num_consumers)]

        await producer_task
        await self.queue.join()  # Wait until all items in the queue have been processed

        for _ in range(self.num_consumers):
            await self.queue.put(None)  # Send a signal to consumers to stop
        await asyncio.gather(*consumer_tasks)


if __name__ == "__main__":
    processor = AsyncFileProcessor(model=Whisper('base'), path='./segments', num_consumers=3)
    asyncio.run(processor.run())
