# 'AQVN3NvPmtiUySQUR27b_CLg_6swX-6PBCE1sPdm'
import types
from typing import get_args

from aiogram import Router, F, html
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from states import *
from aiogram.utils.keyboard import InlineKeyboardBuilder
import ast
from audio_dp import AudioDispatcher
import httpx as htttpx
import time


router = Router()

limit = 10


URL = 'http://127.0.0.1:8000/'



@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    await msg.answer(f"Привет, {msg.from_user.full_name}! 👋 Пришлите название спортивного события!")
    await state.set_state(User.wait_name_video)


# Function for searching video

@router.message(User.wait_name_video)
async def echo_handler(msg: Message, state: FSMContext):
    try:
        count = 0

        t = await req_url(f'{URL}search_video/',
                    params={'query': msg.text},
                    headers={'accept': 'application/json',},
                    type_post='get')
        # for q = t['results']
        kb_links = InlineKeyboardBuilder()

        for search in t['results']:
            count += 1
            kb_links.row(InlineKeyboardButton(text=str(count) + ". " + search['title'], url=search['link']))

        await msg.answer("Введите номер события", reply_markup=kb_links.as_markup(), parse_mode='HTML')
        await state.update_data(match=t)
        await state.set_state(User.wait_num_video)

    except TypeError:

        await msg.answer("К сожалению, мы не смогли распознать ваш запрос. Попробуйте еще раз!")
        await msg.answer("Пришлите название спортивного события!")
        await state.set_state(User.wait_name_video)




# Function for stt and summary text

@router.message(User.wait_num_video)
async def num_handler(msg: Message, state: FSMContext):

    data = await state.get_data()
    url = data['match']['results'][int(msg.text) - 1]['link']

    print(url)

    #url = data['match'][int(msg.text) - 1]['link']

    #aud_disp = AudioDispatcher()
    #aud_disp.dl_get_audio(link=url)

    #PATH = 'audio/'

    #AudioDispatcher.split_into_batches(file_name=PATH)

    #await msg.answer('Загрузка...')
    async with htttpx.AsyncClient() as client:
        data_download = {"title": str(data['match']['results'][int(msg.text) - 1]['title']), "link": str(data['match']['results'][int(msg.text) - 1]['link'])}

        response = await client.post('http://127.0.0.1:8000/video', json=data, timeout=None)
        await msg.answer(str(response.json()))


    # Request for stt
    await msg.answer("Загружаем видео...")

    url = 'http://127.0.0.1:8000/stt'
    data = {"file_path": "/home/ubuntu/ya-sport-vision/3h_example.mp3", "id": str(msg.chat.id)}

    count = 0
    result_text_fs = ""

    temp = []
    count_chunk = 0
    start = time.time()
    async with htttpx.AsyncClient() as client:
        async with client.stream('POST', url, json=data, timeout=None) as r:
            async for chunk in r.aiter_raw():
                if count_chunk == 0:
                    print(time.time() - start)
                count_chunk += 1
                temp.append(chunk.decode('utf-8'))
                if len(temp) == 5:
                    data2 = {"for_summary_text": "\n".join(temp), "id": str(msg.chat.id), "part_mode": False}
                    response = await client.post('http://127.0.0.1:8000/sum', json=data2, timeout=None)
                    await msg.answer(str(response.json()["ans"]))
                    temp = [temp[-1]]
            print(len(temp))
            if len(temp) > 1:
                data2 = {"for_summary_text": "\n".join(temp), "id": str(msg.chat.id), "part_mode": False}
                response = await client.post('http://127.0.0.1:8000/sum', json=data2, timeout=None)
            print(count_chunk)
    await msg.answer("Если хотите обсудить матч, то напишите мне об этом")
    await state.set_state(User.llm_question)


@router.message(User.llm_question)
async def chat_handler(msg: Message, state: FSMContext):
    await msg.answer("Хорошо, задавай вопросы!")
    await state.set_state(User.wait_question)


@router.message(User.wait_question)
async def chat_with_llm(msg: Message, state: FSMContext):

    user_mess = msg.text

    async with htttpx.AsyncClient() as client:
        data = {"prompt": str(user_mess), "id": str(msg.chat.id)}

        response = await client.post('http://127.0.0.1:8000/llm_question', json=data, timeout=None)
        await msg.answer(str(response.json()['ans']))


# Function for send requests

async def req_url(url, type_post, params, headers):
    async with htttpx.AsyncClient() as client:
        if type_post == 'get':
            response = await client.get(url,
                    params=params,
                    headers=headers, timeout=None)
            return response.json()

        else:
            print(params)

            response = await client.post(url, json=params, timeout=None)
            return response.text


