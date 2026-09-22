import sys
import os
import json
import locale
import ctypes
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import keyboard
import pystray
from pystray import MenuItem as item

# --- 1. Reliable config path storage in AppData ---
def get_config_path():
    appdata = os.getenv("APPDATA")
    if appdata:
        folder = os.path.join(appdata, "OverlayNote")
    else:
        folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")


CONFIG_FILE = get_config_path()

# --- 2. System UI language detection ---
def get_system_language():
    try:
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage() & 0x3ff
        if lang_id == 0x19: # Russian Primary Language ID
            return "ru"
    except Exception:
        pass
    
    try:
        sys_lang = locale.getlocale()[0]
        if sys_lang and "ru" in sys_lang.lower():
            return "ru"
    except Exception:
        pass

    return "en"


# --- Safe extraction of unformatted text from Windows Clipboard ---
def get_clean_clipboard_text():
    # Method 1: Direct reading via WinAPI (removes formatting, supports Unicode & Emojis)
    try:
        user32 = ctypes.windll.user32
        user32.OpenClipboard(0)
        # CF_UNICODETEXT = 13
        handle = user32.GetClipboardData(13)
        if handle:
            kernel32 = ctypes.windll.kernel32
            p_text = kernel32.GlobalLock(handle)
            if p_text:
                text = ctypes.wstring_at(p_text)
                kernel32.GlobalUnlock(handle)
                user32.CloseClipboard()
                return text
        user32.CloseClipboard()
    except Exception:
        pass


    # Method 2: Fallback via Tkinter
    temp_root = tk.Tk()
    temp_root.withdraw()
    text = ""
    try:
        text = temp_root.clipboard_get()
    except Exception:
        pass
    finally:
        temp_root.destroy()

    return text

