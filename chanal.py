from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

CHANNELS = ["@it_corse", "-10023867376036"]

class majburiy_follow(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        
        user = event.from_user
        if not user:
            return await handler(event, data)

        bot = data['bot']
        not_joined_channels = []

        for channel in CHANNELS:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=user.id)
                if member.status in ["left", "kicked"]:
                    not_joined_channels.append(channel)
            except Exception:
                continue 

        if not_joined_channels:
            buttons = []
            for i, ch in enumerate(not_joined_channels, 1):
                url = f"https://t.me/{ch[1:]}" if ch.startswith('@') else "https://t.me/it_corse"
                buttons.append([InlineKeyboardButton(text=f"{i}-kanalga a'zo bo'lish", url=url)])
            
            buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            if isinstance(event, CallbackQuery):
                await event.answer("Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
                return
            
            return await event.answer(
                "🎬 **Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling!**", 
                reply_markup=keyboard
            )

        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            await event.message.delete()
            await event.message.answer("Rahmat! Botdan foydalanishingiz mumkin.")
            return

        return await handler(event, data)