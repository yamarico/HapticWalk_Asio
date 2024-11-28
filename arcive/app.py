import sounddevice as sd
import numpy as np

fs = 44100
sd.default.samplerate = fs

# 音声データを生成
duration = 1  # 再生時間（秒）
frequency = 440  # 音の周波数（Hz）
t = np.linspace(0, duration, int(fs * duration), endpoint=False)
amplitude = 0.5  # 音量（0.0から1.0の範囲で設定）
myarray = amplitude * np.sin(2 * np.pi * frequency * t).astype('float32')

# 使用可能なデバイスの一覧を表示
print(sd.query_devices())

# デバイス28で通常の音声を再生
device_22 = 11  # 適切なインデックスを設定
sd.default.device = device_22
sd.default.dtype = 'float32'

# デバイス14で左チャンネルを無音にして右チャンネルに音声を送信
device_15 = 7  # 適切なインデックスを設定
right_channel_data = np.column_stack((np.zeros_like(myarray), myarray))  # 左チャンネル無音、右チャンネルに音声
left_channel_data = np.column_stack((myarray, np.zeros_like(myarray)))

# デバイス14で左チャンネルを無音にして右チャンネルに音声を送信
device_64 = 9  # 適切なインデックスを設定
right_channel_data = np.column_stack((np.zeros_like(myarray), myarray))  # 左チャンネル無音、右チャンネルに音声
left_channel_data = np.column_stack((myarray, np.zeros_like(myarray)))

# デバイス28で音声を再生
with sd.OutputStream(device=device_22, samplerate=fs, channels=2, dtype='float32') as stream:
    stream.write(np.column_stack((myarray, myarray)))

# 再生終了まで待機
sd.wait()

# デバイス14で音声を再生
with sd.OutputStream(device=device_15, samplerate=fs, channels=2, dtype='float32') as stream:
    stream.write(right_channel_data)
    


# 再生終了まで待機
sd.wait()

# デバイス14で音声を再生

    
with sd.OutputStream(device=device_64, samplerate=fs, channels=2, dtype='float32') as stream:
    stream.write(left_channel_data)

# 再生終了まで待機
sd.wait()