# --- 3. Default configuration & loading/saving routines ---
DEFAULT_CONFIG = {
    "lang": get_system_language(),
    "theme": "dark",
    "hotkey_v": "alt+v",
    "hotkey_b": "alt+b"
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config_to_file(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


CONFIG = load_config()

CURRENT_LANG = CONFIG["lang"]
CURRENT_THEME = CONFIG["theme"]
HOTKEY_V = CONFIG["hotkey_v"]
HOTKEY_B = CONFIG["hotkey_b"]

# --- 4. Color Palettes (Themes) ---
THEMES = {
    "dark": {
        "bg": "#121214",
        "card_bg": "#1e1e22",
        "border": "#2e2e34",
        "fg": "#f4f4f5",
        "sub_fg": "#a1a1aa",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "badge_bg": "#2a2a30",
        "quick_copy_bg": "#1e1e22",
        "quick_copy_fg": "#f4f4f5"
    },
    "light": {
        "bg": "#f8fafc",
        "card_bg": "#ffffff",
        "border": "#cbd5e1",
        "fg": "#0f172a",
        "sub_fg": "#64748b",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "badge_bg": "#e2e8f0",
        "quick_copy_bg": "#f1f5f9",
        "quick_copy_fg": "#0f172a"
    }
}

# --- 5. Localization Dictionary ---
TEXTS = {
    "ru": {
        "app_title": "Overlay Note — Настройки",
        "header": "⚙️ Настройки Overlay Note",
        "img_title": "Скриншот",
        "notepad_title": "Блокнот",
        "quick_title": "Клик = Копировать",
        "copied": "Скопировано в буфер!",
        "tray_help": "⚙️ Настройки",
        "tray_exit": "❌ Выход",
        "tray_status": "Работает в трее ↘",
        "hide_btn": "Скрыть в трей",
        "lang_label": "Язык:",
        "theme_label": "Тема:",
        "theme_dark": "Тёмная",
        "theme_light": "Светлая",
        "hotkeys_group": "Горячие клавиши",
        "hk_v_label": "Блокнот / Скриншот:",
        "hk_b_label": "Быстрое копирование:",
        "record_btn": "Записать",
        "press_keys": "Жду...",
        "save_btn": "Сохранить",
        "admin_warning": "Запустите от имени Администратора для работы хоткеев!",
        "success_save": "Настройки успешно сохранены!"
    },
    "en": {
        "app_title": "Overlay Note — Settings",
        "header": "⚙️ Overlay Note Settings",
        "img_title": "Screenshot",
        "notepad_title": "Notepad",
        "quick_title": "Click = Copy",
        "copied": "Copied to clipboard!",
        "tray_help": "⚙️ Settings",
        "tray_exit": "❌ Exit",
        "tray_status": "Running in tray ↘",
        "hide_btn": "Hide to tray",
        "lang_label": "Language:",
        "theme_label": "Theme:",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "hotkeys_group": "Hotkeys Configuration",
        "hk_v_label": "Notepad / Screenshot:",
        "hk_b_label": "Quick Copy Mode:",
        "record_btn": "Record",
        "press_keys": "Press...",
        "save_btn": "Save Settings",
        "admin_warning": "Run as Administrator to enable global hotkeys!",
        "success_save": "Settings updated successfully!"
    }
}


def t(key):
    return TEXTS[CURRENT_LANG].get(key, "")

# --- 6. Custom Drawing Utilities (Rounded Corners) ---
def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1+radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2-radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1+radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedCard(tk.Canvas):
    def __init__(self, master, bg_color, border_color="#2e2e34", radius=16, **kw):
        super().__init__(master, bd=0, highlightthickness=0, bg=master["bg"], **kw)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.bind("<Configure>", self._redraw)


    def _redraw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w > 10 and h > 10:
            draw_rounded_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=self.bg_color, outline=self.border_color, width=1)


class RoundedButton(tk.Canvas):
    def __init__(self, master, text="", command=None, bg_color="#3b82f6", fg_color="#ffffff", radius=12, width=120, height=34, **kw):
        super().__init__(master, width=width, height=height, bd=0, highlightthickness=0, bg=master["bg"], cursor="hand2", **kw)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.radius = radius
        self.text_str = text
        self.rect_id = None
        self.text_id = None
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)
        self.draw_btn()

    def draw_btn(self):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        self.rect_id = draw_rounded_rect(self, 0, 0, w, h, self.radius, fill=self.bg_color, outline="")
        self.text_id = self.create_text(w // 2, h // 2, text=self.text_str, fill=self.fg_color, font=("Segoe UI", 9, "bold"))

    def set_text(self, text):
        self.text_str = text
        if self.text_id:
            self.itemconfig(self.text_id, text=text)

    def set_bg(self, bg_color, fg_color=None):
        self.bg_color = bg_color
        if fg_color:
            self.fg_color = fg_color
        self.configure(bg=self.master["bg"])
        self.draw_btn()


# --- 7. Application Icon Loader ---
def get_icon_image():
    icon_filename = "app_icon.ico"
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        res_icon = os.path.join(base_dir, icon_filename)
        if os.path.exists(res_icon):
            return Image.open(res_icon)
            
    if os.path.exists(icon_filename):
        return Image.open(icon_filename)
    
    # Fallback dynamically generated icon
    img = Image.new('RGBA', (128, 128), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([8, 8, 120, 120], radius=24, fill="#2563eb", outline="#1d4ed8", width=4)
    draw.rounded_rectangle([28, 28, 100, 100], radius=12, fill="#ffffff", outline="#e2e8f0", width=2)
    draw.rectangle([40, 48, 88, 56], fill="#cbd5e1")
    draw.rectangle([40, 68, 88, 76], fill="#cbd5e1")
    draw.rectangle([40, 88, 70, 96], fill="#cbd5e1")
    return img


def apply_icon(window):
    try:
        icon_img = get_icon_image()
        tk_img = ImageTk.PhotoImage(icon_img)
        window.iconphoto(True, tk_img)
    except Exception:
        pass


# --- 8. Custom Drag-And-Drop Text Widget ---
class DragDropText(tk.Text):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.dragged_text = ""
        self.is_dragging = False
        self.config(cursor="xterm")

        self.bind("<ButtonPress-1>", self.on_left_click_press)
        self.bind("<B1-Motion>", self.on_left_click_drag)
        self.bind("<ButtonRelease-1>", self.on_left_click_release)
        
        # Intercept paste event (Ctrl+V or middle click) to force unformatted text insertion
        self.bind("<<Paste>>", self.handle_paste)

    def handle_paste(self, event):
        text = get_clean_clipboard_text()
        if text:
            try:
                # Replace active selection if present
                if self.tag_ranges("sel"):
                    self.delete("sel.first", "sel.last")
                self.insert("insert", text)
            except Exception:
                pass
        return "break" # Prevent standard Tkinter paste with rich formatting

    def on_left_click_press(self, event):
        try:
            click_index = self.index(f"@{event.x},{event.y}")
            if self.tag_ranges("sel"):
                sel_start = self.index("sel.first")
                sel_end = self.index("sel.last")
                if self.compare(sel_start, "<=", click_index) and self.compare(click_index, "<=", sel_end):
                    self.dragged_text = self.get("sel.first", "sel.last")
                    self.is_dragging = True
                    return "break"
        except Exception:
            pass
        self.is_dragging = False


    def on_left_click_drag(self, event):
        if self.is_dragging and self.dragged_text:
            self.config(cursor="fleur")
            self.mark_set("insert", f"@{event.x},{event.y}")
            return "break"

    def on_left_click_release(self, event):
        if self.is_dragging and self.dragged_text:
            try:
                if self.tag_ranges("sel"):
                    self.delete("sel.first", "sel.last")
                self.mark_set("insert", f"@{event.x},{event.y}")
                self.insert("insert", self.dragged_text)
            except Exception:
                pass
            self.dragged_text = ""
            self.is_dragging = False
            self.config(cursor="xterm")
            return "break"
        self.config(cursor="xterm")

# --- 9. Overlay Windows (Always-On-Top) ---

class ImageOverlay:
    def __init__(self, image):
        colors = THEMES[CURRENT_THEME]
        self.root = tk.Toplevel()
        self.root.title(f"{t('img_title')} ({HOTKEY_V.upper()})")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=colors["bg"])
        apply_icon(self.root)

        img_w, img_h = image.size
        min_width, min_height = 250, 150
        win_w, win_h = max(img_w, min_width), max(img_h, min_height)
        
        self.root.minsize(min_width, min_height)
        self.root.geometry(f"{win_w}x{win_h}")

        self.tk_image = ImageTk.PhotoImage(image)
        self.label = tk.Label(self.root, image=self.tk_image, bd=0, bg=colors["bg"])
        self.label.pack(fill="both", expand=True)
        self.root.bind("<Escape>", lambda e: self.root.destroy())


class TextEditorOverlay:
    def __init__(self, text):
        colors = THEMES[CURRENT_THEME]
        self.root = tk.Toplevel()
        self.root.title(f"{t('notepad_title')} ({HOTKEY_V.upper()})")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=colors["bg"])
        
        self.root.minsize(250, 150)
        self.root.geometry("480x320")
        apply_icon(self.root)

        self.text_area = DragDropText(
            self.root, 
            wrap="word", 
            font=("Segoe UI Emoji", 11),
            bg=colors["card_bg"], 
            fg=colors["fg"],
            insertbackground=colors["fg"],
            bd=0,
            padx=12,
            pady=12,
            undo=True
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.text_area.insert("1.0", text)
        self.root.bind("<Escape>", lambda e: self.root.destroy())


class QuickCopyOverlay:
    def __init__(self, text):
        colors = THEMES[CURRENT_THEME]
        self.root = tk.Toplevel()
        self.root.title(f"{t('quick_title')} ({HOTKEY_B.upper()})")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=colors["bg"])
        
        self.root.minsize(200, 100)
        self.root.geometry("380x200")
        apply_icon(self.root)

        self.text_content = text

        self.label = tk.Label(
            self.root, 
            text=self.text_content, 
            justify="left", 
            anchor="nw",
            wraplength=350, 
            bg=colors["quick_copy_bg"], 
            fg=colors["quick_copy_fg"], 
            font=("Segoe UI Emoji", 11),
            padx=14, 
            pady=14,
            cursor="hand2"
        )
        self.label.pack(fill="both", expand=True, padx=10, pady=10)

        self.label.bind("<Button-1>", self.copy_to_clipboard)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def copy_to_clipboard(self, event=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_content)
        self.root.update()

        self.root.title(t("copied"))
        self.root.after(1200, lambda: self.root.title(f"{t('quick_title')} ({HOTKEY_B.upper()})"))


