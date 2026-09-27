import os
import threading
import asyncio
import logging
import requests
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route("/")
def index():
    return "Bot is running"


@app.route("/health")
def health():
    return "OK"


TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

if not TOKEN:
    raise ValueError("Нет переменной TELEGRAM_TOKEN!")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("cod") != 200:
            return f"Город '{city}' не найден"
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"]
        return (f"Погода в {city}:\n"
                f"{description.capitalize()}\n"
                f"Температура: {temp}°C\n"
                f"Ощущается как: {feels_like}°C")
    except Exception as e:
        logging.error(f"Ошибка погоды: {e}")
        return "Не удалось получить погоду. Попробуй позже."


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот погоды. Напиши /weather Москва")


@dp.message(Command("weather"))
async def cmd_weather(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Напиши город так: /weather Москва")
        return
    city = parts[1]
    await message.answer(f"Секунду, запрашиваю погоду в {city}...")
    weather_text = get_weather(city)
    await message.answer(weather_text)


@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


async def main():
    # Flask — в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Бот — в главном потоке
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
