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
import customtkinter
import darkdetect
import json
import os
import pyperclip
import keyboard
import time
import datetime
import threading
import uuid
historyfile = "history_data.json"
item = ""
maxitems = 50

class clipboardManager:
    def __init__(self):
        self.history_file = historyfile
        self.max_items = maxitems
        self.last_copied = ""
        self.id = 1
        self.loadcurrentid()
    
    def loadcurrentid(self):
        history = self.load_history()
        if history:
            self.current_id = max(item.get('id', 0) for item in history) + 1

    def load_history(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file,"r",encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError,IOError):
            return []
        
    def save_his(self,data):
        with open(self.history_file,"w") as f:
            json.dump(data, f, indent=2)

    def add_clipboarditem(self,item_con):
        if not item_con or self.last_copied == item_con or len(item_con.strip()) == 0:
            return False
        
        history = self.load_history()
        recent_items = history[:10] if len(history)>=10 else history
        for i in recent_items:
            if i.get('content') == item_con:
                return False
        if item_con != last_copied:
            last_copied = item_con
            self.id+=1
            entry ={"id":id,"content":item_con,"preview":item_con[:100]+"..." if len(item_con)>100 else item_con,"timestamp":time.time(),"formatted time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"pinned":False}
            history.insert(0,entry)

            not_pinned = [i for i in history if not i["pinned"]]
            if len(not_pinned)>50:
                toremove =len(not_pinned) - self.max_items
                history = [i for i in history if i["pinned"] or toremove <=0 or (toremove:=toremove-1)<0]
            self.save_his(history)


    def track_clipboard(self):
        global last_copied
        while True:
            current_clipboard = pyperclip.paste()
            if current_clipboard != self.last_copied:
                self.add_clipboarditem(current_clipboard)
                self.last_copied = current_clipboard
            time.sleep(3)

    def removeitem(self,item_id):
        history = self.load_history()
        history = [item for item in history if item["id"] != item_id]
        self.save_his(history)

    def pin_item(self,item_id):
        history = self.load_history()
        for item in history:
            if item["id"] == item_id:
                item["pinned"] = True
                break
        self.save_his(history)

    def export_as_txt(self,selected_ids=None):
        Rcode = uuid.uuid4()
        history = self.load_history()
        if selected_ids:
            history = [i for i in history if i['id'] in selected_ids]
        file_name = f"history_copy{Rcode}.txt"
        try:
            with open(file_name,"w", encoding='utf-8') as f:
                f.write("ClipStack exported data\n")
                f.write("_"*50+"\n\n")
                for i in history:
                    f.write(f"ID: {i['id']}\n")
                    f.write(f"Time: {i.get('formatted_time','Unknown')}\n")
                    f.write(f"Pinned: {'Yes' if i.get('pinned') else 'No'}\n")
                    f.write(f"Content:\n{i['content']}\n")
                    f.write("-"*50+"\n\n")
            return file_name
        except IOError:
            return None
    def export_as_json(self,selected_ids):
        history = self.load_history()
        if selected_ids:
            history = [i for i in history if i['id'] in selected_ids]
        Rcode = uuid.uuid4()
        fileName = f"history_copy{Rcode}.json"
        try:
            with open(fileName, "w", encoding='utf-8') as f:
                json.dump(history,f,indent=2,ensure_ascii=False)
            return fileName
        except IOError:
            return None


class trackclipboard:
    def __init__(self):
        self.
        pass
    pass
def hotkey():
    if keyboard.is_pressed('ctrl+alt+c'):
        print("Hotkey pressed, opening history window...")
        # Incomplete
        pass

    pass


def on_modechoose(choice):
    if choice == "System":
        ctk.set_appearance_mode("system")
    elif choice == "Dark":
        ctk.set_appearance_mode("dark")
    elif choice == "Light":
        ctk.set_appearance_mode("light")
#class copiedtext_box(ctk.):
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")
class App(ctk.CTk):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        system_mode = darkdetect.theme()
        self.title("ClipStack")
        self.geometry("800x600")
        self.pinned_font = ctk.CTkFont(family="",size=20,weight='bold')
        self.norm_font = ctk.CTkFont(family="",size=20,weight='normal')
        self.modeOptionmenu = ctk.CTkOptionMenu(self,values=["System","Dark","Light"],command=on_modechoose)
        self.modeOptionmenu.grid(row = 0, column=4,padx = 7, pady = 10,columnspan=2,sticky="ew")
        self.modeOptionmenu.set("System")


if __name__ == "__main__":
    app = App()
    app.mainloop()
print("App has started successfully.")