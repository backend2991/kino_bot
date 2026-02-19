import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

def sub_markup():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="1-kanalga a'zo bo'lish", url="https://t.me/it_corse"))
    
    builder.row(types.InlineKeyboardButton(text="Tekshirish ✅", callback_data="sub_check"))
    return builder.as_markup()

async def check_user_sub(user_id: int, bot: Bot):
    CHANNELS = ["@itcorse", ] 
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Xatolik: {e}")
            return False
    return True