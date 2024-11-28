import sounddevice as sd
import numpy as np
import soundfile as sf
import time
import threading
import tkinter as tk
from tkinter import ttk

class SoundPlayer:
    def __init__(self):
        # サンプリングレートの設定
        self.fs = 44100
        sd.default.samplerate = self.fs

        # 足音の読み込み
        self.footstep_file = "footStep.mp3"
        self.foot_audiodata, _ = sf.read(self.footstep_file, dtype='float32')

        # 振動用の音の生成（モノラル）
        duration = 0.1  # 秒
        frequency = 70  # Hz
        t = np.linspace(0, duration, int(self.fs * duration), endpoint=False)
        amplitude = 1.0
        self.vibration_sound = amplitude * np.sin(2 * np.pi * frequency * t).astype('float32')

        # デバイスインデックスの設定
        self.device_index_foot = 11   # 足音用デバイス
        self.device_index_calf = 10  # 脹脛用デバイス（Right）
        self.device_index_thigh = 13  # 太腿用デバイス（Left）

        # ラグの初期値とロック
        self.lag1 = 0.15  # ラグ1（脹脛）
        self.lag2 = 0.15  # ラグ2（太腿）
        self.lag_lock = threading.Lock()

        # 足音の周期
        self.footstep_period = 0.7

        # 停止イベント
        self.stop_event = threading.Event()

        # デバイスの切り替えフラグ（True: 右脚、False: 左脚）
        self.is_right_leg = True

        # サウンド再生スレッドの開始
        self.play_thread = threading.Thread(target=self.play_sequence)
        self.play_thread.start()

        # GUIの設定
        self.root = tk.Tk()
        self.root.title("ラグ調整")
        self.root.geometry("450x450")
        self.root.configure(background='blue')

        self.lag1_var = tk.DoubleVar(value=self.lag1)
        self.lag2_var = tk.DoubleVar(value=self.lag2)

        # スライダーのスタイル設定
        style = ttk.Style()
        style.configure("TScale", background="blue")

        # ラグ1のスライダー
        lag1_label = ttk.Label(self.root, text="ラグ1（脹脛）", background='blue', foreground='white', font=('Arial', 12))
        lag1_label.pack(pady=5)

        lag1_scale = ttk.Scale(self.root, from_=0.0, to=self.footstep_period, orient='horizontal',
                               variable=self.lag1_var, command=self.update_lag1, length=300)
        lag1_scale.pack()

        # スライダーの両端にラベルを追加
        lag1_scale_frame = tk.Frame(self.root, background='blue')
        lag1_scale_frame.pack()
        lag1_min_label = ttk.Label(lag1_scale_frame, text="0", background='blue', foreground='white')
        lag1_min_label.pack(side='left')
        lag1_max_label = ttk.Label(lag1_scale_frame, text="700ms", background='blue', foreground='white')
        lag1_max_label.pack(side='right')

        # ラグ1の値を表示
        self.lag1_value_label = ttk.Label(self.root, text=f"ラグ1の値: {self.lag1*1000:.1f} ms", background='blue', foreground='white')
        self.lag1_value_label.pack(pady=5)

        # ラグ2のスライダー
        lag2_label = ttk.Label(self.root, text="ラグ2（太腿）", background='blue', foreground='white', font=('Arial', 12))
        lag2_label.pack(pady=5)

        lag2_scale = ttk.Scale(self.root, from_=0.0, to=self.footstep_period, orient='horizontal',
                               variable=self.lag2_var, command=self.update_lag2, length=300)
        lag2_scale.pack()

        # スライダーの両端にラベルを追加
        lag2_scale_frame = tk.Frame(self.root, background='blue')
        lag2_scale_frame.pack()
        lag2_min_label = ttk.Label(lag2_scale_frame, text="0", background='blue', foreground='white')
        lag2_min_label.pack(side='left')
        lag2_max_label = ttk.Label(lag2_scale_frame, text="700ms", background='blue', foreground='white')
        lag2_max_label.pack(side='right')

        # ラグ2の値を表示
        self.lag2_value_label = ttk.Label(self.root, text=f"ラグ2の値: {self.lag2*1000:.1f} ms", background='blue', foreground='white')
        self.lag2_value_label.pack(pady=5)

        # 現在の状態を表示
        self.current_state_label = ttk.Label(self.root, text="", background='blue', foreground='white', font=('Arial', 14))
        self.current_state_label.pack(pady=10)

        # GUIイベントループの開始
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def update_lag1(self, value):
        with self.lag_lock:
            self.lag1 = min(float(value), self.footstep_period)
            # ラグ1の値を更新
            self.lag1_value_label.config(text=f"ラグ1の値: {self.lag1*1000:.1f} ms")

    def update_lag2(self, value):
        with self.lag_lock:
            self.lag2 = min(float(value), self.footstep_period)
            # ラグ2の値を更新
            self.lag2_value_label.config(text=f"ラグ2の値: {self.lag2*1000:.1f} ms")

    def play_footstep(self):
        try:
            with sd.OutputStream(device=self.device_index_foot, samplerate=self.fs,
                                 channels=len(self.foot_audiodata.shape), dtype='float32') as stream:
                stream.write(self.foot_audiodata)
            # 状態を更新
            self.update_current_state("足音再生中")
        except Exception as e:
            print(f"足音の再生エラー: {e}")

    def play_vibration(self, device_index, location):
        try:
            with sd.OutputStream(device=device_index, samplerate=self.fs,
                                 channels=1, dtype='float32') as stream:
                stream.write(self.vibration_sound)
            # 状態を更新
            leg = "右脚" if self.is_right_leg else "左脚"
            self.update_current_state(f"{leg}の{location}を刺激中")
        except Exception as e:
            print(f"デバイス{device_index}の再生エラー: {e}")

    def update_current_state(self, state_text):
        def update_label():
            self.current_state_label.config(text=state_text)
        self.root.after(0, update_label)

    def play_sequence(self):
        while not self.stop_event.is_set():
            start_time = time.time()

            with self.lag_lock:
                lag1 = self.lag1
                lag2 = self.lag2

            # ラグが足音の周期を超えないように制限
            lag1 = min(lag1, self.footstep_period)
            lag2 = min(lag2, self.footstep_period)

            # 足音の再生
            self.play_footstep()

            # 現在の脚に対応するデバイスインデックスを設定
            if self.is_right_leg:
                calf_device = self.device_index_calf   # 脹脛（右脚）
                thigh_device = self.device_index_thigh # 太腿（右脚）※デバイス設定が必要
            else:
                calf_device = self.device_index_calf   # 脹脛（左脚）※デバイス設定が必要
                thigh_device = self.device_index_thigh # 太腿（左脚）

            # スレッドを使って並行に刺激を再生
            threads = []

            # ラグ1後に脹脛を刺激
            t1 = threading.Thread(target=self.delayed_play_vibration, args=(lag1, calf_device, "脹脛"))
            threads.append(t1)
            t1.start()

            # ラグ2後に太腿を刺激
            t2 = threading.Thread(target=self.delayed_play_vibration, args=(lag2, thigh_device, "太腿"))
            threads.append(t2)
            t2.start()

            # スレッドの終了を待機
            for t in threads:
                t.join()

            # デバイスを切り替え
            self.is_right_leg = not self.is_right_leg

            # 足音の周期まで待機
            elapsed_time = time.time() - start_time
            remaining_time = self.footstep_period - elapsed_time
            if remaining_time > 0:
                time.sleep(remaining_time)

    def delayed_play_vibration(self, delay, device_index, location):
        if delay > 0:
            time.sleep(delay)
        if not self.stop_event.is_set():
            self.play_vibration(device_index, location)

    def on_closing(self):
        self.stop_event.set()
        self.play_thread.join()
        self.root.destroy()

if __name__ == '__main__':
    SoundPlayer()
