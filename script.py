#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import uuid
import json
import subprocess
import threading
import time
import random
import requests
import webbrowser
import logging
from datetime import datetime, timedelta

import keyboard            # pip install keyboard
import pyautogui           # pip install pyautogui
import pyperclip           # pip install pyperclip
from tkinter import *
from tkinter import simpledialog, filedialog, messagebox

# ====== Настройки ======
VERSION          = "1.2.0"
VERSION_URL      = "https://raw.githubusercontent.com/KWISH12/PyQZone/main/version.txt"
SCRIPT_URL       = "https://raw.githubusercontent.com/KWISH12/PyQZone/main/script.py"
HWID_STORE_FILE  = "hwid_store.json"
CONFIG_FILE      = "config.json"
LOG_FILE         = "auto_text.log"
FUNPAY_URL       = "https://funpay.com/users/6551539/"
TELEGRAM_URL     = "https://t.me/PyQZone"
REVIEWS_URL      = "https://t.me/+kosYl4xb3EFkZWRi"

TYPO_RATE        = 0.03
ERROR_RATE       = 0.1
ERROR_CHARS      = list("абвгдеёжз")

# ====== Логирование ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# ====== Управление HWID-кодами ======
def load_hwid_store():
    if os.path.exists(HWID_STORE_FILE):
        try:
            return json.load(open(HWID_STORE_FILE, encoding="utf-8"))
        except:
            logging.warning("Не удалось прочитать hwid_store.json")
    return {"codes": {}}

