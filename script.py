#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
import time
import requests
import webbrowser
import logging
from datetime import datetime
from tkinter import *
from tkinter import simpledialog, filedialog, messagebox

import keyboard    # pip install keyboard
import pyautogui   # pip install pyautogui
import pyperclip   # pip install pyperclip

# ====== Настройки ======
VERSION       = "1.0.2"

# Ссылки на сервере (должны быть публично доступны по HTTPS)
LICENSE_URL   = "https://raw.githubusercontent.com/KWISH12/PyQZone/refs/heads/main/licenses.json"
VERSION_URL   = "https://raw.githubusercontent.com/KWISH12/PyQZone/refs/heads/main/version.txt"
EXE_URL       = "https://github.com/You/AutoText/releases/latest/download/script.exe"

FUNPAY_URL    = "https://funpay.com/users/6551539/"
TELEGRAM_URL  = "https://t.me/PyQZone"
REVIEWS_URL   = "https://t.me/+kosYl4xb3EFkZWRi"

LOG_FILE      = "auto_text.log"
CONFIG_FILE   = "config.json"

TYPO_RATE     = 0.03
ERROR_RATE    = 0.1
ERROR_CHARS   = list("абвгдеёжз")

# ====== Подготовка путей ======
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

BASE_DIR      = get_base_dir()
CONFIG_PATH   = os.path.join(BASE_DIR, CONFIG_FILE)
LOG_PATH      = os.path.join(BASE_DIR, LOG_FILE)

# ====== Логирование ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# ====== HWID-функция ======
def get_hwid():
    try:
        out = subprocess.check_output(
            'wmic csproduct get uuid', shell=True,
            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        ).decode('utf-8', errors='ignore').splitlines()
        hw = out[1].strip()
        if hw and "FFFF" not in hw:
            return hw
    except:
        pass
    try:
        import uuid
        mac = uuid.getnode()
        if (mac >> 40) % 2 == 0:
            return ':'.join(f"{(mac >> i) & 0xff:02X}"
                            for i in range(40, -1, -8))
    except:
        pass
    return None

# ====== Лицензирование ======
def load_remote_licenses():
    try:
        resp = requests.get(LICENSE_URL, timeout=5)
        data = resp.json()
        return data.get("codes", {})
    except Exception as e:
        logging.error("Не удалось загрузить licenses.json: %s", e)
        return {}

def validate_license():
    codes = load_remote_licenses()
    code  = simpledialog.askstring("Авторизация", "Введите лицензионный код:")
    if not code or code.strip() not in codes:
        messagebox.showerror("Ошибка", "Неверный код.")
        sys.exit(1)
    info = codes[code.strip()]

    # 1) дата окончания
    today = datetime.now().strftime("%Y-%m-%d")
    if today > info.get("expires", ""):
        messagebox.showerror("Ошибка", "Срок действия кода истёк.")
        sys.exit(1)

    # 2) привязка по HWID
    hwid = get_hwid()
    assigned = info.get("assigned_hwid", "")
    if assigned and assigned != hwid:
        messagebox.showerror("Ошибка", "Код привязан к другой машине.")
        sys.exit(1)
    if not assigned:
        info["assigned_hwid"] = hwid  # первая привязка

    # 3) число запусков
    uses = info.get("uses_left", -1)
    if uses == 0:
        messagebox.showerror("Ошибка", "Запуски исчерпаны.")
        sys.exit(1)
    if uses > 0:
        info["uses_left"] = uses - 1

    # Для реального продакшена здесь нужно отправить обновлённый словарь
    # обратно на сервер через HTTP API (PUT/POST). Здесь – локальное сохранение:
    with open(os.path.join(BASE_DIR, "licenses.local.json"), "w", encoding="utf-8") as f:
        json.dump({"codes": codes}, f, ensure_ascii=False, indent=2)

# ====== Авто-обновление ======
def fetch_remote_version():
    try:
        return requests.get(VERSION_URL, timeout=5).text.strip()
    except:
        return VERSION

def version_gt(a, b):
    A = list(map(int, a.split(".")))
    B = list(map(int, b.split(".")))
    return B > A

