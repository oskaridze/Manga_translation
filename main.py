from inference import get_model
import supervision as sv
from paddleocr import PaddleOCR
from deep_translator import GoogleTranslator
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import cv2
import os

# Get environment variables
API_KEY = os.getenv('API_KEY')
MODEL_ID = os.getenv('MODEL_ID')
DEFAULT_TARGET_LANG = os.getenv('DEFAULT_TARGET_LANG')
OCR_LANG = os.getenv('OCR_LANG')
FONT_PATH = os.getenv('FONT_PATH')
MAX_FONT_SIZE = int(os.getenv('MAX_FONT_SIZE', 15))

def check_required_env_vars():
    required_vars = ['API_KEY', 'MODEL_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Load evironment variables
load_dotenv()
check_required_env_vars()

def remove_text_from_image(image, x, y, w, h):
    # Create a mask for text removal
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    mask[y:y+h, x:x+w] = 255
    
    # Apply OpenCV inpainting
    result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    return result

def translate_text(text, target_lang=DEFAULT_TARGET_LANG):
    translator = GoogleTranslator(source='auto', target=target_lang)
    try:
        return translator.translate(text)
    except:
        return text

def draw_text_on_image(image, text, x, y, w, h, max_font_size=MAX_FONT_SIZE, padding=2):
    # Convert cv2 image to PIL Image
    img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Create a reduced rectangle for text background
    inner_x, inner_y = x + padding, y + padding
    inner_w, inner_h = w - 2 * padding, h - 2 * padding
    draw.rectangle([inner_x, inner_y, inner_x + inner_w, inner_y + inner_h], fill=None)

    # Load font
    try:
        font = ImageFont.truetype(FONT_PATH, max_font_size)
    except:
        font = ImageFont.load_default()
    
    # Split text into lines
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if the word fits in the current line
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= inner_w:
            current_line = test_line
        else:
            # If word doesn't fit, add current line and start a new one
            lines.append(current_line)
            current_line = word

    # Add the last line
    if current_line:
        lines.append(current_line)

    # Center text vertically
    total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines)
    current_y = inner_y + (inner_h - total_text_height) // 2

    # Draw each line centered in the block
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        text_x = inner_x + (inner_w - line_width) // 2
        draw.text((text_x, current_y), line, fill='black', font=font)
        current_y += line_height

    # Convert back to cv2 image
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# Define the image path for inference
image_file = "examples/original/manga_page1.png"
image = cv2.imread(image_file)
output_image = image.copy()

# Load pre-trained yolov8n model
# Using new-version-bubble-speech/1
model = get_model(model_id=MODEL_ID, api_key=API_KEY)

# Run inference on the image
results = model.infer(image)[0]

# Load results into supervision Detections API
detections = sv.Detections.from_inference(results)

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang=OCR_LANG)

# Create list to store text and coordinates
text_blocks = []

# Extract text from detected bounding boxes
for detection in detections:
    x, y, w, h = detection[0]
    x, y, w, h = int(x), int(y), int(w), int(h)
    text_region = image[y:y+h, x:x+w]
    result = ocr.ocr(text_region, cls=True)
    if result[0]:
        texts = [line[1][0] for line in result[0] if 'text_bubble' not in line[1][0].lower()]
        if texts:
            text = ' '.join(texts)
            text_blocks.append({
                'text': text,
                'x': x,
                'y': y,
                'w': w,
                'h': h
            })

# Sort text blocks manga-style
page_height = image.shape[0]
section_height = page_height / 3

def get_section(block):
    y = block['y']
    if y < section_height:
        return 0
    elif y < section_height * 2:
        return 1
    else:
        return 2

# Sort text blocks
sorted_blocks = sorted(text_blocks, key=lambda b: (get_section(b), -b['x']))

# Print original text and translation
print("\nText and translation:")
print("-" * 50)
for i, block in enumerate(sorted_blocks, 1):
    original_text = block['text']
    translated_text = translate_text(original_text)
    print(f"{i}. Original: {original_text}")
    print(f"   Translation: {translated_text}\n")
    
    # First remove the original text
    output_image = remove_text_from_image(
        output_image,
        block['x'],
        block['y'],
        block['w'],
        block['h']
    )
    
    # Ask if translation needs to be modified
    custom_text = input("Enter your custom translation (or press Enter to use auto-translation): ")
    final_text = custom_text if custom_text else translated_text
    output_image = draw_text_on_image(
        output_image,
        final_text,
        block['x'],
        block['y'],
        block['w'],
        block['h']
    )

# Save the image with translated text
cv2.imwrite('examples/translated/translated_page.jpg', output_image)

print("\nTranslated image has been saved as 'examples/translated/translated_page.jpg'")