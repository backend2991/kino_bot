from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

CHANNELS = ["@it_corse", "-1003867376036"]

class majburiy_follow(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        bot = data['bot']
        
        for channel in CHANNELS:
            member = await bot.get_chat_member(chat_id=channel, user_id=event.from_user.id)
            
            if member.status == "left":
                buttons = [
                    [InlineKeyboardButton(text="1-kanalga a'zo bo'lish", url="https://t.me/it_corse")],
                    
                ]
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                
                return await event.answer(
                    "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
                    reply_markup=keyboard
                )

        return await handler(event, data)