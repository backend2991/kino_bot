import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

CHANNELS = ["@it_corse"] 

def sub_markup():
    builder = InlineKeyboardBuilder()
    for channel in CHANNELS:
        url = f"https://t.me/{channel.replace('@', '')}"
        builder.row(types.InlineKeyboardButton(text="Kanalga a'zo bo'lish 📢", url=url))
    
    builder.row(types.InlineKeyboardButton(text="Tekshirish ✅", callback_data="sub_check"))
    return builder.as_markup()

async def check_user_sub(user_id: int, bot: Bot):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logging.error(f"Kanalni tekshirishda xatolik ({channel}): {e}")
            return False
    return True