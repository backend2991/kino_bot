from aiogram.fsm.state import State, StatesGroup

class admin_data(StatesGroup):
    title = State()
    janr = State()
    country = State()
    language = State()
    about = State()
    adjactive = State()
    code = State()
    file_id = State()


class find_movie(StatesGroup):
    code_find = State() 

class find_movie_admin(StatesGroup):
    code_find_admin = State() 

class block_user(StatesGroup):
    blcok_user_ = State() 
    confirm_user = State()

class unblock_user(StatesGroup):
    blcok_user_unblock = State() 
    confirm_user_unblock = State()

from aiogram.fsm.state import State, StatesGroup

class DeleteMovieState(StatesGroup):
    waiting_for_code = State() 
    confirm_delete = State()