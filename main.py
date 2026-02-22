import asyncio
import logging
import sys
from aiogram.types import FSInputFile
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, types,F
from aiogram.filters import Command
from db import creat_table, insert_movie, insert_users, get_movie_by_code, find_user, is_ban, check_user_ban, is_not_ban, delete_movie_by_code, update_user_subscription, check_subscription_expiry, insert_payment
from buttons import admin_menu, users_menu, confirm_yes_no, kino_sifati_menu, language_menu, janr_menu, mir_menu, subscription_reply_menu, admin_approval_keys
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from states import admin_data, find_movie, find_movie_admin, block_user, unblock_user, DeleteMovieState, PaymentState, PaymentStateHistory
from chanal import check_user_sub, sub_markup
from aiogram.types import ReplyKeyboardRemove
from pdf_usres import generate_users_pdf
from pdf_movies import generate_movies_pdf
from datetime import datetime
from pymant_history import generate_payments_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TOKEN = "8222917234:AAGxqndfNnBAzh9lS8HrYeNuABz3YNINSJQ"
ADMINS = [8584543342,]
from aiogram.client.session.aiohttp import AiohttpSession


PROXY_URL = 'http://proxy.server:3128'
session = AiohttpSession(proxy=PROXY_URL)

bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()


@dp.message(Command('start'))
async def start_handler(message: types.Message, bot: Bot):
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
        "💳 Karta: `9987 1000 1543 7888`\n"
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
    
    await message.answer("✅ Rahmat! Chekingiz adminga yuborildi.")
    
    await bot.send_photo(
        admin_id, 
        message.photo[-1].file_id, 
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
        end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
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
    action, user_id = parts[1], int(parts[2])
    sub_type = parts[3] if len(parts) > 3 else "noma'lum"

    if action == 'app': 
        await update_user_subscription(user_id, sub_type, 30)
        await insert_payment(user_id, "User", sub_type, "noma'lum", callback.message.photo[-1].file_id, "tasdiqlandi")
        
        await bot.send_message(user_id, "✅ To'lovingiz tasdiqlandi! Bot ochildi.", reply_markup=users_menu())
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ TASDIQLANDI")
        await callback.answer("Tasdiqlandi")

    elif action == 'rej': 
        await state.set_state(PaymentStateHistory.waiting_for_reject_reason)
        await state.update_data(reject_user_id=user_id, reject_msg_id=callback.message.message_id, 
                                rej_sub_type=sub_type, rej_photo=callback.message.photo[-1].file_id)
        
        await callback.message.answer("❌ Rad etish sababini yozing:")
        await callback.answer()

@dp.callback_query(F.data == "sub_check")
async def callback_sub_check(call: types.CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    full_name = call.from_user.full_name

    if await check_user_sub(user_id, bot):
        await call.message.delete()
        
        if user_id in ADMINS:
            await call.message.answer(f"Xush kelibsiz Admin, {full_name}", reply_markup=admin_menu())
            return

        user_data = await find_user(user_id)
        
        if not user_data:
            await insert_users(user_id=user_id, full_name=full_name, is_bann='false')
            user_data = await find_user(user_id)

        if user_data[4] == 'none': 
            await call.message.answer(
                f"Rahmat {full_name}! Kanallarga a'zo bo'ldingiz.\n"
                "Endi botdan foydalanish uchun tariflardan birini tanlang:", 
                reply_markup=subscription_reply_menu()
            )
        else:
            await call.message.answer(f"Xush kelibsiz {full_name}", reply_markup=users_menu())
            
    else:
        await call.answer("Siz hali barcha kanallarga a'zo bo'lmagansiz! ❌", show_alert=True)
            
@dp.message(F.text == "📜 To'lovlar tarixi")
async def send_payments_report(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    status_msg = await message.answer("⏳ To'lovlar tarixi tayyorlanmoqda...")
    
    try:
        pdf_path = await generate_payments_pdf()
        
        if pdf_path:
            document = FSInputFile(pdf_path)
            await message.answer_document(
                document, 
                caption=f"📊 To'lovlar tarixi (Oxirgi yangilanish: {datetime.now().strftime('%d.%m.%Y')})"
            )
            await status_msg.delete()
            os.remove(pdf_path) 
        else:
            await status_msg.edit_text("❌ Ma'lumot topilmadi.")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

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
        await state.set_state(unblock_user.blcok_user_unblock) # To'g'ri state
    else:
        await message.answer("❌ Bu amal faqat adminlar uchun")

@dp.message(unblock_user.blcok_user_unblock) # State mos kelishi kerak
async def get_user_id_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.update_data(user_id=message.text) 
        await state.set_state(unblock_user.confirm_user_unblock)
        
        await message.answer(
            f"💬 ID: {message.text}\nBu foydalanuvchini blokdan chiqarishga rozimisiz?", 
            reply_markup=confirm_yes_no()
        )
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
            await is_not_ban(user_id) # Endi bazada 0 (Active) bo'ladi
            await call.message.edit_text(f"✅ Foydalanuvchi (ID: {user_id}) blokdan chiqarildi")
        else:
            await call.message.edit_text(f"❌ ID: {user_id} bazadan topilmadi")
        await state.clear()
    else:
        await call.message.edit_text("❌ Blokdan chiqarish bekor qilindi")
        await state.clear()


@dp.message(F.text == "📂 Foydalanuvchilarni ko'rish") 
async def ghg(message: types.Message):
    status_msg = await message.answer("⏳ PDF tayyorlanmoqda, iltimos kiting...")
    
    try:
        pdf_path = await generate_users_pdf() 
        
        if pdf_path is None:
            await message.answer("❌ Ma'lumotlar bazasi topilmadi!")
            return

        document = FSInputFile(pdf_path)
        await message.answer_document(
            document, 
            caption="📄 Bot foydalanuvchilari ro'yxati"
        )
        
        await status_msg.delete()
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

@dp.message(Command('secret_backend_miraziz77'))
async def miraziz(message: types.Message):
    await message.answer("Salom! Miraziz Mirdjalilov sizni tanidim", reply_markup=mir_menu())

@dp.message(F.text == 'Foydalanuvchilar ro\'yhati')
async def f(message: types.Message):
    status_msg = await message.answer("⏳ PDF tayyorlanmoqda, iltimos kiting...")
    
    try:
        pdf_path = await generate_users_pdf() 
        
        if pdf_path is None:
            await message.answer("❌ Ma'lumotlar bazasi topilmadi!")
            return

        document = FSInputFile(pdf_path)
        await message.answer_document(
            document, 
            caption="📄 Bot foydalanuvchilari ro'yxati"
        )
        
        await status_msg.delete()
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    

@dp.message(F.text == "🗑 Kino o'chirish")
async def start_del_process(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("🔢 O'chirmoqchi bo'lgan kino kodini kiriting:")
        await state.set_state(DeleteMovieState.waiting_for_code)
    else:
        await message.answer("❌ Kechirasiz, bu amal faqat adminlar uchun.")

@dp.message(DeleteMovieState.waiting_for_code)
async def process_del_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    movie = await get_movie_by_code(code) 

    if movie:
        title = movie.get('title') if isinstance(movie, dict) else movie[1]
        
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Ha, o'chirilsin ✅", callback_data=f"conf_del:{code}"))
        builder.add(types.InlineKeyboardButton(text="Yo'q, bekor qilish ❌", callback_data="cancel_del"))
        builder.adjust(2)

        await message.answer(
            f"🎬 **Kino topildi:**\n\n"
            f"📌 Nomi: {title}\n"
            f"🔢 Kodi: {code}\n\n"
            f"⚠️ Rostdan ham ushbu kinoni bazadan o'chirmoqchimisiz?",
            reply_markup=builder.as_markup()
        )
        await state.set_state(DeleteMovieState.confirm_delete)
    else:
        await message.answer(f"❌ `{code}` kodli kino topilmadi. Qayta urinib ko'ring.")
        await state.clear()

@dp.callback_query(F.data.startswith("conf_del:"))
async def finalize_delete(call: types.CallbackQuery, state: FSMContext):
    code = call.data.split(":")[1]
    
    result = await delete_movie_by_code(code)
    
    if result:
        await call.message.edit_text(f"✅ Kod {code} bo'lgan kino bazadan butunlay o'chirildi.")
    else:
        await call.message.edit_text("❌ Xatolik yuz berdi yoki kino allaqachon o'chirilgan.")
    
    await state.clear()
    await call.answer()

@dp.callback_query(F.data == "cancel_del")
async def cancel_del_process(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ O'chirish jarayoni bekor qilindi.")
    await state.clear()
    await call.answer()

@dp.message(F.text == "📂 Kinolarni ko'rish")
async def send_movies_pdf_handler(message: types.Message):
    wait_msg = await message.answer("🔄 PDF hisobot tayyorlanmoqda, iltimos kuting...")
    
    try:
        file_path = await generate_movies_pdf()
        
        if file_path and os.path.exists(file_path):
            document = FSInputFile(file_path)
            await message.answer_document(
                document, 
                caption="🎬 Bazadagi barcha kinolar ro'yxati (PDF)"
            )
            await wait_msg.delete()
            
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            await wait_msg.edit_text("❌ Ma'lumotlar bazasi topilmadi yoki bo'sh.")
            
    except Exception as e:
        logging.error(f"PDF yuborishda xatolik: {e}")
        await wait_msg.edit_text("⚠️ PDF yaratishda texnik xatolik yuz berdi.")

async def main():
    await creat_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())