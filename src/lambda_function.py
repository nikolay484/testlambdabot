import json
import logging
import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import tempfile
from io import BytesIO
import requests
import openai

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Получение токена из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
bot = telegram.Bot(token=TOKEN)

# Инициализация OpenAI API
openai.api_key = OPENAI_API_KEY

def start(update, context):
    """Обработчик команды /start"""
    keyboard = [
        [telegram.InlineKeyboardButton("Генерировать изображение", callback_data='generate_image')],
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Я бот для генерации изображений с помощью OpenAI. Выберите опцию:', reply_markup=reply_markup)

def help_command(update, context):
    """Обработчик команды /help"""
    update.message.reply_text(
        'Доступные команды:\n'
        '/start - Начать работу с ботом\n'
        '/help - Показать справку\n'
        '/generate - Генерировать изображение по описанию\n\n'
        'Или просто отправьте мне текст, начинающийся с "Нарисуй" или "Сгенерируй"'
    )

def generate_command(update, context):
    """Обработчик команды /generate"""
    # Проверяем, есть ли аргументы команды
    if context.args:
        prompt = ' '.join(context.args)
        generate_image_process(update, context, prompt)
    else:
        update.message.reply_text(
            'Пожалуйста, укажите описание изображения после команды.\n'
            'Например: /generate красивый закат над морем'
        )

def echo(update, context):
    """Обработчик текстовых сообщений"""
    text = update.message.text.lower()
    
    # Проверяем, начинается ли сообщение с ключевых слов для генерации
    if text.startswith(('нарисуй', 'сгенерируй', 'создай', 'draw', 'generate')):
        # Извлекаем описание изображения
        for prefix in ['нарисуй', 'сгенерируй', 'создай', 'draw', 'generate']:
            if text.startswith(prefix):
                prompt = text[len(prefix):].strip()
                break
        
        if prompt:
            generate_image_process(update, context, prompt)
        else:
            update.message.reply_text('Пожалуйста, укажите описание изображения.')
    else:
        update.message.reply_text(f"Вы сказали: {update.message.text}\n\nЧтобы сгенерировать изображение, начните сообщение со слова 'Нарисуй' или используйте команду /generate.")

def generate_image_process(update, context, prompt):
    """Процесс генерации изображения с использованием OpenAI"""
    # Проверяем настройки API
    if not OPENAI_API_KEY:
        logger.error("API ключ OpenAI не настроен")
        update.message.reply_text('Извините, API для генерации изображений не настроен.')
        return
    
    # Отправляем сообщение о начале генерации
    message = update.message.reply_text('Генерирую изображение, это может занять некоторое время...')
    
    try:
        # Генерируем изображение с помощью OpenAI DALL-E
        logger.info(f"Начинаем генерацию изображения с запросом: {prompt}")
        
        response = openai.Image.create(
            prompt=prompt,
            n=1,  # количество изображений
            size="1024x1024"  # размер изображения
        )
        
        # Получаем URL изображения
        image_url = response['data'][0]['url']
        
        # Скачиваем изображение
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            raise Exception(f"Не удалось скачать изображение, код ответа: {image_response.status_code}")
        
        # Создаем объект BytesIO из скачанного изображения
        img_byte_arr = BytesIO(image_response.content)
        
        # Отправляем изображение пользователю
        bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_byte_arr,
            caption=f"Изображение по запросу: {prompt}"
        )
        
        # Удаляем сообщение о генерации
        bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=message.message_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {str(e)}")
        update.message.reply_text(f'Произошла ошибка при генерации изображения: {str(e)}')

def button_callback(update, context):
    """Обработчик callback-запросов от инлайн-кнопок"""
    query = update.callback_query
    query.answer()  # Отправляем уведомление о получении запроса
    
    # Обработка различных callback_data
    if query.data == 'generate_image':
        query.edit_message_text(
            text="Пожалуйста, отправьте мне описание изображения, которое хотите сгенерировать.\n"
                 "Например: 'Нарисуй космический корабль в стиле киберпанк'"
        )
    else:
        query.edit_message_text(text=f"Получен неизвестный callback: {query.data}")

def setup_dispatcher():
    """Настройка диспетчера команд"""
    dispatcher = Updater(TOKEN, use_context=True).dispatcher
    
    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("generate", generate_command, pass_args=True))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))  # Добавляем обработчик callback-запросов
    
    return dispatcher

def process_telegram_update(update_json):
    """Обработка обновления от Telegram"""
    update = telegram.Update.de_json(update_json, bot)
    dispatcher = setup_dispatcher()
    dispatcher.process_update(update)

def lambda_handler(event, context):
    """Функция-обработчик AWS Lambda"""
    logger.info('Event: %s', event)
    
    try:
        # Проверка, является ли запрос от API Gateway
        if 'body' in event:
            update_json = json.loads(event['body'])
            process_telegram_update(update_json)
            return {
                'statusCode': 200,
                'body': json.dumps('OK')
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('Bad Request: Not a Telegram Update')
            }
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }