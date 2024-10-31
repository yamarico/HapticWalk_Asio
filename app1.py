import sounddevice as sd
import numpy as np
import soundfile as sf
import time
from concurrent.futures import ThreadPoolExecutor
import socket
import threading

fs = 44100
sd.default.samplerate = fs

# Load footStep.mp3
file_path = "footStep.mp3"
foot_audiodata, fs = sf.read(file_path, dtype='float32')

duration = 0.1  # Duration in seconds
frequency = 70  # Frequency of the sound (Hz)
t = np.linspace(0, duration, int(fs * duration), endpoint=False)
amplitude = 1.0
myarray = amplitude * np.sin(2 * np.pi * frequency * t).astype('float32')

right_channel_data = np.column_stack((np.zeros_like(myarray), myarray))
left_channel_data = np.column_stack((myarray, np.zeros_like(myarray)))

device_index_foot = 3 # 適切なデバイスインデックスを設定
device_index_a =  6 # 適切なデバイスインデックスを設定
device_index_b = 9  # 適切なデバイスインデックスを設定

# Define the sound functions
def play_footstep():
    try:
        with sd.OutputStream(device=device_index_foot, samplerate=fs, channels=len(foot_audiodata.shape), dtype='float32') as stream:
            stream.write(foot_audiodata)
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_a_right():
    try:
        with sd.OutputStream(device=device_index_a, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(right_channel_data)
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_a_left():
    try:
        with sd.OutputStream(device=device_index_a, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(left_channel_data)
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_b_right():
    try:
        with sd.OutputStream(device=device_index_b, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(right_channel_data)
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_b_left():
    try:
        with sd.OutputStream(device=device_index_b, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(left_channel_data)
    except Exception as e:
        print(f"Error playing sound: {e}")

# Play sequence function with stop control
def play_sequence(lag1, lag2, stop_event):
    with ThreadPoolExecutor() as executor:
        while not stop_event.is_set():  # Unityから「stop」が来るまでループ
            executor.submit(play_footstep)
            executor.submit(play_sound_a_left)
            time.sleep(lag1)
            executor.submit(play_sound_a_right)
            time.sleep(lag2)

            executor.submit(play_footstep)
            executor.submit(play_sound_b_right)
            time.sleep(lag1)
            executor.submit(play_sound_b_left)
            time.sleep(lag2)

# Socket server to listen to Unity
def start_server():
    host = '127.0.0.1'  # Localhost
    port = 65432  # Port to listen on
    stop_event = threading.Event()  # 停止のためのイベント
    play_thread = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("Waiting for Unity connection...")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode()
                if message == 'start':
                    if play_thread is None or not play_thread.is_alive():
                        # 新しいスレッドでplay_sequenceを実行
                        stop_event.clear()  # stop_eventをリセット
                        play_thread = threading.Thread(target=play_sequence, args=(0.15, 0.7, stop_event))
                        play_thread.start()
                elif message == 'stop':
                    if play_thread is not None and play_thread.is_alive():
                        stop_event.set()  # スレッドを停止
                        play_thread.join()  # スレッドが完全に終了するまで待機
                    print("Stopped sequence")
                elif message == 'exit':
                    # サーバーの終了
                    if play_thread is not None and play_thread.is_alive():
                        stop_event.set()
                        play_thread.join()
                    print("Shutting down server")
                    break

if __name__ == '__main__':
    start_server()
