# ClipStack
ClipStack is a minimalist clipboard manager that tracks your recent text copies and lets you quickly access or export them. Designed for developers, writers, and power users who frequently copy code, notes, or snippets.

## Features
* Automatically tracks last 50 text copies (ignores images)
* Single-key hotkey (Ctrl+Alt+C) to open history window
* Right-click menu for items to copy, delete, or pin
* Export selected items as text or JSON file
* Auto-cleans on exit if history exceeds 50 items
* Store history as plain text with timestamps for simplicity
* Implement hotkey registration using keyboard module with low resource mode

## Memory Optimization Techniques
* Uses file-based JSON storage (data written to disk not RAM)
* Implements strict 50-item limit for history
* Loads data on-demand (only in memory when UI is open)
* make the copy content loaded to memory as preview for the first 100 charcaters only in the UI Tech Stack

