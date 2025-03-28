import os
import shutil
import re
import json
import nltk
import joblib
import mimetypes
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from collections import Counter

# Ensure nltk resources are available
nltk.download('punkt')

# File categories
CATEGORIES = {
    "Images": [".jpg", ".png", ".jpeg", ".gif", ".bmp"],
    "Documents": [".pdf", ".docx", ".txt", ".pptx", ".xlsx"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv"],
    "Audio": [".mp3", ".wav", ".aac", ".flac"],
    "Archives": [".zip", ".rar", ".tar", ".gz"],
    "Others": []
}

# Function to categorize files
def categorize_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Others"

# Function to sort files into categories
def sort_files(directory):
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            category = categorize_file(file)
            category_dir = os.path.join(directory, category)
            os.makedirs(category_dir, exist_ok=True)
            shutil.move(file_path, os.path.join(category_dir, file))

# Function to train a model for text-based file categorization
def train_text_classifier():
    data = [
        ("Annual Report 2022.pdf", "Documents"),
        ("holiday_photo.jpg", "Images"),
        ("presentation.pptx", "Documents"),
        ("song.mp3", "Audio"),
        ("movie.mp4", "Videos")
    ]
    df = pd.DataFrame(data, columns=["filename", "category"])
    
    vectorizer = TfidfVectorizer()
    classifier = MultinomialNB()
    model = make_pipeline(vectorizer, classifier)
    
    model.fit(df["filename"], df["category"])
    joblib.dump(model, "file_classifier.pkl")
    
# Function to predict file category using AI
def predict_category(filename):
    model = joblib.load("file_classifier.pkl")
    return model.predict([filename])[0]

# Function to implement smart search
def smart_search(directory, query):
    query_tokens = set(nltk.word_tokenize(query.lower()))
    matches = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(token in file.lower() for token in query_tokens):
                matches.append(os.path.join(root, file))
    
    return matches

# Function to analyze file usage patterns
def analyze_file_usage(directory):
    file_stats = Counter()
    for root, _, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            file_stats[ext] += 1
    
    return dict(file_stats)

# Example usage
directory = "./test_directory"
train_text_classifier()  # Train model once
sort_files(directory)  # Organize files
detected_files = smart_search(directory, "report")  # Search files
file_patterns = analyze_file_usage(directory)  # Analyze file patterns

print("Detected Files:", detected_files)
print("File Usage Patterns:", file_patterns)
