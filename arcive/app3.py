import sounddevice as sd
import numpy as np
import soundfile as sf
import time
import threading
import tkinter as tk
from tkinter import ttk
import concurrent.futures

class SoundPlayer:
    def __init__(self):
        # サンプリングレートの設定
        self.fs = 44100
        sd.default.samplerate = self.fs

        # 足音の読み込み
        self.footstep_file = "footStep.mp3"
        self.foot_audiodata, _ = sf.read(self.footstep_file, dtype='float32')

        # 他の音の生成
        duration = 0.1  # 秒
        #frequency = 70  # Hz
        frequency = 2000  # Hz
        t = np.linspace(0, duration, int(self.fs * duration), endpoint=False)
        amplitude = 1.0
        myarray = amplitude * np.sin(2 * np.pi * frequency * t).astype('float32')
        self.right_channel_data = np.column_stack((np.zeros_like(myarray), myarray))
        self.left_channel_data = np.column_stack((myarray, np.zeros_like(myarray)))

        # デバイスインデックスの設定（適切な値に変更してください）
        self.device_index_foot = 3
        self.device_index_a = 3

        # ラグの初期値とロック
        self.lag1 = 0.15
        self.lag2 = 0.15
        self.lag_lock = threading.Lock()

        # 足音の周期
        self.footstep_period = 0.7

        # 停止イベント
        self.stop_event = threading.Event()

        # サウンド再生スレッドの開始
        self.play_thread = threading.Thread(target=self.play_sequence)
        self.play_thread.start()

        # GUIの設定
        self.root = tk.Tk()
        self.root.title("ラグ調整")
        self.root.geometry("450x250")
        self.root.configure(background='blue')

        self.lag1_var = tk.DoubleVar(value=self.lag1)
        self.lag2_var = tk.DoubleVar(value=self.lag2)

        # スライダーのスタイル設定
        style = ttk.Style()
        style.configure("TScale", background="blue")

        # ラグ1のスライダー
        lag1_label = ttk.Label(self.root, text="ラグ1", background='blue', foreground='white', font=('Arial', 12))
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
        lag2_label = ttk.Label(self.root, text="ラグ2", background='blue', foreground='white', font=('Arial', 12))
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

        # GUIイベントループの開始
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def update_lag1(self, value):
        with self.lag_lock:
            self.lag1 = float(value)
            # ラグ1の値を更新
            self.lag1_value_label.config(text=f"ラグ1の値: {self.lag1*1000:.1f} ms")

    def update_lag2(self, value):
        with self.lag_lock:
            self.lag2 = float(value)
            # ラグ2の値を更新
            self.lag2_value_label.config(text=f"ラグ2の値: {self.lag2*1000:.1f} ms")

    def play_footstep(self):
        try:
            with sd.OutputStream(device=self.device_index_foot, samplerate=self.fs,
                                 channels=len(self.foot_audiodata.shape), dtype='float32') as stream:
                stream.write(self.foot_audiodata)
        except Exception as e:
            print(f"足音の再生エラー: {e}")

    def play_sound_right(self):
        try:
            with sd.OutputStream(device=self.device_index_a, samplerate=self.fs,
                                 channels=2, dtype='float32') as stream:
                stream.write(self.right_channel_data)
        except Exception as e:
            print(f"振動右の再生エラー: {e}")

    def play_sound_left(self):
        try:
            with sd.OutputStream(device=self.device_index_a, samplerate=self.fs,
                                 channels=2, dtype='float32') as stream:
                stream.write(self.left_channel_data)
        except Exception as e:
            print(f"振動左の再生エラー: {e}")

    def play_sequence(self):
        while not self.stop_event.is_set():
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(self.play_footstep)

                with self.lag_lock:
                    lag1 = self.lag1
                    lag2 = self.lag2

                # ラグ1後に振動右を再生
                executor.submit(self.delayed_play, self.play_sound_right, lag1)
                # ラグ2後に振動左を再生
                executor.submit(self.delayed_play, self.play_sound_left, lag2)

            # 足音の周期ごとに繰り返し
            time.sleep(self.footstep_period)

    def delayed_play(self, func, delay):
        time.sleep(delay)
        func()

    def on_closing(self):
        self.stop_event.set()
        self.play_thread.join()
        self.root.destroy()

if __name__ == '__main__':
    SoundPlayer()
