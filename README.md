Manga Text Translator
A Python-based tool for automatic manga text translation. This project detects text bubbles in manga images, extracts the text using OCR, translates it, and replaces the original text with the translated version while maintaining the original layout and style.
🌟 Features

An intelligent tool for translating manga text with support for automatic and manual translation modes. The project uses computer vision to detect text bubbles, OCR for text recognition, and translation mechanisms to create translated versions of manga while preserving the original style and layout.

## ✨ Key Features

- 🔍 Automatic text bubble detection
- 📝 Text recognition using PaddleOCR
- 🌐 Automatic translation via Google Translate
- ✏️ Manual translation correction option
- 🎨 Intelligent text removal and replacement
- 📊 Visual progress tracking of translation
- 🌍 Support for different languages
- 🔄 Image loading both locally and from websites

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/oskaridze/Manga-translation.git
cd Manga-translation

python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

⚙️ Configuration
Edit the .env file with your parameters:

Configuration
Update the following variables in your .env file:
envCopyAPI_KEY=your_api_key_here
MODEL_ID=your_model_id
IMAGES_DIR=examples/
INPUT_IMAGES_DIR=original/
OUTPUT_IMAGE_PATH=translated/
DEFAULT_TARGET_LANG=ru
OCR_LANG=en
FONT_PATH=fonts/animeacev05.ttf
MAX_FONT_SIZE=15

📖 Usage

Place your manga images in the input directory specified in .env
Run the script:

python main.py

For each detected text bubble, you can:

Accept the automatic translation
Enter your own translation
Skip the bubble


The translated image will be saved to the specified output path

3. Performance
    Process images in batches
    Use automatic mode for bulk translation
    Adjust processing parameters as needed



🆘 Troubleshooting
Common issues and solutions:

1. Text Detection Issues
    Check image quality
    Adjust contrast and brightness
    Verify language settings


2. Translation Errors
    Review target language settings
    Check network connectivity
    Use manual mode for verification


3. Image Processing Problems
    Verify file formats
    Check image resolution
    Ensure sufficient system resources