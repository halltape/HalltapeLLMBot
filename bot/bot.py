import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatAction, ContentType
from aiogram.utils.chat_action import ChatActionSender
from aiogram.filters import Command
import random
import aiohttp
import re
import html

from big_rag import build_context
from utils.excuses import EXCUSES
from utils.typing import WAITING
from utils.extra_instructions import prompt_instructions
from dotenv import load_dotenv


load_dotenv(dotenv_path="/app/.env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

dp = Dispatcher()
model_lock = asyncio.Lock()


def random_excuse(list_of_phrases: list):
    return random.choice(list_of_phrases)


async def ask_model(user_text: str) -> str:
    """
    Асинхронный запрос в DeepSeek (OpenAI-совместимый API).
    """
    if not DEEPSEEK_API_KEY:
        print("[CONFIG ERROR] DEEPSEEK_API_KEY пуст")
        return "У бота ключ на 12 украли!"

    # 1) Тянем контекст из векторной БД в отдельном треде,
    # чтобы не блокировать event loop aiogram
    try:
        loop = asyncio.get_running_loop()
        rag_context = await loop.run_in_executor(None, build_context, user_text)
    except Exception as e:
        print(f"[RAG ERROR] {e}")
        rag_context = ""

    # 2) Собираем финальный system prompt
    system_prompt = prompt_instructions

    if rag_context:
        system_prompt = system_prompt + "\n\n<context>\n" + rag_context + "\n</context>"

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.7,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        ) as session:
            async with session.post(
                DEEPSEEK_URL, json=payload, headers=headers
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"[MODEL HTTP ERROR {resp.status}] {error_text}")
                    return "Че-то бот походу того.. лег спать"

                data = await resp.json()

    except Exception as e:
        return "Че-то бот походу того.. лег"

    return (
        data.get("choices", [{}])[0].get("message", {}).get("content", "Пустой ответ.")
    )


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    text = (
        "Привет! 👋\n\n"
        "Я — демо-бот на базе LLM DeepSeek. Меня можно настроить под свои данные и ответы.\n\n"
        "Что могу показать:\n"
        "• как работать с RAG на Markdown и JSON;\n"
        "• как подключить свой контент и быстро переобучить контекст;\n"
        "• как выглядит диалог с кастомными инструкциями.\n\n"
        "Напиши вопрос — отвечу, опираясь на текущий демо-контент. Настроить под себя можно в коде и данных."
    )
    await message.answer(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@dp.message(Command("info"))
async def info_handler(message: types.Message):
    text = (
        "Нужна помощь?\n\n"
        "Также вступай в наш чат: https://t.me/+p-0NiSWmQ5ZhZmEy"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


# 🔹 Новый хендлер для медиа
@dp.message(
    F.content_type.in_(
        {
            ContentType.PHOTO,
            ContentType.VIDEO,
            ContentType.DOCUMENT,
            ContentType.AUDIO,
            ContentType.VOICE,
            ContentType.VIDEO_NOTE,
            ContentType.ANIMATION,
            ContentType.STICKER,
        }
    )
)
async def media_handler(message: types.Message):
    # Просто отвечаем одной из отмазок, модель не трогаем
    await message.answer(
        random_excuse(EXCUSES),
        disable_web_page_preview=True,
    )


@dp.message()
async def handle_message(message: types.Message):
    # отправляем мгновенное сообщение
    temp_msg = await message.answer(
        random_excuse(WAITING), disable_web_page_preview=True
    )
    async with model_lock:  # ⬅️ тут очередь к модели
        async with ChatActionSender(
            bot=bot, chat_id=message.chat.id, action=ChatAction.TYPING
        ):
            answer = await ask_model(message.text)

            text = re.sub(r"(?m)^\s*[\*\-]\s+", "• ", answer)
            safe = html.escape(text)
            safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)

            await message.answer(
                safe, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
    # пробуем удалить временное сообщение
    try:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=temp_msg.message_id,
        )
    except Exception:
        pass


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":

    print("start")

    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN пуст. Проверьте .env")

    bot = Bot(token=TOKEN)
    print(">>> Bot(token=..) прошёл. Debug #2")

    print(">>> Стартуем polling. Debug #3")
    asyncio.run(main())
