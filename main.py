import asyncio
import logging
import sys
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession

from db import (
    creat_table, insert_movie, insert_users, get_movie_by_code, 
    find_user, is_ban, check_user_ban, is_not_ban, 
    delete_movie_by_code, update_user_subscription, 
    check_subscription_expiry, insert_payment
)
from buttons import (
    admin_menu, users_menu, confirm_yes_no, kino_sifati_menu, 
    language_menu, janr_menu, mir_menu, subscription_reply_menu, 
    admin_approval_keys
)
from states import (
    admin_data, find_movie, find_movie_admin, 
    block_user, unblock_user, DeleteMovieState, 
    PaymentState, PaymentStateHistory
)
from chanal import check_user_sub, sub_markup
from pdf_usres import generate_users_pdf
from pdf_movies import generate_movies_pdf
from pymant_history import generate_payments_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TOKEN = "8222917234:AAGxqndfNnBAzh9lS8HrYeNuABz3YNINSJQ"
ADMINS = [8584543342, 8252835848]

PROXY_URL = 'http://proxy.server:3128'
session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

@dp.message(Command('start'))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    is_not_banned = await check_user_ban(user_id)
    if not is_not_banned:
        return await message.answer("Siz botdan foydalanishdan chetlatilgansiz! ❌")

    if await check_user_sub(user_id, bot):
        if user_id in ADMINS:
            await message.answer(f"Xush kelibsiz Admin, {full_name}", reply_markup=admin_menu())
            return

        user_data = await find_user(user_id)
        if not user_data:
            await insert_users(user_id=user_id, full_name=full_name, is_bann='false')
            user_data = await find_user(user_id)

        if user_data[4] == 'none': 
            await message.answer(
                f"Xush kelibsiz {full_name}!\nBotdan foydalanish uchun tariflardan birini tanlang va obuna bo'ling:", 
                reply_markup=subscription_reply_menu()
            )
        else:
            await message.answer(f"Xush kelibsiz {full_name}", reply_markup=users_menu())
    else:
        await message.answer(
            f"Hurmatli {full_name}, botdan foydalanish uchun kanallarga a'zo bo'ling:",
            reply_markup=sub_markup() 
        )

