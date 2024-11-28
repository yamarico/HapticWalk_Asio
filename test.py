import sounddevice as sd
import numpy as np
import soundfile as sf
import time
from concurrent.futures import ThreadPoolExecutor

fs = 44100
sd.default.samplerate = fs

# footStep.mp3の読み込み
file_path = "footStep.mp3"  # 音声ファイルのパス
foot_audiodata, fs = sf.read(file_path, dtype='float32')

# 音声データを生成
duration = 0.1  # 再生時間（秒）
frequency = 70  # 音の周波数（Hz）
t = np.linspace(0, duration, int(fs * duration), endpoint=False)
amplitude = 1.0  # 音量（0.0~1.0の範囲で設定）
myarray = amplitude * np.sin(2 * np.pi * frequency * t).astype('float32')

right_channel_data = np.column_stack((np.zeros_like(myarray), myarray))  # 左チャンネル無音、右チャンネルに音声
left_channel_data = np.column_stack((myarray, np.zeros_like(myarray)))  # 右チャンネル無音、左チャンネルに音声

# 使用可能なデバイスの一覧を表示
print(sd.query_devices())

device_index_foot = 3 # 適切なデバイスインデックスを設定
device_index_a =  13 # 適切なデバイスインデックスを設定
device_index_b = 10  # 適切なデバイスインデックスを設定

# 音を出す関数
def play_footstep():
    try:
        # 音声を再生
        with sd.OutputStream(device=device_index_foot, samplerate=fs, channels=len(foot_audiodata.shape), dtype='float32') as stream:
            stream.write(foot_audiodata)
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_a_right():
    try:
        # 音声を再生
        with sd.OutputStream(device=device_index_a, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(right_channel_data)  # 左チャンネルで音声を再生
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_a_left():
    try:
        # 音声を再生
        with sd.OutputStream(device=device_index_a, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(left_channel_data)  # 左チャンネルで音声を再生
    except Exception as e:
        print(f"Error playing sound: {e}")


def play_sound_b_right():
    try:
        # 音声を再生
        with sd.OutputStream(device=device_index_b, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(right_channel_data)  # 左チャンネルで音声を再生
    except Exception as e:
        print(f"Error playing sound: {e}")

def play_sound_b_left():
    try:
        # 音声を再生
        with sd.OutputStream(device=device_index_b, samplerate=fs, channels=2, dtype='float32') as stream:
            stream.write(left_channel_data)  # 左チャンネルで音声を再生
    except Exception as e:
        print(f"Error playing sound: {e}")


def play_sequence(lag1, lag2):
    with ThreadPoolExecutor() as executor:
        while True:
 # 右脚 - 足音と音を同時に再生
            executor.submit(play_footstep)
            executor.submit(play_sound_a_left)
            time.sleep(lag1)
            executor.submit(play_sound_a_right)
            time.sleep(lag2)

            # 左脚 - 足音と音を同時に再生
            executor.submit(play_footstep)
            executor.submit(play_sound_b_right)
            time.sleep(lag1)
            executor.submit(play_sound_b_left)  # 左側の音声を同時に実行
            time.sleep(lag2)

# 使用例
if __name__ == '__main__':
    lag1 = 0.15  # 1秒のラグ
    lag2 = 0.7 # 1.5秒のラグ
    play_sequence(lag1, lag2)