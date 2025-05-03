import tkinter as tk
from tkinter import scrolledtext
import serial
import threading
from datetime import datetime
from tag_info import known_cards  # 外部のUID→名前データ

# ---------- シリアル設定 ----------
PORT = 'COM3'  # ←Arduinoのポートに合わせて変更
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)

# ---------- GUIアプリ ----------
class RFIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID 読み取りアプリ")

        self.label = tk.Label(root, text="カードをかざしてください", font=("Helvetica", 16))
        self.label.pack(pady=10)

        self.log = scrolledtext.ScrolledText(root, width=50, height=10, state='disabled')
        self.log.pack()

        # シリアル受信スレッド開始
        self.running = True
        threading.Thread(target=self.read_serial, daemon=True).start()

    def read_serial(self):
        while self.running:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    name = known_cards.get(line, "未登録のカード")
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    message = f"{now} - {name} ({line})"
                    self.update_log(message)

    def update_log(self, message):
        self.log.config(state='normal')
        self.log.insert(tk.END, message + "\n")
        self.log.yview(tk.END)
        self.log.config(state='disabled')

# ---------- 起動 ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDApp(root)
    root.mainloop()
