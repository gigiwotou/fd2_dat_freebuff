#!/usr/bin/env python3
"""
多种方法播放WAV文件 - 确保音频能正常输出
"""

import wave
import struct
import math
import os
import tempfile
import time
import subprocess
from pathlib import Path

# 方法1: 使用Windows MediaPlayer
def play_with_mplayer(filepath):
    try:
        print("方法1: 使用wmplayer...")
        subprocess.Popen(['wmplayer', filepath], shell=True)
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False

# 方法2: 使用PowerShell
def play_with_powershell(filepath):
    try:
        print("方法2: 使用PowerShell...")
        cmd = f'powershell -c "(New-Object Media.SoundPlayer \'{filepath}\').PlaySync()"'
        subprocess.run(cmd, shell=True, timeout=5)
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False

# 方法3: 使用ctypes调用Windows API
def play_with_winapi(filepath):
    try:
        import ctypes
        import ctypes.wintypes
        
        winmm = ctypes.windll.winmm
        result = winmm.PlaySoundW(filepath, 0x0001)  # SND_FILENAME
        if result:
            print("方法3: 使用Windows API成功")
            return True
        else:
            print("方法3: Windows API返回失败")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def main():
    # 首先生成一个简单的测试音调
    print("生成1秒 440Hz测试音调...")
    sample_rate = 44100
    duration = 1.0
    freq = 440.0
    
    test_wav = os.path.join(tempfile.gettempdir(), "simple_test.wav")
    with wave.open(test_wav, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            # 简单正弦波
            val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack('<h', val))
    
    print(f"测试文件: {test_wav}")
    print(f"文件大小: {os.path.getsize(test_wav)} bytes")
    
    print("\n尝试不同播放方法:")
    print("="*50)
    
    # 尝试所有方法
    methods = [
        play_with_winapi,
        play_with_powershell,
        play_with_mplayer,
    ]
    
    for method in methods:
        print(f"\n尝试: {method.__name__}")
        success = method(test_wav)
        if success:
            print("播放成功!")
            time.sleep(2)
            break
        else:
            print("播放失败")
    
    # 检查系统音频
    print("\n" + "="*50)
    print("如果以上方法都失败，请检查:")
    print("1. 系统音量是否静音")
    print("2. 扬声器/耳机是否正常连接")
    print("3. 尝试播放其他音频文件")
    print("4. 重启音频服务")

if __name__ == "__main__":
    main()
