import os
import hashlib
import mimetypes
import PyPDF2
import pytesseract
from PIL import Image
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

class AIDirectoryManager:
    def __init__(self):
        self.categories = {
            "Images": [".jpg", ".png", ".jpeg", ".gif", ".bmp"],
            "Documents": [".pdf", ".doc", ".docx", ".txt"],
            "Videos": [".mp4", ".mkv", ".avi", ".mov"],
            "Audio": [".mp3", ".wav", ".flac"],
            "Code": [".py", ".cpp", ".java", ".js"],
            "Other": []
        }
        self.stop_words = set(stopwords.words('english'))

    def categorize_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        for category, extensions in self.categories.items():
            if ext in extensions:
                return category
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if "image" in mime_type:
                return "Images"
            elif "text" in mime_type or "pdf" in mime_type:
                return "Documents"
            elif "video" in mime_type:
                return "Videos"
            elif "audio" in mime_type:
                return "Audio"
        return "Other"

    def suggest_folder_structure(self, directory):
        structure = {}
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                category = self.categorize_file(full_path)
                if category not in structure:
                    structure[category] = []
                structure[category].append(item)
        return structure

    def get_file_hash(self, file_path):
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
        return hash_md5.hexdigest()

    def find_duplicates(self, directory):
        hashes = {}
        duplicates = []
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                file_hash = self.get_file_hash(full_path)
                if file_hash in hashes:
                    duplicates.append((full_path, hashes[file_hash]))
                else:
                    hashes[file_hash] = full_path
        return duplicates

    def extract_text(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif ext == ".pdf":
                with open(file_path, "rb") as f:
                    pdf = PyPDF2.PdfReader(f)
                    text = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
                    return text if text.strip() else ""
            elif ext in [".jpg", ".png", ".jpeg"]:
                text = pytesseract.image_to_string(Image.open(file_path))
                return text if text.strip() else ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

    def generate_tags(self, file_path):
        if not os.path.isfile(file_path):
            return []
        text = self.extract_text(file_path)
        tags = []
        if text:
            tokens = word_tokenize(text.lower())
            tags = [word for word in tokens if word.isalnum() and word not in self.stop_words]
            tag_freq = nltk.FreqDist(tags)
            tags = [tag for tag, _ in tag_freq.most_common(5)]
        # Fallback: use file extension or name-based tags
        if not tags:
            ext = os.path.splitext(file_path)[1].lower()
            if ext:
                tags.append(ext[1:])  # e.g., "pdf"
            name = os.path.basename(file_path).lower().split('.')[0]
            tags.extend(word for word in name.split() if word.isalnum())
        return tags[:5]