# --- 10. Global Hotkey Event Handlers ---
def handle_alt_v():
    # Check for image data in clipboard first
    img = ImageGrab.grabclipboard()
    if isinstance(img, Image.Image):
        ImageOverlay(img)
        return

    # Extract clean unformatted text
    text = get_clean_clipboard_text()
    if text and text.strip():
        TextEditorOverlay(text)


def handle_alt_b():
    text = get_clean_clipboard_text()
    if text and text.strip():
        QuickCopyOverlay(text)


# --- 11. Interactive Hotkey Key-Binder Widget ---
class HotkeyPicker(tk.Frame):
    def __init__(self, master, default_hk="", **kw):
        colors = THEMES[CURRENT_THEME]
        super().__init__(master, bg=colors["card_bg"], **kw)
        self.current_hk = default_hk
        self.recording = False

        self.badge = tk.Label(
            self, 
            text=self.current_hk.upper(), 
            font=("Segoe UI", 9, "bold"), 
            bg=colors["badge_bg"], 
            fg=colors["accent"],
            padx=12, 
            pady=5
        )
        self.badge.pack(side="left", padx=(0, 10))

        self.btn = RoundedButton(
            self, 
            text=t("record_btn"), 
            command=self.toggle_recording,
            bg_color=colors["accent"],
            fg_color="#ffffff",
            radius=10,
            width=100,
            height=32
        )
        self.btn.pack(side="right")

    def toggle_recording(self):
        colors = THEMES[CURRENT_THEME]
        if not self.recording:
            self.recording = True
            self.btn.set_text(t("press_keys"))
            self.btn.set_bg("#e11d48")
            self.badge.config(bg="#3f3f46", fg="#ffffff")
            self.focus_set()
            self.bind("<KeyPress>", self.on_key_press)
        else:
            self.stop_recording()


    def stop_recording(self):
        colors = THEMES[CURRENT_THEME]
        self.recording = False
        self.unbind("<KeyPress>")
        self.btn.set_text(t("record_btn"))
        self.btn.set_bg(colors["accent"])
        self.badge.config(bg=colors["badge_bg"], fg=colors["accent"])

    def on_key_press(self, event):
        keys = []
        if event.state & 0x0004:
            keys.append("ctrl")
        if event.state & 0x0001:
            keys.append("shift")
        if event.state & 0x20000 or event.state & 0x0008:
            keys.append("alt")
        
        vk = event.keycode
        if 65 <= vk <= 90:
            key_name = chr(vk).lower()
        elif 48 <= vk <= 57:
            key_name = chr(vk)
        else:
            key_name = event.keysym.lower()

        if key_name in ["control_l", "control_r", "shift_l", "shift_r", "alt_l", "alt_r", "iso_level3_shift"]:
            return "break"

        if key_name and key_name not in keys:
            keys.append(key_name)

        if keys:
            self.current_hk = "+".join(keys)
            self.badge.config(text=self.current_hk.upper())

        self.stop_recording()
        return "break"

    def apply_theme(self):
        colors = THEMES[CURRENT_THEME]
        self.config(bg=colors["card_bg"])
        self.badge.config(bg=colors["badge_bg"], fg=colors["accent"])
        self.btn.set_bg(colors["accent"])
        self.btn.set_text(t("press_keys") if self.recording else t("record_btn"))


