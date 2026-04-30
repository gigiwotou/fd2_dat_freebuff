#!/usr/bin/env python3
"""
检查WAV文件内容和生成测试音调
"""

import wave
import struct
import math
import os
import tempfile
import time

wav_path = os.path.join(tempfile.gettempdir(), "fd2_track.wav")

# 检查文件
if os.path.exists(wav_path):
    with wave.open(wav_path, 'rb') as wf:
        print(f"WAV文件: {wav_path}")
        print(f"  文件大小: {os.path.getsize(wav_path)} bytes")
        print(f"  声道数: {wf.getnchannels()}")
        print(f"  采样率: {wf.getframerate()}")
        print(f"  位深度: {wf.getsampwidth() * 8} bits")
        print(f"  总帧数: {wf.getnframes()}")
        print(f"  时长: {wf.getnframes() / wf.getframerate():.2f} 秒")
        
        # 读取前100个样本检查内容
        samples = []
        for i in range(min(100, wf.getnframes())):
            frame = wf.readframes(1)
            val = struct.unpack('<h', frame)[0]
            samples.append(val)
        
        max_val = max(abs(v) for v in samples) if samples else 0
        print(f"  前100样本最大值: {max_val}")
        
        if max_val == 0:
            print("  警告: 样本全部为零，没有声音!")
        else:
            print("  文件包含有效音频数据")
else:
    print("WAV文件不存在")

# 生成一个简单的测试音调（440Hz正弦波）
print("\n生成440Hz测试音调...")
sample_rate = 44100
duration = 2.0
freq = 440.0

test_wav = os.path.join(tempfile.gettempdir(), "test_tone.wav")
with wave.open(test_wav, 'w') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
        wf.writeframes(struct.pack('<h', val))

print(f"测试音调已生成: {test_wav}")
print(f"  文件大小: {os.path.getsize(test_wav)} bytes")
print(f"  时长: {duration}秒")
print(f"  频率: {freq}Hz")

print("\n播放测试音调...")
os.startfile(test_wav)
time.sleep(3)
print("测试完成")
