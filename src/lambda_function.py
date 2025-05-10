import json
import logging
import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Получение токена из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telegram.Bot(token=TOKEN)

def start(update, context):
    """Обработчик команды /start"""
    keyboard = [
        [telegram.InlineKeyboardButton("Опция 1", callback_data='option1'),
         telegram.InlineKeyboardButton("Опция 2", callback_data='option2'),
         telegram.InlineKeyboardButton("Last check", callback_data='option3')
         ]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Я бот, работающий на AWS Lambda. Выберите опцию:', reply_markup=reply_markup)

def help_command(update, context):
    """Обработчик команды /help"""
    update.message.reply_text('Отправьте мне сообщение, и я отвечу вам!')

def echo(update, context):
    """Обработчик текстовых сообщений"""
    update.message.reply_text(f"Вы сказали: {update.message.text}")

def button_callback(update, context):
    """Обработчик callback-запросов от инлайн-кнопок"""
    query = update.callback_query
    query.answer()  # Отправляем уведомление о получении запроса
    
    # Обработка различных callback_data
    if query.data == 'option1':
        query.edit_message_text(text="Вы выбрали опцию 1!")
    elif query.data == 'option2':
        query.edit_message_text(text="Вы выбрали опцию 2!")
    elif query.data == 'option3':
        query.edit_message_text(text="vse rabotaet kak nado ")    
    else:
        query.edit_message_text(text=f"Получен неизвестный callback: {query.data}")

def setup_dispatcher():
    """Настройка диспетчера команд"""
    dispatcher = Updater(TOKEN, use_context=True).dispatcher
    
    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
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