
import logging
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware


API_TOKEN = '6835315645:AAGPyEZKih_bTD7uj4N86_pWxKF73z8F0oc'


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class Form(StatesGroup):
    name = State()        # Имя пользователя
    faculty = State()     # Факультет
    group = State()       # Группа
    photo = State()       # Фото
    edit_name = State()   # Редактирование имени
    edit_faculty = State()# Редактирование факультета
    edit_group = State()  # Редактирование группы
    edit_photo = State()  # Редактирование фото
    add_question = State()# Добавление вопроса


dp.middleware.setup(LoggingMiddleware())


async def init_db():
    db = await aiosqlite.connect('users.db')
    await db.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT,
                        faculty TEXT,
                        group_number TEXT,
                        photo_id TEXT)''')
    await db.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        question TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    await db.execute('''CREATE TABLE IF NOT EXISTS likes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        liked_user_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (liked_user_id) REFERENCES users (user_id))''')
    await db.commit()
    await db.close()

# Обработчик команды /start
@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await Form.name.set()
    await message.reply("Как тебя зовут?")


# код обработчиков для регистрации!!!


# код обработчиков для редактирования профиля!


async def add_question_to_db(user_id, question):
    db = await aiosqlite.connect('users.db')
    await db.execute('INSERT INTO questions (user_id, question) VALUES (?, ?)', (user_id, question))
    await db.commit()
    await db.close()


async def add_like(user_id, liked_user_id):
    db = await aiosqlite.connect('users.db')
    await db.execute('INSERT INTO likes (user_id, liked_user_id) VALUES (?, ?)', (user_id, liked_user_id))
    await db.commit()
    await db.close()


async def get_user_data(user_id):
    db = await aiosqlite.connect('users.db')
    cursor = await db.execute('SELECT name, faculty, group_number, photo_id FROM users WHERE user_id = ?', (user_id,))
    row = await cursor.fetchone()
    await cursor.close()
    await db.close()
    return row


async def get_users_for_search(current_user_id):
    db = await aiosqlite.connect('users.db')
    cursor = await db.execute('SELECT user_id, name, faculty, group_number, photo_id FROM users WHERE user_id != ?', (current_user_id,))
    rows = await cursor.fetchall()
    await cursor.close()
    await db.close()
    return rows


async def get_user_likes(user_id):


db = await aiosqlite.connect('users.db')
    cursor = await db.execute('''SELECT u.user_id, u.name, u.faculty, u.group_number, u.photo_id
                                 FROM users u
                                 JOIN likes l ON u.user_id = l.liked_user_id
                                 WHERE l.user_id = ?''', (user_id,))
    rows = await cursor.fetchall()
    await cursor.close()
    await db.close()
    return rows


@dp.message_handler(commands=['add_question'])
async def cmd_add_question(message: types.Message):
    await Form.add_question.set()
    await message.reply("Введите ваш вопрос:")

@dp.message_handler(state=Form.add_question)
async def process_add_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    question = message.text
    await add_question_to_db(user_id, question)
    await state.finish()
    await message.reply("Вопрос добавлен.")

# Обработчик для команды поиска
@dp.message_handler(commands=['search'])
async def cmd_search(message: types.Message):
    user_id = message.from_user.id
    users = await get_users_for_search(user_id)
    if users:
        for user in users:
            user_id, name, faculty, group, photo_id = user
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Лайк", callback_data=f"like_{user_id}"))
            markup.add(types.InlineKeyboardButton("Дизлайк", callback_data=f"dislike_{user_id}"))
            await bot.send_photo(chat_id=message.chat.id, photo=photo_id, caption=f"Имя: {name}\nФакультет: {faculty}\nГруппа: {group}", reply_markup=markup)
    else:
        await message.reply("Пользователи не найдены.")


@dp.callback_query_handler(lambda c: c.data.startswith('like_'))
async def handle_like(callback_query: types.CallbackQuery):
    liking_user_id = callback_query.from_user.id
    liked_user_id = int(callback_query.data.split('_')[1])
    await add_like(liking_user_id, liked_user_id)
    await bot.answer_callback_query(callback_query.id, text="Вы поставили лайк!")

@dp.callback_query_handler(lambda c: c.data.startswith('dislike_'))
async def handle_dislike(callback_query: types.CallbackQuery):
    # код обработчика!!!


@dp.message_handler(commands=['likes'])
async def cmd_likes(message: types.Message):
    user_id = message.from_user.id
    likes = await get_user_likes(user_id)
    if likes:
        for like in likes:
            user_id, name, faculty, group, photo_id = like
            await bot.send_photo(chat_id=message.chat.id, photo=photo_id, caption=f"Имя: {name}\nФакультет: {faculty}\nГруппа: {group}")
    else:
        await message.reply("У вас пока нет лайков.")

if name == 'main':
    asyncio.run(init_db())
    executor.start_polling(dp, skip_updates=True)
