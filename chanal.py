from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

# Kanallar ro'yxati
CHANNELS = ["@it_corse", "-10023867376036"] # ID larda -100 bilan boshlanishiga e'tibor bering

class majburiy_follow(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Agar foydalanuvchi xabar yubormasa (masalan, edit qilsa) davom ettirish
        if not event.from_user:
            return await handler(event, data)

        bot = data['bot']
        not_joined_channels = []

        for channel in CHANNELS:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=event.from_user.id)
                if member.status in ["left", "kicked"]:
                    not_joined_channels.append(channel)
            except TelegramBadRequest:
                # Agar bot admin bo'lmasa yoki kanal topilmasa shu yerga tushadi
                print(f"Xatolik: Bot {channel} kanalida admin emas!")
                continue 

        if not_joined_channels:
            # Dinamik ravishda tugmalar yaratish
            buttons = []
            for i, ch in enumerate(not_joined_channels, 1):
                # Username bo'lsa @ ni olib tashlab link qilish, ID bo'lsa asosiy kanal linkini qo'yish
                url = f"https://t.me/{ch[1:]}" if ch.startswith('@') else "https://t.me/it_corse"
                buttons.append([InlineKeyboardButton(text=f"{i}-kanalga a'zo bo'lish", url=url)])
            
            # Tekshirish tugmasini qo'shish (ixtiyoriy)
            buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            return await event.answer(
                "🎬 **Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling!**\n\nA'zo bo'lib qayta /start bosing.",
                reply_markup=keyboard
            )

        return await handler(event, data)