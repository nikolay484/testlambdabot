import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import lambda_function

class TestLambdaFunction(unittest.TestCase):
    
    @patch('src.lambda_function.bot')
    @patch('src.lambda_function.client')
    def test_lambda_handler_valid_request(self, mock_openai_client, mock_bot):
        # Настраиваем моки
        mock_bot.send_message = MagicMock()
        mock_update = MagicMock()
        mock_update.message.text = "Привет"
        mock_update.effective_chat.id = 123456789
        
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
                    'text': 'Привет'
                }
            })
        }
        
        # Патчим функцию process_telegram_update
        with patch('src.lambda_function.process_telegram_update') as mock_process:
            # Вызываем функцию lambda_handler
            response = lambda_function.lambda_handler(event, None)
            
            # Проверяем, что функция process_telegram_update была вызвана
            mock_process.assert_called_once()
            
            # Проверяем ответ
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(response['body'], json.dumps('OK'))
    
    def test_lambda_handler_invalid_request(self):
        # Создаем тестовый запрос без тела
        event = {}
        
        # Вызываем функцию lambda_handler
        response = lambda_function.lambda_handler(event, None)
        
        # Проверяем ответ
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps('Bad Request: Not a Telegram Update'))

if __name__ == '__main__':
    unittest.main()