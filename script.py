import os
import threading
import time
import random
import webbrowser
import keyboard
import pyautogui
from tkinter import *
from tkinter import filedialog, messagebox
import subprocess
import uuid
import sys
import requests

# ====== ССЫЛКИ ======
FUNPAY_URL = "https://funpay.com/users/6551539/"
TELEGRAM_URL = "https://t.me/PyQZone"
REVIEWS_URL = "https://t.me/+kosYl4xb3EFkZWRi"

# ====== ССЫЛКА НА ОБНОВЛЕНИЕ ======
UPDATE_URL = "https://raw.githubusercontent.com/KWISH12/PyQZone/main/script.py"

HWID_FILE = "hwid_lock.txt"

# ====== Получение HWID (универсально) ======
def get_hwid():
    try:
        output = subprocess.check_output('wmic csproduct get uuid', shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        output = output.decode().split('\n')[1].strip()
        if output and output != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
            return output
    except Exception:
        pass
    try:
        mac = uuid.getnode()
        if (mac >> 40) % 2 == 0:
            return ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    except Exception:
        pass
    return None

# ====== Проверка и создание файла HWID ======
def check_and_lock_hwid():
    current_hwid = get_hwid()
    if current_hwid is None:
        messagebox.showerror("Ошибка", "Не удалось получить HWID. Программа завершается.")
        sys.exit(1)

    if os.path.exists(HWID_FILE):
        with open(HWID_FILE, "r") as f:
            saved_hwid = f.read().strip()
        if saved_hwid != current_hwid:
            messagebox.showerror("Ошибка", "HWID не совпадает. Запуск запрещён.")
            sys.exit(1)
    else:
        with open(HWID_FILE, "w") as f:
            f.write(current_hwid)
        messagebox.showinfo("Привязка", f"Программа привязана к этому компьютеру.\nHWID: {current_hwid}")

# ====== Автообновление ======
def check_for_update():
    try:
        response = requests.get(UPDATE_URL, timeout=10)
        response.encoding = "utf-8"
        if response.status_code != 200:
            print(f"Ошибка обновления: HTTP {response.status_code}")
            return
        new_code = response.text
        with open(__file__, "r", encoding="utf-8") as f:
            current_code = f.read()
        if new_code.strip() != current_code.strip():
            with open(__file__, "w", encoding="utf-8") as f:
                f.write(new_code)
            messagebox.showinfo("Обновление", "Программа обновлена! Перезапусти её.")
            sys.exit(0)
    except Exception as e:
        print(f"Ошибка обновления: {e}")

# ====== Функции автотекста ======
def add_typos(text):
    result = ""
    for char in text:
        if random.random() < 0.03:
            result += random.choice("asdfghjklqwertyuiop")
        result += char
    return result

def auto_type(text, interval, count, typos):
    lines = text.splitlines()
    for i in range(count):
        line = lines[i % len(lines)]
        if typos:
            line = add_typos(line)
        for char in line:
            pyautogui.typewrite(char)
            time.sleep(interval / 10)
        pyautogui.press("enter")
        time.sleep(interval)

def start_auto_type():
    try:
        interval = float(interval_entry.get())
        lines = int(lines_entry.get())
        text = text_area.get("1.0", END).strip()
        if not text:
            messagebox.showwarning("⚠️", "Введите текст или загрузите файл.")
            return
        threading.Thread(target=auto_type, args=(text, interval, lines, typo_var.get()), daemon=True).start()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Проверь поля ввода.\n{e}")

def listen_hotkey():
    hotkey = hotkey_entry.get().lower()
    pressed = False
    while True:
        if keyboard.is_pressed(hotkey) and not pressed:
            pressed = True
            start_auto_type()
        elif not keyboard.is_pressed(hotkey):
            pressed = False
        time.sleep(0.1)

def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            text_area.delete("1.0", END)
            content = f.read()
            text_area.insert("1.0", content)
        messagebox.showinfo("Файл загружен", f"Загружено {len(content.splitlines())} строк.")

# ====== GUI ======
root = Tk()
root.title("🔥 AutoText — by PyQZone")
root.configure(bg="#1a0000")
root.geometry("430x560")
root.resizable(False, False)

# ====== Открываем ссылки при запуске ======
webbrowser.open_new_tab(FUNPAY_URL)
webbrowser.open_new_tab(TELEGRAM_URL)

# ====== HWID проверка ======
check_and_lock_hwid()

# ====== Проверка обновлений ======
check_for_update()

# ====== Интерфейс ======
Button(root, text="📂 Открыть файл", bg="darkred", fg="white", command=load_file).pack(pady=10)

Label(root, text="Или введите текст вручную:", bg="#1a0000", fg="white").pack()
text_area = Text(root, height=6, width=45, bg="#300000", fg="white")
text_area.pack(pady=5)

Label(root, text="Интервал (сек):", bg="#1a0000", fg="white").pack()
interval_entry = Entry(root, bg="#300000", fg="white")
interval_entry.insert(0, "1")
interval_entry.pack()

Label(root, text="Сколько строк:", bg="#1a0000", fg="white").pack()
lines_entry = Entry(root, bg="#300000", fg="white")
lines_entry.insert(0, "5")
lines_entry.pack()

Label(root, text="Клавиша (например, f8):", bg="#1a0000", fg="white").pack()
hotkey_entry = Entry(root, bg="#300000", fg="white")
hotkey_entry.insert(0, "f8")
hotkey_entry.pack(pady=5)

typo_var = BooleanVar()
Checkbutton(root, text="Добавлять ошибки в текст", variable=typo_var, bg="#1a0000", fg="white").pack(pady=5)

Button(root, text="🚀 Запустить", bg="red", fg="white", command=start_auto_type).pack(pady=10)

# ====== Нижние кнопки ======
bottom_frame = Frame(root, bg="#1a0000")
bottom_frame.pack(pady=10)

Button(bottom_frame, text="💬 Отзывы", bg="darkred", fg="white", command=lambda: webbrowser.open(REVIEWS_URL)).pack(side=LEFT, padx=5)
Button(bottom_frame, text="👤 Telegram", bg="darkred", fg="white", command=lambda: webbrowser.open(TELEGRAM_URL)).pack(side=LEFT, padx=5)
Button(bottom_frame, text="🛒 FunPay", bg="darkred", fg="white", command=lambda: webbrowser.open(FUNPAY_URL)).pack(side=LEFT, padx=5)

# ====== Запуск слушателя hotkey ======
threading.Thread(target=listen_hotkey, daemon=True).start()

root.mainloop()
