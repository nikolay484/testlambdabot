import requests
import json
import time
import base64
import os
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class KandinskyAPI:
    def __init__(self, api_key=None, api_secret=None):
        """Инициализация клиента API Kandinsky"""
        self.api_key = api_key or os.environ.get('KANDINSKY_API_KEY')
        self.api_secret = api_secret or os.environ.get('KANDINSKY_API_SECRET')
        self.base_url = "https://api.kandinsky.ai/v1"
        
        if not self.api_key or not self.api_secret:
            logger.warning("API ключи Kandinsky не настроены")
    
    def _get_auth_header(self):
        """Получение заголовка авторизации"""
        return {
            "X-API-KEY": self.api_key,
            "X-API-SECRET": self.api_secret,
            "Content-Type": "application/json"
        }
    
    def generate_image(self, prompt, negative_prompt="", width=1024, height=1024, num_images=1):
        """Генерация изображения по текстовому описанию"""
        try:
            # Шаг 1: Создание задания на генерацию
            task_url = f"{self.base_url}/text2image/run"
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_images": num_images
            }
            
            response = requests.post(
                task_url, 
                headers=self._get_auth_header(),
                data=json.dumps(payload)
            )
            response.raise_for_status()
            
            task_id = response.json().get("task_id")
            if not task_id:
                logger.error("Не удалось получить task_id")
                return None
            
            # Шаг 2: Ожидание завершения генерации
            status_url = f"{self.base_url}/text2image/status/{task_id}"
            
            max_attempts = 30
            for attempt in range(max_attempts):
                status_response = requests.get(
                    status_url,
                    headers=self._get_auth_header()
                )
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "DONE":
                    # Шаг 3: Получение результатов
                    images = status_data.get("images", [])
                    if not images:
                        logger.error("Изображения не найдены в ответе")
                        return None
                    
                    # Возвращаем список изображений в формате PIL
                    result_images = []
                    for img_data in images:
                        img_bytes = base64.b64decode(img_data)
                        img = Image.open(BytesIO(img_bytes))
                        result_images.append(img)
                    
                    return result_images
                
                elif status == "FAILED":
                    logger.error(f"Задание не выполнено: {status_data.get('error')}")
                    return None
                
                # Ждем перед следующей проверкой
                time.sleep(2)
            
            logger.error("Превышено максимальное время ожидания")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения: {str(e)}")
            return None
    
    def save_image(self, image, output_path):
        """Сохранение изображения на диск"""
        try:
            image.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении изображения: {str(e)}")
            return False