import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import shutil
import datetime
import subprocess
import sys
import json
from ai import AIDirectoryManager

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
        self.root = root
        self.root.title("\U0001F4C1 AI-Powered Directory Management System")
        self.root.state('zoomed')

        self.current_path = os.path.expanduser("~")
        self.file_paths = []
        self.ai_manager = AIDirectoryManager()
        self.tags_cache = {}  # Store tags for files
        self.undo_stack = []  # Store undoable actions

        # Top Frame
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(top_frame, text="⬅️", command=self.go_back).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(top_frame, text="Current Directory:").pack(side=tk.LEFT)
        self.path_entry = tk.Entry(top_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        self.path_entry.insert(0, self.current_path)

        tk.Button(top_frame, text="Browse", command=self.browse_directory).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="\U0001F50D Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_entry = tk.Entry(top_frame, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.search_items)
        tk.Button(top_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="Search By:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_mode_var = tk.StringVar(value="name")
        tk.Radiobutton(top_frame, text="Name", variable=self.search_mode_var, value="name", command=self.search_items).pack(side=tk.LEFT)
        tk.Radiobutton(top_frame, text="Tags", variable=self.search_mode_var, value="tags", command=self.search_items).pack(side=tk.LEFT)

        self.menu_button = tk.Menubutton(top_frame, text="⋮", relief=tk.RAISED, font=("Arial", 14, "bold"), width=2)
        self.menu_button.menu = tk.Menu(self.menu_button, tearoff=0)
        self.menu_button["menu"] = self.menu_button.menu
        self.menu_button.menu.add_command(label="Open Recycle Bin", command=self.open_recycle_bin)
        self.menu_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Treeview
        self.tree = ttk.Treeview(root, columns=('Name', 'Size', 'Modified', 'Tags'), show='headings')
        self.tree.heading('Name', text='\U0001F4C4 File / \U0001F4C1 Folder', command=lambda: self.sort_by_column('Name', False))
        self.tree.heading('Size', text='Size (KB)', command=lambda: self.sort_by_column('Size', False))
        self.tree.heading('Modified', text='Last Modified', command=lambda: self.sort_by_column('Modified', False))
        self.tree.heading('Tags', text='Tags', command=lambda: self.sort_by_column('Tags', False))
        self.tree.column('Name', width=350)
        self.tree.column('Size', width=100)
        self.tree.column('Modified', width=200)
        self.tree.column('Tags', width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree.bind("<Double-1>", self.on_double_click)

        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Button Frame with Wrapping Layout
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, pady=10)

        buttons = [
            ("✏️ Rename", self.rename_item),
            ("\U0001F5D1️ Delete", self.delete_item),
            ("\U0001F4C4 Create File", self.create_file),
            ("\U0001F4C1 Create Folder", self.create_folder),
            ("🤖 Categorize", self.categorize_files),
            ("🔍 Find Duplicates", self.find_duplicates),
            ("🏷️ Tag Files", self.tag_files),
            ("↩️ Undo", self.undo_action),
        ]

        for idx, (text, cmd) in enumerate(buttons):
            btn = tk.Button(btn_frame, text=text, command=cmd, width=12)
            btn.grid(row=idx // 4, column=idx % 4, padx=5, pady=2)
            if text == "↩️ Undo":
                self.undo_button = btn
                self.undo_button.config(state=tk.DISABLED)

        self.empty_bin_button = None

        self.status_label = tk.Label(root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        self.create_context_menu()
        self.bind_shortcuts()
        self.list_directory()

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

    def browse_directory(self):
        folder_selected = filedialog.askdirectory(initialdir=self.current_path)
        if folder_selected:
            self.current_path = folder_selected
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.current_path)
            self.undo_stack.clear()
            self.update_undo_button()
            self.list_directory()

    def go_back(self):
        parent = os.path.dirname(self.current_path)
        if parent and os.path.exists(parent):
            self.current_path = parent
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.current_path)
            self.undo_stack.clear()
            self.update_undo_button()
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
            icon = "\U0001F4C1" if os.path.isdir(full_path) else "\U0001F4C4"
            tags = ", ".join(self.tags_cache.get(full_path, [])) if os.path.isfile(full_path) else ""
            item_id = self.tree.insert("", "end", values=(f"{icon} {item}", size_kb, modified, tags))
            self.file_paths.append((item_id, full_path))

        if self.current_path == RECYCLE_BIN:
            self.empty_bin_button = tk.Button(self.root, text="Empty Recycle Bin", command=self.empty_recycle_bin, bg="red", fg="white")
            self.empty_bin_button.pack(side=tk.TOP, pady=(0, 5), fill=tk.X, padx=10, before=self.status_label)

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
            self.undo_stack.append(action)  # Re-push action if it fails
        self.update_undo_button()
        self.list_directory()

    def rename_item(self):
        _, path = self.get_selected_path()
        if not path:
            messagebox.showwarning("Warning", "Select a file or folder to rename.")
            return

        old_name = os.path.basename(path)
        new_name = simpledialog.askstring("Rename", f"Rename '{old_name}' to:")
        if new_name:
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