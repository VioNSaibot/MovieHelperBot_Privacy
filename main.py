import requests
import os
import random
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request

load_dotenv()

TOKEN = os.getenv("TOKEN_BOT")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
WEBHOOK_URL = "https://moviehelperbot-privacy.onrender.com"

bot = Bot(token=TOKEN)

app = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

GENRES = {
    "💣 Боевик": 28,
    "🤡 Комедия": 35,
    "🎭 Драма": 18,
    "🪐 Фантастика": 878,
    "🧙🏻‍♂️ Фэнтези": 14,
    "👫 Мелодрама": 10749,
    "📖 Исторический": 36,
    "⚔️ Военный": 10752,
    "🔪 Триллер": 53,
    "👹 Ужасы": 27,
    "👾 Мультфильм": 16
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🔎 Поиск фильма"), KeyboardButton("❓ Случайный фильм"), KeyboardButton("🌟 Топ фильмов")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я помогу тебе подобрать или найти фильм на вечер", reply_markup=reply_markup)

async def send_top_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{TMDB_BASE_URL}/movie/top_rated?api_key={TMDB_API_KEY}&language=ru&page=1"
    response = requests.get(url)
    data = response.json()

    if data.get("results"):
        top_movies = data["results"][:10]

        for movie in top_movies:
            title = movie["title"]
            rating = movie.get("vote_average", "Нет оценки")
            description = movie.get("overview", "Описание отсутствует.")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            message = f"🎬 <b>{title}</b>\n⭐ Оценка: {rating}/10\n\n📝 {description}"
            if poster_url:
                await update.message.reply_photo(photo=poster_url, caption=message, parse_mode='HTML')
            else:
                await update.message.reply_text(message, parse_mode='HTML')

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    url = f'{TMDB_BASE_URL}/search/movie?query={query}&api_key={TMDB_API_KEY}&language=ru'
    response = requests.get(url)
    data = response.json()

    if data.get('results'):
        movie = data['results'][0]
        title = movie['title']
        description = movie.get('overview', 'Описание отсутствует.')
        rating = movie.get('vote_average', 'Нет оценки')
        poster_path = movie.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        message = f"Название: 🎬 <b>{title}</b>\n"
        message += f"Оценка: ⭐ {rating}/10\n\n"
        message += f"Описание: 📝 {description}"

        if poster_url:
            await update.message.reply_photo(photo=poster_url, caption=message, parse_mode='HTML')
        else:
            await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text("Фильм не найден. Попробуйте другое название.")

async def send_random_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, genre_id=None):
    page = random.randint(1, 500)
    url = f"{TMDB_BASE_URL}/discover/movie?api_key={TMDB_API_KEY}&language=ru&sort_by=popularity.desc&page={page}"
    if genre_id:
        url += f"&with_genres={genre_id}"
    response = requests.get(url)
    data = response.json()

    if data.get("results"):
        filtred_movie = [movie for movie in data["results"] if movie.get("vote_average", 0) > 4]
        if filtred_movie:
            movie = random.choice(filtred_movie)
            title = movie["title"]
            description = movie.get("overview", "Описание отсутствует.")
            rating = movie.get("vote_average", "Нет оценки")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            message = f"🎬 <b>{title}</b>\n⭐ Оценка: {rating}/10\n\n📝 {description}"
            keyboard = [[KeyboardButton("➕ Еще фильм")], [KeyboardButton("❌ Назад")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            if poster_url:
                await update.message.reply_photo(photo=poster_url, caption=message, parse_mode='HTML',
                                                 reply_markup=reply_markup)
            else:
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

async def handle_movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Логируем для отладки
    print(f"Получено сообщение: {text}")

    # Если пользователь выбрал команду "Поиск фильма"
    if text == "🔎 Поиск фильма":
        context.user_data["awaiting_search"] = True  # Устанавливаем флаг, что ожидаем название фильма
        await update.message.reply_text("Введите название фильма:")
        print("Установлен флаг ожидания названия фильма.")

    # Если пользователь ввел текст после команды поиска фильма
    elif context.user_data.get("awaiting_search"):
        query = text.strip()
        if query:  # Проверяем, что введено не пустое название
            print(f"Ищем фильм по запросу: {query}")
            await search_movie(update, context, query)
        else:
            await update.message.reply_text("Название фильма не может быть пустым. Пожалуйста, введите название.")
        context.user_data["awaiting_search"] = False  # Сбрасываем флаг поиска после получения фильма
        print("Флаг ожидания сброшен.")

    # Кнопка "Случайный фильм"
    elif text == "❓ Случайный фильм":
        # Если жанр не выбран, то предложим выбрать его
        if "awaiting_genre" not in context.user_data or context.user_data["awaiting_genre"] is False:
            genres_list = list(GENRES.keys())
            genres_list.append("❌ Назад")
            keyboard = []
            i = 0
            while i < len(genres_list):
                if i + 1 < len(genres_list):
                    keyboard.append([KeyboardButton(genres_list[i]), KeyboardButton(genres_list[i + 1])])
                    i += 2
                else:
                    keyboard.append([KeyboardButton(genres_list[i])])
                    i += 1
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Выберите жанр:", reply_markup=reply_markup)
            context.user_data["awaiting_genre"] = True  # Ожидаем жанр для случайного фильма
        else:
            # Если уже выбран жанр, то просто отправляем случайный фильм
            await send_random_movie(update, context, context.user_data.get("selected_genre"))



    # Кнопка "Назад"
    elif text == "❌ Назад":
        context.user_data["awaiting_genre"] = False  # Сбрасываем ожидание жанра
        await start(update, context)

    # Кнопка "Топ фильмов"
    elif text == "🌟 Топ фильмов":
        await send_top_movies(update, context)

    elif text == "➕ Еще фильм":
        genre_id = context.user_data.get("selected_genre")
        if genre_id:
            await send_random_movie(update, context, genre_id)
        else:
            await update.message.reply_text("Выберите жанр")

    # Обработка выбора жанра
    elif context.user_data.get("awaiting_genre"):
        genre_name = text
        genre_id = GENRES.get(genre_name)

        if genre_id:
            context.user_data["awaiting_genre"] = False  # Сбрасываем флаг ожидания жанра
            context.user_data["selected_genre"] = genre_id  # Сохраняем выбранный жанр
            await send_random_movie(update, context, genre_id)  # Отправляем случайный фильм для выбранного жанра
        else:
            await update.message.reply_text("Жанр не распознан, попробуйте снова")

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        await application.process_update(update)
        return "ok"
    except Exception as e:
        print("Webhook error:", e)
        return "error", 500

@app.route("/", methods=["GET"])
def home():
    return "Бот работает через вебхук! ✅"

# --- Установка хендлеров и webhook

def setup():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_search))

async def on_startup():
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    print("Webhook установлен!")

def run():
    setup()
    asyncio.get_event_loop().run_until_complete(on_startup())
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

run()
