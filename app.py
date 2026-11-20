# -*- coding: utf-8 -*-
"""Golden Cookie Catcher — авто-ловля золотых печенек."""

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import sys
import os
import json
import time
import wave
import threading

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import cv2
import numpy as np
import pyautogui
import keyboard
import winsound
import pystray
import mss
from PIL import Image, ImageDraw
import win32gui
import win32process
import psutil

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

APP_NAME = "Golden Cookie Catcher"
APP_VERSION = "1.5.0"
MUTEX_NAME = "GoldenCookieCatcher_SingleInstance"

SCALE = 0.5
SCALES = (0.7, 0.85, 1.0, 1.15)
NMS_RATIO = 0.5
TPL_FILE = "golden_cookie.png"

C_TEXT = "#e9eaec"
C_MUTED = "#8a9099"
C_CARD = "#1b1d21"
C_CARD_HI = "#23262c"
C_ACCENT = "#f0b429"
C_GREEN = "#1e9e4c"
C_RED = "#c23b3b"

LANG_LABELS = {"English": "en", "Russian": "ru"}
LABEL_FOR = {"en": "English", "ru": "Russian"}

VERSIONS = {
    "steam": {"kind": "process", "value": "Cookie Clicker.exe"},
    "browser": {"kind": "title", "value": "cookie clicker"},
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _writable_dir():
    cands = []
    if getattr(sys, "frozen", False):
        cands.append(os.path.dirname(sys.executable))
    else:
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    cands.append(os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                              "GoldenCookieCatcher"))
    for cand in cands:
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".write_test")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("1")
            os.remove(probe)
            return cand
        except Exception:
            continue
    return os.getcwd()


BASE_DIR = _writable_dir()
RES_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
CRASH_FILE = os.path.join(BASE_DIR, "crash.log")
CHIME_FILE = os.path.join(BASE_DIR, "chime.wav")


def _bundled_template():
    for base in (RES_DIR, BASE_DIR):
        p = os.path.join(base, "assets", TPL_FILE)
        if os.path.exists(p):
            return p
    return None


def _make_chime(path):
    """Генерирует короткий мягкий сигнал: две ноты с плавной огибающей."""
    if os.path.exists(path):
        return path
    rate = 44100

    def tone(freq, dur, amp):
        n = max(1, int(rate * dur))
        t = np.arange(n) / rate
        env = np.sin(np.pi * np.arange(n) / n) ** 2
        body = np.sin(2 * np.pi * freq * t) * 0.75 + np.sin(4 * np.pi * freq * t) * 0.25
        return body * env * amp

    data = np.concatenate([
        tone(880.0, 0.11, 0.30),
        np.zeros(int(rate * 0.02)),
        tone(1318.5, 0.22, 0.26),
    ])
    pcm = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    try:
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm.tobytes())
        return path
    except Exception:
        return None


LANG = {
    "en": {
        "title": APP_NAME,
        "subtitle": "golden cookies on autopilot",
        "tab_main": "Catch",
        "tab_timing": "Timing",
        "tab_adv": "Fine tuning",
        "tab_log": "Journal",
        "version_frame": "Game version",
        "ver_steam": "Steam",
        "ver_browser": "Browser",
        "ver_hint": "Browser: keep the game tab in front, the window is found by its title.",
        "react_frame": "Click moment",
        "react_instant": "On sight",
        "react_full": "When fully open",
        "react_hint": "On sight grabs the cookie the moment it appears. When fully open waits for it to finish popping up — fewer misses.",
        "hotkey": "Hotkey",
        "record": "Record",
        "apply": "Apply",
        "detect": "Sensitivity",
        "thresh_lbl": "Match threshold",
        "click_cd": "Click cooldown, s",
        "sound_frame": "Sound",
        "beep_cd": "Sound cooldown, s",
        "scan_int": "Scan interval, s",
        "beep_en": "Beep on catch",
        "auto_frame": "Big cookie",
        "auto_en": "Click the big cookie",
        "ac_hotkey": "Autoclick hotkey",
        "ac_hint": "The cursor stays on the big cookie only while autoclick is on. Toggle it with the hotkey or the checkbox.",
        "grab_pt": "Pick point (3 s)",
        "offset": "Offset",
        "cps": "Clicks per second",
        "dbl": "Double clicks",
        "ret_delay": "Return delay, s",
        "settle": "Cursor settle, s",
        "max_clicks": "Max attempts",
        "zone_frame": "Dead zone",
        "select_zone": "Mark zone",
        "test_mask": "Preview detection",
        "open_folder": "Settings folder",
        "start": "START",
        "stop": "STOP",
        "status_stopped": "IDLE",
        "status_running": "WORKING",
        "ready": "Ready. Nothing to set up — just hit START.",
        "err": "Error",
        "win_not_found": "Game window not found.",
        "win_min": "Window is minimized, waiting...",
        "zone_title": "Mark the area to ignore",
        "started": "Running.",
        "stopped": "Stopped.",
        "no_template": "Sprite not loaded.",
        "no_point": "Point not picked — the cursor will not return.",
        "give_up": "No response, muting for 8 s.",
        "bad_value": "Bad value:",
        "capture_hint": "Press any key...",
        "found_n": "Matches:",
        "loop_crash": "Loop crashed:",
        "point_set": "Point:",
        "zone_set": "Dead zone:",
        "key_set": "Hotkey:",
        "ac_on": "Autoclick on.",
        "ac_off": "Autoclick off.",
        "only_one": "Golden Cookie Catcher is already running.",
    },
    "ru": {
        "title": APP_NAME,
        "subtitle": "золотые печеньки на автопилоте",
        "tab_main": "Ловля",
        "tab_timing": "Тайминги",
        "tab_adv": "Тонкая настройка",
        "tab_log": "Журнал",
        "version_frame": "Версия игры",
        "ver_steam": "Steam",
        "ver_browser": "Браузер",
        "ver_hint": "Браузер: держи вкладку с игрой на переднем плане, окно ищется по заголовку.",
        "react_frame": "Момент клика",
        "react_instant": "Сразу",
        "react_full": "После раскрытия",
        "react_hint": "«Сразу» бьёт по печеньке в момент появления. «После раскрытия» ждёт, пока она перестанет расти — промахов меньше.",
        "hotkey": "Горячая клавиша",
        "record": "Запись",
        "apply": "Применить",
        "detect": "Чувствительность",
        "thresh_lbl": "Порог совпадения",
        "click_cd": "Пауза между кликами, с",
        "sound_frame": "Звук",
        "beep_cd": "Пауза между сигналами, с",
        "scan_int": "Частота сканирования, с",
        "beep_en": "Сигнал при поимке",
        "auto_frame": "Большая печенька",
        "auto_en": "Кликать большую печеньку",
        "ac_hotkey": "Клавиша автокликера",
        "ac_hint": "Курсор держится на большой печеньке только пока автокликер включён. Переключается клавишей или галочкой.",
        "grab_pt": "Взять точку (3 с)",
        "offset": "Смещение",
        "cps": "Кликов в секунду",
        "dbl": "Двойные клики",
        "ret_delay": "Задержка возврата, с",
        "settle": "Пауза курсора, с",
        "max_clicks": "Предел попыток",
        "zone_frame": "Мёртвая зона",
        "select_zone": "Отметить зону",
        "test_mask": "Проверить детект",
        "open_folder": "Папка настроек",
        "start": "ЗАПУСТИТЬ",
        "stop": "ОСТАНОВИТЬ",
        "status_stopped": "ОЖИДАНИЕ",
        "status_running": "РАБОТАЕТ",
        "ready": "Готов. Настраивать нечего — жми «ЗАПУСТИТЬ».",
        "err": "Ошибка",
        "win_not_found": "Окно игры не найдено.",
        "win_min": "Окно свёрнуто, жду...",
        "zone_title": "Отметь область, которую игнорировать",
        "started": "Работаю.",
        "stopped": "Остановлено.",
        "no_template": "Спрайт не загружен.",
        "no_point": "Точка не взята — курсор не будет возвращаться.",
        "give_up": "Не поддаётся, глушу на 8 с.",
        "bad_value": "Некорректное значение:",
        "capture_hint": "Нажми любую клавишу...",
        "found_n": "Совпадений:",
        "loop_crash": "Цикл упал:",
        "point_set": "Точка:",
        "zone_set": "Мёртвая зона:",
        "key_set": "Клавиша:",
        "ac_on": "Автокликер включён.",
        "ac_off": "Автокликер выключен.",
        "only_one": "Golden Cookie Catcher уже запущен.",
    },
}

