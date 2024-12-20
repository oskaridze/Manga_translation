from inference import get_model
import supervision as sv
from paddleocr import PaddleOCR
from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
import numpy as np
import re
import cv2
import os

# Get environment variables
API_KEY = os.getenv('API_KEY')
MODEL_ID = os.getenv('MODEL_ID')
IMAGES_DIR = os.getenv('IMAGES_DIR')
INPUT_IMAGES_DIR = os.getenv('INPUT_IMAGES_DIR')
OUTPUT_IMAGE_PATH = os.getenv('OUTPUT_IMAGE_PATH')
DEFAULT_TARGET_LANG = os.getenv('DEFAULT_TARGET_LANG')
OCR_LANG = os.getenv('OCR_LANG')
FONT_PATH = os.getenv('FONT_PATH')
MAX_FONT_SIZE = int(os.getenv('MAX_FONT_SIZE', 15))

def check_required_env_vars():
    required_vars = ['API_KEY', 'MODEL_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def translate_text(text, target_lang=DEFAULT_TARGET_LANG):
    translator = GoogleTranslator(source='auto', target=target_lang)
    try:
        return translator.translate(text)
    except:
        return text

class MangaTranslator:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        self.output_image = self.image.copy()
        self.page_height = self.image.shape[0]
        self.section_height = self.page_height / 3
        
        load_dotenv()
        check_required_env_vars()

        self.model = get_model(model_id=MODEL_ID, api_key=API_KEY)
        # self.ocr = PaddleOCR(use_angle_cls=True, lang=OCR_LANG)
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=OCR_LANG,
            det_db_thresh=0.3,  # Увеличивает чувствительность детектора текста
            det_db_box_thresh=0.5,  # Порог уверенности для текстовых боксов
            rec_batch_num=6,  # Размер батча для распознавания
            use_gpu=True  # Использование GPU если доступно
        )
    

    def preprocess_text_region(self, text_region):
        """Предобработка изображения перед OCR"""
        # Увеличение размера изображения для лучшего распознавания
        scale = 2
        text_region = cv2.resize(text_region, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Преобразование в оттенки серого
        gray = cv2.cvtColor(text_region, cv2.COLOR_BGR2GRAY)
        
        # Повышение контраста
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(gray)
        
        # Бинаризация изображения
        _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary

    def remove_text_from_image(image, x, y, w, h):
        """Удаляет текст из прямоугольной области и заполняет её белым цветом"""
        # Создаем маску с небольшим отступом
        padding = 2
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        mask[max(0, y-padding):min(image.shape[0], y+h+padding), 
            max(0, x-padding):min(image.shape[1], x+w+padding)] = 255
        
        # Создаем белый фон
        white_background = np.ones_like(image) * 255
        
        # Применяем маску
        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        result = np.where(mask_3channel == 255, white_background, image)
        
        # Сглаживаем края
        edge_mask = cv2.dilate(mask, None, iterations=2) - cv2.erode(mask, None, iterations=2)
        result = cv2.inpaint(result, edge_mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
        
        return result

    def draw_text_on_image(self, image, text, x, y, w, h, max_font_size=MAX_FONT_SIZE, padding=4):
        """Рисует текст на изображении с переносом слов"""
        img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # Проверка минимальных размеров
        if w < 20 or h < 20:
            print(f"Warning: Box too small for text: {w}x{h}")
            return image
        
        inner_x = x + padding
        inner_y = y + padding
        inner_w = w - 2 * padding
        inner_h = h - 2 * padding
        
        try:
            min_font_size = 8
            font_size = min(h//2, max_font_size)
            
            while font_size >= min_font_size:
                try:
                    font = ImageFont.truetype(FONT_PATH, font_size)
                except:
                    print("Failed to load custom font, using default")
                    font = ImageFont.load_default()
                    
                words = text.split()
                lines = []
                current_line = ""
                
                for word in words:
                    # Проверяем, поместится ли слово целиком
                    test_line = f"{current_line} {word}".strip()
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    
                    if bbox[2] - bbox[0] <= inner_w:
                        current_line = test_line
                    else:
                        # Если текущая строка не пуста, добавляем её
                        if current_line:
                            lines.append(current_line)
                            current_line = ""
                        
                        # Проверяем, нужно ли разбивать слово
                        word_bbox = draw.textbbox((0, 0), word, font=font)
                        if word_bbox[2] - word_bbox[0] > inner_w:
                            # Разбиваем длинное слово
                            word_parts = self.hyphenate_word(word, inner_w, draw, font)
                            if word_parts:
                                lines.append(word_parts[0])
                                current_line = word_parts[1]
                        else:
                            current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                # Проверяем общую высоту
                total_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] 
                                for line in lines)
                
                if total_height <= inner_h:
                    # Вертикальное центрирование
                    start_y = inner_y + (inner_h - total_height) // 2
                    current_y = start_y
                    
                    # Рисуем текст
                    for line in lines:
                        bbox = draw.textbbox((0, 0), line, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_x = inner_x + (inner_w - text_width) // 2
                        
                        draw.text((text_x, current_y), line, fill='black', font=font)
                        current_y += bbox[3] - bbox[1]
                    
                    break
                
                font_size -= 1
            
            if font_size < min_font_size:
                print(f"Warning: Could not fit text within bounds")
                font = ImageFont.load_default()
                draw.text((inner_x, inner_y), text, fill='black', font=font)
        
        except Exception as e:
            print(f"Error drawing text: {e}")
            font = ImageFont.load_default()
            draw.text((inner_x, inner_y), text, fill='black', font=font)
        
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def get_section(self, block):
        """Определяет секцию на странице для блока текста"""
        y = block['y']
        if y < self.section_height:
            return 0
        elif y < self.section_height * 2:
            return 1
        else:
            return 2

    def detect_speech_bubbles(self):
        """Определяет пузыри с текстом на изображении"""
        # Конвертируем в оттенки серого
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Применяем пороговое значение для получения бинарного изображения
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        # Находим контуры
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bubble_contours = []
        min_area = 100  # Минимальная площадь пузыря
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                # Аппроксимируем контур для сглаживания
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Добавляем контур если он достаточно гладкий
                if len(approx) > 5:
                    bubble_contours.append(contour)
        
        return bubble_contours

    def create_bubble_mask(self, contour):
        """Создает маску для конкретного пузыря"""
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, (255), -1)
        return mask

    def hyphenate_word(self, word, max_width, draw, font):
        """Разбивает длинное слово с помощью дефиса"""
        if not word:
            return []
            
        vowels = 'аеёиоуыэюяАЕЁИОУЫЭЮЯ'
        consonants = 'бвгджзйклмнпрстфхцчшщБВГДЖЗЙКЛМНПРСТФХЦЧШЩ'
        
        for i in range(len(word)-1, 1, -1):
            # Проверяем, можно ли разделить слово в этой позиции
            if (word[i-1] in vowels and word[i] in consonants) or \
            (word[i-1] in consonants and word[i] in consonants):
                # Пробуем разделить слово
                first_part = word[:i] + '-'
                bbox = draw.textbbox((0, 0), first_part, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    return [first_part, word[i:]]
        
        # Если не удалось найти подходящее место для переноса,
        # просто разделим слово пополам с дефисом
        mid = len(word) // 2
        return [word[:mid] + '-', word[mid:]]

    def remove_text_from_bubble(self, contour):
        """Удаляет текст из пузыря и заполняет его белым цветом"""
        # Создаем маску для пузыря
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, (255), -1)
        
        # Сохраняем контур пузыря
        border_mask = np.zeros_like(mask)
        cv2.drawContours(border_mask, [contour], -1, (255), 2)
        
        # Создаем белое изображение того же размера
        white_background = np.ones_like(self.output_image) * 255
        
        # Применяем маску для заполнения белым цветом
        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        self.output_image = np.where(mask_3channel == 255, white_background, self.output_image)
        
        # Восстанавливаем контур пузыря
        border_mask_3channel = cv2.cvtColor(border_mask, cv2.COLOR_GRAY2BGR)
        original_borders = cv2.bitwise_and(self.image, border_mask_3channel)
        self.output_image = cv2.addWeighted(self.output_image, 1, original_borders, 1, 0)

    def get_bubble_bounds(self, contour):
        """Получает границы пузыря"""
        return cv2.boundingRect(contour)

    def process_bubbles(self):
        """Обрабатывает все пузыри на изображении"""
        bubble_contours = self.detect_speech_bubbles()
        text_blocks = []
        
        # Сортируем контуры по размеру, чтобы исключить слишком маленькие
        bubble_contours = sorted(bubble_contours, key=cv2.contourArea, reverse=True)
        
        for contour in bubble_contours:
            area = cv2.contourArea(contour)
            if area < 100:  # Пропускаем слишком маленькие области
                continue
                
            x, y, w, h = self.get_bubble_bounds(contour)
            
            # Проверяем соотношение сторон пузыря
            aspect_ratio = w / h
            if aspect_ratio > 5 or aspect_ratio < 0.2:  # Пропускаем слишком узкие или широкие области
                continue
                
            # Создаем маску для текущего пузыря
            mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, (255), -1)
            
            # Вырезаем область с текстом
            text_region = self.image[y:y+h, x:x+w].copy()
            
            # Предобработка изображения
            processed_region = self.preprocess_text_region(text_region)
            
            # Применяем OCR с повышенной точностью
            result = self.ocr.ocr(processed_region, cls=True)
            
            if result and result[0]:
                texts = []
                confidences = []
                
                for line in result[0]:
                    if isinstance(line, list):
                        for item in line:
                            if isinstance(item, tuple) and len(item) >= 2:
                                text = item[0]  # Текст
                                confidence = item[1]  # Уверенность распознавания
                                
                                # Фильтруем результаты с низкой уверенностью
                                if confidence > 0.5:  # Порог уверенности
                                    texts.append(text)
                                    confidences.append(confidence)
                
                if texts:
                    # Объединяем текст с учетом уверенности распознавания
                    final_text = ' '.join(texts)
                    avg_confidence = sum(confidences) / len(confidences)
                    
                    # Очистка текста
                    final_text = self.clean_text(final_text)
                    
                    text_blocks.append({
                        'text': final_text,
                        'confidence': avg_confidence,
                        'contour': contour,
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h
                    })
        
        # Сортировка блоков с учетом их расположения на странице
        sorted_blocks = sorted(text_blocks, 
                            key=lambda b: (self.get_section(b), b['y'], b['x']))
        
        return sorted_blocks

    def validate_text(self, text):
        """Валидация распознанного текста"""
        if not text:
            return False
            
        # Минимальная длина текста
        if len(text) < 2:
            return False
        
        # Процент допустимых символов
        valid_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ!?.,- ')
        text_chars = set(text)
        valid_ratio = len(text_chars.intersection(valid_chars)) / len(text_chars)
        
        return valid_ratio > 0.8

    def merge_nearby_text(self, texts, max_distance=50):
        """Объединение близко расположенных текстовых блоков"""
        merged = []
        current_group = []
        
        for text in sorted(texts, key=lambda t: (t['y'], t['x'])):
            if not current_group:
                current_group.append(text)
                continue
                
            last = current_group[-1]
            if (abs(text['y'] - last['y']) < max_distance and 
                abs(text['x'] - last['x']) < max_distance):
                current_group.append(text)
            else:
                merged.append(' '.join(t['text'] for t in current_group))
                current_group = [text]
        
        if current_group:
            merged.append(' '.join(t['text'] for t in current_group))
        
        return merged

    def clean_text(self, text):
        """Очистка и нормализация распознанного текста"""
        # Удаление лишних пробелов
        text = ' '.join(text.split())
        
        # Исправление распространенных ошибок OCR
        text = text.replace('0', 'О').replace('3', 'З')
        
        return text.strip()

    def show_current_bubble(self, current_contour, processed_contours=None):
        """
        Показывает текущий обрабатываемый пузырь и уже обработанные пузыри на изображении
        
        Args:
            current_contour: Текущий обрабатываемый контур
            processed_contours: Список уже обработанных контуров
        """
        # Создаем копию изображения для отображения
        display_image = self.image.copy()
        
        # Рисуем уже обработанные контуры зеленым цветом
        if processed_contours:
            cv2.drawContours(display_image, processed_contours, -1, (0, 255, 0), 2)
        
        # Рисуем текущий контур красным цветом
        cv2.drawContours(display_image, [current_contour], -1, (0, 0, 255), 2)
        
        # Получаем размер экрана
        screen_width = 1920  # Стандартное разрешение FullHD
        screen_height = 1080
        
        # Вычисляем размер окна (70% от размера экрана)
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.7)
        
        # Масштабируем изображение, сохраняя пропорции
        aspect_ratio = display_image.shape[1] / display_image.shape[0]
        
        if aspect_ratio > 1:
            # Изображение шире, чем выше
            new_width = window_width
            new_height = int(window_width / aspect_ratio)
        else:
            # Изображение выше, чем шире
            new_height = window_height
            new_width = int(window_height * aspect_ratio)
        
        # Изменяем размер изображения
        resized_image = cv2.resize(display_image, (new_width, new_height))
        
        # Показываем изображение
        cv2.namedWindow('Current bubble', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Current bubble', new_width, new_height)
        cv2.imshow('Current bubble', resized_image)
        cv2.waitKey(1)

    def save_result(self, output_path):
        """Сохраняет результат"""
        cv2.imwrite(output_path, self.output_image)
        print(f"\nTranslated image saved as '{output_path}'")

    def translate_and_replace_text(self, text_blocks, auto_mode=False):
        """Переводит и заменяет текст в пузырях"""
        if not text_blocks:
            print("No text blocks found!")
            return
            
        previous_texts = set()  # Для отслеживания дубликатов
        processed_contours = []  # Для отслеживания обработанных контуров
        
        # Создаем окно заранее
        cv2.namedWindow('Current bubble', cv2.WINDOW_NORMAL)
            
        for i, block in enumerate(text_blocks, 1):
            original_text = block['text']
            confidence = block.get('confidence', 0)
            
            # Пропускаем дубликаты текста
            if original_text in previous_texts:
                continue
            
            previous_texts.add(original_text)
            
            # Показываем текущий пузырь и обработанные
            self.show_current_bubble(block['contour'], processed_contours)
            
            print(f"\n{i}. Original text (confidence: {confidence:.2f}):")
            print(f"   {original_text}")
            
            try:
                translated_text = translate_text(original_text)
                print(f"   Translation: {translated_text}")
            except Exception as e:
                print(f"   Translation error: {e}")
                translated_text = original_text
            
            # В автоматическом режиме используем перевод без подтверждения
            if auto_mode:
                final_text = translated_text
            else:
                custom_text = input("Enter correct text (or press Enter for auto): ")
                final_text = custom_text if custom_text else translated_text
            
            if final_text and final_text.strip() != ' ':
                self.remove_text_from_bubble(block['contour'])
                self.output_image = self.draw_text_on_image(
                    self.output_image,
                    final_text.strip().capitalize(),
                    block['x'],
                    block['y'],
                    block['w'],
                    block['h']
                )
                processed_contours.append(block['contour'])

        # Закрываем окно после завершения
        cv2.destroyAllWindows()

def main():
    # Путь к изображению
    # image_path = f'{IMAGES_DIR}{INPUT_IMAGES_DIR}4.jpeg'
    # images = glob.glob(f'{IMAGES_DIR}{INPUT_IMAGES_DIR}*.jpeg')

    response = requests.get("https://w43.1piecemanga.com/manga/one-piece-chapter-1128-2/")
    soup = BeautifulSoup(response.text, "html.parser")

    # path = f'{IMAGES_DIR}{INPUT_IMAGES_DIR}'
    # dir_list = os.listdir(path)
    # print(len(dir_list))
    
    i = 0
    for pic in soup.find_all('img'):
        i += 1
        response = requests.get(pic.get('src'))

        image_path = f'{IMAGES_DIR}{INPUT_IMAGES_DIR}{i}.png'
        output_path = f'{IMAGES_DIR}{OUTPUT_IMAGE_PATH}translated_{i}.png'

        if response.status_code == 200:
            with open(image_path, 'wb') as file:
                file.write(response.content)
            print('File downloaded successfully')
        else:
            print('Failed to download file')

        # Создаем экземпляр транслятора
        translator = MangaTranslator(image_path)
    
        # Обрабатываем изображение
        text_blocks = translator.process_bubbles()
        
        # Переводим и заменяем текст
        translator.translate_and_replace_text(text_blocks)
        
        # Сохраняем результат
        translator.save_result(output_path)

    # for image in range(len(dir_list)):
    #     image = f'{IMAGES_DIR}{INPUT_IMAGES_DIR}{i}.png'
    #     output_path = f'{IMAGES_DIR}{OUTPUT_IMAGE_PATH}translated_{i}.png'
    #     # Создаем экземпляр транслятора
    #     translator = MangaTranslator(image)
    
    #     # Обрабатываем изображение
    #     text_blocks = translator.process_bubbles()
        
    #     # Переводим и заменяем текст
    #     translator.translate_and_replace_text(text_blocks)
        
    #     # Сохраняем результат
    #     translator.save_result(output_path)

    #     i += 1

if __name__ == "__main__":
    main()