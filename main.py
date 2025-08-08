import customtkinter as ctk
import tkinter as tk
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
import platform
from typing import List, Dict, Any, Optional, Set

HISTORY_FILE = "clipstack_history_data.json"
MAX_ITEMS = 50
POLL_INTERVAL = 3
HOTKEY = 'ctrl+alt+c'


class ClipboardManager:    
    def __init__(self, history_file: str = HISTORY_FILE, max_items: int = MAX_ITEMS):
        self.history_file = history_file
        self.max_items = max_items
        self.last_copied = ""
        self.current_id = 1
        self._load_current_id()
    
    def _load_current_id(self) -> None:
        history = self.load_history()
        if history:
            self.current_id = max(item.get('id', 0) for item in history) + 1
        else:
            self.current_id = 1
    
    def load_history(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load history file: {e}")
            return []
        
    def _save_history(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save history file: {e}")

    def add_clipboard_item(self, item_content: str) -> bool:
        if not item_content or self.last_copied == item_content or len(item_content.strip()) == 0:
            return False
        
        history = self.load_history()
        recent_items = history[:10] if len(history) >= 10 else history
        for item in recent_items:
            if item.get('content') == item_content:
                return False
        
        if item_content != self.last_copied:
            self.last_copied = item_content
            self.current_id += 1
            
            entry = {
                "id": self.current_id,
                "content": item_content,
                "preview": item_content[:100] + "..." if len(item_content) > 100 else item_content,
                "timestamp": time.time(),
                "formatted_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pinned": False
            }
            history.insert(0, entry)
            pinned_items = [item for item in history if item.get("pinned", False)]
            unpinned_items = [item for item in history if not item.get("pinned", False)]
            
            if len(unpinned_items) > self.max_items:
                unpinned_items = unpinned_items[:self.max_items]
            
            history = pinned_items + unpinned_items
            self._save_history(history)
            return True
        return False

    def remove_item(self, item_id: int) -> None:
        history = self.load_history()
        history = [item for item in history if item.get("id") != item_id]
        self._save_history(history)

    def pin_item(self, item_id: int) -> None:
        history = self.load_history()
        for item in history:
            if item.get("id") == item_id:
                item["pinned"] = True
                break
        self._save_history(history)

    def unpin_item(self, item_id: int) -> None:
        history = self.load_history()
        for item in history:
            if item.get('id') == item_id:
                item['pinned'] = False
                break
        self._save_history(history)

    def clear_history(self) -> None:
        self._save_history([])

    def export_as_txt(self, selected_ids: Optional[Set[int]] = None) -> Optional[str]:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        history = self.load_history()
        
        if selected_ids:
            history = [item for item in history if item.get('id') in selected_ids]
        
        file_name = f"clipstack_export_{timestamp}.txt"
        try:
            with open(file_name, "w", encoding='utf-8') as f:
                f.write("ClipStack Export\n")
                f.write("=" * 50 + "\n\n")
                for item in history:
                    f.write(f"ID: {item.get('id')}\n")
                    f.write(f"Time: {item.get('formatted_time', 'Unknown')}\n")
                    f.write(f"Pinned: {'Yes' if item.get('pinned') else 'No'}\n")
                    f.write(f"Content:\n{item.get('content', '')}\n")
                    f.write("-" * 50 + "\n\n")
            return file_name
        except IOError as e:
            print(f"Error exporting to text: {e}")
            return None
    
    def export_as_json(self, selected_ids: Optional[Set[int]] = None) -> Optional[str]:
        history = self.load_history()
        if selected_ids:
            history = [item for item in history if item.get('id') in selected_ids]
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"clipstack_export_{timestamp}.json"
        
        try:
            with open(file_name, "w", encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            return file_name
        except IOError as e:
            print(f"Error exporting to JSON: {e}")
            return None


class BackgroundClipboardMonitor:
    def __init__(self, clipboard_manager: ClipboardManager):
        self.clipboard_manager = clipboard_manager
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start_tracking(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.thread.start()
    
    def _tracking_loop(self) -> None:
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.clipboard_manager.last_copied:
                    self.clipboard_manager.add_clipboard_item(current_clipboard)
            except Exception as e:
                print(f"Clipboard tracking error: {e}")
            time.sleep(POLL_INTERVAL)
    
    def stop_tracking(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)


class HotkeyManager:
    def __init__(self, app_callback):
        self.hotkey_registered = False
        self.app_callback = app_callback

    def register(self) -> bool:
        try:
            keyboard.add_hotkey(HOTKEY, self._hotkey_activated)
            self.hotkey_registered = True
            return True
        except Exception as e:
            print(f"Failed to register hotkey {HOTKEY}: {e}")
            return False

    def unregister(self) -> None:
        try:
            if self.hotkey_registered:
                keyboard.unhook_all_hotkeys()
                self.hotkey_registered = False
        except Exception as e:
            print(f"Error unregistering hotkey: {e}")

    def _hotkey_activated(self) -> None:
        if self.app_callback:
            try:
                self.app_callback()
            except Exception as e:
                print(f"Error handling hotkey callback: {e}")


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class ClipStackApp(ctk.CTk):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.clipboard_manager = ClipboardManager()
        self.background_monitor = BackgroundClipboardMonitor(self.clipboard_manager)
        self.hotkey_manager = HotkeyManager(self._hotkey_callback)
        
        self.selected_items: Set[int] = set()
        
        self._setup_window()
        self._setup_ui()
        self._start_background_services()
        
        self.protocol("WM_DELETE_WINDOW", self._hide_window)
        
        self._setup_cleanup()
    
    def _setup_window(self) -> None:
        """Configure main window."""
        self.title("ClipStack")
        self.geometry("900x700")
        self.minsize(600, 400)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _setup_ui(self) -> None:
        """Setup user interface components."""
        self.app_content = ctk.CTkFrame(self)
        self.app_content.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.app_content.grid_rowconfigure(2, weight=1)
        self.app_content.grid_columnconfigure(0, weight=1)
        
        self._setup_header()
        self.status_label = ctk.CTkLabel(
            self.app_content, 
            text="", 
            font=ctk.CTkFont(size=13, slant='italic')
        )
        self.status_label.grid(row=1, column=0, padx=10, pady=2, sticky="ew")
        
        self.main_frame = ctk.CTkScrollableFrame(self.app_content)
        self.main_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
    
    def _setup_header(self) -> None:
        header_frame = ctk.CTkFrame(self.app_content)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="📋 ClipStack", 
            font=ctk.CTkFont(family="monospace", size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        buttons_frame = ctk.CTkFrame(header_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.select_all_var = ctk.BooleanVar()
        select_all_cb = ctk.CTkCheckBox(
            buttons_frame, 
            text="Select All", 
            variable=self.select_all_var, 
            command=self._toggle_select_all
        )
        select_all_cb.grid(row=0, column=0, padx=5, pady=5)
        
        export_txt_btn = ctk.CTkButton(
            buttons_frame, 
            text="Export as TXT", 
            command=self._export_as_txt
        )
        export_txt_btn.grid(row=0, column=1, padx=5, pady=5)
        
        export_json_btn = ctk.CTkButton(
            buttons_frame, 
            text="Export as JSON", 
            command=self._export_as_json
        )
        export_json_btn.grid(row=0, column=2, padx=5, pady=5)
        
        clear_btn = ctk.CTkButton(
            buttons_frame, 
            text="Clear History", 
            command=self._clear_history
        )
        clear_btn.grid(row=0, column=3, padx=5, pady=5)
        
        refresh_btn = ctk.CTkButton(
            buttons_frame, 
            text="Refresh", 
            command=self.refresh_ui
        )
        refresh_btn.grid(row=0, column=4, padx=5, pady=5)
        
        self.theme_selector = ctk.CTkOptionMenu(
            buttons_frame,
            values=["System", "Dark", "Light"],
            command=self._change_theme
        )
        self.theme_selector.grid(row=0, column=5, padx=5, pady=5)
        self.theme_selector.set("System")
    
    def _start_background_services(self) -> None:
        self.background_monitor.start_tracking()
        if not self.hotkey_manager.register():
            self._update_status("Warning: Could not register global hotkey")
    
    def _stop_background_services(self) -> None:
        self.background_monitor.stop_tracking()
        self.hotkey_manager.unregister()
    
    def _setup_cleanup(self) -> None:
        def cleanup():
            self._stop_background_services()
        
        atexit.register(cleanup)
        
        def signal_handler(signum, frame):
            cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM') and platform.system() != 'Windows':
            signal.signal(signal.SIGTERM, signal_handler)
    
    def _hide_window(self) -> None:
        self.withdraw()
    
    def _hotkey_callback(self) -> None:
        try:
            if self.state() == 'withdrawn' or not self.winfo_viewable():
                self.deiconify()
                self.lift()
                self.focus_force()
                self.refresh_ui()
            else:
                self.withdraw()
        except Exception as e:
            print(f"Hotkey callback error: {e}")
    
    def _change_theme(self, theme: str) -> None:
        theme_map = {
            "Dark": "dark",
            "Light": "light", 
            "System": "system"
        }
        ctk.set_appearance_mode(theme_map.get(theme, "system"))
    
    def _update_status(self, message: str) -> None:
        self.status_label.configure(text=message)
    
    def _toggle_select_all(self) -> None:
        select_all = self.select_all_var.get()
        history = self.clipboard_manager.load_history()
        
        if select_all:
            self.selected_items = {item['id'] for item in history}
        else:
            self.selected_items.clear()
        
        self.refresh_ui()
    
    def _select_item(self, item_id: int, selected: bool) -> None:
        if selected:
            self.selected_items.add(item_id)
        else:
            self.selected_items.discard(item_id)
        
        self._update_status(f"Selected {len(self.selected_items)} items")
    
    def _copy_item(self, item_id: int) -> None:
        history = self.clipboard_manager.load_history()
        for item in history:
            if item['id'] == item_id:
                try:
                    pyperclip.copy(item['content'])
                    self._update_status(f"Copied item {item_id} to clipboard")
                except Exception as e:
                    self._update_status(f"Error copying item: {e}")
                break
    
    def _delete_item(self, item_id: int) -> None:
        self.clipboard_manager.remove_item(item_id)
        self.selected_items.discard(item_id)
        self.refresh_ui()
        self._update_status(f"Item {item_id} deleted")
    
    def _pin_item(self, item_id: int) -> None:
        self.clipboard_manager.pin_item(item_id)
        self.refresh_ui()
        self._update_status(f"Item {item_id} pinned")
    
    def _unpin_item(self, item_id: int) -> None:
        self.clipboard_manager.unpin_item(item_id)
        self.refresh_ui()
        self._update_status(f"Item {item_id} unpinned")
    
    def _clear_history(self) -> None:
        result = CTkMessagebox.CTkMessagebox(
            title="Clear History",
            message="Are you sure you want to clear all clipboard history?",
            option_1="Yes",
            option_2="No"
        ).get()
        
        if result == "Yes":
            self.clipboard_manager.clear_history()
            self.selected_items.clear()
            self.refresh_ui()
            self._update_status("History cleared successfully")
        else:
            self._update_status("History preserved")
    
    def _export_as_txt(self) -> None:
        if not self.selected_items:
            CTkMessagebox.CTkMessagebox(
                title="No Selection",
                message="Please select items to export",
                icon="warning"
            )
            return
        
        file_name = self.clipboard_manager.export_as_txt(self.selected_items)
        if file_name:
            self._update_status(f"Exported to {file_name}")
        else:
            self._update_status("Export failed")
    
    def _export_as_json(self) -> None:
        if not self.selected_items:
            CTkMessagebox.CTkMessagebox(
                title="No Selection",
                message="Please select items to export",
                icon="warning"
            )
            return
        
        file_name = self.clipboard_manager.export_as_json(self.selected_items)
        if file_name:
            self._update_status(f"Exported to {file_name}")
        else:
            self._update_status("Export failed")
    
    def refresh_ui(self) -> None:
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        history = self.clipboard_manager.load_history()
        
        if not history:
            empty_label = ctk.CTkLabel(
                self.main_frame,
                text="📋 No clipboard items yet\n\nCopy some text to get started!\nPress Ctrl+Alt+C to show/hide this window",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.grid(row=0, column=0, pady=50)
            self._update_status("No items in clipboard history")
            return
        
        for i, item in enumerate(history):
            item_widget = ClipboardItemWidget(
                self.main_frame,
                item,
                copy_callback=self._copy_item,
                delete_callback=self._delete_item,
                pin_callback=self._pin_item,
                unpin_callback=self._unpin_item,
                select_callback=self._select_item
            )
            item_widget.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            if item['id'] in self.selected_items:
                item_widget.update_selection(True)
        
        pinned_count = sum(1 for item in history if item.get('pinned'))
        self._update_status(
            f"📋 {len(history)} items ({pinned_count} pinned, {len(self.selected_items)} selected)"
        )


class ClipboardItemWidget(ctk.CTkFrame):    
    def __init__(self, parent, item_data: Dict[str, Any], copy_callback, delete_callback, 
                 pin_callback, unpin_callback, select_callback):
        super().__init__(parent)
        
        self.item_data = item_data
        self.copy_callback = copy_callback
        self.delete_callback = delete_callback
        self.pin_callback = pin_callback
        self.unpin_callback = unpin_callback
        self.select_callback = select_callback
        
        self._setup_ui()
        self._setup_bindings()
    
    def _setup_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.select_var = ctk.BooleanVar()
        self.checkbox = ctk.CTkCheckBox(
            self, 
            text="", 
            variable=self.select_var, 
            width=20,
            command=self._on_selection_change
        )
        self.checkbox.grid(row=0, column=0, padx=5, pady=2, sticky="nw")
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)
        pin_indicator = "📌 " if self.item_data.get('pinned') else ""
        time_text = f"{pin_indicator}{self.item_data.get('formatted_time', 'Unknown')}"
        self.time_label = ctk.CTkLabel(
            content_frame,
            text=time_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.time_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        preview = self.item_data.get('preview', '')
        font_weight = "bold" if self.item_data.get('pinned') else "normal"
        self.content_label = ctk.CTkLabel(
            content_frame,
            text=preview,
            font=ctk.CTkFont(size=12, weight=font_weight),
            anchor="w",
            justify="left"
        )
        self.content_label.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
    
    def _setup_bindings(self) -> None:
        widgets = [self, self.time_label, self.content_label]
        for widget in widgets:
            widget.bind("<Button-3>", self._show_context_menu)  # Right-click
            widget.bind("<Double-Button-1>", lambda e: self._on_double_click())  # Double-click
    
    def _on_selection_change(self) -> None:
        self.select_callback(self.item_data['id'], self.select_var.get())
    
    def _on_double_click(self) -> None:
        self.copy_callback(self.item_data['id'])
    
    def _show_context_menu(self, event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="📋 Copy", 
            command=lambda: self.copy_callback(self.item_data['id'])
        )
        menu.add_separator()
        if self.item_data.get('pinned'):
            menu.add_command(
                label="📌 Unpin", 
                command=lambda: self.unpin_callback(self.item_data['id'])
            )
        else:
            menu.add_command(
                label="📌 Pin", 
                command=lambda: self.pin_callback(self.item_data['id'])
            )
        
        menu.add_separator()
        menu.add_command(
            label="🗑️ Delete", 
            command=lambda: self.delete_callback(self.item_data['id'])
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def update_selection(self, selected: bool) -> None:
        self.select_var.set(selected)


def main():
    try:
        app = ClipStackApp()
        print("ClipStack started successfully!")
        print(f"Global hotkey: {HOTKEY}")
        print("Press Ctrl+C to exit")
        
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\nShutting down ClipStack...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting ClipStack: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()