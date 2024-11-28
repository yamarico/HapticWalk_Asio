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
        frequency = 80  # Hz
        t = np.linspace(0, duration, int(self.fs * duration), endpoint=False)
        amplitude = 1.0
        self.vibration_sound = amplitude * np.sin(2 * np.pi * frequency * t).astype('float32')

        # 左右チャンネル用のデータを作成
        self.left_channel_data = np.column_stack((self.vibration_sound, np.zeros_like(self.vibration_sound)))
        self.right_channel_data = np.column_stack((np.zeros_like(self.vibration_sound), self.vibration_sound))

        # デバイスインデックスの設定
        self.device_index_foot = 11   # 足音用デバイス
        self.device_index_a = 10      # デバイスA
        self.device_index_b = 13      # デバイスB

        # デバイスを脚と部位にマッピング
        self.device_index_calf = self.device_index_a   # 脹脛用デバイス
        self.device_index_thigh = self.device_index_b  # 太腿用デバイス

        # ラグの初期値とロック
        self.lag1 = 0.15  # ラグ1（脹脛）
        self.lag2 = 0.15  # ラグ2（太腿）
        self.lag_lock = threading.Lock()

        # 足音の周期
        self.footstep_period = 0.50  # ここを変更するとラグの上限も変更されます

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
        self.root.geometry("450x500")
        self.root.configure(background='blue')

        self.lag1_var = tk.DoubleVar(value=self.lag1)
        self.lag2_var = tk.DoubleVar(value=self.lag2)

        # スライダーのスタイル設定
        style = ttk.Style()
        style.configure("TScale", background="blue")

        # ラグ1のスライダー
        lag1_label = ttk.Label(self.root, text="ラグ1（脹脛）", background='blue', foreground='white', font=('Arial', 12))
        lag1_label.pack(pady=5)

        self.lag1_scale = ttk.Scale(self.root, from_=0.0, to=self.footstep_period, orient='horizontal',
                                    variable=self.lag1_var, command=self.update_lag1, length=300)
        self.lag1_scale.pack()

        # スライダーの両端にラベルを追加
        lag1_scale_frame = tk.Frame(self.root, background='blue')
        lag1_scale_frame.pack()
        lag1_min_label = ttk.Label(lag1_scale_frame, text="0", background='blue', foreground='white')
        lag1_min_label.pack(side='left')
        self.lag1_max_label = ttk.Label(lag1_scale_frame, text=f"{int(self.footstep_period*1000)}ms", background='blue', foreground='white')
        self.lag1_max_label.pack(side='right')

        # ラグ1の値を表示
        self.lag1_value_label = ttk.Label(self.root, text=f"ラグ1の値: {self.lag1*1000:.1f} ms", background='blue', foreground='white')
        self.lag1_value_label.pack(pady=5)

        # ラグ2のスライダー
        lag2_label = ttk.Label(self.root, text="ラグ2（太腿）", background='blue', foreground='white', font=('Arial', 12))
        lag2_label.pack(pady=5)

        self.lag2_scale = ttk.Scale(self.root, from_=0.0, to=self.footstep_period, orient='horizontal',
                                    variable=self.lag2_var, command=self.update_lag2, length=300)
        self.lag2_scale.pack()

        # スライダーの両端にラベルを追加
        lag2_scale_frame = tk.Frame(self.root, background='blue')
        lag2_scale_frame.pack()
        lag2_min_label = ttk.Label(lag2_scale_frame, text="0", background='blue', foreground='white')
        lag2_min_label.pack(side='left')
        self.lag2_max_label = ttk.Label(lag2_scale_frame, text=f"{int(self.footstep_period*1000)}ms", background='blue', foreground='white')
        self.lag2_max_label.pack(side='right')

        # ラグ2の値を表示
        self.lag2_value_label = ttk.Label(self.root, text=f"ラグ2の値: {self.lag2*1000:.1f} ms", background='blue', foreground='white')
        self.lag2_value_label.pack(pady=5)

        # 現在の状態を表示
        self.current_state_label = ttk.Label(self.root, text="", background='blue', foreground='white', font=('Arial', 14))
        self.current_state_label.pack(pady=10)

        # プログラム終了ボタンを追加
        exit_button = ttk.Button(self.root, text="プログラム終了", command=self.on_closing)
        exit_button.pack(pady=10)

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

    # 足音の周期が変更されたときにスライダーの上限を更新
    def update_footstep_period(self, new_period):
        self.footstep_period = new_period
        # スライダーの最大値を更新
        self.lag1_scale.configure(to=self.footstep_period)
        self.lag2_scale.configure(to=self.footstep_period)
        # スライダーの右端のラベルを更新
        self.lag1_max_label.config(text=f"{int(self.footstep_period*1000)}ms")
        self.lag2_max_label.config(text=f"{int(self.footstep_period*1000)}ms")

    def play_footstep(self):
        try:
            with sd.OutputStream(device=self.device_index_foot, samplerate=self.fs,
                                 channels=len(self.foot_audiodata.shape), dtype='float32') as stream:
                stream.write(self.foot_audiodata)
            # 状態を更新
            self.update_current_state("足音再生中")
        except Exception as e:
            print(f"足音の再生エラー: {e}")

    def play_vibration(self, device_index, location, channel):
        try:
            if channel == 'left':
                data = self.left_channel_data
            elif channel == 'right':
                data = self.right_channel_data
            else:
                data = self.vibration_sound  # モノラルデータ
            with sd.OutputStream(device=device_index, samplerate=self.fs,
                                 channels=2, dtype='float32') as stream:
                stream.write(data)
            # 状態を更新
            leg = "右脚" if self.is_right_leg else "左脚"
            self.update_current_state(f"{leg}の{location}を刺激中")
        except Exception as e:
            print(f"デバイス{device_index}の再生エラー: {e}")

    def update_current_state(self, state_text):
        def update_label():
            self.current_state_label.config(text=state_text)
        self.root.after(0, update_label)

    def sleep_until_stop_event(self, delay):
        # stop_event がセットされるか、指定した時間が経過するまで待機
        self.stop_event.wait(timeout=delay)

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

            # 現在の脚に対応するデバイスインデックスとチャンネルを設定
            if self.is_right_leg:
                calf_device = self.device_index_calf   # 脹脛（右脚）
                thigh_device = self.device_index_thigh # 太腿（右脚）
                calf_channel = 'right'
                thigh_channel = 'left'
            else:
                calf_device = self.device_index_calf   # 脹脛（左脚）
                thigh_device = self.device_index_thigh # 太腿（左脚）
                calf_channel = 'right'
                thigh_channel = 'left'

            # スレッドを使って並行に刺激を再生
            threads = []

            # ラグ1後に脹脛を刺激
            t1 = threading.Thread(target=self.delayed_play_vibration, args=(lag1, calf_device, "脹脛", calf_channel))
            threads.append(t1)
            t1.start()

            # ラグ2後に太腿を刺激
            t2 = threading.Thread(target=self.delayed_play_vibration, args=(lag2, thigh_device, "太腿", thigh_channel))
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
                self.sleep_until_stop_event(remaining_time)

        print("play_sequence スレッドが停止しました。")

    def delayed_play_vibration(self, delay, device_index, location, channel):
        if delay > 0:
            self.sleep_until_stop_event(delay)
            if self.stop_event.is_set():
                return
        if not self.stop_event.is_set():
            self.play_vibration(device_index, location, channel)

    def on_closing(self):
        print("プログラムを終了します...")
        self.stop_event.set()
        self.play_thread.join()
        self.root.destroy()

if __name__ == '__main__':
    player = SoundPlayer()
