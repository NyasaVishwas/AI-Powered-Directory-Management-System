#!/usr/bin/env python
# coding: utf-8

# In[3]:


import os
import joblib
import numpy as np
import re
import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict
import nltk
from nltk.corpus import stopwords


# In[4]:


nltk.download("stopwords")


# In[5]:


class AIModule:
    def __init__(self):
        self.model_path = "file_classifier.pkl"
        self.vectorizer_path = "vectorizer.pkl"

        # Load existing model or create a new one
        if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
            self.vectorizer = joblib.load(self.vectorizer_path)
            self.model = joblib.load(self.model_path)
        else:
            self.vectorizer = None
            self.model = None

    def extract_features(self, filenames):
        """Extracts text features from file names."""
        stop_words = set(stopwords.words("english"))
        cleaned_filenames = [" ".join(re.sub(r"[^a-zA-Z0-9]", " ", file).split()) for file in filenames]
        filtered_filenames = [" ".join([word for word in file.split() if word.lower() not in stop_words]) for file in cleaned_filenames]

        # Vectorize filenames using TF-IDF
        self.vectorizer = TfidfVectorizer(max_features=100)
        features = self.vectorizer.fit_transform(filtered_filenames)
        return features

    def train_model(self, file_list):
        """Trains a K-Means model to categorize files."""
        if not file_list:
            return "No files to categorize!"

        features = self.extract_features(file_list)
        self.model = KMeans(n_clusters=5, random_state=42)
        self.model.fit(features)

        # Save the trained model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)

        return "AI Model trained successfully!"

    def categorize_files(self, file_list):
        """Categorizes files using the trained model."""
        if not self.model or not self.vectorizer:
            return "Train the model first!"

        features = self.vectorizer.transform(file_list)
        predictions = self.model.predict(features)

        categorized_files = defaultdict(list)
        for i, category in enumerate(predictions):
            categorized_files[f"Category {category + 1}"].append(file_list[i])

        return categorized_files

    def predict_file_usage(self, directory):
        """Predicts file usage patterns based on modification dates."""
        usage_patterns = defaultdict(int)
        current_time = datetime.datetime.now()

        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                days_old = (current_time - mod_time).days
                if days_old < 30:
                    usage_patterns["Recent"] += 1
                elif days_old < 90:
                    usage_patterns["Last 3 Months"] += 1
                else:
                    usage_patterns["Older"] += 1

        return dict(usage_patterns)

    def smart_search(self, directory, query):
        """Performs smart search using NLP techniques."""
        results = []
        query = query.lower()

        for file in os.listdir(directory):
            if query in file.lower():
                results.append(file)

        return results