def save_hwid_store(store):
    with open(HWID_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

def parse_expiry(text):
    text = text.strip()
    if text.endswith("d"):
        days = int(text[:-1])
        return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    if text.endswith("m"):
        months = int(text[:-1])
        now = datetime.now()
        month = now.month - 1 + months
        year = now.year + month // 12
        month = month % 12 + 1
        day = min(now.day, [31,29 if year%4==0 and year%100!=0 or year%400==0 else 28,31,30,31,30,31,31,30,31,30,31][month-1])
        return f"{year:04d}-{month:02d}-{day:02d}"
    # assume YYYY-MM-DD
    datetime.strptime(text, "%Y-%m-%d")
    return text

def add_hwid_code():
    """CLI: добавить новый HWID-код, срок и число запусков."""
    store = load_hwid_store()
    code = input("Новый код (любой текст): ").strip()
    if not code:
        print("Код не может быть пустым.")
        return
    exp = input("Срок годности (YYYY-MM-DD или '30d' или '1m'): ").strip()
    try:
        exp_date = parse_expiry(exp)
    except Exception as e:
        print("Неверный формат даты.", e)
        return
    uses = input("Число запусков [1]: ").strip() or "1"
    try:
        uses = int(uses)
    except:
        print("Запускаем раз.")
        uses = 1
    store["codes"][code] = {"expires": exp_date, "uses_left": uses}
    save_hwid_store(store)
    print(f"Добавлен код «{code}», действует до {exp_date}, запусков: {uses}")

def validate_hwid_interactive():
    """UI: запросить у пользователя код и проверить его."""
    store = load_hwid_store()
    code = simpledialog.askstring("Авторизация", "Введите ваш HWID-код:")
    if not code:
        messagebox.showerror("Ошибка", "Код не введён.")
        sys.exit(1)
    info = store["codes"].get(code.strip())
    if not info:
        messagebox.showerror("Ошибка", "Неверный код.")
        sys.exit(1)
    # проверка срока
    if datetime.now().strftime("%Y-%m-%d") > info["expires"]:
        messagebox.showerror("Ошибка", "Срок действия кода истёк.")
        sys.exit(1)
    # проверка числа запусков
    if info["uses_left"] < 1:
        messagebox.showerror("Ошибка", "Код исчерпал число запусков.")
        sys.exit(1)
    # уменьшаем и сохраняем
    info["uses_left"] -= 1
    save_hwid_store(store)

# ====== Конфиг-функции ======
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            return json.load(open(CONFIG_FILE, encoding="utf-8"))
        except:
            logging.warning("Не удалось загрузить config.json")
    return {}

def save_config(cfg):
    try:
        json.dump(cfg, open(CONFIG_FILE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        logging.info("Настройки сохранены")
    except:
        logging.exception("Ошибка сохранения config.json")

# ====== Обновление ======
def fetch_remote_version():
    try:
        r = requests.get(VERSION_URL, timeout=5)
        if r.ok:
            return r.text.strip()
    except:
        pass
    return VERSION

def version_gt(a, b):
    A = [int(x) for x in a.split(".")]
    B = [int(x) for x in b.split(".")]
    return B > A

def ask_update():
    remote = fetch_remote_version()
    if version_gt(VERSION, remote):
        if messagebox.askyesno("Обновление доступно",
                               f"Найдена версия {remote}\n(у вас {VERSION}). Обновить?"):
            do_update()

def do_update():
    try:
        r = requests.get(SCRIPT_URL, timeout=10)
        r.raise_for_status()
        tmp = __file__ + ".tmp"
        open(tmp, "w", encoding="utf-8").write(r.text)
        os.replace(tmp, __file__)
        messagebox.showinfo("Обновлено", "Программа обновлена, перезапуск...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logging.exception("Ошибка обновления")
        messagebox.showerror("Ошибка обновления", str(e))

# ====== Опечатки и авто-буквы ======
def add_typos(s):
    out = ""
    for ch in s:
        if random.random() < TYPO_RATE:
            out += random.choice("asdfghjklqwertyuiop")
        out += ch
    return out

def insert_error_char(s):
    if not s or random.random() >= ERROR_RATE:
        return s
    pos = random.randrange(len(s))
    return s[:pos] + random.choice(ERROR_CHARS) + s[pos:]

# ====== Ввод и отправка строки ======
def type_line(line):
    try:
        keyboard.write(line)
    except:
        pyperclip.copy(line)
        pyautogui.hotkey("ctrl", "v")
    keyboard.send("enter")

def auto_type(text, delay, count, typos, errors, start_delay, status_label):
    status_label.master.iconify()
    status_label.config(text=f"Старт через {start_delay:.1f} сек…")
    time.sleep(start_delay)
    status_label.config(text="Печать…")

    lines = [l for l in text.splitlines() if l.strip()]
    for i in range(count):
        ln = lines[i % len(lines)]
        if typos:
            ln = add_typos(ln)
        if errors:
            ln = insert_error_char(ln)
        type_line(ln)
        status_label.config(text=f"Отправлено {i+1}/{count}")
        time.sleep(delay)

    status_label.master.deiconify()
    status_label.config(text="Готово")

# ====== Основное GUI ======
class AutoTextApp:
    def __init__(self, root):
        self.root = root
        self.cfg  = load_config()
        self.build_ui()
        self.load_settings()
        self.schedule_startup()

    def build_ui(self):
        self.root.title("🔥 AutoText — PyQZone")
        self.root.geometry("520x680")
        self.root.configure(bg="#1a0000")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        menubar = Menu(self.root)
        fm = Menu(menubar, tearoff=0)
        fm.add_command(label="Добавить код (--add-hwid)", command=lambda: None)
        fm.add_command(label="Проверить обновление", command=ask_update)
        fm.add_separator()
        fm.add_command(label="Выход", command=self.on_close)
        menubar.add_cascade(label="Файл", menu=fm)

        hm = Menu(menubar, tearoff=0)
        hm.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=hm)
        self.root.config(menu=menubar)

        lf = Frame(self.root, bg="#1a0000"); lf.pack(pady=10)
        for txt, url in [("🌐 FunPay", FUNPAY_URL),
                         ("💬 Telegram", TELEGRAM_URL),
                         ("⭐️ Отзывы", REVIEWS_URL)]:
            Button(lf, text=txt, bg="darkred", fg="white",
                   command=lambda u=url: webbrowser.open_new_tab(u)
            ).pack(side=LEFT, padx=5)

        self.hwid_lbl = Label(self.root, text="Authorized", bg="#1a0000", fg="white")
        self.hwid_lbl.pack(pady=(0,10))

        Label(self.root, text="Текст для автопечати:", bg="#1a0000", fg="white").pack()
        self.text_area = Text(self.root, bg="#300000", fg="white", width=64, height=8)
        self.text_area.pack(pady=5)

        params = Frame(self.root, bg="#1a0000"); params.pack(pady=5)
        Label(params, text="Интервал:", bg="#1a0000", fg="white")\
            .grid(row=0, column=0, padx=5)
        self.interval_e = Entry(params, width=6, bg="#300000", fg="white")
        self.interval_e.grid(row=0, column=1)
        Label(params, text="Строк:", bg="#1a0000", fg="white")\
            .grid(row=0, column=2, padx=5)
        self.count_e = Entry(params, width=6, bg="#300000", fg="white")
        self.count_e.grid(row=0, column=3)
        Label(params, text="Задержка старта:", bg="#1a0000", fg="white")\
            .grid(row=1, column=0, pady=5, padx=5)
        self.start_e = Entry(params, width=6, bg="#300000", fg="white")
        self.start_e.grid(row=1, column=1)
        Label(params, text="Хоткей:", bg="#1a0000", fg="white")\
            .grid(row=1, column=2, padx=5)
        self.hk_e = Entry(params, width=8, bg="#300000", fg="white")
        self.hk_e.grid(row=1, column=3)

        self.typo_var = BooleanVar()
        Checkbutton(self.root, text="Добавлять опечатки",
                    variable=self.typo_var, bg="#1a0000", fg="white").pack(pady=5)
        self.err_var = BooleanVar()
        Checkbutton(self.root, text="Авто-ошибки (русск.)",
                    variable=self.err_var, bg="#1a0000", fg="white").pack(pady=5)

        Button(self.root, text="📂 Открыть .txt", bg="darkred", fg="white",
               command=self.load_file).pack(pady=5)
        Button(self.root, text="🚀 Старт (F8)", bg="red", fg="white",
               command=self.start_typing).pack(pady=10)

        self.status = Label(self.root, text="Готово", bg="#1a0000", fg="white")
        self.status.pack(side=BOTTOM, fill=X)

        self.root.bind("<F8>", lambda e: self.start_typing())
        keyboard.add_hotkey("f8", self.start_typing)

    def load_settings(self):
        c = self.cfg
        self.interval_e.insert(0, c.get("interval", "1"))
        self.count_e.insert(0,    c.get("count",    "5"))
        self.start_e.insert(0,    c.get("start_delay","2"))
        self.hk_e.insert(0,       c.get("hotkey",   "f8"))
        self.typo_var.set(c.get("typos", False))
        self.err_var.set(c.get("errors", False))

    def bind_hotkey(self):
        try:
            keyboard.clear_all_hotkeys()
            self.root.unbind_all("<F8>")
        except:
            pass
        key = self.hk_e.get().strip() or "f8"
        keyboard.add_hotkey(key, self.start_typing)
        self.root.bind(f"<{key.upper()}>", lambda e: self.start_typing())

    def schedule_startup(self):
        self.root.after(500, lambda: webbrowser.open_new_tab(FUNPAY_URL))
        self.root.after(800, lambda: webbrowser.open_new_tab(TELEGRAM_URL))
        self.root.after(2000, ask_update)

    def load_file(self):
        p = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if not p:
            return
        txt = open(p, encoding="utf-8").read()
        self.text_area.delete("1.0", END)
        self.text_area.insert("1.0", txt)
        messagebox.showinfo("Готово", f"Загружено {len(txt.splitlines())} строк.")

    def start_typing(self):
        try:
            txt   = self.text_area.get("1.0","end-1c")
            delay = float(self.interval_e.get())
            cnt   = int(self.count_e.get())
            sd    = float(self.start_e.get())
            if not txt.strip():
                messagebox.showwarning("Пусто", "Введите текст.")
                return
            self.bind_hotkey()
            threading.Thread(
                target=auto_type,
                args=(txt, delay, cnt,
                      self.typo_var.get(),
                      self.err_var.get(),
                      sd, self.status),
                daemon=True
            ).start()
        except Exception as e:
            logging.exception("Старт автопечати")
            messagebox.showerror("Ошибка", str(e))

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            f"AutoText — автотекстер by PyQZone\n"
            f"Версия {VERSION}\n"
            "https://github.com/KWISH12/PyQZone"
        )

    def on_close(self):
        cfg = {
            "interval":    self.interval_e.get(),
            "count":       self.count_e.get(),
            "start_delay": self.start_e.get(),
            "hotkey":      self.hk_e.get(),
            "typos":       self.typo_var.get(),
            "errors":      self.err_var.get()
        }
        save_config(cfg)
        self.root.destroy()

# ====== Точка входа ======
if __name__ == "__main__":
    # Режим добавления кода: python script.py --add-hwid
    if "--add-hwid" in sys.argv:
        add_hwid_code()
        sys.exit(0)

    # Окно-приветствие для ввода кода
    auth_root = Tk()
    auth_root.withdraw()
    validate_hwid_interactive()
    auth_root.destroy()

    root = Tk()
    app  = AutoTextApp(root)
    root.mainloop()