def check_update():
    remote = fetch_remote_version()
    if version_gt(VERSION, remote):
        if messagebox.askyesno("Обновление доступно",
                               f"Версия {remote} (ваша {VERSION}). Обновить?"):
            do_update()

def do_update():
    try:
        resp = requests.get(EXE_URL, stream=True, timeout=30)
        tmp  = os.path.join(BASE_DIR, "update.tmp")
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(1024*1024):
                f.write(chunk)

        cur = sys.executable
        bak = cur + ".bak"
        os.replace(cur, bak)
        os.replace(tmp, cur)

        messagebox.showinfo("Обновлено", "Перезапуск для применения обновления")
        os.execv(cur, [cur] + sys.argv)
    except Exception as e:
        logging.error("Ошибка обновления: %s", e)
        messagebox.showerror("Ошибка обновления", str(e))

# ====== Настройки GUI ======
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            return json.load(open(CONFIG_PATH, encoding="utf-8"))
        except:
            logging.warning("Не удалось загрузить config.json")
    return {}

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ====== Опечатки ======
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
    i = random.randrange(len(s))
    return s[:i] + random.choice(ERROR_CHARS) + s[i:]

# ====== Печать текста ======
def type_line(line):
    try:
        keyboard.write(line)
    except:
        pyperclip.copy(line)
        pyautogui.hotkey("ctrl", "v")
    keyboard.send("enter")

def auto_type(text, delay, cnt, typos, errs, sd, status):
    status.master.iconify()
    status.config(text=f"Старт через {sd:.1f} сек…")
    time.sleep(sd)
    status.config(text="Печать…")
    lines = [l for l in text.splitlines() if l.strip()]
    for i in range(cnt):
        ln = lines[i % len(lines)]
        if typos: ln = add_typos(ln)
        if errs:  ln = insert_error_char(ln)
        type_line(ln)
        status.config(text=f"{i+1}/{cnt} отправлено")
        time.sleep(delay)
    status.master.deiconify()
    status.config(text="Готово")

