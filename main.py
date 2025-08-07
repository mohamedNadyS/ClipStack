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
4
make the copy content loaded to memory as preview for the first 100 charcaters only in the UI
Tech Stack
1
Python 3.10+
2
custom Tkinter (GUI toolkit)
3
pyperclip (clipboard access)
4
json (standard library for storage)
5
threading (track the keyboard)
6
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
import CTkMessagebox
import json
import os
import pyperclip
import keyboard
import time
import datetime
import threading
import uuid
import atexit
import sys
import signal
historyfile = "clipstack_history_data.json"
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
        if item_con != self.last_copied:
            self.last_copied = item_con
            self.id+=1
            entry ={"id":self.id,"content":item_con,"preview":item_con[:100]+"..." if len(item_con)>100 else item_con,"timestamp":time.time(),"formatted time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"pinned":False}
            history.insert(0,entry)

            not_pinned = [i for i in history if not i["pinned"]]
            if len(not_pinned)>50:
                toremove =len(not_pinned) - self.max_items
                history = [i for i in history if i["pinned"] or toremove <=0 or (toremove:=toremove-1)<0]
            self.save_his(history)


    def track_clipboard(self):
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

    def unpin_item(self,item_id):
        history = self.load_history()
        for i in history:
            if i['id'] ==item_id:
                i['pinned'] = False
                break
        self.save_his(history)

    def clear_history(self):
        self.save_his([])

    def export_as_txt(self,selected_ids=None):
        Rcode = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
        Rcode = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fileName = f"history_copy{Rcode}.json"
        try:
            with open(fileName, "w", encoding='utf-8') as f:
                json.dump(history,f,indent=2,ensure_ascii=False)
            return fileName
        except IOError:
            return None

class backgroundCM:
    def __init__(self,clipboardmanager):
        self.clipboardM = clipboardmanager
        self.running = False
        self.tread = None
    
    def startTracking(self):
        if self.running:
            return
        self.running=True
        self.tread=threading.Thread(target=self.trackingloop,daemon=True)
        self.tread.start()
    
    def trackingloop(self):
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.clipboardM.last_copied:
                    self.clipboardM.add_clipboarditem(current_clipboard)
            except Exception as e:
                print(f"clipboard tacking error {e}")
            time.sleep(3)
    
    def stopTracking(self):
        self.running=False
        if self.tread:
            self.tread.join(timeout=1)

class hotkeymanager:
    def __init__(self,appcallback):
        self.hotkeyregistered=False
        self.appcallback=appcallback

    def register(self):
        try:
            keyboard.add_hotkey('ctrl+alt+c',self.hotkeyActiv)
            self.hotkeyregistered=True
            return True
        except Exception as e:
            print(f"failed to register hotkey {e}")
            return False

    def unregister(self):
        try:
            if self.hotkeyregistered:
                keyboard.unhook_all_hotkeys()
                self.hotkeyregistered=False
        except Exception as e:
            print(f"unregister hotkey error {e}")

    def hotkeyActiv(self):
        if self.appcallback:
            self.appcallback()



#class copiedtext_box(ctk.):
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")
class App(ctk.CTk):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.clipboard_manager= clipboardManager()
        self.bgtrack = backgroundCM(self.clipboard_manager)
        self.hotkey_manager = hotkeymanager(self.hotkeyCallback)
        self.selectedItems = set()
        self.randerWindow() 
        self.startBG()

        self.protocol("WM_DELETE_WINDOW",self.Fakeclosing)
    
    def startBG(self):
        self.bgtrack.startTracking()
        self.hotkey_manager.register()

    def stopBG(self):
        self.bgtrack.stopTracking()
        self.hotkey_manager.unregister()

    def Fakeclosing(self):
        self.withdraw()

    def hotkeyCallback(self):
        try:
            if self.state()== 'withdraw' or not self.winfo_viewable():
                self.deiconify()
                self.lift()
                self.focus_force()
                self.refresh()
            else:
                self.withdraw()
        except Exception as e:
            print(f"hotkey failed to do the function {e}")

    def runInBG(self):
        def cleanup():
            self.stopBG()
        
        atexit.register(cleanup)
        def signalstop(signum,frame):
            cleanup()
            sys.exit(0)
        signal.signal(signal.SIGINT,signalstop)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signalstop)
    def randerWindow(self):
        self.title("ClipStack")
        self.geometry("900x700")
        self.minsize(600,400)
        self.appcontentUI()
    
    def appcontentUI(self):
        self.appcontent = ctk.CTkFrame(self)
        self.appcontent.grid(row=0,column=0,sticky="nsew")
        self.appcontent.grid_rowconfigure(0,weight=1)
        self.appcontent.grid_columnconfigure(0,weight=1)
        headerFrame = ctk.CTkFrame(self.appcontent)
        headerFrame.grid(row=0,column=0,sticky="ew")
        headerFrame.grid_columnconfigure(1,weight=1)

        title =ctk.CTkLabel(headerFrame,text="ClipStack",font=ctk.CTkFont(family="monospace",size=20,weight="bold"))
        title.grid(row=0,column=0,padx=10,pady=5,sticky="ew")
        self.pinned_font = ctk.CTkFont(family="",size=20,weight='bold')
        self.norm_font = ctk.CTkFont(family="",size=20,weight='normal')
        self.status_font = ctk.CTkFont(family="",size=13,weight='normal',slant='italic')
        
        buttonsFrame =ctk.CTkFrame(headerFrame)
        buttonsFrame.grid(row=1,column=0,padx=10,pady=5,sticky="ew")
        self.modeOptionmenu = ctk.CTkOptionMenu(buttonsFrame,values=["System","Dark","Light"],command=self.on_modechoose)
        self.modeOptionmenu.grid(row = 0, column=5,padx = 7, pady = 10,sticky="ew")
        self.modeOptionmenu.set("System")

        refresh=ctk.CTkButton(buttonsFrame,text="Refresh",command=self.refresh)
        refresh.grid(row=0,column=4,padx=5,pady=5,sticky="ew")

        exporttxt = ctk.CTkButton(buttonsFrame,text="Export As Text",command=self.export_as_txt)
        exporttxt.grid(row=0,column=1,padx=5,pady=5,sticky="ew")

        exportjson =ctk.CTkButton(buttonsFrame,text="Export As JSON",command=self.export_as_JSON)
        exportjson.grid(row=0,column=2,padx=5,pady=5,sticky="ew")

        clear = ctk.CTkButton(buttonsFrame,text="Clear History",command=self.clear_history)
        clear.grid(row=0,column=3,padx=5,pady=5,sticky="ew")

        self.currentStatus = ctk.CTkLabel(self.appcontent,text="",font=self.status_font)
        self.currentStatus.grid(row=1,column=0,padx=10,pady=2,sticky="ew")

        self.selectAllVAr = ctk.BooleanVar()
        selectall = ctk.CTkCheckBox(buttonsFrame,text="Select All",variable=self.selectAllVAr,command=self.SelectALL)
        selectall.grid(row=0,column=0,padx=10,pady=2)

        self.mainFrame = ctk.CTkScrollableFrame(self)
        self.mainFrame.grid(row=1,column=0,padx=10,pady=5,sticky="nsew")
        self.mainFrame.grid_columnconfigure(0,weight=1)

    def on_modechoose(self,choice):
        if choice == "Dark":
            ctk.set_appearance_mode("dark")
        elif choice == "Light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("system")

    def selectItem(self,id):
        self.selectedItems.add(id)

    def unselectItem(self,id):
        self.selectedItems.remove(id)

    def coping(self,id):
        history = self.clipboard_manager.load_history()
        for i in history:
            if i['id'] ==id:
                pyperclip.copy(i['content'])
                break
    
    def delete(self,id):
        self.clipboard_manager.removeitem(id)
        self.refresh()
        self.currentStatus.configure(text=f"Item {id} deleted successfully.")
        self.selectedItems.discard(id)
    
    def pin(self,id):
        self.clipboard_manager.pin_item(id)
        self.refresh()
        self.currentStatus.configure(text=f"Item {id} pinned successfully.")
    
    def unpin(self,id):
        self.clipboard_manager.unpin_item(id)
        self.refresh()
        self.currentStatus.configure(text=f"Item {id} unpinned successfully.")

    def clear_history(self):
        if CTkMessagebox.CTkMessagebox(title="Clear History",message="Are you sure you want to clear all clipboard history?",option_1="Yes",option_2="No").get() =="Yes":
            self.clipboard_manager.clear_history()
            self.selectedItems.clear()
            self.refresh()
            self.currentStatus.configure(text="History cleared successfully.")
        else:
            self.currentStatus.configure(text="Clipboard history kept")

    def export_as_txt(self):
        if not self.selectedItems:
            CTkMessagebox.CTkMessagebox(title="No selection",message="Please select items to export",icon="warning")
            return
        selectedIDs = self.selectedItems
        file_name = self.clipboard_manager.export_as_txt(selectedIDs)
        if file_name:
            self.currentStatus.configure(text=f"Exported to {file_name}")
        else:
            self.currentStatus.configure(text="Failed to export.")
    
    def export_as_JSON(self):
        if not self.selectedItems:
            CTkMessagebox.CTkMessagebox(title="No selection",message="Please select items to export",icon="warning")
            return
        selectedIDs = self.selectedItems
        file_name = self.clipboard_manager.export_as_json(selectedIDs)
        if file_name:
            self.currentStatus.configure(text=f"Exported to {file_name}")
        else:
            self.currentStatus.configure(text="Failed to export.")

    def SelectALL(self):
        selectall = self.selectAllVAr.get()
        history = self.clipboard_manager.load_history()
        if selectall:
            self.selectedItems={i['id'] for i in history}
        else:
            self.selectedItems.clear()
        self.refresh

    
    def refresh(self):
        for widget in self.mainFrame.winfo_children():
            widget.destroy()
        history = self.clipboard_manager.load_history()
        
        if not history:
            empty_label = ctk.CTkLabel(
                self.mainFrame, 
                text="📋 No clipboard items yet\n\nCopy some text to get started!\nPress Ctrl+Alt+C to show/hide this window",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.grid(row=0, column=0, pady=50)
            self.currentStatus.configure(text="No items in clipboard history")
            return
        
        for i, item in enumerate(history):
            item_widget = ClipboardItemWidget(
                self.mainFrame, item,
                on_copy=self.coping,
                on_delete=self.delete,
                on_pin=self.pin,
                on_unpin=self.unpin,
                on_select=self.selectItem
            )
            item_widget.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            
            if item['id'] in self.selectedItems:
                item_widget.update_selection(True)
        pinned_count = sum(1 for item in history if item.get('pinned'))
        self.currentStatus.configure(
            text=f"📋 {len(history)} items ({pinned_count} pinned, {len(self.selectedItems)} selected)"
        )

class ClipboardItemWidget:
    def __init__(self,parent,item_data,copied,deleted,pinneed,unpinneed,to_select):
        super().__init__(parent)
        self.item_data = item_data
        self.copied = copied
        self.deleted = deleted
        self.pinneed = pinneed
        self.unpinneed = unpinneed
        self.to_select = to_select
        self.setUI()

if __name__ == "__main__":
    app = App()
    app.runInBG()
    app.mainloop()
print("App has started successfully.")