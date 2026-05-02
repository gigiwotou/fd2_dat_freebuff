#!/usr/bin/env python3
"""
根据DOSBox日志重新生成闪电音效
关键发现:
- 采样率: 11111 Hz (从DOSBox日志获取)
- 编码格式: 8-bit PCM Mono (不是IMA ADPCM!)
- 样本大小: 6359 bytes (从res78头部获取)
- 时长: 6359 / 11111 ≈ 0.57秒
"""
import struct
import os
import numpy as np

def main():
    # 读取res78样本数据
    with open('game/FDOTHER.DAT', 'rb') as f:
        f.read(10)
        offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(200)]
        f.seek(offsets[78])
        res78 = f.read(6801)
    
    sample_size = struct.unpack_from('<I', res78, 12)[0]  # 6359
    sample_start = struct.unpack_from('<I', res78, 8)[0]  # 16
    sample_data = res78[sample_start:sample_start + sample_size]
    
    print(f"res78样本数据: {len(sample_data)} bytes")
    print(f"DOSBox日志显示: 8-bit PCM @ 11111 Hz")
    
    # 创建输出目录
    output_dir = 'output/sfx_wav/res078_dosbox'
    os.makedirs(output_dir, exist_ok=True)
    
    # 8-bit PCM直接转为WAV (需要添加128偏移)
    pcm8 = np.frombuffer(sample_data, dtype=np.uint8).astype(np.int16) - 128
    
    # 生成WAV
    sample_rate = 11111
    duration = len(sample_data) / sample_rate
    print(f"时长: {duration:.3f} 秒")
    
    pcm_bytes = (pcm8 + 128).astype(np.uint8).tobytes()
    byte_rate = sample_rate * 1 * 8 // 8
    block_align = 1 * 8 // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(pcm_bytes), b'WAVE', b'fmt ',
        16, 1, 1, sample_rate, byte_rate, block_align,
        8, b'data', len(pcm_bytes))
    
    wav_data = header + pcm_bytes
    filename = 'thunder_11111hz_8bit.wav'
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(wav_data)
    
    print(f"生成: {filename}")
    print(f"文件已保存到: {output_dir}")
    
    # 也生成16-bit版本便于对比
    pcm16 = pcm8.astype(np.int16)
    wav16 = create_wav_16bit(pcm16, sample_rate)
    filename16 = 'thunder_11111hz_16bit.wav'
    filepath16 = os.path.join(output_dir, filename16)
    with open(filepath16, 'wb') as f:
        f.write(wav16)
    print(f"生成: {filename16}")

def create_wav_16bit(pcm_data, sample_rate):
    pcm_bytes = pcm_data.astype(np.int16).tobytes()
    byte_rate = sample_rate * 1 * 16 // 8
    block_align = 1 * 16 // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(pcm_bytes), b'WAVE', b'fmt ',
        16, 1, 1, sample_rate, byte_rate, block_align,
        16, b'data', len(pcm_bytes))
    
    return header + pcm_bytes

if __name__ == '__main__':
    main()