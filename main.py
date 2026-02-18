import asyncio
import logging
from aiogram import Bot, Dispatcher, types,F
from aiogram.filters import Command
from db import creat_table, insert_movie, insert_users, get_movie_by_code, find_user, is_ban, check_user_ban, is_not_ban
from buttons import admin_menu, users_menu, confirm_yes_no, kino_sifati_menu, language_menu, janr_menu
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from states import admin_data, find_movie, find_movie_admin, block_user, unblock_user
from chanal import majburiy_follow
from aiogram.types import ReplyKeyboardRemove
from aiogram.client.session.aiohttp import AiohttpSession


API_TOKEN = "8405959828:AAGf0Mo53xL34D2g-DwG1UXbSdRHe7nnfFY"
ADMINS = [8584543342,]
PROXY_URL = 'http://proxy.server:3128'

session = AiohttpSession(proxy=PROXY_URL)

bot = Bot(token=API_TOKEN, session=session)
dp = Dispatcher()
dp.message.middleware(majburiy_follow())

@dp.message(Command('start'))
async def start_hendler(message: types.Message):
    is_ban =await  check_user_ban(message.from_user.id)
    if is_ban:
        if message.from_user.id in ADMINS:
            await message.answer(f"Xush kelibsiz {message.from_user.full_name}", reply_markup=admin_menu())
        else:
            await message.answer(f"Xush kelibsiz {message.from_user.full_name}", reply_markup=users_menu())
            await insert_users(
                user_id=message.from_user.id,
                full_name=message.from_user.full_name,
                is_bann='false'
            

        )
            

@dp.message(F.text == '➕ Kino qo\'shish')
async def creat_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await message.answer("📰 Kino sarlovhasini kiting:")
        await state.set_state(admin_data.title)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")
    
@dp.message(admin_data.title)
async def title_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(title = message.text)
        await message.answer("🎥 Kino janrini kiriting:", reply_markup=janr_menu)
        await state.set_state(admin_data.janr)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")
