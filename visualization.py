import os
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans

class DirectoryVisualizer:
    @staticmethod
    def get_files_and_folders(path):
        """Scan directory and return files and folders with sizes"""
        files = []
        folders = []
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_file():
                            files.append((entry.path, entry.stat().st_size))
                        elif entry.is_dir():
                            size = sum(os.path.getsize(os.path.join(r, f)) 
                                     for r, _, fs in os.walk(entry.path) 
                                     for f in fs if os.path.exists(os.path.join(r, f)))
                            folders.append((entry.path, size))
                    except (FileNotFoundError, PermissionError):
                        continue
        except Exception as e:
            print(f"Scan error: {e}")
        return files, folders

    @staticmethod
    def create_largest_files_chart(path, callback=None):
        """Create bar chart of largest files"""
        files, _ = DirectoryVisualizer.get_files_and_folders(path)
        if not files:
            return None
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)[:10]
        file_names = [os.path.basename(f[0]) for f in sorted_files]
        file_paths =万人门票在线观看完整版file_sizes = [f[1] / (1024 * 1024) for f in sorted_files]  # MB

        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(file_names, file_sizes, color='skyblue')
        ax.set_xlabel('Size (MB)')
        ax.set_title('Top 10 Largest Files')
        if callback:
            def on_click(event):
                if event.inaxes == ax:
                    for i, bar in enumerate(bars):
                        if bar.contains(event)[0]:
                            callback(sorted_files[i][0])
            fig.canvas.mpl_connect('button_press_event', on_click)
        plt.tight_layout()
        return fig

    @staticmethod
    def create_folder_sizes_chart(path):
        """Create bar chart of largest folders"""
        _, folders = DirectoryVisualizer.get_files_and_folders(path)
        if not folders:
            return None
        sorted_folders = sorted(folders, key=lambda x: x[1], reverse=True)[:8]
        folder_names = [os.path.basename(f[0]) for f in sorted_folders]
        folder_sizes = [f[1] / (1024 * 1024) for f in sorted_folders]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(folder_names, folder_sizes, color='lightgreen')
        ax.set_xlabel('Size (MB)')
        ax.set_title('Largest Folders')
        plt.tight_layout()
        return fig

    @staticmethod
    def create_file_types_pie_chart(path):
        """Create pie chart of file type distribution"""
        files, _ = DirectoryVisualizer.get_files_and_folders(path)
        if not files:
            return None
        type_sizes = defaultdict(int)
        for filepath, size in files:
            ext = os.path.splitext(filepath)[1].lower() or 'No Extension'
            type_sizes[ext] += size

        threshold = sum(type_sizes.values()) * 0.03
        filtered_types = {k: v for k, v in type_sizes.items() if v >= threshold}
        other_size = sum(v for v in type_sizes.values() if v < threshold)
        if other_size > 0:
            filtered_types['Other'] = other_size

        labels = list(filtered_types.keys())
        sizes = [v / (1024 * 1024) for v in filtered_types.values()]

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.set_title('File Type Distribution by Size')
        return fig

    @staticmethod
    def create_file_clusters(path):
        """AI-powered file clustering by size and mod time"""
        files, _ = DirectoryVisualizer.get_files_and_folders(path)
        if len(files) < 3:
            return None, None
        features = np.array([[f[1], os.path.getmtime(f[0])] for f in files])
        kmeans = KMeans(n_clusters=min(3, len(files)), random_state=42).fit(features)
        
        cluster_info = {}
        for i, label in enumerate(kmeans.labels_):
            cluster_info.setdefault(label, []).append(files[i][0])
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.scatter(features[:, 1], features[:, 0] / 1024, c=kmeans.labels_, cmap='viridis')
        ax.set_xlabel('Last Modified (Unix Time)')
        ax.set_ylabel('Size (KB)')
        ax.set_title('File Clusters')
        plt.tight_layout()
        return fig, cluster_info

    @staticmethod
    def get_visualization_frame(parent, path, callback=None):
        """Create tabbed visualization interface"""
        frame = ttk.Frame(parent)
        tab_control = ttk.Notebook(frame)
        
        tabs = [
            ("Large Files", DirectoryVisualizer.create_largest_files_chart(path, callback)),
            ("Large Folders", DirectoryVisualizer.create_folder_sizes_chart(path)),
            ("File Types", DirectoryVisualizer.create_file_types_pie_chart(path)),
            ("AI Clustering", DirectoryVisualizer.create_file_clusters(path)[0])
        ]
        
        for name, fig in tabs:
            tab = ttk.Frame(tab_control)
            if fig:
                canvas = FigureCanvasTkAgg(fig, master=tab)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                tk.Label(tab, text=f"No data for {name}").pack()
            tab_control.add(tab, text=name)
        
        tab_control.pack(fill=tk.BOTH, expand=True)
        cluster_info = DirectoryVisualizer.create_file_clusters(path)[1]
        return frame, cluster_info