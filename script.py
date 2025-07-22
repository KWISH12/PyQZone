import os
import threading
import time
import random
import webbrowser
import requests
import keyboard
import pyautogui
from tkinter import *
from tkinter import filedialog, messagebox

# ====== ССЫЛКИ ======
FUNPAY_URL = "https://funpay.com/users/6551539/"
TELEGRAM_URL = "https://t.me/PyQZone"
REVIEWS_URL = "https://t.me/+kosYl4xb3EFkZWRi"

# ====== ССЫЛКА НА ОБНОВЛЕНИЕ ======
UPDATE_URL = "https://raw.githubusercontent.com/KWISH12/PyQZone/main/script.py"

# ====== АВТООБНОВЛЕНИЕ ======
def check_for_update():
    try:
        r = requests.get(UPDATE_URL)
        r.encoding = "utf-8"
        new_code = r.text.strip()
        with open(__file__, "r", encoding="utf-8") as f:
            current_code = f.read().strip()
        if new_code != current_code:
            with open(__file__, "w", encoding="utf-8") as f:
                f.write(new_code)
            messagebox.showinfo("Обновление", "Обновление завершено! Перезапусти программу.")
            os._exit(0)
    except Exception as e:
        print("Ошибка обновления:", e)

# ====== ТЕКСТ С ОШИБКАМИ ======
def add_typos(text):
    result = ""
    for char in text:
        if random.random() < 0.03:
            result += random.choice("asdfghjklqwertyuiop")
        result += char
    return result

# ====== АВТОНАБОР ======
def auto_type(text, interval, count, typos):
    for i in range(count):
        line = text[i % len(text.splitlines())]
        if typos:
            line = add_typos(line)
        pyautogui.typewrite(line)
        pyautogui.press("enter")
        time.sleep(interval)

# ====== F8: ЗАПУСК ПО КУРСОРУ ======
def listen_hotkey():
    while True:
        if keyboard.is_pressed(hotkey_entry.get()):
            try:
                interval = float(interval_entry.get())
                lines = int(lines_entry.get())
                text = text_area.get("1.0", END).strip()
                if not text:
                    messagebox.showwarning("⚠️", "Введите текст или загрузите файл.")
                    return
                threading.Thread(target=auto_type, args=(text, interval, lines, typo_var.get()), daemon=True).start()
                time.sleep(1)
            except:
                messagebox.showerror("Ошибка", "Проверь правильность ввода.")
        time.sleep(0.1)

# ====== ЗАГРУЗКА .TXT ======
def load_file():
    path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if path:
        with open(path, "r", encoding="utf-8") as f:
            text_area.delete("1.0", END)
            text_area.insert("1.0", f.read())

# ====== GUI ======
root = Tk()
root.title("🔥 AutoText — by PyQZone")
root.configure(bg="#1a0000")
root.geometry("430x560")
root.resizable(False, False)

# ====== АВТООТКРЫТИЕ ССЫЛОК ======
webbrowser.open_new_tab(FUNPAY_URL)
webbrowser.open_new_tab(TELEGRAM_URL)

# ====== ПРОВЕРКА ОБНОВЛЕНИЯ ======
check_for_update()

# ====== GUI ЭЛЕМЕНТЫ ======
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

Label(root, text="Клавиша (F8):", bg="#1a0000", fg="white").pack()
hotkey_entry = Entry(root, bg="#300000", fg="white")
hotkey_entry.insert(0, "F8")
hotkey_entry.pack(pady=5)

typo_var = BooleanVar()
Checkbutton(root, text="Добавлять ошибки в текст", variable=typo_var, bg="#1a0000", fg="white").pack(pady=5)

Button(root, text="🚀 Запустить (по F8)", bg="red", fg="white", command=lambda: None).pack(pady=10)

# ====== КНОПКИ НИЖНИЕ ======
bottom = Frame(root, bg="#1a0000")
bottom.pack(pady=10)

Button(bottom, text="💬 Отзывы", bg="darkred", fg="white", command=lambda: webbrowser.open(REVIEWS_URL)).pack(side=LEFT, padx=5)
Button(bottom, text="👤 Telegram", bg="darkred", fg="white", command=lambda: webbrowser.open(TELEGRAM_URL)).pack(side=LEFT, padx=5)
Button(bottom, text="🛒 FunPay", bg="darkred", fg="white", command=lambda: webbrowser.open(FUNPAY_URL)).pack(side=LEFT, padx=5)

# ====== СЛУШАТЕЛЬ F8 ======
threading.Thread(target=listen_hotkey, daemon=True).start()

root.mainloop()
