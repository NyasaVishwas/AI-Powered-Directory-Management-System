import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import shutil
import datetime
import subprocess
import sys
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ai import AIDirectoryManager
from visualization import VisualizationManager

RECYCLE_BIN = os.path.join(os.path.expanduser("~"), ".recycle_bin")
if not os.path.exists(RECYCLE_BIN):
    os.makedirs(RECYCLE_BIN)

def purge_old_files():
    now = datetime.datetime.now()
    for item in os.listdir(RECYCLE_BIN):
        full_path = os.path.join(RECYCLE_BIN, item)
        modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
        if (now - modified_time).days > 30:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

purge_old_files()

class FileManagerApp:
    def __init__(self, root):
        self.style = ttkb.Style()  # Initialize Style
        self.style.theme_use("flatly")  # Set initial theme
        self.root = ttkb.Window(themename="flatly")
        self.root.title("\U0001F4C1 AI-Powered Directory Management System")
        self.root.state('zoomed')

        self.current_path = os.path.expanduser("~")
        self.file_paths = []
        self.ai_manager = AIDirectoryManager()
        self.vis_manager = VisualizationManager()
        self.tags_cache = {}
        self.undo_stack = []
        self.vis_mode = "pie"
        self.theme_var = tk.StringVar(value="flatly")  # Track theme

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(self.top_frame, text="⬅️", command=self.go_back, style="primary.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(self.top_frame, text="Current Directory:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(self.top_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        self.path_entry.insert(0, self.current_path)
        ttk.Button(self.top_frame, text="Browse", command=self.browse_directory, style="primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Label(self.top_frame, text="\U0001F50D Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_entry = ttk.Entry(self.top_frame, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.search_items)
        ttk.Button(self.top_frame, text="Clear", command=self.clear_search, style="secondary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Label(self.top_frame, text="Search By:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_mode_var = tk.StringVar(value="name")
        ttk.Radiobutton(self.top_frame, text="Name", variable=self.search_mode_var, value="name", command=self.search_items).pack(side=tk.LEFT)
        ttk.Radiobutton(self.top_frame, text="Tags", variable=self.search_mode_var, value="tags", command=self.search_items).pack(side=tk.LEFT)
        self.menu_button = ttk.Menubutton(self.top_frame, text="⋮", style="primary.TButton")
        self.menu_button.menu = tk.Menu(self.menu_button, tearoff=0)
        self.menu_button["menu"] = self.menu_button.menu
        self.menu_button.menu.add_command(label="Open Recycle Bin", command=self.open_recycle_bin)
        self.menu_button.pack(side=tk.RIGHT, padx=(0, 10))

        self.toggle_frame = ttk.Frame(self.main_frame)
        self.toggle_frame.pack(fill=tk.X, pady=5)
        self.left_separator = ttk.Separator(self.toggle_frame, orient='horizontal')
        self.left_separator.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button_container = ttk.Frame(self.toggle_frame)
        self.button_container.pack(side=tk.LEFT)
        self.normal_button = ttk.Button(self.button_container, text="🖥️ Explore", command=self.show_normal_ui, style="primary.Outline.TButton", width=12)
        self.normal_button.pack(side=tk.LEFT, padx=2)
        self.visualize_button = ttk.Button(self.button_container, text="📊 Visualize", command=self.show_visualization, style="primary.Outline.TButton", width=12)
        self.visualize_button.pack(side=tk.LEFT, padx=2)
        self.right_separator = ttk.Separator(self.toggle_frame, orient='horizontal')
        self.right_separator.pack(side=tk.LEFT, fill=tk.X, padx=(5, 5))
        self.theme_button = ttk.Button(self.toggle_frame, text="🌙 Dark Mode", command=self.toggle_theme, style="primary.Outline.TButton", width=12)
        self.theme_button.pack(side=tk.LEFT, padx=2)
        self.final_separator = ttk.Separator(self.toggle_frame, orient='horizontal')
        self.final_separator.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree_frame = ttk.Frame(self.content_frame)
        self.tree = ttk.Treeview(self.tree_frame, columns=('Name', 'Size', 'Modified', 'Tags'), show='headings', style="Treeview")
        self.tree.heading('Name', text='File / Folder', command=lambda: self.sort_by_column('Name', False))
        self.tree.heading('Size', text='Size (KB)', command=lambda: self.sort_by_column('Size', False))
        self.tree.heading('Modified', text='Last Modified', command=lambda: self.sort_by_column('Modified', False))
        self.tree.heading('Tags', text='Tags', command=lambda: self.sort_by_column('Tags', False))
        self.tree.column('Name', width=400, minwidth=200)
        self.tree.column('Size', width=120, minwidth=80)
        self.tree.column('Modified', width=220, minwidth=150)
        self.tree.column('Tags', width=200, minwidth=100)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.vis_frame = ttk.Frame(self.content_frame)
        self.vis_canvas = None
        self.vis_buttons_frame = ttk.Frame(self.vis_frame)
        self.vis_buttons = []

        self.btn_frame = ttk.Frame(self.main_frame)
        buttons = [
            ("\U0001F4C4 Create File", self.create_file),
            ("\U0001F4C1 Create Folder", self.create_folder),
            ("✏️ Rename", self.rename_item),
            ("\U0001F5D1️ Delete", self.delete_item),
            ("🤖 Categorize", self.categorize_files),
            ("🔍 Find Duplicates", self.find_duplicates),
            ("🏷️ Tag Files", self.tag_files),
            ("↩️ Undo", self.undo_action),
        ]
        for idx, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(self.btn_frame, text=text, command=cmd, style="outline.TButton", width=12)
            btn.grid(row=idx // 4, column=idx % 4, padx=5, pady=2)
            if text == "↩️ Undo":
                self.undo_button = btn
                self.undo_button.config(state=tk.DISABLED)

        self.empty_bin_button = None
        self.status_label = ttk.Label(self.main_frame, text="", bootstyle="inverse", anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        self.style.configure("Treeview", rowheight=25)
        self.style.map("Treeview", background=[('selected', '#007bff')])

        self.create_context_menu()
        self.bind_shortcuts()
        self.show_normal_ui()
        self.list_directory()

    def toggle_theme(self):
        current_theme = self.theme_var.get()
        if current_theme == "flatly":
            self.style.theme_use("darkly")
            self.theme_var.set("darkly")
            self.theme_button.config(text="☀️ Light Mode")
        else:
            self.style.theme_use("flatly")
            self.theme_var.set("flatly")
            self.theme_button.config(text="🌙 Dark Mode")
        # Refresh widget styles
        self.style.configure("Treeview", rowheight=25)
        self.style.map("Treeview", background=[('selected', '#007bff')])
        # Update status_label if it has bootstyle
        if self.status_label:
            try:
                current_bootstyle = self.status_label.cget("bootstyle")
                self.status_label.configure(bootstyle=current_bootstyle or "inverse")
            except tk.TclError:
                pass  # Skip if bootstyle isn't supported
        # Update other widgets
        for widget in self.top_frame.winfo_children() + self.toggle_frame.winfo_children() + self.btn_frame.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Menubutton)):
                style_name = widget.cget("style") or "TButton"
                widget.configure(style=style_name)
            elif isinstance(widget, ttk.Label):
                try:
                    current_bootstyle = widget.cget("bootstyle")
                    widget.configure(bootstyle=current_bootstyle or "")
                except tk.TclError:
                    pass  # Skip if bootstyle isn't supported
            # Skip Entries to avoid bootstyle issues; theme change handles their appearance
            # elif isinstance(widget, ttk.Entry):
            #     pass

    def create_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="✏️ Rename", command=self.rename_item)
        self.menu.add_command(label="\U0001F5D1️ Delete", command=self.delete_item)
        self.menu.add_command(label="\U0001F4C4 Create File", command=self.create_file)
        self.menu.add_command(label="\U0001F4C1 Create Folder", command=self.create_folder)
        self.menu.add_command(label="🤖 Categorize", command=self.categorize_files)
        self.menu.add_command(label="🔍 Find Duplicates", command=self.find_duplicates)
        self.menu.add_command(label="🏷️ Tag Selected", command=self.tag_selected_file)
        self.menu.add_command(label="↩️ Undo", command=self.undo_action)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        try:
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.menu.post(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def bind_shortcuts(self):
        self.root.bind('<Delete>', lambda e: self.delete_item())
        self.root.bind('<Control-r>', lambda e: self.rename_item())
        self.root.bind('<Control-n>', lambda e: self.create_file())
        self.root.bind('<Control-z>', lambda e: self.undo_action())

    def show_normal_ui(self):
        if self.vis_canvas:
            self.vis_canvas.get_tk_widget().pack_forget()
            self.vis_canvas = None
        self.vis_buttons_frame.pack_forget()
        self.vis_frame.pack_forget()
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        self.btn_frame.pack(fill=tk.X, pady=10)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
        self.normal_button.config(state=tk.DISABLED)
        self.visualize_button.config(state=tk.NORMAL)

    def show_visualization(self):
        self.tree_frame.pack_forget()
        self.btn_frame.pack_forget()
        self.status_label.pack_forget()
        self.vis_frame.pack(fill=tk.BOTH, expand=True)

        _, path = self.get_selected_path()
        if not path:
            path = self.current_path

        fig, ax = plt.subplots(figsize=(12, 8))
        if os.path.isdir(path):
            file_types = self.vis_manager.get_file_type_distribution(path)
            if not file_types and self.vis_mode not in ["timeline", "depth", "cloud", "age"]:
                messagebox.showinfo("Visualize", "No files to visualize.")
                self.show_normal_ui()
                return

            def set_vis_mode(mode):
                self.vis_mode = mode
                ax.clear()
                if mode == "pie":
                    counts = [data["count"] for data in file_types.values()]
                    labels = file_types.keys()
                    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.vis_manager.colors, textprops={'fontsize': 12})
                    ax.axis('equal')
                    ax.set_title("File Type Distribution", fontsize=16)
                    self.status_label.config(text=f"Pie Chart visualization for: {self.current_path}")
                elif mode == "tree":
                    self.vis_manager.plot_tree_map(ax, file_types)
                    ax.set_aspect('equal')
                    ax.set_title("File Size Tree Map", fontsize=16)
                    ax.axis('off')
                    self.status_label.config(text=f"Tree Map visualization for: {self.current_path}")
                elif mode == "timeline":
                    self.vis_manager.plot_timeline(ax, path)
                    self.status_label.config(text=f"Timeline visualization for: {self.current_path}")
                elif mode == "depth":
                    self.vis_manager.plot_depth_pie(ax, path)
                    self.status_label.config(text=f"Depth Pie visualization for: {self.current_path}")
                elif mode == "cloud":
                    self.vis_manager.plot_tag_cloud(ax, path, self.tags_cache)
                    self.status_label.config(text=f"Tag Cloud visualization for: {self.current_path}")
                elif mode == "age":
                    self.vis_manager.plot_file_age_bar(ax, path)
                    self.status_label.config(text=f"File Age visualization for: {self.current_path}")
                plt.tight_layout()
                self.vis_canvas.draw()

            def on_click(tag, files):
                self.show_normal_ui()
                self.tree.delete(*self.tree.get_children())
                self.file_paths = []
                for file_path in files:
                    item = os.path.basename(file_path)
                    size_kb = os.path.getsize(file_path) // 1024
                    modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')
                    icon = self.vis_manager.get_file_icon(file_path)
                    tags = ", ".join(self.tags_cache.get(file_path, []))
                    item_id = self.tree.insert("", "end", values=(f"{icon} {item}", size_kb, modified, tags))
                    self.file_paths.append((item_id, file_path))
                self.status_label.config(text=f"{len(self.file_paths)} files with tag '{tag}' in: {self.current_path}")

            self.vis_manager.set_click_callback(on_click)

            if self.vis_mode == "pie":
                counts = [data["count"] for data in file_types.values()]
                labels = file_types.keys()
                ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.vis_manager.colors, textprops={'fontsize': 12})
                ax.axis('equal')
                ax.set_title("File Type Distribution", fontsize=16)
                self.status_label.config(text=f"Pie Chart visualization for: {self.current_path}")
            elif self.vis_mode == "tree":
                self.vis_manager.plot_tree_map(ax, file_types)
                ax.set_aspect('equal')
                ax.set_title("File Size Tree Map", fontsize=16)
                ax.axis('off')
                self.status_label.config(text=f"Tree Map visualization for: {self.current_path}")
            elif self.vis_mode == "timeline":
                self.vis_manager.plot_timeline(ax, path)
                self.status_label.config(text=f"Timeline visualization for: {self.current_path}")
            elif self.vis_mode == "depth":
                self.vis_manager.plot_depth_pie(ax, path)
                self.status_label.config(text=f"Depth Pie visualization for: {self.current_path}")
            elif self.vis_mode == "cloud":
                self.vis_manager.plot_tag_cloud(ax, path, self.tags_cache)
                self.status_label.config(text=f"Tag Cloud visualization for: {self.current_path}")
            elif self.vis_mode == "age":
                self.vis_manager.plot_file_age_bar(ax, path)
                self.status_label.config(text=f"File Age visualization for: {self.current_path}")

            plt.tight_layout()
            self.vis_buttons_frame.pack(side=tk.TOP, fill=tk.X)
            for btn in self.vis_buttons:
                btn.pack_forget()
            self.vis_buttons = [
                ttk.Button(self.vis_buttons_frame, text="Pie Chart", command=lambda: set_vis_mode("pie")),
                ttk.Button(self.vis_buttons_frame, text="Tree Map", command=lambda: set_vis_mode("tree")),
                ttk.Button(self.vis_buttons_frame, text="Timeline", command=lambda: set_vis_mode("timeline")),
                ttk.Button(self.vis_buttons_frame, text="Depth Pie", command=lambda: set_vis_mode("depth")),
                ttk.Button(self.vis_buttons_frame, text="Tag Cloud", command=lambda: set_vis_mode("cloud")),
                ttk.Button(self.vis_buttons_frame, text="File Age", command=lambda: set_vis_mode("age")),
            ]
            for btn in self.vis_buttons:
                btn.pack(side=tk.LEFT, padx=5)

        else:
            file_info = self.vis_manager.get_file_info(path)
            if not file_info:
                messagebox.showinfo("Visualize", "No visualization available.")
                self.show_normal_ui()
                return
            ax.bar(['Size (KB)'], [file_info['size_kb']], color='skyblue')
            ax.set_title(f"File: {os.path.basename(path)}", fontsize=16)
            ax.tick_params(axis='both', labelsize=12)
            if file_info["thumbnail"]:
                img = file_info["thumbnail"]
                ax_image = fig.add_axes([0.1, 0.6, 0.2, 0.2])
                ax_image.imshow(img)
                ax_image.axis('off')
            ax.text(0, file_info['size_kb'], f"Type: {file_info['type']}\nModified: {file_info['modified']}\nIcon: {file_info['icon']}",
                    ha='center', va='bottom', fontsize=12)
            self.status_label.config(text=f"File visualization for: {os.path.basename(path)}")
            plt.tight_layout()

        self.vis_canvas = FigureCanvasTkAgg(fig, master=self.vis_frame)
        self.vis_canvas.draw()
        self.vis_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.normal_button.config(state=tk.NORMAL)
        self.visualize_button.config(state=tk.DISABLED)

    def browse_directory(self):
        folder_selected = filedialog.askdirectory(initialdir=self.current_path)
        if folder_selected:
            self.current_path = folder_selected
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.current_path)
            self.undo_stack.clear()
            self.update_undo_button()
            self.show_normal_ui()
            self.list_directory()

    def go_back(self):
        parent = os.path.dirname(self.current_path)
        if parent and os.path.exists(parent):
            self.current_path = parent
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.current_path)
            self.undo_stack.clear()
            self.update_undo_button()
            self.show_normal_ui()
            self.list_directory()

    def list_directory(self, filter_text="", search_mode="name"):
        path = self.path_entry.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "Invalid directory path.")
            return

        self.current_path = path
        self.tree.delete(*self.tree.get_children())
        self.file_paths = []

        if self.empty_bin_button:
            self.empty_bin_button.destroy()
            self.empty_bin_button = None

        filter_text = filter_text.lower()
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if search_mode == "name":
                name_words = os.path.splitext(item)[0].lower().split()
                if filter_text and not any(filter_text in word for word in name_words):
                    continue
            elif search_mode == "tags":
                if not os.path.isfile(full_path):
                    continue
                tags = self.tags_cache.get(full_path, [])
                if filter_text and not any(filter_text in tag.lower() for tag in tags):
                    continue

            size_kb = os.path.getsize(full_path) // 1024 if os.path.isfile(full_path) else "-"
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M')
            icon = self.vis_manager.get_file_icon(full_path)
            tags = ", ".join(self.tags_cache.get(full_path, [])) if os.path.isfile(full_path) else ""
            item_id = self.tree.insert("", "end", values=(f"{icon} {item}", size_kb, modified, tags))
            self.file_paths.append((item_id, full_path))

        if self.current_path == RECYCLE_BIN:
            self.empty_bin_button = ttk.Button(self.main_frame, text="Empty Recycle Bin", command=self.empty_recycle_bin, style="danger.TButton")
            self.empty_bin_button.pack(side=tk.TOP, pady=(0, 5), fill=tk.X, padx=10)

        self.status_label.config(text=f"{len(self.file_paths)} items found in: {self.current_path}")

    def sort_by_column(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        data.sort(reverse=reverse)
        for index, (val, k) in enumerate(data):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def get_selected_path(self):
        selected = self.tree.selection()
        if not selected:
            return None, None
        item_id = selected[0]
        for tree_id, path in self.file_paths:
            if tree_id == item_id:
                return tree_id, path
        return None, None

    def update_undo_button(self):
        if self.undo_stack:
            self.undo_button.config(state=tk.NORMAL)
        else:
            self.undo_button.config(state=tk.DISABLED)

    def undo_action(self):
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        try:
            if action["type"] == "delete":
                src = action["recycle_path"]
                dst = action["original_path"]
                shutil.move(src, dst)
                if "tags" in action and action["tags"]:
                    self.tags_cache[dst] = action["tags"]
                messagebox.showinfo("Undo", f"Restored '{os.path.basename(dst)}'")
            elif action["type"] == "rename":
                src = action["new_path"]
                dst = action["old_path"]
                os.rename(src, dst)
                if src in self.tags_cache:
                    self.tags_cache[dst] = self.tags_cache.pop(src)
                messagebox.showinfo("Undo", f"Reverted to '{os.path.basename(dst)}'")
        except Exception as e:
            messagebox.showerror("Error", f"Could not undo: {e}")
            self.undo_stack.append(action)
        self.update_undo_button()
        self.list_directory()

    def rename_item(self):
        _, path = self.get_selected_path()
        if not path:
            messagebox.showwarning("Warning", "Select a file or folder to rename.")
            return

        old_name = os.path.basename(path)
        base_name, ext = os.path.splitext(old_name)
        new_base_name = simpledialog.askstring("Rename", f"Rename '{old_name}' to:", initialvalue=base_name)
        if new_base_name:
            new_name = new_base_name + ext if ext and os.path.isfile(path) else new_base_name
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                self.undo_stack.append({
                    "type": "rename",
                    "old_path": path,
                    "new_path": new_path
                })
                if path in self.tags_cache:
                    self.tags_cache[new_path] = self.tags_cache.pop(path)
                messagebox.showinfo("Success", f"Renamed to {new_name}")
                self.update_undo_button()
                self.list_directory()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_item(self):
        _, path = self.get_selected_path()
        if not path:
            messagebox.showwarning("Warning", "Select a file or folder to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Move '{os.path.basename(path)}' to Recycle Bin?")
        if confirm:
            try:
                recycle_path = os.path.join(RECYCLE_BIN, os.path.basename(path))
                shutil.move(path, recycle_path)
                tags = self.tags_cache.pop(path, None)
                self.undo_stack.append({
                    "type": "delete",
                    "original_path": path,
                    "recycle_path": recycle_path,
                    "tags": tags
                })
                messagebox.showinfo("Deleted", "Item moved to Recycle Bin.")
                self.update_undo_button()
                self.list_directory()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def on_double_click(self, event):
        _, path = self.get_selected_path()
        if path:
            if os.path.isdir(path):
                self.current_path = path
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, self.current_path)
                self.undo_stack.clear()
                self.update_undo_button()
                self.show_normal_ui()
                self.list_directory()
            else:
                self.open_path(path)

    def open_path(self, path):
        try:
            if sys.platform.startswith("darwin"):
                subprocess.call(["open", path])
            elif os.name == "nt":
                os.startfile(path)
            elif os.name == "posix":
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open item.\n{e}")

    def create_file(self):
        name = simpledialog.askstring("Create File", "Enter file name:")
        if name:
            path = os.path.join(self.current_path, name)
            try:
                with open(path, 'w') as f:
                    f.write("")
                self.list_directory()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def create_folder(self):
        name = simpledialog.askstring("Create Folder", "Enter folder name:")
        if name:
            path = os.path.join(self.current_path, name)
            try:
                os.makedirs(path)
                self.list_directory()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def search_items(self, event=None):
        query = self.search_entry.get().strip()
        mode = self.search_mode_var.get()
        self.list_directory(filter_text=query, search_mode=mode)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.list_directory()

    def open_recycle_bin(self):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, RECYCLE_BIN)
        self.current_path = RECYCLE_BIN
        self.undo_stack.clear()
        self.update_undo_button()
        self.show_normal_ui()
        self.list_directory()

    def empty_recycle_bin(self):
        confirm = messagebox.askyesno("Empty Recycle Bin", "Are you sure you want to permanently delete all items in the Recycle Bin?")
        if confirm:
            for item in os.listdir(RECYCLE_BIN):
                full_path = os.path.join(RECYCLE_BIN, item)
                try:
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not delete: {item}\n{e}")
            self.list_directory()

    def categorize_files(self):
        structure = self.ai_manager.suggest_folder_structure(self.current_path)
        if not structure:
            messagebox.showinfo("Categorize", "No files to categorize.")
            return
        for category, files in structure.items():
            cat_dir = os.path.join(self.current_path, category)
            if not os.path.exists(cat_dir):
                os.makedirs(cat_dir)
            for file in files:
                src = os.path.join(self.current_path, file)
                dst = os.path.join(cat_dir, file)
                try:
                    shutil.move(src, dst)
                    if src in self.tags_cache:
                        self.tags_cache[dst] = self.tags_cache.pop(src)
                except Exception as e:
                    print(f"Error moving {file}: {e}")
        messagebox.showinfo("Categorize", "Files organized into category folders.")
        self.list_directory()

    def find_duplicates(self):
        duplicates = self.ai_manager.find_duplicates(self.current_path)
        if not duplicates:
            messagebox.showinfo("Duplicates", "No duplicates found.")
            return
        dup_text = "\n".join([f"{os.path.basename(dup[0])} <-> {os.path.basename(dup[1])}" for dup in duplicates])
        messagebox.showinfo("Duplicates Found", f"Found {len(duplicates)} duplicate pairs:\n{dup_text}")

    def tag_files(self):
        tagged_files = []
        for _, path in self.file_paths:
            if os.path.isfile(path):
                tags = self.ai_manager.generate_tags(path)
                if tags:
                    self.tags_cache[path] = tags
                    tagged_files.append(os.path.basename(path))
        self.list_directory()
        if tagged_files:
            messagebox.showinfo("Tagging", f"Tagged {len(tagged_files)} files: {', '.join(tagged_files)}")
        else:
            messagebox.showinfo("Tagging", "No tags generated for files.")

    def tag_selected_file(self):
        _, path = self.get_selected_path()
        if not path or not os.path.isfile(path):
            messagebox.showwarning("Warning", "Select a file to tag.")
            return
        tags = self.ai_manager.generate_tags(path)
        self.tags_cache[path] = tags
        messagebox.showinfo("Tags", f"Tags for {os.path.basename(path)}: {', '.join(tags)}")
        self.list_directory()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()