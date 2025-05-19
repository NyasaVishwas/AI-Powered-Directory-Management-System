# AI-Powered Directory Management System

A modern, interactive file manager with AI-driven features and vibrant visualizations, built with Python and `ttkbootstrap`. Manage files and folders with ease, visualize data, and leverage AI for tagging and organization.

## Features
- **File Operations**:
  - Create, rename, delete files/folders with undo support.
  - Recycle bin integration.
  - Double-click to open files or navigate folders.
- **AI Capabilities**:
  - Auto-generate tags for files (e.g., "photo", "document").
  - Categorize files into folders based on content.
  - Find duplicate files.
- **Visualizations**:
  - **Pie Chart**: File type distribution.
  - **Tree Map**: File sizes, clickable to filter by extension.
  - **Timeline**: Files by modification date.
  - **Depth Pie**: Files by directory depth.
  - **Tag Cloud**: Tag frequency, clickable to filter by tag.
  - **File Age Bar**: Files by age (Today, This Week, This Month, Older).
- **Search**: Filter by name, tags, or content.
- **UI**:
  - Light (`flatly`) and dark (`darkly`) themes, toggleable.
  - Maximized window, clean layout with emojis (e.g., 🖥️ Explore, 📊 Visualize).
  - Context menu and keyboard shortcuts (e.g., Ctrl+R to rename).

## Requirements
- Python 3.13
- macOS (tested), Windows/Linux (untested but likely compatible)
- Tesseract OCR (for AI tagging of images/PDFs)

## Installation

1. **Clone the Repository** (or copy files to your directory):
   ```bash
   git clone <https://github.com/NyasaVishwas/AI-Powered-Directory-Management-System.git>
   cd AI-Powered-Directory-Management-System

2. **Create a Virtual Environment**: 
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows

3. **Install Dependencies**: 
   ```bash
   pip install -r requirements.txt

**Requirements include**:
- nltk==3.8.1
- pytesseract==0.3.10
- matplotlib==3.8.0
- PyPDF2==3.0.1
- python-docx==1.1.0
- ttkbootstrap==1.10.1

4. **Install Tesseract OCR**: 
- **macOS:**
   ```bash
   brew install tesseract

- **Windows:** Download and install from Tesseract at UB Mannheim.

- **Linux:**
   ```bash
   sudo apt-get install tesseract-ocr


5. **Download NLTK Data**: 
   ```bash
   import nltk
   nltk.download('punkt')
   nltk.download('averaged_perceptron_tagger')
   nltk.download('stopwords')

## Usage
- **Run the Application**: 
   ```bash
   python interface.py