DEFAULTS = {
    "language": "ru",
    "version": "steam",
    "react": "full",
    "hotkey": "f8",
    "ac_hotkey": "f9",
    "match_threshold": 0.72,
    "click_cooldown": 0.5,
    "beep_cooldown": 1.0,
    "beep_enabled": True,
    "scan_interval": 0.08,
    "autoclick_enabled": True,
    "autoclick_cps": 20.0,
    "double_click": True,
    "offset_x": 0,
    "offset_y": 0,
    "return_delay": 0.1,
    "settle": 0.06,
    "max_clicks": 3,
    "ac_x": 0,
    "ac_y": 0,
    "ignore_x": 0,
    "ignore_y": 0,
    "ignore_w": 300,
    "ignore_h": 150,
}


def load_settings():
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}

    if "autoclick_cps" not in data and data.get("autoclick_interval"):
        try:
            data["autoclick_cps"] = round(1.0 / float(data["autoclick_interval"]), 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    out = dict(DEFAULTS)
    for key, default in DEFAULTS.items():
        if key not in data:
            continue
        value = data[key]
        try:
            if isinstance(default, bool):
                out[key] = bool(value)
            elif isinstance(default, int):
                out[key] = int(value)
            elif isinstance(default, float):
                out[key] = float(value)
            else:
                out[key] = str(value)
        except (TypeError, ValueError):
            pass
    if out["version"] not in VERSIONS:
        out["version"] = "steam"
    if out["react"] not in ("instant", "full"):
        out["react"] = "full"
    return out


class WindowInfo:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.left = self.top = 0
        self.width = self.height = 0
        self.update_rect()

    def update_rect(self):
        rect = win32gui.GetWindowRect(self.hwnd)
        self.left, self.top = rect[0], rect[1]
        self.width = rect[2] - rect[0]
        self.height = rect[3] - rect[1]

    @property
    def valid(self):
        return bool(win32gui.IsWindow(self.hwnd))

    @property
    def minimized(self):
        return bool(win32gui.IsIconic(self.hwnd))

    @property
    def visible(self):
        return bool(win32gui.IsWindowVisible(self.hwnd))

    @property
    def usable(self):
        return (self.valid and self.visible and not self.minimized
                and self.width > 10 and self.height > 10)


class GoldenCatcherApp:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.worker = None
        self._tl = threading.local()

        self.settings = load_settings()
        self.current_lang = self.settings["language"]
        if self.current_lang not in LANG:
            self.current_lang = "en"

        self._hotkey_handle = None
        self._ac_hotkey_handle = None
        self._capture_hook = None
        self._capture_target = None
        self.tray_icon = None
        self.template_img = None
        self.cfg = {}
        self._suppress = None
        self._tries = 0
        self._last_w = 0
        self.ac_active = bool(self.settings["autoclick_enabled"])
        self.sound_path = _make_chime(CHIME_FILE)

        self.build_ui()
        self.apply_hotkey()
        self.apply_ac_hotkey()
        self.setup_tray()
        self.load_template()
        self.log(self.tr("ready"))

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def tr(self, key):
        return LANG[self.current_lang].get(key, key)

    # ---------- settings ----------

    def save_settings(self):
        try:
            self.settings.update({
                "language": self.current_lang,
                "version": self._ver_key(),
                "react": self._react_key(),
                "hotkey": self.ent_hotkey.get().strip().lower(),
                "ac_hotkey": self.ent_achotkey.get().strip().lower(),
                "match_threshold": float(self.ent_thresh.get()),
                "click_cooldown": float(self.ent_clickcd.get()),
                "beep_cooldown": float(self.ent_beepcd.get()),
                "beep_enabled": bool(self.var_beep.get()),
                "scan_interval": float(self.ent_scanint.get()),
                "autoclick_enabled": bool(self.var_autoclick.get()),
                "autoclick_cps": float(self.ent_cps.get()),
                "double_click": bool(self.var_dbl.get()),
                "offset_x": int(self.ent_offx.get() or 0),
                "offset_y": int(self.ent_offy.get() or 0),
                "return_delay": float(self.ent_retdelay.get()),
                "settle": float(self.ent_settle.get()),
                "max_clicks": int(self.ent_maxclicks.get() or 3),
                "ac_x": int(self.ent_acx.get() or 0),
                "ac_y": int(self.ent_acy.get() or 0),
                "ignore_x": int(self.ent_igx.get() or 0),
                "ignore_y": int(self.ent_igy.get() or 0),
                "ignore_w": int(self.ent_igw.get() or 0),
                "ignore_h": int(self.ent_igh.get() or 0),
            })
        except (ValueError, tk.TclError, AttributeError):
            pass

        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"Save error: {e}")

    def _ver_key(self):
        return "browser" if self.seg_version.get() == self.tr("ver_browser") else "steam"

    def _react_key(self):
        return "instant" if self.seg_react.get() == self.tr("react_instant") else "full"

    # ---------- sprite ----------

    def _fallback_template(self):
        path = os.path.join(BASE_DIR, "default_template.png")
        if not os.path.exists(path):
            img = np.zeros((64, 64, 3), dtype=np.uint8)
            cv2.circle(img, (32, 32), 28, (0, 200, 245), -1)
            cv2.circle(img, (32, 32), 26, (0, 160, 215), 2)
            for cx, cy, r in ((22, 22, 5), (44, 26, 4), (26, 45, 5), (43, 44, 3)):
                cv2.circle(img, (cx, cy), r, (35, 55, 140), -1)
            cv2.imwrite(path, img)
        return path

    def load_template(self):
        path = _bundled_template() or self._fallback_template()
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is not None and img.size > 0:
            self.template_img = img
            self.log(f"{self.tr('tpl_loaded')} {os.path.basename(path)}")
        else:
            self.template_img = None
            self.log(self.tr("no_template"))

    # ---------- tray ----------

    def setup_tray(self):
        image = Image.new("RGB", (64, 64), color=(24, 26, 30))
        dc = ImageDraw.Draw(image)
        dc.ellipse((6, 6, 58, 58), fill=(240, 180, 41))
        dc.ellipse((6, 6, 58, 58), outline=(120, 82, 15), width=3)
        for cx, cy, r in ((22, 22, 5), (43, 26, 4), (26, 44, 5), (42, 44, 3)):
            dc.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(60, 34, 12))

        menu = pystray.Menu(
            pystray.MenuItem("Open", self.show_window, default=True),
            pystray.MenuItem("Start / Stop", lambda: self.root.after(0, self.toggle)),
            pystray.MenuItem("Exit", self.quit_app),
        )
        self.tray_icon = pystray.Icon("cookie", image, APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def update_tray(self):
        if self.tray_icon:
            try:
                state = "working" if self.running else "idle"
                self.tray_icon.title = f"{APP_NAME} — {state}"
            except Exception:
                pass

    def hide_window(self):
        self.save_settings()
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon=None, item=None):
        self.running = False
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=2)
        for handle in (self._hotkey_handle, self._ac_hotkey_handle):
            if handle is not None:
                try:
                    keyboard.remove_hotkey(handle)
                except Exception:
                    pass
        if self._capture_hook is not None:
            try:
                keyboard.unhook(self._capture_hook)
            except Exception:
                pass
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.root.after(0, self.root.destroy)

    # ---------- capture ----------

    def _sct(self):
        sct = getattr(self._tl, "sct", None)
        if sct is None:
            sct = mss.mss()
            self._tl.sct = sct
        return sct

    def grab_window_frame(self, win):
        raw = self._sct().grab({
            "left": win.left, "top": win.top,
            "width": win.width, "height": win.height,
        })
        return np.ascontiguousarray(np.array(raw)[:, :, :3])

    def find_game_window(self):
        preset = VERSIONS.get(self._ver_key(), VERSIONS["steam"])
        if preset["kind"] == "process":
            return self._find_by_process(preset["value"].lower())
        return self._find_by_title(preset["value"].lower())

    def _find_by_process(self, name):
        def callback(hwnd, found):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    if name in psutil.Process(pid).name().lower():
                        found.append(hwnd)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True

        found = []
        win32gui.EnumWindows(callback, found)
        return WindowInfo(found[0]) if found else None

    def _find_by_title(self, needle):
        def callback(hwnd, found):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if needle in title and "golden cookie catcher" not in title:
                    found.append(hwnd)
            return True

        found = []
        win32gui.EnumWindows(callback, found)
        return WindowInfo(found[0]) if found else None

    # ---------- ui ----------

    def build_ui(self):
        s = self.settings
        geo = self.root.geometry()
        if geo.startswith("1x1"):
            geo = "640x740"
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title(f"{self.tr('title')} {APP_VERSION}")
        self.root.geometry(geo)
        self.root.minsize(580, 620)
        self.root.configure(fg_color="#121316")

        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 4))

        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text=self.tr("title"), font=("Segoe UI Semibold", 19),
                     text_color=C_TEXT).pack(anchor="w")
        ctk.CTkLabel(titles, text=self.tr("subtitle"), font=("Segoe UI", 11),
                     text_color=C_MUTED).pack(anchor="w")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")
        ctk.CTkComboBox(right, values=list(LANG_LABELS), width=104,
                        variable=ctk.StringVar(value=LABEL_FOR[self.current_lang]),
                        command=self.change_language).pack(side="left", padx=(0, 10))

        self.pill = ctk.CTkFrame(right, fg_color=C_CARD_HI, corner_radius=14)
        self.pill.pack(side="left")
        self.lbl_status = ctk.CTkLabel(self.pill, text=self.tr("status_stopped"),
                                       font=("Segoe UI Semibold", 10), text_color=C_MUTED)
        self.lbl_status.pack(padx=12, pady=5)

        self.tabs = ctk.CTkTabview(self.root, fg_color="transparent",
                                   segmented_button_selected_color=C_ACCENT,
                                   segmented_button_selected_hover_color="#d9a121",
                                   segmented_button_fg_color=C_CARD,
                                   segmented_button_unselected_hover_color=C_CARD_HI)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        for name in ("tab_main", "tab_timing", "tab_adv", "tab_log"):
            self.tabs.add(self.tr(name))

        self._build_main(self.tabs.tab(self.tr("tab_main")))
        self._build_timing(self.tabs.tab(self.tr("tab_timing")))
        self._build_adv(self.tabs.tab(self.tr("tab_adv")))

        log_tab = self.tabs.tab(self.tr("tab_log"))
        self.txt_log = ctk.CTkTextbox(log_tab, fg_color=C_CARD, corner_radius=10,
                                      font=("Consolas", 11), text_color=C_MUTED)
        self.txt_log.pack(fill="both", expand=True, padx=4, pady=4)
        self.txt_log.configure(state="disabled")

        actions = ctk.CTkFrame(self.root, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=14)
        self.btn_start = ctk.CTkButton(actions, text=self.tr("start"), command=self.start,
                                       fg_color=C_GREEN, hover_color="#17803c",
                                       height=44, corner_radius=10,
                                       font=("Segoe UI Semibold", 14))
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.btn_stop = ctk.CTkButton(actions, text=self.tr("stop"), command=self.stop,
                                      state="disabled", fg_color=C_RED,
                                      hover_color="#9e2f2f", height=44, corner_radius=10,
                                      font=("Segoe UI Semibold", 14))
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.set_status()

    def _card(self, parent, title=None):
        frame = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=12)
        frame.pack(fill="x", padx=4, pady=6)
        if title:
            ctk.CTkLabel(frame, text=title, font=("Segoe UI Semibold", 12),
                         text_color=C_MUTED).pack(anchor="w", padx=14, pady=(10, 2))
        return frame

    def _hint(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 10), text_color=C_MUTED,
                     wraplength=520, justify="left").pack(anchor="w", padx=14, pady=(2, 8))

    def _row(self, parent, label, widget_factory):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=5)
        ctk.CTkLabel(row, text=label, font=("Segoe UI", 12),
                     text_color=C_TEXT).pack(side="left")
        return widget_factory(row)

    def _num(self, parent, label, value, width=70):
        def factory(row):
            e = ctk.CTkEntry(row, width=width, fg_color=C_CARD_HI, border_width=0,
                             corner_radius=8, justify="center")
            e.insert(0, str(value))
            e.pack(side="right")
            return e
        return self._row(parent, label, factory)

    def _build_main(self, tab):
        s = self.settings

        ver = self._card(tab, self.tr("version_frame"))
        self.seg_version = ctk.CTkSegmentedButton(
            ver, values=[self.tr("ver_steam"), self.tr("ver_browser")],
            selected_color=C_ACCENT, selected_hover_color="#d9a121",
            unselected_color=C_CARD_HI, unselected_hover_color="#2d3138",
            text_color="#1a1a1a", font=("Segoe UI Semibold", 12))
        self.seg_version.set(self.tr("ver_steam") if s["version"] == "steam"
                             else self.tr("ver_browser"))
        self.seg_version.pack(fill="x", padx=14, pady=(0, 8))
        self._hint(ver, self.tr("ver_hint"))

        react = self._card(tab, self.tr("react_frame"))
        self.seg_react = ctk.CTkSegmentedButton(
            react, values=[self.tr("react_instant"), self.tr("react_full")],
            selected_color=C_ACCENT, selected_hover_color="#d9a121",
            unselected_color=C_CARD_HI, unselected_hover_color="#2d3138",
            text_color="#1a1a1a", font=("Segoe UI Semibold", 12))
        self.seg_react.set(self.tr("react_instant") if s["react"] == "instant"
                           else self.tr("react_full"))
        self.seg_react.pack(fill="x", padx=14, pady=(0, 8))
        self._hint(react, self.tr("react_hint"))

        hk_card = self._card(tab, self.tr("hotkey"))
        row = ctk.CTkFrame(hk_card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 12))
        self.ent_hotkey = ctk.CTkEntry(row, width=90, fg_color=C_CARD_HI, border_width=0,
                                       corner_radius=8, justify="center")
        self.ent_hotkey.insert(0, s["hotkey"])
        self.ent_hotkey.pack(side="left")
        ctk.CTkButton(row, text=self.tr("record"), command=lambda: self.capture_hotkey("main"),
                      width=100, fg_color=C_CARD_HI, hover_color="#2d3138",
                      corner_radius=8).pack(side="left", padx=8)
        ctk.CTkButton(row, text=self.tr("apply"), command=self.apply_hotkey, width=100,
                      fg_color=C_ACCENT, hover_color="#d9a121", text_color="#1a1a1a",
                      corner_radius=8).pack(side="left")

    def _build_timing(self, tab):
        s = self.settings
        card = self._card(tab, self.tr("detect"))
        self.ent_thresh = self._num(card, self.tr("thresh_lbl"), s["match_threshold"])
        self.ent_clickcd = self._num(card, self.tr("click_cd"), s["click_cooldown"])
        self.ent_scanint = self._num(card, self.tr("scan_int"), s["scan_interval"])
        ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

        snd = self._card(tab, self.tr("sound_frame"))
        self.var_beep = ctk.BooleanVar(value=s["beep_enabled"])
        ctk.CTkCheckBox(snd, text=self.tr("beep_en"), variable=self.var_beep,
                        font=("Segoe UI", 12), text_color=C_TEXT,
                        fg_color=C_ACCENT, hover_color=C_ACCENT,
                        checkmark_color="#1a1a1a").pack(anchor="w", padx=14, pady=(0, 6))
        self.ent_beepcd = self._num(snd, self.tr("beep_cd"), s["beep_cooldown"])
        ctk.CTkFrame(snd, fg_color="transparent", height=6).pack()

    def _build_adv(self, tab):
        s = self.settings

        ac_card = self._card(tab, self.tr("auto_frame"))
        self.var_autoclick = ctk.BooleanVar(value=self.ac_active)
        ctk.CTkCheckBox(ac_card, text=self.tr("auto_en"), variable=self.var_autoclick,
                        command=self._on_ac_toggle, font=("Segoe UI", 12),
                        text_color=C_TEXT, fg_color=C_ACCENT, hover_color=C_ACCENT,
                        checkmark_color="#1a1a1a").pack(anchor="w", padx=14, pady=(0, 6))
        self._hint(ac_card, self.tr("ac_hint"))

        hk = ctk.CTkFrame(ac_card, fg_color="transparent")
        hk.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(hk, text=self.tr("ac_hotkey"), font=("Segoe UI", 12),
                     text_color=C_TEXT).pack(side="left")
        self.ent_achotkey = ctk.CTkEntry(hk, width=80, fg_color=C_CARD_HI, border_width=0,
                                         corner_radius=8, justify="center")
        self.ent_achotkey.insert(0, s["ac_hotkey"])
        self.ent_achotkey.pack(side="left", padx=8)
        ctk.CTkButton(hk, text=self.tr("record"), command=lambda: self.capture_hotkey("ac"),
                      width=90, fg_color=C_CARD_HI, hover_color="#2d3138",
                      corner_radius=8).pack(side="left", padx=(0, 6))
        ctk.CTkButton(hk, text=self.tr("apply"), command=self.apply_ac_hotkey, width=90,
                      fg_color=C_ACCENT, hover_color="#d9a121", text_color="#1a1a1a",
                      corner_radius=8).pack(side="left")

        pt = ctk.CTkFrame(ac_card, fg_color="transparent")
        pt.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(pt, text="X", font=("Segoe UI", 12),
                     text_color=C_MUTED).pack(side="left")
        self.ent_acx = ctk.CTkEntry(pt, width=64, fg_color=C_CARD_HI, border_width=0,
                                    corner_radius=8, justify="center")
        self.ent_acx.insert(0, str(s["ac_x"]))
        self.ent_acx.pack(side="left", padx=(6, 12))
        ctk.CTkLabel(pt, text="Y", font=("Segoe UI", 12),
                     text_color=C_MUTED).pack(side="left")
        self.ent_acy = ctk.CTkEntry(pt, width=64, fg_color=C_CARD_HI, border_width=0,
                                    corner_radius=8, justify="center")
        self.ent_acy.insert(0, str(s["ac_y"]))
        self.ent_acy.pack(side="left", padx=(6, 12))
        ctk.CTkButton(pt, text=self.tr("grab_pt"), command=self.grab_point, width=120,
                      fg_color=C_CARD_HI, hover_color="#2d3138",
                      corner_radius=8).pack(side="left")

        off = ctk.CTkFrame(ac_card, fg_color="transparent")
        off.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(off, text=self.tr("offset"), font=("Segoe UI", 12),
                     text_color=C_TEXT).pack(side="left")
        self.ent_offx = ctk.CTkEntry(off, width=56, fg_color=C_CARD_HI, border_width=0,
                                     corner_radius=8, justify="center")
        self.ent_offx.insert(0, str(s["offset_x"]))
        self.ent_offx.pack(side="left", padx=(8, 6))
        self.ent_offy = ctk.CTkEntry(off, width=56, fg_color=C_CARD_HI, border_width=0,
                                     corner_radius=8, justify="center")
        self.ent_offy.insert(0, str(s["offset_y"]))
        self.ent_offy.pack(side="left")

        self.ent_cps = self._num(ac_card, self.tr("cps"), s["autoclick_cps"])
        self.var_dbl = ctk.BooleanVar(value=s["double_click"])
        dbl_row = ctk.CTkFrame(ac_card, fg_color="transparent")
        dbl_row.pack(fill="x", padx=14, pady=5)
        ctk.CTkCheckBox(dbl_row, text=self.tr("dbl"), variable=self.var_dbl,
                        font=("Segoe UI", 12), text_color=C_TEXT,
                        fg_color=C_ACCENT, hover_color=C_ACCENT,
                        checkmark_color="#1a1a1a").pack(side="left")
        self.ent_retdelay = self._num(ac_card, self.tr("ret_delay"), s["return_delay"])
        self.ent_settle = self._num(ac_card, self.tr("settle"), s["settle"])
        self.ent_maxclicks = self._num(ac_card, self.tr("max_clicks"), s["max_clicks"])
        ctk.CTkFrame(ac_card, fg_color="transparent", height=6).pack()

        zone = self._card(tab, self.tr("zone_frame"))
        zr = ctk.CTkFrame(zone, fg_color="transparent")
        zr.pack(fill="x", padx=14, pady=(0, 10))
        self.ent_igx = ctk.CTkEntry(zr, width=56, fg_color=C_CARD_HI, border_width=0,
                                    corner_radius=8, justify="center")
        self.ent_igy = ctk.CTkEntry(zr, width=56, fg_color=C_CARD_HI, border_width=0,
                                    corner_radius=8, justify="center")
        self.ent_igw = ctk.CTkEntry(zr, width=56, fg_color=C_CARD_HI, border_width=0,
                                    corner_radius=8, justify="center")
        self.ent_igh = ctk.CTkEntry(zr, width=56, fg_color=C_CARD_HI, border_width=0,
                                    corner_radius=8, justify="center")
        for ent, val in ((self.ent_igx, s["ignore_x"]), (self.ent_igy, s["ignore_y"]),
                         (self.ent_igw, s["ignore_w"]), (self.ent_igh, s["ignore_h"])):
            ent.insert(0, str(val))
            ent.pack(side="left", padx=(0, 6))
        ctk.CTkButton(zr, text=self.tr("select_zone"), command=self.select_ignore_zone,
                      width=110, fg_color=C_CARD_HI, hover_color="#2d3138",
                      corner_radius=8).pack(side="left", padx=(6, 0))

        tools = self._card(tab)
        ctk.CTkButton(tools, text=self.tr("test_mask"), command=self.test_mask, width=200,
                      fg_color=C_ACCENT, hover_color="#d9a121", text_color="#1a1a1a",
                      corner_radius=8).pack(anchor="w", padx=14, pady=(10, 6))
        ctk.CTkButton(tools, text=self.tr("open_folder"), command=self.open_folder,
                      width=200, fg_color=C_CARD_HI, hover_color="#2d3138",
                      corner_radius=8).pack(anchor="w", padx=14, pady=(0, 12))

    def open_folder(self):
        try:
            os.startfile(BASE_DIR)
        except Exception as e:
            self.log(str(e))

    def change_language(self, choice=None):
        if self.running:
            self.stop()
        self.current_lang = LANG_LABELS.get(choice, self.current_lang)
        self.save_settings()
        self.build_ui()

    def log(self, msg):
        if not hasattr(self, "txt_log"):
            return
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def set_status(self, color=C_MUTED):
        if not hasattr(self, "lbl_status"):
            return
        text = self.tr("status_running") if self.running else self.tr("status_stopped")
        self.lbl_status.configure(text=text, text_color=color)
        self.update_tray()

    def _ui_stopped(self):
        if hasattr(self, "btn_start"):
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
        self.set_status()

    def _on_ac_toggle(self):
        self.ac_active = bool(self.var_autoclick.get())

    # ---------- helpers ----------

    def grab_point(self):
        self.log("3...")
        self.root.after(3000, self._grab_point_now)

    def _grab_point_now(self):
        x, y = pyautogui.position()
        self.ent_acx.delete(0, "end")
        self.ent_acx.insert(0, str(x))
        self.ent_acy.delete(0, "end")
        self.ent_acy.insert(0, str(y))
        self.log(f"{self.tr('point_set')} ({x}, {y})")

    def _show_zone_selector(self, title, callback):
        win = self.find_game_window()
        if not win:
            messagebox.showerror(self.tr("err"), self.tr("win_not_found"))
            return
        try:
            win.update_rect()
            if win.width < 20 or win.height < 20:
                raise RuntimeError(self.tr("win_min"))
            frame = self.grab_window_frame(win)
        except Exception as e:
            messagebox.showerror(self.tr("err"), str(e))
            return

        shot = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        top = ctk.CTkToplevel(self.root)
        top.title(title)
        top.attributes("-topmost", True)

        w, h = shot.size
        scale = min(1.0, 1000 / w, 800 / h)
        if scale < 1.0:
            shot = shot.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

        canvas = tk.Canvas(top, width=shot.width, height=shot.height,
                           bg="#2b2b2b", highlightthickness=0)
        canvas.pack()
        photo = ctk.CTkImage(light_image=shot, dark_image=shot, size=(shot.width, shot.height))
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo

        state = {"rect": None, "sx": 0, "sy": 0}

        def on_press(event):
            state["sx"], state["sy"] = event.x, event.y
            if state["rect"]:
                canvas.delete(state["rect"])
            state["rect"] = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                    outline=C_ACCENT, width=2)

        def on_drag(event):
            if state["rect"]:
                canvas.coords(state["rect"], state["sx"], state["sy"], event.x, event.y)

        def on_release(event):
            rx = int(min(state["sx"], event.x) / scale)
            ry = int(min(state["sy"], event.y) / scale)
            rw = int(abs(event.x - state["sx"]) / scale)
            rh = int(abs(event.y - state["sy"]) / scale)
            top.destroy()
            if rw > 5 and rh > 5:
                callback(rx, ry, rw, rh, frame)

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

    def select_ignore_zone(self):
        def done(x, y, w, h, frame):
            for ent, val in ((self.ent_igx, x), (self.ent_igy, y),
                             (self.ent_igw, w), (self.ent_igh, h)):
                ent.delete(0, "end")
                ent.insert(0, str(val))
            self.log(f"{self.tr('zone_set')} {x}, {y}, {w}, {h}")

        self._show_zone_selector(self.tr("zone_title"), done)

    # ---------- matching ----------

    def find_matches(self, frame, template, threshold, ignore):
        if template is None or frame is None:
            return []
        if template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        small = cv2.resize(gray, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
        tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        tpl_gray = cv2.GaussianBlur(tpl_gray, (3, 3), 0)

        cands = []
        for s in SCALES:
            t = cv2.resize(tpl_gray, None, fx=SCALE * s, fy=SCALE * s,
                           interpolation=cv2.INTER_AREA)
            if t.shape[0] >= small.shape[0] or t.shape[1] >= small.shape[1]:
                continue
            res = cv2.matchTemplate(small, t, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(res >= threshold)
            for yy, xx in zip(ys, xs):
                tw = int(t.shape[1] / SCALE)
                th = int(t.shape[0] / SCALE)
                cands.append((int(xx / SCALE + tw / 2), int(yy / SCALE + th / 2),
                              tw, th, float(res[yy, xx])))

        if not cands:
            return []

        ig_x, ig_y, ig_w, ig_h = ignore
        have_zone = ig_w > 0 and ig_h > 0

        cands.sort(key=lambda c: -c[4])
        picked = []
        for cx, cy, tw, th, score in cands:
            limit = max(tw, th) * NMS_RATIO
            if any(abs(cx - px) < limit and abs(cy - py) < limit
                   for px, py, _, _, _ in picked):
                continue
            if have_zone and ig_x <= cx <= ig_x + ig_w and ig_y <= cy <= ig_y + ig_h:
                continue
            picked.append((cx, cy, tw, th, score))
            if len(picked) >= 8:
                break
        return picked

    def read_ignore(self):
        def num(widget):
            try:
                return int(widget.get() or 0)
            except ValueError:
                return 0
        return (num(self.ent_igx), num(self.ent_igy),
                num(self.ent_igw), num(self.ent_igh))

    def test_mask(self):
        win = self.find_game_window()
        if not win:
            messagebox.showerror(self.tr("err"), self.tr("win_not_found"))
            return
        if self.template_img is None:
            messagebox.showerror(self.tr("err"), self.tr("no_template"))
            return
        try:
            win.update_rect()
            frame = self.grab_window_frame(win)
            thresh = float(self.ent_thresh.get())
        except Exception as e:
            messagebox.showerror(self.tr("err"), str(e))
            return

        ig = self.read_ignore()
        matches = self.find_matches(frame, self.template_img, thresh, ig)

        vis = frame.copy()
        if ig[2] > 0 and ig[3] > 0:
            cv2.rectangle(vis, (ig[0], ig[1]), (ig[0] + ig[2], ig[1] + ig[3]),
                          (60, 60, 220), 2)
        for cx, cy, tw, th, score in matches:
            cv2.rectangle(vis, (cx - tw // 2, cy - th // 2), (cx + tw // 2, cy + th // 2),
                          (60, 200, 90), 2)
            cv2.putText(vis, f"{score:.2f}", (cx - tw // 2, max(12, cy - th // 2 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 200, 90), 1)

        top = ctk.CTkToplevel(self.root)
        top.title(f"{self.tr('found_n')} {len(matches)}")
        top.attributes("-topmost", True)
        h, w = vis.shape[:2]
        sc = min(1.0, 900 / w, 600 / h)
        small = cv2.resize(vis, (max(1, int(w * sc)), max(1, int(h * sc))))
        img = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        ppm = f"P6 {img.shape[1]} {img.shape[0]} 255 ".encode() + img.tobytes()
        photo = tk.PhotoImage(data=ppm, format="PPM")
        lbl = tk.Label(top, image=photo, bg="#2b2b2b", borderwidth=0)
        lbl.image = photo
        lbl.pack()

    # ---------- hotkey ----------

    def capture_hotkey(self, target="main"):
        if self._capture_hook is not None:
            try:
                keyboard.unhook(self._capture_hook)
            except Exception:
                pass
            self._capture_hook = None
        self._capture_target = target
        self.log(self.tr("capture_hint"))

        def on_key(event):
            if event.event_type != keyboard.KEY_DOWN:
                return
            try:
                keyboard.unhook(self._capture_hook)
            except Exception:
                pass
            self._capture_hook = None
            self.root.after(0, self._set_hotkey_field, event.name, target)

        self._capture_hook = keyboard.hook(on_key, suppress=False)

    def _set_hotkey_field(self, name, target):
        widget = self.ent_achotkey if target == "ac" else self.ent_hotkey
        widget.delete(0, "end")
        widget.insert(0, name)
        self.log(f"{self.tr('key_set')} {name}")
        if target == "ac":
            self.apply_ac_hotkey()
        else:
            self.apply_hotkey()

    def apply_hotkey(self):
        name = self.ent_hotkey.get().strip().lower()
        if not name:
            return
        if self._hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self._hotkey_handle)
            except Exception:
                pass
            self._hotkey_handle = None
        try:
            self._hotkey_handle = keyboard.add_hotkey(name, lambda: self.root.after(0, self.toggle))
            self.settings["hotkey"] = name
        except Exception as e:
            self.log(f"Hotkey error: {e}")

    def apply_ac_hotkey(self):
        name = self.ent_achotkey.get().strip().lower()
        if not name:
            return
        if self._ac_hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self._ac_hotkey_handle)
            except Exception:
                pass
            self._ac_hotkey_handle = None
        try:
            self._ac_hotkey_handle = keyboard.add_hotkey(
                name, lambda: self.root.after(0, self.toggle_autoclick))
            self.settings["ac_hotkey"] = name
        except Exception as e:
            self.log(f"Hotkey error: {e}")

    def toggle_autoclick(self):
        new = not self.ac_active
        self.ac_active = new
        self.var_autoclick.set(new)
        self.log(self.tr("ac_on") if new else self.tr("ac_off"))

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    # ---------- run ----------

    def _read_cfg(self):
        cfg = {
            "threshold": float(self.ent_thresh.get()),
            "click_cd": max(0.0, float(self.ent_clickcd.get())),
            "beep_cd": max(0.0, float(self.ent_beepcd.get())),
            "interval": max(0.02, float(self.ent_scanint.get())),
            "cps": min(60.0, max(1.0, float(self.ent_cps.get() or 20))),
            "double": bool(self.var_dbl.get()),
            "return_delay": max(0.0, float(self.ent_retdelay.get())),
            "settle": max(0.0, float(self.ent_settle.get())),
            "max_clicks": max(1, int(self.ent_maxclicks.get() or 3)),
            "beep_on": bool(self.var_beep.get()),
            "ac_x": int(self.ent_acx.get() or 0),
            "ac_y": int(self.ent_acy.get() or 0),
            "off_x": int(self.ent_offx.get() or 0),
            "off_y": int(self.ent_offy.get() or 0),
            "ignore": self.read_ignore(),
            "react": self._react_key(),
        }
        if not 0.05 <= cfg["threshold"] <= 1.0:
            raise ValueError("threshold 0.05 - 1.0")
        return cfg

    def start(self):
        if self.running:
            return
        if self.template_img is None:
            messagebox.showerror(self.tr("err"), self.tr("no_template"))
            return
        try:
            self.cfg = self._read_cfg()
        except ValueError as e:
            messagebox.showerror(self.tr("err"), f"{self.tr('bad_value')} {e}")
            return

        self.save_settings()
        self._suppress = None
        self._tries = 0
        self._last_w = 0
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.set_status(C_GREEN)
        self.log(self.tr("started"))

        if self.cfg["ac_x"] <= 0 or self.cfg["ac_y"] <= 0:
            self.log(self.tr("no_point"))

        if self.tray_icon:
            try:
                self.tray_icon.notify(self.tr("started"), APP_NAME)
            except Exception:
                pass

        self.worker = threading.Thread(target=self.loop, daemon=True)
        self.worker.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=2)
        self._ui_stopped()
        self.log(self.tr("stopped"))

    def loop(self):
        try:
            self._loop_body()
        except Exception as e:
            self.log(f"{self.tr('loop_crash')} {e}")
        finally:
            self.running = False
            self.root.after(0, self._ui_stopped)

    def _beep(self):
        try:
            if self.sound_path and os.path.exists(self.sound_path):
                winsound.PlaySound(
                    self.sound_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            else:
                winsound.PlaySound("SystemAsterisk",
                                   winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass

    def _suppressed(self, match, now):
        if not self._suppress:
            return False
        sx, sy, until, radius = self._suppress
        if now > until:
            self._suppress = None
            return False
        return abs(match[0] - sx) < radius and abs(match[1] - sy) < radius

    def _press(self, x, y, dbl):
        pyautogui.moveTo(x, y)
        pyautogui.click()
        if dbl:
            time.sleep(0.02)
            pyautogui.click()

    def _click_golden(self, win, target):
        sx = int(win.left + target[0])
        sy = int(win.top + target[1])
        try:
            pyautogui.moveTo(sx, sy)
            time.sleep(self.cfg["settle"])
            self._press(sx, sy, self.cfg["double"])
        except Exception:
            pass
        return sx, sy

    def _loop_body(self):
        cfg = self.cfg
        ignore = cfg["ignore"]
        template = self.template_img
        win = None
        last_click = 0.0
        last_beep = 0.0
        last_ac = 0.0
        last_pos = (-9999, -9999)
        ac_delay = 1.0 / cfg["cps"]

        while self.running:
            if win is None or not win.valid:
                win = self.find_game_window()
                if win is None:
                    time.sleep(1)
                    continue

            if not win.usable:
                time.sleep(0.4)
                continue

            try:
                win.update_rect()
                frame = self.grab_window_frame(win)
            except Exception:
                win = None
                time.sleep(0.5)
                continue

            now = time.time()
            matches = self.find_matches(frame, template, cfg["threshold"], ignore)
            fresh = [m for m in matches if not self._suppressed(m, now)]
            clicked = False
            sleep_for = cfg["interval"]

            if fresh and now - last_click > cfg["click_cd"]:
                target = fresh[0]

                if cfg["react"] == "full" and target[2] > self._last_w + 1:
                    self._last_w = target[2]
                    time.sleep(cfg["interval"])
                    continue
                self._last_w = target[2]

                same = abs(target[0] - last_pos[0]) <= 12 and abs(target[1] - last_pos[1]) <= 12
                self._tries = self._tries + 1 if same else 1

                if self._tries <= cfg["max_clicks"]:
                    sx, sy = self._click_golden(win, target)
                    clicked = True
                    last_click = now
                    last_pos = (target[0], target[1])
                    self._suppress = (target[0], target[1],
                                      now + max(0.25, cfg["click_cd"]),
                                      max(30, target[2] * 0.6))
                    self.log(f"click {sx},{sy} try {self._tries}")
                    if cfg["beep_on"] and now - last_beep > cfg["beep_cd"]:
                        self._beep()
                        last_beep = now
                else:
                    self._suppress = (target[0], target[1], now + 8.0, max(30, target[2]))
                    self._tries = 0
                    self.log(self.tr("give_up"))
            else:
                self._last_w = 0

            if self.ac_active and cfg["ac_x"] > 0 and cfg["ac_y"] > 0:
                px = cfg["ac_x"] + cfg["off_x"]
                py = cfg["ac_y"] + cfg["off_y"]
                if clicked:
                    time.sleep(cfg["return_delay"])
                try:
                    if not clicked and now - last_ac >= ac_delay:
                        self._press(px, py, cfg["double"])
                        last_ac = now
                    else:
                        pyautogui.moveTo(px, py)
                except Exception:
                    pass
                sleep_for = min(sleep_for, max(0.005, ac_delay - (time.time() - last_ac)))

            time.sleep(sleep_for)


def _single_instance():
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return handle, ctypes.windll.kernel32.GetLastError() != 183


def _run():
    handle, first = _single_instance()
    if not first:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(APP_NAME, LANG["ru"]["only_one"])
        root.destroy()
        return

    root = ctk.CTk()
    app = GoldenCatcherApp(root)
    root.mainloop()
    try:
        ctypes.windll.kernel32.ReleaseMutex(handle)
    except Exception:
        pass


def main():
    try:
        _run()
    except Exception:
        import traceback
        with open(CRASH_FILE, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        messagebox.showerror(APP_NAME, f"crash.log:\n{BASE_DIR}")
        raise


if __name__ == "__main__":
    main()