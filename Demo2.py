import sounddevice as sd
import numpy as np
import soundfile as sf
import time
from concurrent.futures import ThreadPoolExecutor
import socket

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

device_index_foot = 11  # 適切なデバイスインデックスを設定
device_index_a = 10      # 適切なデバイスインデックスを設定
device_index_b = 13     # 適切なデバイスインデックスを設定

# Define the sound functions
def play_footstep():
    try:
        with sd.OutputStream(device=device_index_foot, samplerate=fs, channels=len(foot_audiodata.shape), dtype='float32') as stream:
            stream.write(foot_audiodata)
    except Exception as e:
        print(f"Error playing footstep sound: {e}")

def play_sound_a_left():
    try:
        with sd.OutputStream(device=device_index_a, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(left_channel_data)
    except Exception as e:
        print(f"Error playing sound A left: {e}")

def play_sound_a_right():
    try:
        with sd.OutputStream(device=device_index_a, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(right_channel_data)
    except Exception as e:
        print(f"Error playing sound A right: {e}")

def play_sound_b_left():
    try:
        with sd.OutputStream(device=device_index_b, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(left_channel_data)
    except Exception as e:
        print(f"Error playing sound B left: {e}")

def play_sound_b_right():
    try:
        with sd.OutputStream(device=device_index_b, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(right_channel_data)
    except Exception as e:
        print(f"Error playing sound B right: {e}")

# Socket server to listen to Unity
def start_server():
    host = '127.0.0.1'  # Localhost
    port = 65432        # Port to listen on

    step_count = 0  # ステップのカウント

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("Waiting for Unity connection...")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            with ThreadPoolExecutor() as executor:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    message = data.decode()
                    if message == 'step':
                        step_count += 1
                        # 偶数ステップと奇数ステップで再生するサウンドを切り替える
                        if step_count % 2 == 1:
                            # 奇数ステップ
                            executor.submit(play_footstep)
                            executor.submit(play_sound_a_left)
                            time.sleep(0.15)
                            executor.submit(play_sound_a_right)
                            time.sleep(0.7)
                        else:
                            # 偶数ステップ
                            executor.submit(play_footstep)
                            executor.submit(play_sound_b_right)
                            time.sleep(0.15)
                            executor.submit(play_sound_b_left)
                            time.sleep(0.7)
                    elif message == 'exit':
                        print("Shutting down server")
                        break

if __name__ == '__main__':
    start_server()