@dp.message(F.text.contains("Standart"))
async def process_standard(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(chosen_sub="standard", price="4.000")
    await message.answer(
        "Siz **Standart** tarifini tanladingiz.\n\n"
        "💳 Karta: `5614 6889 5214 8194`\n"
        "👤 Mirdjalilova.D\n"
        "💰 Summa: 4.000 so'm\n\n"
        "📸 To'lov qiling va chekni (skrinshot) yuboring.",
        parse_mode="Markdown"
    )
    await state.set_state(PaymentState.waiting_for_screenshot)

@dp.message(F.text.contains("Premium"))
async def process_premium(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(chosen_sub="premium", price="8.000")
    await message.answer(
        "Siz **Premium** tarifini tanladingiz.\n\n"
        "💳 Karta: `9987 1000 1543 7888`\n"
        "💰 Summa: 8.000 so'm\n\n"
        "📸 To'lov qiling va chekni (skrinshot) yuboring.",
        parse_mode="Markdown"
    )
    await state.set_state(PaymentState.waiting_for_screenshot)

@dp.message(PaymentState.waiting_for_screenshot, F.photo)
async def get_payment_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sub_type = data.get('chosen_sub')
    price = data.get('price')
    
    admin_id = 8584543342
    
    await message.answer("✅ Rahmat! Chekingiz adminga yuborildi. Tasdiqlanishini kuting.")
    
    await bot.send_photo(
        chat_id=admin_id, 
        photo=message.photo[-1].file_id, 
        caption=f"🔔 Yangi to'lov!\n👤: {message.from_user.full_name}\n🆔: {message.from_user.id}\n💎 Tarif: {sub_type}\n💵 Summa: {price}",
        reply_markup=admin_approval_keys(message.from_user.id, sub_type)
    )
    await state.clear()

@dp.message(F.text == "😍 Obunalarim")
async def check_my_subscription(message: types.Message):
    user_id = message.from_user.id
    user_data = await find_user(user_id) 

    if not user_data or user_data[4] == 'none':
        await message.answer("Sizda hozirda faol obuna mavjud emas. ❌")
        return

    sub_type = user_data[4].capitalize()
    start_date = user_data[5]
    end_date = user_data[6]

    try:
        end_dt = datetime.strptime(str(end_date), "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        remaining = end_dt - now
        
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if remaining.total_seconds() <= 0:
            status = "Muddati tugagan 🔴"
            time_left = "0 kun"
        else:
            status = "Faol ✅"
            time_left = f"{days} kun, {hours} soat, {minutes} daqiqa"
    except:
        time_left = "Aniqlab bo'lmadi"
        status = "Noma'lum"

    text = (
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"💎 <b>Tarif turi:</b> {sub_type}\n"
        f"📅 <b>Sotib olingan sana:</b> <code>{start_date}</code>\n"
        f"⌛ <b>Amal qilish muddati:</b> <code>{end_date}</code>\n"
        f"🔄 <b>Holati:</b> {status}\n\n"
        f"🕒 <b>Qolgan vaqt:</b> {time_left}"
    )
    await message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data.startswith('admin_'))
async def admin_decision(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    action = parts[1]
    user_id = int(parts[2])
    sub_type = parts[3] if len(parts) > 3 else "noma'lum"
    
    full_name = callback.message.caption.split('\n')[1].split(': ')[1] if callback.message.caption else "Noma'lum"

    if action == 'app': 
        await insert_payment(user_id, full_name, "user", "Noma'lum", sub_type, "tasdiqlandi") 
        await update_user_subscription(user_id, sub_type) 
        
        await callback.bot.send_message(
            user_id, 
            f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi.\n💎 Tarif: {sub_type.capitalize()}\n🚀 Endi barcha kinolarni ko'rishingiz mumkin!", 
            reply_markup=users_menu()
        )
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ TASDIQLANDI")
        await callback.answer("Obuna faollashtirildi")

    elif action == 'rej': 
        await state.set_state(PaymentStateHistory.waiting_for_reject_reason)
        await state.update_data(
            reject_user_id=user_id, 
            reject_msg_id=callback.message.message_id
        )
        await callback.message.answer(f"❌ ID: {user_id} uchun rad etish sababini yozing:")
        await callback.answer()

@dp.message(PaymentStateHistory.waiting_for_reject_reason)
async def process_reject_reason_msg(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('reject_user_id')
    reason = message.text

    await bot.send_message(user_id, f"❌ Sizning to'lovingiz rad etildi.\n⚠️ Sabab: {reason}")
    await message.answer(f"✅ Foydalanuvchiga (ID: {user_id}) rad javobi yuborildi.")
    await state.clear()

@dp.message(F.text == "📜 To'lovlar tarixi")
async def send_payments_report(message: types.Message):
    if message.from_user.id not in ADMINS: return
    status_msg = await message.answer("⏳ To'lovlar tarixi tayyorlanmoqda...")
    try:
        pdf_path = await generate_payments_pdf()
        if pdf_path and os.path.exists(pdf_path):
            await message.answer_document(FSInputFile(pdf_path), caption=f"📊 To'lovlar tarixi")
            await status_msg.delete()
            os.remove(pdf_path) 
        else:
            await status_msg.edit_text("❌ Ma'lumot topilmadi.")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

@dp.message(F.text == '➕ Kino qo\'shish')
async def creat_films_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("📰 Kino sarlovhasini kiriting:")
        await state.set_state(admin_data.title)
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")
    
@dp.message(admin_data.title)
async def title_films_handler(message: types.Message, state: FSMContext):
    await state.update_data(title = message.text)
    await message.answer("🎥 Kino janrini kiriting:", reply_markup=janr_menu)
    await state.set_state(admin_data.janr)

@dp.message(admin_data.janr)
async def janr_films_handler(message: types.Message, state: FSMContext):
    await state.update_data(janr = message.text)
    await message.answer("🌍 Ishlab chiqargan davlat nomi:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(admin_data.country)

@dp.message(admin_data.country)
async def country_handler(message: types.Message, state: FSMContext):
    await state.update_data(country = message.text)
    await message.answer("🌐 Tarjima tili:", reply_markup=language_menu)
    await state.set_state(admin_data.language)

@dp.message(admin_data.language)
async def language_handler(message: types.Message, state: FSMContext):
    await state.update_data(language = message.text)
    await message.answer("💬 Kino haqida qisqacha:")
    await state.set_state(admin_data.about)

@dp.message(admin_data.about)
async def about_handler(message: types.Message, state: FSMContext):
    await state.update_data(about = message.text)
    await message.answer("🎦 Kino sifati: ", reply_markup=kino_sifati_menu)
    await state.set_state(admin_data.adjactive)

@dp.message(admin_data.adjactive)
async def adjactive_handler(message: types.Message, state: FSMContext):
    await state.update_data(adjactive = message.text)
    await message.answer("🎬 Kino uchun 4 xonali kod yarating:")
    await state.set_state(admin_data.code)

@dp.message(admin_data.code)
async def code_handler(message: types.Message, state: FSMContext):
    await state.update_data(code = message.text)
    await message.answer("🎥 Kino videosini yuboring: ")
    await state.set_state(admin_data.file_id)
    
@dp.message(admin_data.file_id, F.video)
async def file_id_handler(message: types.Message, state: FSMContext):
    file_id = message.video.file_id
    data = await state.get_data() 
    await insert_movie(
        title=data.get("title"), janr=data.get("janr"), country=data.get("country"),
        language=data.get("language"), about=data.get("about"),
        adjactive=data.get("adjactive"), code=data.get("code"), file_id=file_id
    )
    await message.answer("✅ Kino muvaffaqiyatli qo'shildi")
    await state.clear()

@dp.message(F.text == '🔎 Kino qidirish')
async def find_movie_handler(message: types.Message, state: FSMContext):
    await message.answer("✏ Kino kodini kiriting: ")
    await state.set_state(find_movie.code_find)

@dp.message(find_movie.code_find)
async def find_movie_with_code(message: types.Message, state: FSMContext):
    data = await get_movie_by_code(message.text)
    if data:
        text = f"🎥 Kodi: {data['code']}\n🌍 Davlat: {data['country']}\n📄 Janr: {data['janr']}\n🌐 Til: {data['language']}\n✏ Haqida: {data['about']}\n🎬 Sifat: {data['adjactive']}"
        await message.answer_video(video=data['file_id'], caption=text)
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")
    await state.clear()

@dp.message(F.text == '🎥 Kinolarni ko\'rish')
async def admin_view_movies(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("✏ Kino kodini kiriting: ")
        await state.set_state(find_movie_admin.code_find_admin)

@dp.message(find_movie_admin.code_find_admin)
async def admin_movie_search_result(message: types.Message, state: FSMContext):
    data = await get_movie_by_code(message.text)
    if data:
        text = f"🎥 Kodi: {data['code']}\n🌍 Davlat: {data['country']}\n📄 Janr: {data['janr']}\n🎬 Sifat: {data['adjactive']}"
        await message.answer_video(video=data['file_id'], caption=text)
    else:
        await message.answer("❌ Bunday kino topilmadi")
    await state.clear()

@dp.message(F.text == '🚫 Foydalanuvchilarni bloklash')
async def start_block_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("✏ Foydalanuvchining id-sini kiriting")
        await state.set_state(block_user.blcok_user_) 

@dp.message(block_user.blcok_user_)
async def get_user_id_handler(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.text) 
    await state.set_state(block_user.confirm_user)
    await message.answer(f"💬 ID: {message.text}\nBloklashga rozimisiz?", reply_markup=confirm_yes_no())

@dp.callback_query(block_user.confirm_user)
async def confirm_block_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    user_id = data.get('user_id') 
    if call.data == 'yes':
        if await find_user(user_id):
            await is_ban(user_id) 
            await call.message.edit_text(f"✅ ID: {user_id} bloklandi")
        else:
            await call.message.edit_text("❌ Foydalanuvchi topilmadi")
    else:
        await call.message.edit_text("❌ Bekor qilindi")
    await state.clear()

@dp.message(F.text == '🔓 Foydalanuvchilarni blokdan chiqarish')
async def start_unblock_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("✏ Foydalanuvchining id-sini kiriting")
        await state.set_state(unblock_user.blcok_user_unblock)

@dp.message(unblock_user.blcok_user_unblock)
async def get_unblock_id(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.text) 
    await state.set_state(unblock_user.confirm_user_unblock)
    await message.answer(f"💬 ID: {message.text}\nBlokdan chiqarilsinmi?", reply_markup=confirm_yes_no())

@dp.callback_query(unblock_user.confirm_user_unblock)
async def confirm_unblock(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    user_id = data.get('user_id') 
    if call.data == 'yes':
        if await find_user(user_id):
            await is_not_ban(user_id)
            await call.message.edit_text(f"✅ ID: {user_id} blokdan chiqarildi")
        else:
            await call.message.edit_text("❌ Foydalanuvchi topilmadi")
    else:
        await call.message.edit_text("❌ Bekor qilindi")
    await state.clear()

@dp.message(F.text == 'Foydalanuvchilar ro\'yhati')
async def users_list_pdf(message: types.Message):
    if message.from_user.id not in ADMINS: return
    status_msg = await message.answer("⏳ PDF tayyorlanmoqda...")
    try:
        pdf_path = await generate_users_pdf() 
        if pdf_path:
            await message.answer_document(FSInputFile(pdf_path), caption="📄 Foydalanuvchilar ro'yxati")
            await status_msg.delete()
            os.remove(pdf_path)
        else:
            await status_msg.edit_text("❌ Baza bo'sh.")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

@dp.message(F.text == "🗑 Kino o'chirish")
async def start_del_process(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("🔢 O'chirmoqchi bo'lgan kino kodini kiriting:")
        await state.set_state(DeleteMovieState.waiting_for_code)

@dp.message(DeleteMovieState.waiting_for_code)
async def process_del_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    movie = await get_movie_by_code(code) 
    if movie:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Ha", callback_data=f"conf_del:{code}"))
        builder.add(types.InlineKeyboardButton(text="Yo'q", callback_data="cancel_del"))
        await message.answer(f"🎬 Kod: {code}\nO'chirilsinmi?", reply_markup=builder.as_markup())
        await state.set_state(DeleteMovieState.confirm_delete)
    else:
        await message.answer("❌ Kino topilmadi.")
        await state.clear()

@dp.callback_query(F.data.startswith("conf_del:"))
@dp.callback_query(F.data == "cancel_del")
async def finalize_delete(call: types.CallbackQuery, state: FSMContext):
    if call.data.startswith("conf_del:"):
        code = call.data.split(":")[1]
        await delete_movie_by_code(code)
        await call.message.edit_text(f"✅ Kod {code} o'chirildi.")
    else:
        await call.message.edit_text("❌ Bekor qilindi.")
    await state.clear()
    await call.answer()

@dp.message(F.text == "📂 Kinolarni ko'rish")
async def send_movies_pdf_handler(message: types.Message):
    wait_msg = await message.answer("🔄 PDF tayyorlanmoqda...")
    try:
        file_path = await generate_movies_pdf()
        if file_path:
            await message.answer_document(FSInputFile(file_path), caption="🎬 Kinolar ro'yxati")
            await wait_msg.delete()
            os.remove(file_path)
        else:
            await wait_msg.edit_text("❌ Baza bo'sh.")
    except Exception as e:
        await wait_msg.edit_text(f"Xatolik: {e}")

@dp.message(Command('secret_backend_miraziz77'))
async def miraziz(message: types.Message):
    await message.answer("Salom! Miraziz Mirdjalilov sizni tanidim", reply_markup=mir_menu())

async def main():
    await creat_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())