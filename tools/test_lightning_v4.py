#!/usr/bin/env python3
"""
基于之前的用户反馈：skip4_8000hz.wav听起来更舒服
尝试跳过不同字节数的头部，使用8-bit PCM @ 8000Hz
"""
import struct
import os
import wave

def write_wav(filepath, sample_rate, data, sample_width=2):
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sample_path = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_correct', 'lightning_6359.bin')
    
    with open(sample_path, 'rb') as f:
        sample_data = f.read()
    
    print(f"样本数据大小: {len(sample_data)} 字节")
    print(f"样本前32字节: {sample_data[:32].hex(' ')}")
    
    output_dir = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_v4')
    os.makedirs(output_dir, exist_ok=True)
    
    # 尝试跳过不同字节数
    for skip in [0, 4, 8, 12, 16, 20, 24, 32]:
        audio = sample_data[skip:]
        
        # 8-bit unsigned PCM @ 8000Hz
        write_wav(os.path.join(output_dir, f'skip{skip}_8bit_8000hz.wav'), 8000, audio, 1)
        
        # 8-bit signed PCM @ 8000Hz
        signed = bytes([(b - 128) % 256 for b in audio])
        write_wav(os.path.join(output_dir, f'skip{skip}_signed8_8000hz.wav'), 8000, signed, 1)
        
        # 8-bit @ 11025Hz
        write_wav(os.path.join(output_dir, f'skip{skip}_8bit_11025hz.wav'), 11025, audio, 1)
        
        # 8-bit @ 16000Hz
        write_wav(os.path.join(output_dir, f'skip{skip}_8bit_16000hz.wav'), 16000, audio, 1)
        
        print(f"跳过{skip}字节: 剩余{len(audio)}字节")
    
    # 重点: 尝试将样本数据作为差分值解码
    print(f"\n--- 差分编码测试 ---")
    for skip in [0, 4, 8, 16]:
        audio = sample_data[skip:]
        # 累积差分解码
        decoded = bytearray([audio[0]])
        for i in range(1, len(audio)):
            val = (decoded[-1] + audio[i]) % 256
            decoded.append(val)
        decoded = bytes(decoded)
        
        write_wav(os.path.join(output_dir, f'cumulative_skip{skip}_8000hz.wav'), 8000, decoded, 1)
        write_wav(os.path.join(output_dir, f'cumulative_skip{skip}_11025hz.wav'), 11025, decoded, 1)
    
    print(f"\n生成文件到: {output_dir}")
    print("\n推荐试听 (基于之前用户反馈):")
    print("  skip4_8bit_8000hz.wav")
    print("  skip4_signed8_8000hz.wav")
    print("  skip4_8bit_11025hz.wav")
    print("  skip0_8bit_8000hz.wav")

if __name__ == '__main__':
    main()
