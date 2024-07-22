import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN: str = os.getenv("TG_TOKEN")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')

