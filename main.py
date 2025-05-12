import tkinter as tk
from tkinter import messagebox
import serial
import threading
import os
from datetime import datetime
from tag_info import tag_database

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RFID Poker Tracker")
        self.geometry("800x400")
        self.configure(bg="#f0f0f0")
        self.resizable(False, False)

        self.mode = "manager"
        self.hand_count = 1
        self.log_filename = None

        self.card_data = {
            "P1": ["?", "?"], 
            "P2": ["?", "?"], 
            "BOARD": ["?", "?", "?", "?", "?"]
        }
        self.read_uids = set()
        self.sections = {}
        self.create_ui()
        self.update_display_for_mode()

        self.serial_threads = [
            threading.Thread(target=self.read_serial, args=("COM3",)),  # COM3 for Arduino 1
            threading.Thread(target=self.read_serial, args=("COM4",))   # COM4 for Arduino 2
        ]
        for thread in self.serial_threads:
            thread.daemon = True
            thread.start()

    def create_ui(self):
        self.mode_label = tk.Label(self, text="Manager Mode", font=("Arial", 14, "bold"))
        self.mode_label.pack(pady=5)

        self.hand_label = tk.Label(self, text=f"HAND {self.hand_count}", font=("Arial", 12))
        self.hand_label.pack()

        self.container = tk.Frame(self, bg="#f0f0f0")
        self.container.pack(expand=True)

        for section_name, count in [("P1", 2), ("P2", 2), ("BOARD", 5)]:
            frame = tk.Frame(self.container, bg="#f0f0f0")
            frame.pack(side=tk.TOP, anchor="w", padx=20, pady=5)

            label = tk.Label(frame, text=section_name, font=("Arial", 12, "bold"), width=6, anchor="w")
            label.pack(side=tk.LEFT)

            self.sections[section_name] = []
            for _ in range(count):
                card_label = tk.Label(frame, text="?", font=("Arial", 16), width=6, height=2, relief="groove", bg="white")
                card_label.pack(side=tk.LEFT, padx=4)
                self.sections[section_name].append(card_label)

        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(pady=10)

        self.reset_button = tk.Button(button_frame, text="リセット", command=self.reset_cards)
        self.reset_button.pack(side=tk.LEFT, padx=10)

        self.save_button = tk.Button(button_frame, text="保存", command=self.save_log)
        self.save_button.pack(side=tk.LEFT, padx=10)

        self.toggle_button = tk.Button(button_frame, text="モード切替", command=self.toggle_mode)
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        self.game_reset_button = tk.Button(button_frame, text="ゲームリセット", command=self.game_reset)
        self.game_reset_button.pack(side=tk.LEFT, padx=10)

        self.update_mode_appearance()

    def toggle_mode(self):
        self.mode = "player" if self.mode == "manager" else "manager"
        self.update_display_for_mode()
        self.update_mode_appearance()

    def update_mode_appearance(self):
        if self.mode == "player":
            self.mode_label.config(text="Player Mode", bg="#e0f7fa", fg="black")
            self.configure(bg="#e0f7fa")
        else:
            self.mode_label.config(text="Manager Mode", bg="#f0f0f0", fg="black")
            self.configure(bg="#f0f0f0")

    def get_color_from_card(self, card):
        if len(card) >= 2:
            suit = card[1]
            return {
                's': 'black',
                'h': 'red',
                'c': 'green',
                'd': 'blue'
            }.get(suit, 'black')
        return "black"

    def update_display_for_mode(self):
        for area in ["P1", "P2"]:
            for i, card in enumerate(self.card_data[area]):
                if self.mode == "player":
                    display_value = "〇" if card != "?" else "?"
                    color = "black"
                else:
                    display_value = card
                    color = self.get_color_from_card(card)
                self.sections[area][i].config(text=display_value, fg=color)

        for i, card in enumerate(self.card_data["BOARD"]):
            display_value = card
            color = self.get_color_from_card(card)
            self.sections["BOARD"][i].config(text=display_value, fg=color)

    def reset_cards(self):
        self.card_data = {
            "P1": ["?", "?"], 
            "P2": ["?", "?"], 
            "BOARD": ["?", "?", "?", "?", "?"]
        }
        self.read_uids.clear()
        self.update_display_for_mode()

    def game_reset(self):
        # ゲームリセット処理
        confirm = messagebox.askyesno("確認", "本当に対局をリセットしますか？")
        if not confirm:
            return
        self.hand_count = 1
        self.log_filename = None
        self.hand_label.config(text=f"HAND {self.hand_count}")
        self.reset_cards()

    def save_log(self):
        # ログ保存処理
        os.makedirs("log", exist_ok=True)
        if not self.log_filename:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_filename = os.path.join("log", f"log_{now}.txt")

        with open(self.log_filename, "a") as f:
            f.write(f"HAND {self.hand_count}\n")
            f.write("P1: " + " ".join(self.card_data["P1"]) + "\n")
            f.write("P2: " + " ".join(self.card_data["P2"]) + "\n")
            f.write("BOARD: " + " ".join(self.card_data["BOARD"]) + "\n\n")

        self.hand_count += 1
        self.hand_label.config(text=f"HAND {self.hand_count}")
        self.reset_cards()

    def read_serial(self, port):
        try:
            ser = serial.Serial(port, 9600, timeout=1)
        except serial.SerialException:
            print(f"シリアルポート {port} が開けません")
            return

        while True:
            try:
                line = ser.readline().decode("utf-8").strip()
                if line:
                    self.handle_uid(line)
            except Exception as e:
                print("エラー:", e)

    def handle_uid(self, uid):
        if uid in self.read_uids:
            return

        if uid in tag_database:
            card = tag_database[uid]
        else:
            card = "?"

        placed = False
        for area in ["P1", "P2", "BOARD"]:
            for i in range(len(self.card_data[area])):
                if self.card_data[area][i] == "?":
                    self.card_data[area][i] = card
                    self.read_uids.add(uid)
                    placed = True
                    break
            if placed:
                break
        self.update_display_for_mode()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