# --- 12. Segmented Switch Control (Language / Theme) ---
class SegmentedControl(tk.Canvas):
    def __init__(self, master, options, current_val, command, width=170, height=32, **kw):
        colors = THEMES[CURRENT_THEME]
        super().__init__(master, width=width, height=height, bd=0, highlightthickness=0, bg=colors["bg"], cursor="hand2", **kw)
        self.options = options
        self.current_val = current_val
        self.command = command
        self.bind("<Button-1>", self.on_click)
        self.draw()

    def draw(self):
        self.delete("all")
        colors = THEMES[CURRENT_THEME]
        self.configure(bg=self.master["bg"])
        w, h = int(self["width"]), int(self["height"])
        
        draw_rounded_rect(self, 0, 0, w, h, 10, fill=colors["card_bg"], outline=colors["border"])
        
        num_opts = len(self.options)
        opt_w = w / num_opts

        for i, (val, text) in enumerate(self.options):
            x1 = i * opt_w + 2
            x2 = (i + 1) * opt_w - 2
            if val == self.current_val:
                draw_rounded_rect(self, x1, 2, x2, h - 2, 8, fill=colors["accent"], outline="")
                txt_color = "#ffffff"
            else:
                txt_color = colors["sub_fg"]

            self.create_text((x1 + x2) / 2, h / 2, text=text, fill=txt_color, font=("Segoe UI", 9, "bold"))


    def on_click(self, event):
        w = int(self["width"])
        opt_w = w / len(self.options)
        idx = int(event.x // opt_w)
        if 0 <= idx < len(self.options):
            new_val = self.options[idx][0]
            if new_val != self.current_val:
                self.current_val = new_val
                self.draw()
                self.command(new_val)


# --- 13. Main Application Control Panel ---
class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.minsize(460, 420)
        self.root.geometry("480x430")
        apply_icon(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.main_frame, font=("Segoe UI", 13, "bold"))
        self.title_label.pack(anchor="w", pady=(0, 15))

        # Language and Theme Selection Controls
        opts_frame = tk.Frame(self.main_frame)
        opts_frame.pack(fill="x", pady=(0, 15))

        self.lang_lbl = tk.Label(opts_frame, font=("Segoe UI", 9, "bold"))
        self.lang_lbl.grid(row=0, column=0, sticky="w", pady=4)

        self.seg_lang = SegmentedControl(
            opts_frame, 
            [("ru", "Русский"), ("en", "English")], 
            CURRENT_LANG, 
            self.change_lang, 
            width=170, 
            height=32
        )
        self.seg_lang.grid(row=0, column=1, sticky="e", padx=(20, 0))

        self.theme_lbl = tk.Label(opts_frame, font=("Segoe UI", 9, "bold"))
        self.theme_lbl.grid(row=1, column=0, sticky="w", pady=4)

        self.seg_theme = SegmentedControl(
            opts_frame, 
            [("dark", t("theme_dark")), ("light", t("theme_light"))], 
            CURRENT_THEME, 
            self.change_theme, 
            width=170, 
            height=32
        )
        self.seg_theme.grid(row=1, column=1, sticky="e", padx=(20, 0))

        # Hotkeys Settings Block
        self.card_hk = RoundedCard(self.main_frame, bg_color=THEMES[CURRENT_THEME]["card_bg"], border_color=THEMES[CURRENT_THEME]["border"], radius=16)
        self.card_hk.pack(fill="x", pady=(5, 15), ipady=12)

        self.hk_title = tk.Label(self.card_hk, font=("Segoe UI", 10, "bold"))
        self.hk_title.pack(anchor="w", padx=15, pady=(10, 8))

        # Notepad / Screenshot Hotkey Picker
        hk_v_frame = tk.Frame(self.card_hk)
        hk_v_frame.pack(fill="x", padx=15, pady=4)
        self.hk_v_lbl = tk.Label(hk_v_frame, font=("Segoe UI", 9))
        self.hk_v_lbl.pack(side="left")
        self.picker_v = HotkeyPicker(hk_v_frame, default_hk=HOTKEY_V)
        self.picker_v.pack(side="right")

        # Quick Copy Hotkey Picker
        hk_b_frame = tk.Frame(self.card_hk)
        hk_b_frame.pack(fill="x", padx=15, pady=4)
        self.hk_b_lbl = tk.Label(hk_b_frame, font=("Segoe UI", 9))
        self.hk_b_lbl.pack(side="left")
        self.picker_b = HotkeyPicker(hk_b_frame, default_hk=HOTKEY_B)
        self.picker_b.pack(side="right")

        # Save Settings Button
        self.save_btn = RoundedButton(
            self.main_frame, 
            text=t("save_btn"), 
            command=self.apply_settings,
            bg_color=THEMES[CURRENT_THEME]["accent"],
            radius=12,
            width=140,
            height=36
        )
        self.save_btn.pack(anchor="e", pady=(0, 10))

        # Bottom Action Bar
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(fill="x", side="bottom")

        self.status_label = tk.Label(btn_frame, font=("Segoe UI", 9, "italic"))
        self.status_label.pack(side="left")

        self.hide_btn = RoundedButton(
            btn_frame, 
            text=t("hide_btn"), 
            command=self.hide_window,
            bg_color=THEMES[CURRENT_THEME]["card_bg"],
            fg_color=THEMES[CURRENT_THEME]["fg"],
            radius=10,
            width=120,
            height=32
        )
        self.hide_btn.pack(side="right")

        self.tray_icon = None
        self.apply_theme_colors()
        self.update_ui_texts()
        self.register_hotkeys()

        self.setup_tray()
        self.root.withdraw()


    def apply_theme_colors(self):
        colors = THEMES[CURRENT_THEME]
        self.root.configure(bg=colors["bg"])
        self.main_frame.configure(bg=colors["bg"])
        
        self.title_label.configure(bg=colors["bg"], fg=colors["accent"])
        self.lang_lbl.configure(bg=colors["bg"], fg=colors["fg"])
        self.theme_lbl.configure(bg=colors["bg"], fg=colors["fg"])
        self.lang_lbl.master.configure(bg=colors["bg"])
        self.status_label.master.configure(bg=colors["bg"])

        self.card_hk.configure(bg=colors["bg"])
        self.card_hk.bg_color = colors["card_bg"]
        self.card_hk.border_color = colors["border"]
        self.card_hk._redraw()

        self.hk_title.configure(bg=colors["card_bg"], fg=colors["fg"])
        
        for frame in [self.hk_v_lbl.master, self.hk_b_lbl.master]:
            frame.configure(bg=colors["card_bg"])

        self.hk_v_lbl.configure(bg=colors["card_bg"], fg=colors["fg"])
        self.hk_b_lbl.configure(bg=colors["card_bg"], fg=colors["fg"])

        self.picker_v.apply_theme()
        self.picker_b.apply_theme()

        self.save_btn.set_bg(colors["accent"])
        self.hide_btn.set_bg(colors["card_bg"], fg_color=colors["fg"])
        
        self.status_label.configure(bg=colors["bg"], fg="#16a34a" if CURRENT_THEME == "dark" else "#15803d")

        self.seg_lang.draw()
        self.seg_theme.options = [("dark", t("theme_dark")), ("light", t("theme_light"))]
        self.seg_theme.draw()

    def change_theme(self, new_theme):
        global CURRENT_THEME
        CURRENT_THEME = new_theme
        self.apply_theme_colors()
        self.save_config()

    def change_lang(self, new_lang):
        global CURRENT_LANG
        CURRENT_LANG = new_lang
        self.update_ui_texts()
        self.apply_theme_colors()
        self.save_config()


    def save_config(self):
        cfg = {
            "lang": CURRENT_LANG,
            "theme": CURRENT_THEME,
            "hotkey_v": HOTKEY_V,
            "hotkey_b": HOTKEY_B
        }
        save_config_to_file(cfg)

    def register_hotkeys(self):
        global HOTKEY_V, HOTKEY_B
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(HOTKEY_V, handle_alt_v)
            keyboard.add_hotkey(HOTKEY_B, handle_alt_b)
        except Exception:
            messagebox.showwarning("Warning", t("admin_warning"))

    def apply_settings(self):
        global HOTKEY_V, HOTKEY_B
        HOTKEY_V = self.picker_v.current_hk
        HOTKEY_B = self.picker_b.current_hk
        self.register_hotkeys()
        self.save_config()
        self.update_tray_menu()
        messagebox.showinfo("Overlay Note", t("success_save"))


    def update_ui_texts(self):
        self.root.title(t("app_title"))
        self.title_label.config(text=t("header"))
        self.lang_lbl.config(text=t("lang_label"))
        self.theme_lbl.config(text=t("theme_label"))
        self.hk_title.config(text=t("hotkeys_group"))
        self.hk_v_lbl.config(text=t("hk_v_label"))
        self.hk_b_lbl.config(text=t("hk_b_label"))
        self.save_btn.set_text(t("save_btn"))
        self.status_label.config(text=t("tray_status"))
        self.hide_btn.set_text(t("hide_btn"))

        if self.tray_icon:
            self.update_tray_menu()

    def update_tray_menu(self):
        menu = pystray.Menu(
            item(t("tray_help"), self.show_window, default=True),
            pystray.Menu.SEPARATOR,
            item(f'🟢 {HOTKEY_V.upper()} — Notepad / Image', lambda: None, enabled=False),
            item(f'🟢 {HOTKEY_B.upper()} — Quick Copy', lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item(t("tray_exit"), self.quit_app)
        )
        self.tray_icon.menu = menu


    def setup_tray(self):
        menu = pystray.Menu(
            item(t("tray_help"), self.show_window, default=True),
            pystray.Menu.SEPARATOR,
            item(f'🟢 {HOTKEY_V.upper()} — Notepad / Image', lambda: None, enabled=False),
            item(f'🟢 {HOTKEY_B.upper()} — Quick Copy', lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item(t("tray_exit"), self.quit_app)
        )
        
        self.tray_icon = pystray.Icon(
            "OverlayNote", 
            get_icon_image(), 
            "Overlay Note", 
            menu
        )
        
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        self.root.after(0, self.root.deiconify)

    def hide_window(self):
        self.root.withdraw()

    def quit_app(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass

        if self.tray_icon:
            self.tray_icon.stop()

        try:
            self.root.destroy()
        except Exception:
            pass

        os._exit(0)


if __name__ == "__main__":
    app = Application()
    app.root.mainloop()