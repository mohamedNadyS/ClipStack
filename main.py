"""
ClipStack is a minimalist clipboard manager that tracks your recent text copies and lets you quickly access or export them. Designed for developers, writers, and power users who frequently copy code, notes, or snippets.

Core Features
1
Automatically tracks last 50 text copies (ignores images)
2
Single-key hotkey (Ctrl+Alt+C) to open history window
3
Right-click menu for items to copy, delete, or pin
4
Export selected items as text or JSON file
5
Auto-cleans on exit if history exceeds 50 items
Memory Optimization
1
Uses file-based JSON storage (data written to disk not RAM)
2
Implements strict 50-item limit for history
3
Loads data on-demand (only in memory when UI is open)
Tech Stack
1
Python 3.10+
2
Tkinter (GUI toolkit)
3
pyperclip (clipboard access)
4
json (standard library for storage)
5
pyinstaller (for final packaging)
Implementation Insights
1
Poll clipboard every 3 seconds when application is active
2
Store history as plain text with timestamps for simplicity
3
Use system tray icon for minimal UI footprint
4
Implement hotkey registration using keyboard module with low resource mode\
"""


import customtkinter as ctk
import json
import os
import pyperclip
import keyboard
import time
import threading
history_file = "history_data.json"
last_copied = ""
item = ""
id = 1
max_items = 50

def load_history():
    if not os.path.exists(history_file):
        return []
    with open(history_file,"r") as f:
        return json.load(f)
    
def save_his(data):
    with open(history_file,"w") as f:
        json.dump(data, f, indent=4)

def add_clipboarditem(item_con):
    global id
    global last_copied
    if last_copied == item_con:
        return
    
    history = load_history()
    if item_con != last_copied:
        item_con = last_copied
        id+=1
        entry ={"id":id,"item":item_con,"timestamp":time.time(),"pinned":False}
        history.insert(0,entry)

        not_pinned = [i for i in history if not i["pinned"]]
        if len(not_pinned)>50:
            toremove =len(not_pinned) - max_items
            history = [i for i in history if i["pinned"] or toremove <=0 or (toremove:=toremove-1)<0]
        save_his(history)

def track_clipboard():
    global last_copied
    while True:
        current_clipboard = pyperclip.paste()
        if current_clipboard != last_copied:
            add_clipboarditem(current_clipboard)
            last_copied = current_clipboard
        time.sleep(3)

def removeitem(item_id):
    history = load_history()
    history = [item for item in history if item["id"] != item_id]
    save_his(history)

def pin_item(item_id):
    history = load_history()
    for item in history:
        if item["id"] == item_id:
            item["pinned"] = True
            break
    save_his(history)

def export_as_txt():
    with open("history_copy.txt","w") as f:
        f.write(history_file)

def export_as_json():
    with open("history_copy.json", "w") as f:
        f.write(history_file)

def hotkey():
    if keyboard.is_pressed('ctrl+alt+c'):
        print("Hotkey pressed, opening history window...")
        # Incomplete
        pass

    pass
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ClipStack")
        self.geometry("800x600")

app = App()
app.mainloop()
print("App has started successfully.")