from aiogram.fsm.state import State, StatesGroup


class User(StatesGroup):
    wait_name_video = State()
    wait_num_video = State()
    wait_count_video = State()
    llm_question = State()
    wait_question = State()

