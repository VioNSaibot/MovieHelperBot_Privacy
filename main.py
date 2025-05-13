import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TMDB_API_KEY = "447ee58f94bd39a2bef2c7593f52675b"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

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
        message += f"⭐ Оценка: {rating}/10\n\n"
        message += f"Описание:📝 {description}"

        if poster_url:
            await update.message.reply_photo(photo=poster_url, caption=message, parse_mode='HTML')
        else:
            await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text("Фильм не найден. Попробуйте другое название.")

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Пожалуйста, введите название фильма. Пример: /movie Матрица")
        return
    await search_movie(update, context, query)

async def handle_movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_title = update.message.text
    await search_movie(update, context, movie_title)

def main():

        #Токен бота
    TOKEN = '7912227603:AAH5tVoB3JuqRTLXBHnyWC8cNXOcZy5_QrI'

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', movie))
    app.add_handler(CommandHandler('movie', movie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_search))

    app.run_polling()

if __name__ == '__main__':
    main()