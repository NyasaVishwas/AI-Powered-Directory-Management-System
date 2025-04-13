# AI-Powered Directory Management System

A modern, interactive file manager with AI-driven features and vibrant visualizations, built with Python and `ttkbootstrap`. Manage files and folders with ease, visualize data, and leverage AI for tagging and organization.

## Features
- **File Operations**:
  - Create, rename, delete files/folders with undo support.
  - Recycle bin integration (auto-purge after 30 days).
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
- **Search**: Filter by name or tags.
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
   git clone <repo-url>
   cd AI-Powered-Directory-Management-System