import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession  # Додано для підтримки проксі
from flask import Flask
from threading import Thread
import asyncio
import requests  # Додано для роботи з API Binance

# Токен бота (замініть на ваш токен)
BOT_TOKEN = "7749413926:AAHQtjDNEMedzk0wW2kiU5ftpFKeTyuQKFM"

# Налаштування проксі (замініть на ваші дані)
PROXY_URL = "http://ваш_проксі:порт"  # Наприклад, "http://123.45.67.89:3128"

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота з використанням проксі
session = AiohttpSession(proxy=PROXY_URL)  # Створюємо сесію з проксі
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=session  # Використовуємо сесію з проксі
)
dp = Dispatcher()

# Список популярних криптовалют
CRYPTOCURRENCIES = [
    "BTC (Bitcoin)",
    "ETH (Ethereum)",
    "BNB (Binance Coin)",
    "XRP (Ripple)",
    "ADA (Cardano)",
    "DOGE (Dogecoin)",
    "DOT (Polkadot)",
    "LTC (Litecoin)",
    "SOL (Solana)",
    "TRX (Tron)"
]

# Тестовий гаманець для криптовалют
TEST_WALLET = "0x1234567890abcdef"

# Функція для отримання курсу криптовалюти через API Binance
def get_crypto_price(crypto_symbol):
    try:
        # Отримуємо символ криптовалюти (наприклад, BTCUSDT)
        symbol = crypto_symbol.split(" ")[0] + "USDT"
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        return data["price"]  # Повертаємо поточну ціну
    except Exception as e:
        return f"Помилка: {e}"

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTOCURRENCIES:
        builder.button(text=crypto, callback_data=f"crypto_{crypto}")
    builder.button(text="Перевірити оплату", callback_data="check_payment")
    builder.adjust(2)  # Кількість кнопок у рядку
    await message.answer(
        "Вітаю! Оберіть криптовалюту для оплати:",
        reply_markup=builder.as_markup()
    )

# Обробник натискання на кнопку "Перевірити оплату"
@dp.callback_query(lambda query: query.data == "check_payment")
async def check_payment(callback: types.CallbackQuery):
    await callback.answer("Оплата перевіряється...\nПоки що це тестовий режим. 😊")

# Обробник натискання на кнопку з криптовалютою
@dp.callback_query(lambda query: query.data.startswith("crypto_"))
async def select_crypto(callback: types.CallbackQuery):
    selected_crypto = callback.data.replace("crypto_", "")
    price = get_crypto_price(selected_crypto)  # Отримуємо курс криптовалюти

    builder = InlineKeyboardBuilder()
    builder.button(text="Сплатити", callback_data=f"pay_{selected_crypto}")
    builder.button(text="Перевірити курс", callback_data=f"price_{selected_crypto}")
    builder.button(text="Назад", callback_data="back_to_menu")
    builder.adjust(1)  # Кнопки у вертикальному рядку

    await callback.message.edit_text(
        f"Ви обрали: {selected_crypto}\n"
        f"Поточний курс: {price} USDT\n\n"
        f"Для оплати використовуйте тестовий гаманець:\n<code>{TEST_WALLET}</code>\n\n"
        f"Після оплати натисніть кнопку 'Сплатити'.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# Обробник натискання на кнопку "Сплатити"
@dp.callback_query(lambda query: query.data.startswith("pay_"))
async def pay_crypto(callback: types.CallbackQuery):
    selected_crypto = callback.data.replace("pay_", "")
    await callback.answer(f"Оплата {selected_crypto} успішно завершена! 🎉")

# Обробник натискання на кнопку "Перевірити курс"
@dp.callback_query(lambda query: query.data.startswith("price_"))
async def check_price(callback: types.CallbackQuery):
    selected_crypto = callback.data.replace("price_", "")
    price = get_crypto_price(selected_crypto)  # Отримуємо курс криптовалюти
    await callback.answer(f"Поточний курс {selected_crypto}: {price} USDT")

# Обробник натискання на кнопку "Назад"
@dp.callback_query(lambda query: query.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTOCURRENCIES:
        builder.button(text=crypto, callback_data=f"crypto_{crypto}")
    builder.button(text="Перевірити оплату", callback_data="check_payment")
    builder.adjust(2)  # Кількість кнопок у рядку
    await callback.message.edit_text(
        "Вітаю! Оберіть криптовалюту для оплати:",
        reply_markup=builder.as_markup()
    )

# Keep-Alive скрипт для підтримки активності
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Запуск бота та Keep-Alive скрипта
async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
