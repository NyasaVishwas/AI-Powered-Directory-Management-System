#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import hashlib
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import numpy as np


# In[2]:


class DirectoryVisualizer:
    @staticmethod
    def get_files_and_folders(path):
        """ Returns files and folders from the selected directory. """
        files = []
        folders = {}

        for root, dirs, filenames in os.walk(path):
            for file in filenames:
                ext = os.path.splitext(file)[-1].lower() or "No Extension"
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    created_time = os.path.getctime(file_path)
                    files.append((file_path, ext, size, created_time))
                except:
                    pass

            for folder in dirs:
                folder_path = os.path.join(root, folder)
                try:
                    total_size = sum(os.path.getsize(os.path.join(folder_path, f)) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)))
                    folders[folder] = total_size
                except:
                    pass

        return files, folders

    @staticmethod
    def visualize_largest_files(path):
        """ Creates a bar chart for the largest files. """
        files, _ = DirectoryVisualizer.get_files_and_folders(path)

        if not files:
            print("No files found in the selected directory.")
            return

        sorted_files = sorted(files, key=lambda x: x[2], reverse=True)[:10]
        file_names = [os.path.basename(f[0]) for f in sorted_files]
        file_sizes = [f[2] / (1024 * 1024) for f in sorted_files]  # Convert to MB

        plt.figure(figsize=(8, 4))
        plt.bar(file_names, file_sizes, color="orange")
        plt.xlabel("Files")
        plt.ylabel("Size (MB)")
        plt.xticks(rotation=45, ha="right")
        plt.title("Top 10 Largest Files")
        plt.show()

    @staticmethod
    def detect_duplicate_files(path):
        """ Detects and lists duplicate files based on their hash. """
        files, _ = DirectoryVisualizer.get_files_and_folders(path)
        hash_map = {}

        def hash_file(file_path):
            """ Returns SHA-256 hash of the given file. """
            try:
                hasher = hashlib.sha256()
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
                return hasher.hexdigest()
            except:
                return None

        duplicates = {}
        for file_path, _, _, _ in files:
            file_hash = hash_file(file_path)
            if file_hash:
                if file_hash in hash_map:
                    duplicates.setdefault(file_hash, []).append(file_path)
                else:
                    hash_map[file_hash] = file_path

        # Display results
        if duplicates:
            print("\n🔍 Duplicate Files Found:")
            for file_hash, paths in duplicates.items():
                print(f"\nHash: {file_hash}")
                for path in paths:
                    print(f" - {path}")
        else:
            print("\n✅ No duplicate files found.")

    @staticmethod
    def visualize_file_types_static(path):
        """ Creates a pie chart for file type distribution. """
        files, _ = DirectoryVisualizer.get_files_and_folders(path)
        ext_counts = Counter(ext for _, ext, _, _ in files)

        if not ext_counts:
            print("No files found in the selected directory.")
            return

        plt.figure(figsize=(6, 4))
        plt.pie(ext_counts.values(), labels=ext_counts.keys(), autopct="%1.1f%%", colors=plt.cm.Paired.colors)
        plt.title("File Type Distribution")
        plt.show()

    @staticmethod
    def visualize_folder_sizes_static(path):
        """ Creates a bar chart for the largest folders. """
        _, folders = DirectoryVisualizer.get_files_and_folders(path)

        if not folders:
            print("No folders found in the selected directory.")
            return

        sorted_folders = sorted(folders.items(), key=lambda x: x[1], reverse=True)[:10]
        folder_names, folder_sizes = zip(*sorted_folders)

        plt.figure(figsize=(8, 4))
        plt.bar(folder_names, np.array(folder_sizes) / (1024 * 1024), color="blue")
        plt.xlabel("Folders")
        plt.ylabel("Size (MB)")
        plt.xticks(rotation=45, ha="right")
        plt.title("Top 10 Largest Folders")
        plt.show()

    @staticmethod
    def visualize_file_ages_static(path):
        """ Creates a histogram showing file age distribution. """
        files, _ = DirectoryVisualizer.get_files_and_folders(path)
        timestamps = [created_time for _, _, _, created_time in files]

        if not timestamps:
            print("No files found in the selected directory.")
            return

        dates = [datetime.fromtimestamp(ts).date() for ts in timestamps]
        date_counts = Counter(dates)

        plt.figure(figsize=(8, 4))
        plt.bar(date_counts.keys(), date_counts.values(), color="green")
        plt.xlabel("Date")
        plt.ylabel("Number of Files")
        plt.xticks(rotation=45, ha="right")
        plt.title("File Age Analysis")
        plt.show()


# In[3]:


get_ipython().system('jupyter nbconvert --to script visualization.ipynb')

