import asyncio
import logging
import sys
from aiogram.types import FSInputFile
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, types,F
from aiogram.filters import Command
from db import creat_table, insert_movie, insert_users, get_movie_by_code, find_user, is_ban, check_user_ban, is_not_ban, delete_movie_by_code, update_user_subscription, check_subscription_expiry
from buttons import admin_menu, users_menu, confirm_yes_no, kino_sifati_menu, language_menu, janr_menu, mir_menu, subscription_reply_menu, admin_approval_keys
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from states import admin_data, find_movie, find_movie_admin, block_user, unblock_user, DeleteMovieState, PaymentState
from chanal import check_user_sub, sub_markup
from aiogram.types import ReplyKeyboardRemove
from pdf_usres import generate_users_pdf
from pdf_movies import generate_movies_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TOKEN = "8222917234:AAGxqndfNnBAzh9lS8HrYeNuABz3YNINSJQ"
ADMINS = [858454334,]
from aiogram.client.session.aiohttp import AiohttpSession


PROXY_URL = 'http://proxy.server:3128'
session = AiohttpSession(proxy=PROXY_URL)

bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

@dp.message(Command('start'))
async def start_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    # Ban holatini tekshirish
    is_not_banned = await check_user_ban(user_id)
    if not is_not_banned:
        return await message.answer("Siz botdan foydalanishdan chetlatilgansiz! ❌")

    # Kanallarga a'zolikni tekshirish
    if await check_user_sub(user_id, bot):
        # Admin bo'lsa
        if user_id in ADMINS:
            await message.answer(f"Xush kelibsiz Admin, {full_name}", reply_markup=admin_menu())
            return

        # Bazadan foydalanuvchini olish
        user_data = await find_user(user_id)
        if not user_data:
            await insert_users(user_id=user_id, full_name=full_name, is_bann='false')
            user_data = await find_user(user_id)

        # PULLIK OBUNANI TEKSHIRISH
        # user_data[4] bu 'sub_type' ustuni
        if user_data[4] == 'none': 
            await message.answer(
                f"Xush kelibsiz {full_name}!\nBotdan foydalanish uchun tariflardan birini tanlang va obuna bo'ling:", 
                reply_markup=subscription_reply_menu()
            )
        else:
            # Obunasi bor foydalanuvchiga asosiy menyu
            await message.answer(f"Xush kelibsiz {full_name}", reply_markup=users_menu())
    else:
        # Kanalga a'zo bo'lmagan bo'lsa
        await message.answer(
            f"Hurmatli {full_name}, botdan foydalanish uchun kanallarga a'zo bo'ling:",
            reply_markup=sub_markup() 
        )

# --- 2. TARIF TANLANGANDA (REPLY TUGMALAR) ---
@dp.message(F.text.contains("Standart (4.000 so'm)"))
async def process_standard_sub(message: types.Message, state: FSMContext):
    await state.update_data(chosen_sub="standard", price="4.000")
    await message.answer(
        "Siz **Standart** tarifini tanladingiz.\n\n"
        "💳 Karta: `8600000011112222`\n"
        "💰 Summa: 4.000 so'm\n\n"
        "📸 To'lov qiling va chekni (skrinshot) yuboring.",
        parse_mode="Markdown"
    )
    await state.set_state(PaymentState.waiting_for_screenshot)

@dp.message(F.text.contains("Premium (8.000 so'm)"))
async def process_premium_sub(message: types.Message, state: FSMContext):
    await state.update_data(chosen_sub="premium", price="8.000")
    await message.answer(
        "Siz **Premium** tarifini tanladingiz.\n\n"
        "💳 Karta: `8600000011112222`\n"
        "💰 Summa: 8.000 so'm\n\n"
        "📸 To'lov qiling va chekni (skrinshot) yuboring.",
        parse_mode="Markdown"
    )
    await state.set_state(PaymentState.waiting_for_screenshot)

# --- 3. SKRINSHOTNI QABUL QILISH ---
@dp.message(PaymentState.waiting_for_screenshot, F.photo)
async def get_payment_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sub_type = data.get('chosen_sub')
    price = data.get('price')
    
    admin_id = 8584543342  # <--- O'Z ID-INGIZNI YOZING
    
    await message.answer("✅ Rahmat! Chekingiz adminga yuborildi.")
    
    await bot.send_photo(
        admin_id, 
        message.photo[-1].file_id, 
        caption=f"🔔 Yangi to'lov!\n👤: {message.from_user.full_name}\n🆔: {message.from_user.id}\n💎 Tarif: {sub_type}\n💵 Summa: {price}",
        reply_markup=admin_approval_keys(message.from_user.id, sub_type)
    )
    await state.clear()

# --- 4. ADMIN TASDIQLASHI (CALLBACK) ---
@dp.callback_query(F.data.startswith('admin_'))
async def admin_decision(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    action, user_id = parts[1], int(parts[2])
    
    if action == 'app':
        sub_type = parts[3]
        await update_user_subscription(user_id, sub_type, 30) # 30 kunga
        await bot.send_message(user_id, "✅ To'lovingiz tasdiqlandi! Bot ochildi.", reply_markup=users_menu())
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ TASDIQLANDI")
    else:
        await bot.send_message(user_id, "❌ To'lovingiz rad etildi.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ RAD ETILDI")
    await callback.answer()

@dp.callback_query(F.data == "sub_check")
async def callback_sub_check(call: types.CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    full_name = call.from_user.full_name

    if await check_user_sub(user_id, bot):
        await call.message.delete()
        if user_id in ADMINS:
            await call.message.answer(f"Xush kelibsiz Admin, {full_name}", reply_markup=admin_menu())
        else:
            await call.message.answer(f"Xush kelibsiz {full_name}", reply_markup=users_menu())
            await insert_users(user_id=user_id, full_name=full_name, is_bann='false')
    else:
        await call.answer("Siz hali barcha kanallarga a'zo bo'lmagansiz! ❌", show_alert=True)
            

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