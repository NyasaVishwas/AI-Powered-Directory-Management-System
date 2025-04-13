import os
import mimetypes
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
from wordcloud import WordCloud
from collections import Counter

class VisualizationManager:
    def __init__(self):
        mimetypes.init()
        self.colors = plt.cm.tab20(np.linspace(0, 1, 20))
        self.on_click_callback = None
        self.tag_positions = {}

    def set_click_callback(self, callback):
        self.on_click_callback = callback

    def get_file_type_distribution(self, directory):
        file_types = {}
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                ext = os.path.splitext(item)[1].lower() or "No Extension"
                size = os.path.getsize(full_path) // 1024
                if ext not in file_types:
                    file_types[ext] = {"count": 0, "size": 0, "files": []}
                file_types[ext]["count"] += 1
                file_types[ext]["size"] += size
                file_types[ext]["files"].append(full_path)
        return file_types

    def get_file_info(self, file_path):
        try:
            size = os.path.getsize(file_path) // 1024
            mime_type, _ = mimetypes.guess_type(file_path)
            file_type = mime_type if mime_type else "Unknown"
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')
            thumbnail = None
            if mime_type and mime_type.startswith("image"):
                try:
                    img = Image.open(file_path)
                    img.thumbnail((100, 100))
                    thumbnail = img
                except:
                    pass
            return {
                "size_kb": size,
                "type": file_type,
                "modified": modified,
                "thumbnail": thumbnail,
                "icon": self.get_file_icon(file_path)
            }
        except:
            return None

    def get_file_icon(self, file_path):
        if os.path.isdir(file_path):
            return "📁"
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith("image"):
                return "🖼️"
            elif mime_type.startswith("video"):
                return "🎥"
            elif mime_type.startswith("audio"):
                return "🎵"
            elif mime_type.startswith("text") or mime_type == "application/pdf":
                return "📄"
        return "📄"

    def plot_tree_map(self, ax, file_types):
        if not file_types:
            return
        sizes = [data["size"] for data in file_types.values()]
        total_size = sum(sizes)
        if total_size == 0:
            return
        sizes = [s / total_size for s in sizes]
        labels = [f"{ext}\n{data['count']} files\n{data['size']} KB" for ext, data in file_types.items()]
        exts = list(file_types.keys())
        colors = self.colors[:len(file_types)]

        sizes = sorted(sizes, reverse=True)
        rects = []
        x, y, width, height = 0, 0, 1, 1
        for size in sizes:
            if width > height:
                w = size / height
                rects.append((x, y, w, height))
                x += w
                width -= w
            else:
                h = size / width
                rects.append((x, y, width, h))
                y += h
                height -= h

        self.rect_patches = []
        for (x, y, w, h), label, ext, color in zip(rects, labels, exts, colors):
            if w > 0 and h > 0:
                patch = patches.Rectangle((x, y), w, h, facecolor=color, edgecolor="white")
                self.rect_patches.append((patch, ext))
                ax.add_patch(patch)
                ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=10, wrap=True)

        def on_click(event):
            if event.inaxes != ax:
                return
            for patch, ext in self.rect_patches:
                if patch.contains_point((event.x, event.y)):
                    if self.on_click_callback:
                        self.on_click_callback(ext, file_types[ext]["files"])
                    break

        ax.figure.canvas.mpl_connect('button_press_event', on_click)
        ax.set_aspect('equal')
        ax.axis('off')

    def plot_timeline(self, ax, directory):
        dates = []
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                mtime = os.path.getmtime(full_path)
                date = datetime.datetime.fromtimestamp(mtime).date()
                dates.append(date)
        if not dates:
            ax.text(0.5, 0.5, "No files to display", ha="center", va="center", fontsize=12)
            return

        date_counts = {}
        for date in dates:
            date_counts[date] = date_counts.get(date, 0) + 1

        sorted_dates = sorted(date_counts.keys())
        counts = [date_counts[d] for d in sorted_dates]
        ax.plot(sorted_dates, counts, marker='o', color=self.colors[0])
        ax.set_xlabel("Date", fontsize=14)
        ax.set_ylabel("Number of Files", fontsize=14)
        ax.set_title("Files by Modification Date", fontsize=16)
        ax.tick_params(axis='x', rotation=45, labelsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)

    def plot_depth_pie(self, ax, directory):
        depths = {}
        for root, _, files in os.walk(directory):
            depth = len(os.path.relpath(root, directory).split(os.sep)) - 1
            if depth == -1:
                depth = 0
            depths[depth] = depths.get(depth, 0) + len(files)

        if not depths:
            ax.text(0.5, 0.5, "No files to display", ha="center", va="center", fontsize=12)
            return

        labels = [f"Depth {d}" for d in depths.keys()]
        sizes = list(depths.values())
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.colors[:len(depths)], textprops={'fontsize': 10})
        ax.axis('equal')
        ax.set_title("Files by Directory Depth", fontsize=16)

    def plot_tag_cloud(self, ax, directory, tags_cache):
        tags = []
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                tags.extend(tags_cache.get(full_path, []))
        if not tags:
            ax.text(0.5, 0.5, "No tags to display", ha="center", va="center", fontsize=12)
            return

        tag_counts = Counter(tags)
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            colormap='tab20',
            min_font_size=10,
            max_font_size=100
        ).generate_from_frequencies(tag_counts)

        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title("Tag Cloud", fontsize=16)

        self.tag_positions = {}
        for word, freq in tag_counts.items():
            self.tag_positions[word] = wordcloud.layout_[:len(tag_counts)]

        def on_click(event):
            if event.inaxes != ax:
                return
            x, y = event.xdata, event.ydata
            if x is None or y is None:
                return
            for tag in self.tag_positions:
                files = [
                    os.path.join(directory, item)
                    for item in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, item))
                    and tag in tags_cache.get(os.path.join(directory, item), [])
                ]
                if files and self.on_click_callback:
                    self.on_click_callback(tag, files)
                    break

        ax.figure.canvas.mpl_connect('button_press_event', on_click)

    def plot_file_age_bar(self, ax, directory):
        now = datetime.datetime.now()
        age_categories = {
            "Today": 0,
            "This Week": 0,
            "This Month": 0,
            "Older": 0
        }
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                age_days = (now - mtime).days
                if age_days < 1:
                    age_categories["Today"] += 1
                elif age_days < 7:
                    age_categories["This Week"] += 1
                elif age_days < 30:
                    age_categories["This Month"] += 1
                else:
                    age_categories["Older"] += 1

        if not any(age_categories.values()):
            ax.text(0.5, 0.5, "No files to display", ha="center", va="center", fontsize=12)
            return

        categories = list(age_categories.keys())
        counts = list(age_categories.values())
        max_count = max(counts) if counts else 1
        ax.bar(categories, counts, color=self.colors[:len(categories)], edgecolor='black', width=0.2)
        ax.set_xlabel("Age", fontsize=10)
        ax.set_ylabel("Number of Files", fontsize=10)
        ax.set_title("File Age Distribution", fontsize=14)
        ax.tick_params(axis='both', labelsize=10)
        ax.set_ylim(0, max_count * 1.1)  # Tight y-axis with 10% padding
        ax.grid(True, linestyle='--', alpha=0.7)