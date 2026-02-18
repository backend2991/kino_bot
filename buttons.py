from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def admin_menu():
    a_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🔄 Kino yangilash'), KeyboardButton(text='➕ Kino qo\'shish'), KeyboardButton(text='🗑 Kino o\'chirish')],
            [KeyboardButton(text='📊 Statistika'), KeyboardButton(text='🎬 Reklama tarqatish'), KeyboardButton(text='🚫 Foydalanuvchilarni bloklash')],
            [KeyboardButton(text='🎥 Kinolarni ko\'rish'), KeyboardButton(text='🔓 Foydalanuvchilarni blokdan chiqarish'), KeyboardButton(text='📂 Foydalanuvchilarni ko\'rish')]
        ],
        resize_keyboard=True
    )
    return a_menu


def users_menu():
    u_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🔎 Kino qidirish')]
        ],
        resize_keyboard=True
    )
    return u_menu


def confirm_yes_no():
    confirm_ = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Ha', callback_data='yes'), 
                InlineKeyboardButton(text='❌ Yo\'q', callback_data='no')
            ]
        ]
    )
    return confirm_


kino_sifati_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎬 480p (Past)"),
            KeyboardButton(text="🎬 720p (HD)")
        ],
        [
            KeyboardButton(text="🎬 1080p (Full HD)"),
            KeyboardButton(text="💎 4K Ultra HD")
        ],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)



language_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🇺🇿 O'zbekcha"),
            KeyboardButton(text="🇷🇺 Русский"),
            KeyboardButton(text="🇺🇸 English")
        ],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)


janr_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍿 Jangari"), KeyboardButton(text="😱 Dahshat")],
        [KeyboardButton(text="😂 Komediya"), KeyboardButton(text="❤️ Melodrama")],
        [KeyboardButton(text="🕵️ Fantastika"), KeyboardButton(text="🧐 Detektiv")],
        [KeyboardButton(text="🎞 Tarixiy"), KeyboardButton(text="🦁 Multfilm")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)

def mir_menu():
    mir_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Foydalanuvchilar ro\'yhati')]
        ],
        resize_keyboard=True
    )
    return mir_menu