@dp.message(admin_data.janr)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(janr = message.text)
        await message.answer("🌍 Ishlab chiqargan davlat nomi:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(admin_data.country)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(admin_data.country)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(country = message.text)
        await message.answer("🌐 Kino qaysi tilga tarjima qilinganligi yoki qaysi tilda ovoz berilganligi (davlat nomi):", reply_markup=language_menu)
        await state.set_state(admin_data.language)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(admin_data.language)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(language = message.text)
        await message.answer("💬 Kino haqida qisqach:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(admin_data.about)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(admin_data.about)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(about = message.text)
        await message.answer("🎦 Kino sifati: ", reply_markup=kino_sifati_menu)
        await state.set_state(admin_data.adjactive)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")


@dp.message(admin_data.adjactive)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(adjactive = message.text)
        await message.answer("🎬 Kino uchun 4 xonali kod yarating:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(admin_data.code)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(admin_data.code)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(code = message.text)
        await message.answer("🎥 Kino videosini yuboring: ")
        await state.set_state(admin_data.file_id)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")
    
@dp.message(admin_data.file_id, F.video)
async def janr_films_handler(message: types.Message, state  : FSMContext):
    if  message.from_user.id in ADMINS:
        await state.update_data(file_id = message.video.file_id)
        await message.answer("✅ Kino muvaffaqiyatli qo'shildi")
        data = await state.get_data() 
       
        await insert_movie(
        title=data.get("title"),
        janr=data.get("janr"),
        country=data.get("country"),
        language=data.get("language"),
        about=data.get("about"),
        adjactive=data.get("adjactive"),
        code=data.get("code"),
        file_id=data.get("file_id")
        )
        text = f"""
🎥 Kino kodi: {data.get("code")}
🌍 Kino qaysi davlatda ishlab chiqarilganligi: {data.get("country")}
---------------------------------------------------------------
📄 Kino janri: {data.get("janr")}
🌐 Kino qaysi tilda olinganligi: {data.get("language")}
✏  Kino haqida qisqacha: {data.get("about")}
🎬 Kino sifati: {data.get("adjactive")}
"""
        await message.answer_video(video=data.get("file_id"), caption=text)
        await state.clear()
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")


@dp.message(F.text == '🔎 Kino qidirish')
async def find_movie_heandler(message: types.Message, state: FSMContext):
    await message.answer("✏ Kino kodini kiriting: ")
    await state.set_state(find_movie.code_find)

@dp.message(find_movie.code_find)
async def find_movie_with_code(message: types.Message, state: FSMContext):
    data = await get_movie_by_code(message.text)
    
    if data:
        text = f"""
🎥 Kino kodi: {data['code']}
🌍 Davlat: {data['country']}
---------------------------------------------------------------
📄 Janr: {data['janr']}
🌐 Til: {data['language']}
✏ Haqida: {data['about']}
🎬 Sifat: {data['adjactive']}
"""
        video = data['file_id']
        await message.answer_video(video=video, caption=text)
        await state.clear() 
    else:
        await message.answer("❌ Bunday kodli kino topilmadi. Qayta urinib ko'ring yoki /start bosing.")
        
# ====================== admin_uhcun qidirish========================================================================================
@dp.message(F.text == '🎥 Kinolarni ko\'rish')
async def find_movie_heandler(message: types.Message, state: FSMContext):
    
    await message.answer("✏ Kino kodini kiriting: ")
    await state.set_state(find_movie_admin.code_find_admin)

@dp.message(find_movie_admin.code_find_admin)
async def find_movie_with_code(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
     data = await get_movie_by_code(message.text)
     text = f"""
🎥 Kino kodi: {data['code']}
🌍 Kino qaysi davlatda ishlab chiqarilganligi: {data['country']}
---------------------------------------------------------------
📄 Kino janri: {data['janr']}
🌐 Kino qaysi tilda olinganligi: {data['language']}
✏  Kino haqida qisqacha: {data['about']}
🎬 Kino sifati: {data['adjactive']}
"""
     video = data['file_id']
     if data:
        await message.answer_video(video=video, caption=text)
        await state.clear()
     else:
        await message.answer("❌ Bunday kino topilmadi")
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")
    
@dp.message(F.text == '🚫 Foydalanuvchilarni bloklash')
async def start_block_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("✏ Foydalanuvchining id-sini kiriting")
        
        await state.set_state(block_user.blcok_user_) 
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(block_user.blcok_user_)
async def get_user_id_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        
        await state.update_data(user_id=message.text) 
        
        
        await state.set_state(block_user.confirm_user)
        
        await message.answer(f"💬 ID: {message.text}\nBu foydalanuvchini bloklashga rozimisiz?", 
                             reply_markup=confirm_yes_no())
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.callback_query(block_user.confirm_user)
async def confirm_block_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    data_state = await state.get_data()
    user_id = data_state.get('user_id') 

    if call.data == 'yes':
        
        user_exists = await find_user(user_id) 
        
        if user_exists:
            await is_ban(user_id) 
            await call.message.edit_text(f"✅ Foydalanuvchi (ID: {user_id}) bloklandi")
        else:
            await call.message.edit_text(f"❌ ID: {user_id} bazadan topilmadi")
        
        await state.clear()
    else:
        await call.message.edit_text("❌ Bloklash bekor qilindi")
        await state.clear()

# ============================================================

@dp.message(F.text == '🔓 Foydalanuvchilarni blokdan chiqarish')
async def start_block_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("✏ Foydalanuvchining id-sini kiriting")
        
        await state.set_state(unblock_user.blcok_user_unblock) 
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(block_user.blcok_user_)
async def get_user_id_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        
        await state.update_data(user_id=message.text) 
        
        
        await state.set_state(unblock_user.confirm_user_unblock)
        
        await message.answer(f"💬 ID: {message.text}\nBu foydalanuvchini blokdan chiqarishga rozimisiz?", 
                             reply_markup=confirm_yes_no())
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.callback_query(unblock_user.confirm_user_unblock)
async def confirm_block_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    data_state = await state.get_data()
    user_id = data_state.get('user_id') 

    if call.data == 'yes':
        
        user_exists = await find_user(user_id) 
        
        if user_exists:
            await is_not_ban(user_id) 
            await call.message.edit_text(f"✅ Foydalanuvchi (ID: {user_id}) blokdan chiqarildi")
        else:
            await call.message.edit_text(f"❌ ID: {user_id} bazadan topilmadi")
        
        await state.clear()
    else:
        await call.message.edit_text("❌ Bloklash bekor qilindi")
        await state.clear()
    
    
async def main():
    await creat_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())