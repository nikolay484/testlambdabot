import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Добавляем путь к исходному коду в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):
    
    @patch('src.lambda_function.process_telegram_update')
    def test_lambda_handler_valid_request(self, mock_process):
        # Создаем тестовый запрос
        event = {
            'body': json.dumps({
                'update_id': 123456789,
                'message': {
                    'message_id': 1,
                    'from': {
                        'id': 123456789,
                        'first_name': 'Test',
                        'username': 'test_user'
                    },
                    'chat': {
                        'id': 123456789,
                        'first_name': 'Test',
                        'username': 'test_user',
                        'type': 'private'
                    },
                    'date': 1631234567,
                    'text': 'Hello, bot!'
                }
            })
        }
        
        # Настраиваем мок, чтобы он возвращал None (как в реальной функции)
        mock_process.return_value = None
        
        # Вызываем функцию-обработчик
        response = lambda_handler(event, None)
        
        # Проверяем, что функция process_telegram_update была вызвана с правильными аргументами
        update_json = json.loads(event['body'])
        mock_process.assert_called_once_with(update_json) 
        
        # Проверяем ответ
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), 'OK')
    
    def test_lambda_handler_invalid_request(self):
        # Создаем тестовый запрос без тела
        event = {}
        
        # Вызываем функцию-обработчик
        response = lambda_handler(event, None)
        
        # Проверяем ответ
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Bad Request: Not a Telegram Update')

if __name__ == '__main__':
    unittest.main()