# Manga Text Translator

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

API_KEY=your_api_key
MODEL_ID=new-version-bubble-speech/1
IMAGES_DIR=images/
INPUT_IMAGES_DIR=original/
OUTPUT_IMAGE_PATH=translated/
DEFAULT_TARGET_LANG=ru
OCR_LANG=en
FONT_PATH=fonts/animeacev05.ttf
MAX_FONT_SIZE=15

📖 Usage
The project supports two operating modes and two ways of obtaining images:
Translation Modes:
    1. Manual Mode (default):
        Shows original text and suggested translation
        Allows entering your own translation variant
        Visually displays current and already translated bubbles
    2. Automatic Mode:
        Automatically translates all text
        Fast processing without user intervention

Image Sources:
    1. Local Files:
        python main.py --mode local
        python main.py --mode local --auto  # for automatic mode
    2. URL Loading:
        python main.py --mode url --url "https://w27.onepiece-manga-online.net/"
        python main.py --mode url --url "https://w27.onepiece-manga-online.net/" --auto

📁 Project Structure
manga_translator_project/
├── main.py                 # Main launch script
├── manga_translator/       # Main module
│   ├── __init__.py
│   └── translator.py       # Translator class
├── requirements.txt        # Dependencies
├── .env                    # Configuration
├── .env.example           # Configuration example
└── examples/              # Images directory
    ├── original/          # Source images
    └── translated/        # Translated images

🛠️ Technologies
    OpenCV for image processing
    PaddleOCR for text recognition
    Google Translator for translation
    PIL for text rendering
    Beautiful Soup for web page parsing

📝 License
    The project is distributed under the MIT license. Details in the LICENSE file.

🙏 Acknowledgments
    PaddleOCR team for the text recognition system
    Google Translate for translation service
    OpenCV community for computer vision tools

🎯 Features in Detail
Visual Progress Tracking
    Green outlines show already translated bubbles
    Red outline shows the currently processed bubble
    Real-time visual feedback during translation

Text Processing
    Intelligent text bubble detection
    High-accuracy OCR with PaddleOCR
    Smart text placement algorithms
    Font size auto-adjustment

Translation Options
    Automatic translation for quick results
    Manual correction for accuracy
    Support for multiple languages
    Context-aware translation

Image Handling
    Support for various image formats
    Web scraping capabilities
    Automatic image preprocessing
    Quality preservation

🔧 Advanced Usage
Custom Font Configuration
You can use custom fonts by placing them in the fonts directory and updating the FONT_PATH in your .env file.
Language Settings
Adjust OCR_LANG and DEFAULT_TARGET_LANG in .env to work with different languages:

OCR_LANG: Language for text recognition
DEFAULT_TARGET_LANG: Target translation language

Image Processing Settings
Fine-tune the translation process by adjusting:

MAX_FONT_SIZE: Maximum font size for translated text
Detection and recognition thresholds
Image quality parameters

💡 Tips for Best Results

1. Image Quality
    Use clear, high-resolution scans
    Ensure good contrast between text and background


2. Translation Accuracy
    Review automatic translations
    Use manual mode for important or complex text
    Consider context when correcting translations

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