# ====== GUI-приложение ======
class AutoTextApp:
    def __init__(self, root):
        self.root = root
        self.cfg  = load_config()
        self.build_ui()
        self.load_settings()
        self.schedule_tasks()

    def build_ui(self):
        r = self.root
        r.title("🔥 AutoText — PyQZone")
        r.geometry("520x660"); r.configure(bg="#1a0000")
        r.resizable(False,False); r.protocol("WM_DELETE_WINDOW", self.on_close)

        # Меню
        m = Menu(r); r.config(menu=m)
        fm= Menu(m, tearoff=0)
        fm.add_command(label="Проверить обновление", command=check_update)
        fm.add_separator(); fm.add_command(label="Выход", command=self.on_close)
        m.add_cascade(label="Файл", menu=fm)
        hm= Menu(m, tearoff=0)
        hm.add_command(label="О программе", command=self.show_about)
        m.add_cascade(label="Справка", menu=hm)

        # Ссылки
        lf = Frame(r,bg="#1a0000"); lf.pack(pady=8)
        for txt,url in [("FunPay",FUNPAY_URL),("Telegram",TELEGRAM_URL),("Отзывы",REVIEWS_URL)]:
            Button(lf,text=txt,bg="darkred",fg="white",
                   command=lambda u=url:webbrowser.open_new_tab(u)
            ).pack(side=LEFT, padx=6)

        # Текст
        Label(r,text="Текст для автопечати:",bg="#1a0000",fg="white").pack()
        self.ta = Text(r,bg="#300000",fg="white",width=64,height=8)
        self.ta.pack(pady=4)

        # Параметры
        frm = Frame(r,bg="#1a0000"); frm.pack(pady=4)
        Label(frm,text="Интервал:",bg="#1a0000",fg="white").grid(row=0,column=0)
        self.e_delay = Entry(frm,width=6,bg="#300000",fg="white"); self.e_delay.grid(row=0,column=1,padx=4)
        Label(frm,text="Строк:",bg="#1a0000",fg="white").grid(row=0,column=2)
        self.e_count = Entry(frm,width=6,bg="#300000",fg="white"); self.e_count.grid(row=0,column=3,padx=4)
        Label(frm,text="Старт Задержка:",bg="#1a0000",fg="white").grid(row=1,column=0,pady=4)
        self.e_start = Entry(frm,width=6,bg="#300000",fg="white"); self.e_start.grid(row=1,column=1,padx=4)
        Label(frm,text="Хоткей:",bg="#1a0000",fg="white").grid(row=1,column=2)
        self.e_hotkey = Entry(frm,width=8,bg="#300000",fg="white"); self.e_hotkey.grid(row=1,column=3,padx=4)

        self.var_typo = BooleanVar()
        Checkbutton(r,text="Опечатки",variable=self.var_typo,bg="#1a0000",fg="white").pack(pady=2)
        self.var_err  = BooleanVar()
        Checkbutton(r,text="Авто-буква",variable=self.var_err,bg="#1a0000",fg="white").pack(pady=2)

        Button(r,text="📂 Открыть .txt",bg="darkred",fg="white",command=self.load_file).pack(pady=4)
        Button(r,text="🚀 Старт (F8)",bg="red",fg="white",command=self.start_typing).pack(pady=6)

        self.status = Label(r,text="Готово",bg="#1a0000",fg="white")
        self.status.pack(side=BOTTOM,fill=X)

        r.bind("<F8>", lambda e: self.start_typing())
        keyboard.add_hotkey("f8", self.start_typing)

    def load_settings(self):
        c = self.cfg
        self.e_delay.insert(0,     c.get("interval",    "1"))
        self.e_count.insert(0,     c.get("count",       "5"))
        self.e_start.insert(0,     c.get("start_delay","2"))
        self.e_hotkey.insert(0,    c.get("hotkey",      "f8"))
        self.var_typo.set(c.get("typos", False))
        self.var_err.set(c.get("errors",False))

    def bind_hotkey(self):
        try:
            keyboard.clear_all_hotkeys()
            self.root.unbind_all("<F8>")
        except:
            pass
        key = self.e_hotkey.get().strip() or "f8"
        keyboard.add_hotkey(key, self.start_typing)
        self.root.bind(f"<{key.upper()}>", lambda e: self.start_typing())

    def schedule_tasks(self):
        self.root.after(500,   lambda: webbrowser.open_new_tab(FUNPAY_URL))
        self.root.after(800,   lambda: webbrowser.open_new_tab(TELEGRAM_URL))
        self.root.after(2000,  check_update)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if not path:
            return
        text = open(path,encoding="utf-8").read()
        self.ta.delete("1.0", END)
        self.ta.insert("1.0", text)
        messagebox.showinfo("Готово", f"Загружено {len(text.splitlines())} строк.")

    def start_typing(self):
        txt   = self.ta.get("1.0","end-1c")
        try:
            delay = float(self.e_delay.get())
            cnt   = int(self.e_count.get())
            sd    = float(self.e_start.get())
        except:
            messagebox.showerror("Ошибка","Неверные параметры."); return
        if not txt.strip():
            messagebox.showwarning("Пусто","Введите текст."); return

        self.bind_hotkey()
        threading.Thread(
            target=auto_type,
            args=(txt,delay,cnt,
                  self.var_typo.get(),
                  self.var_err.get(),
                  sd,self.status),
            daemon=True
        ).start()

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            f"AutoText by PyQZone\nВерсия {VERSION}\n"
            "https://github.com/KWISH12/PyQZone"
        )

    def on_close(self):
        cfg = {
            "interval":    self.e_delay.get(),
            "count":       self.e_count.get(),
            "start_delay": self.e_start.get(),
            "hotkey":      self.e_hotkey.get(),
            "typos":       self.var_typo.get(),
            "errors":      self.var_err.get()
        }
        save_config(cfg)
        self.root.destroy()

# ====== Запуск программы ======
if __name__ == "__main__":
    # 1) Проверка лицензии
    auth = Tk(); auth.withdraw()
    validate_license()
    auth.destroy()

    # 2) Основное GUI
    root = Tk()
    app  = AutoTextApp(root)
    root.mainloop()
