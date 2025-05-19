import json
import time
import requests
import logging
import os
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class FusionBrainAPI:
    def __init__(self, api_key=None, api_secret=None):
        """Инициализация клиента API FusionBrain"""
        self.api_key = api_key or os.environ.get('KANDINSKY_API_KEY')
        self.api_secret = api_secret or os.environ.get('KANDINSKY_SECRET_KEY')
        self.URL = "https://api-key.fusionbrain.ai/"
        
        self.AUTH_HEADERS = {
            'X-Key': f'Key {self.api_key}',
            'X-Secret': f'Secret {self.api_secret}',
        }
        
        if not self.api_key or not self.api_secret:
            logger.warning("API ключи FusionBrain не настроены")

    def get_pipeline(self):
        """Получение ID пайплайна"""
        try:
            response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
            response.raise_for_status()
            data = response.json()
            return data[0]['id']
        except Exception as e:
            logger.error(f"Ошибка при получении pipeline: {str(e)}")
            return None

    def generate(self, prompt, pipeline, images=1, width=1024, height=1024):
        """Запуск генерации изображения"""
        try:
            params = {
                "type": "GENERATE",
                "numImages": images,
                "width": width,
                "height": height,
                "generateParams": {
                    "query": f'{prompt}'
                }
            }

            data = {
                'pipeline_id': (None, pipeline),
                'params': (None, json.dumps(params), 'application/json')
            }
            
            response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
            response.raise_for_status()
            data = response.json()
            return data['uuid']
        except Exception as e:
            logger.error(f"Ошибка при запуске генерации: {str(e)}")
            return None

    def check_generation(self, request_id, attempts=10, delay=10):
        """Проверка статуса генерации и получение результатов"""
        try:
            while attempts > 0:
                response = requests.get(self.URL + 'key/api/v1/pipeline/status/' + request_id, headers=self.AUTH_HEADERS)
                response.raise_for_status()
                data = response.json()
                
                if data['status'] == 'DONE':
                    return data['result']['files']
                
                attempts -= 1
                time.sleep(delay)
            
            logger.warning(f"Превышено время ожидания для запроса {request_id}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса генерации: {str(e)}")
            return None
    
    def generate_image(self, prompt, width=1024, height=1024, num_images=1):
        """Генерация изображения по текстовому описанию"""
        try:
            # Получаем ID пайплайна
            pipeline_id = self.get_pipeline()
            if not pipeline_id:
                logger.error("Не удалось получить pipeline_id")
                return None
            
            # Запускаем генерацию
            uuid = self.generate(prompt, pipeline_id, images=num_images, width=width, height=height)
            if not uuid:
                logger.error("Не удалось запустить генерацию")
                return None
            
            # Получаем результаты
            files = self.check_generation(uuid)
            if not files:
                logger.error("Не удалось получить результаты генерации")
                return None
            
            # Преобразуем результаты в изображения
            result_images = []
            for file_url in files:
                try:
                    # Загружаем изображение по URL
                    img_response = requests.get(file_url)
                    img_response.raise_for_status()
                    
                    # Преобразуем в PIL Image
                    img = Image.open(BytesIO(img_response.content))
                    result_images.append(img)
                except Exception as e:
                    # Избегаем вывода бинарных данных в лог
                    error_type = type(e).__name__
                    logger.error(f"{error_type} ")
                    logger.error(f"Ошибка при загрузке изображения {file_url}: {error_type} - {str(e)[:100]}")
            
            return result_images
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения: {str(e)}")
            return None