import os
import argparse
import requests
from bs4 import BeautifulSoup
from manga_translator.translator import MangaTranslator, translate_text
from dotenv import load_dotenv

def parse_images_from_url(url, input_dir):
    """Парсит изображения с указанного URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        downloaded_images = []
        for i, pic in enumerate(soup.find_all('img'), 1):
            img_url = pic.get('src')
            if not img_url:
                continue
                
            response = requests.get(img_url)
            if response.status_code == 200:
                image_path = os.path.join(input_dir, f"{i}.png")
                with open(image_path, 'wb') as file:
                    file.write(response.content)
                downloaded_images.append(image_path)
                print(f'Downloaded image {i}: {image_path}')
            else:
                print(f'Failed to download image {i}')
        
        return downloaded_images
    except Exception as e:
        print(f"Error parsing images: {e}")
        return []

def process_local_images(input_dir):
    """Получает список локальных изображений"""
    supported_formats = ('.png', '.jpg', '.jpeg', '.webp')
    images = []
    
    for file in sorted(os.listdir(input_dir)):
        if file.lower().endswith(supported_formats):
            images.append(os.path.join(input_dir, file))
    
    return images

def translate_manga(image_path, output_dir, auto_translate=False):
    """Переводит одно изображение манги"""
    try:
        translator = MangaTranslator(image_path)
        text_blocks = translator.process_bubbles()
        
        # Определяем имя выходного файла
        basename = os.path.basename(image_path)
        output_path = os.path.join(output_dir, f"translated_{basename}")
        
        # Используем обновленный метод с поддержкой автоматического режима
        translator.translate_and_replace_text(text_blocks, auto_mode=auto_translate)
        
        translator.save_result(output_path)
        return True
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Manga Translator')
    parser.add_argument('--mode', choices=['url', 'local'], required=True,
                      help='Source of images: url or local directory')
    parser.add_argument('--url', help='URL to parse images from (required if mode=url)')
    parser.add_argument('--auto', action='store_true',
                      help='Enable automatic translation without user confirmation')
    
    args = parser.parse_args()

    # Получаем пути из переменных окружения
    input_dir = os.getenv('IMAGES_DIR') + os.getenv('INPUT_IMAGES_DIR')
    output_dir = os.getenv('IMAGES_DIR') + os.getenv('OUTPUT_IMAGE_PATH')

    # Создаем директории если они не существуют
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Получаем список изображений для обработки
    if args.mode == 'url':
        if not args.url:
            print("Error: URL is required when mode is 'url'")
            return
        images = parse_images_from_url(args.url, input_dir)
    else:
        images = process_local_images(input_dir)

    if not images:
        print("No images found to process!")
        return

    # Обрабатываем изображения
    print(f"\nFound {len(images)} images to process")
    for i, image_path in enumerate(images, 1):
        print(f"\nProcessing image {i}/{len(images)}: {image_path}")
        success = translate_manga(image_path, output_dir, args.auto)
        if success:
            print(f"Successfully processed {image_path}")
        else:
            print(f"Failed to process {image_path}")

if __name__ == "__main__":
    main()