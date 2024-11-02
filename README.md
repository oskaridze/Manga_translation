Manga Text Translator
A Python-based tool for automatic manga text translation. This project detects text bubbles in manga images, extracts the text using OCR, translates it, and replaces the original text with the translated version while maintaining the original layout and style.
🌟 Features

Text bubble detection using YOLOv8
Optical Character Recognition (OCR) using PaddleOCR
Automatic translation with Google Translator
Manual translation correction option
Text removal and replacement with clean inpainting
Manga-style text sorting and placement
Support for custom fonts and text formatting

🚀 Getting Started
Prerequisites

Python 3.8+
OpenCV
PaddleOCR
PIL (Python Imaging Library)
Required Python packages (see requirements.txt)

Installation

Clone the repository:

bashCopygit clone https://github.com/yourusername/manga-translator.git
cd manga-translator

Create and activate virtual environment:

bashCopypython -m venv venv
# For Windows:
venv\Scripts\activate
# For Linux/Mac:
source venv/bin/activate

Install required packages:

bashCopypip install -r requirements.txt

Create .env file based on .env.example:

bashCopycp .env.example .env

Update the .env file with your API credentials and preferences

Configuration
Update the following variables in your .env file:
envCopyAPI_KEY=your_api_key_here
MODEL_ID=your_model_id
INPUT_IMAGES_DIR=images/
OUTPUT_IMAGE_PATH=translated_manga.jpg
DEFAULT_TARGET_LANG=ru
OCR_LANG=en
FONT_PATH=arial.ttf
MAX_FONT_SIZE=15
📖 Usage

Place your manga images in the input directory specified in .env
Run the script:

bashCopypython main.py

For each detected text bubble, you can:

Accept the automatic translation
Enter your own translation
Skip the bubble


The translated image will be saved to the specified output path

📁 Project Structure
Manga_translation/
├── main.py           # Main script
├── requirements.txt  # Python dependencies
├── .env             # Configuration file
├── .env.example     # Example configuration
├── .gitignore       # Git ignore file
└── examples/        # Input images directory
⚙️ How it Works

Text Detection: Uses YOLOv8 model to detect text bubbles in the manga image
Text Extraction: Applies PaddleOCR to extract text from detected regions
Translation: Translates extracted text using Google Translator
Text Removal: Removes original text using inpainting
Text Insertion: Places translated text in the original bubbles

🛠️ Technologies Used

YOLOv8 for text detection
PaddleOCR for text recognition
Google Translator for translation
OpenCV for image processing
PIL for text rendering
Python-dotenv for configuration

📝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the project
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

📜 License
This project is licensed under the MIT License - see the LICENSE file for details
Project Link: https://github.com/oskaridze/Manga_translation
🙏 Acknowledgments

YOLOv8 team for the detection model
PaddleOCR team for the OCR system
Google Translate for translation services
