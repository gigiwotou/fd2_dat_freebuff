#!/usr/bin/env python3
"""
重新分析res78头部结构
res78: 0200 0200 0000 0000 1000 0000 d718 0000
可能的结构:
- WORD[0] = 2
- WORD[2] = 2  
- DWORD[4] = 0
- DWORD[8] = 0x10 (16) ← 可能是样本数据起始偏移
- DWORD[12] = 0x18d7 (6359) ← 样本大小
"""
import struct
import os
import sys
import numpy as np

def ima_adpcm_decode(adpcm_data, initial_predictor=0, initial_index=0):
    """IMA ADPCM 4-bit 解码"""
    IMA_STEP_TABLE = [
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34,
        37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
        157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494,
        544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552,
        1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428,
        4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
        12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
        29794, 32767
    ]
    IMA_INDEX_TABLE = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
    
    output = []
    predictor = initial_predictor
    index = initial_index
    
    for byte in adpcm_data:
        for nibble in [(byte >> 4) & 0x0F, byte & 0x0F]:
            step = IMA_STEP_TABLE[index]
            delta = 0
            if nibble & 0x04: delta += step
            if nibble & 0x02: delta += step >> 1
            if nibble & 0x01: delta += step >> 2
            delta += step >> 3
            
            if nibble & 0x08:
                predictor -= delta
            else:
                predictor += delta
            
            predictor = max(-32768, min(32767, predictor))
            output.append(predictor)
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return np.array(output, dtype=np.int16)

def create_wav(pcm_data, sample_rate, channels=1, bits_per_sample=16):
    """创建WAV文件"""
    pcm_bytes = pcm_data.astype(np.int16).tobytes()
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(pcm_bytes), b'WAVE', b'fmt ',
        16, 1, channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b'data', len(pcm_bytes))
    
    return header + pcm_bytes

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT")
        sys.exit(1)
    
    with open(fdother_path, 'rb') as f:
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        f.seek(10)
        offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(count)]
    
    idx = 78
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
    size = end - start
    
    with open(fdother_path, 'rb') as f:
        f.seek(start)
        res78 = f.read(size)
    
    print(f"res78总大小: {size} bytes")
    print(f"res78完整头部 (32字节):")
    for i in range(0, 32, 4):
        val = struct.unpack_from('<I', res78, i)[0]
        print(f"  +{i:02x}: {val:10d} (0x{val:08x})")
    
    print(f"\nres78前16字节 (十六进制):")
    print(f"  {' '.join(f'{b:02x}' for b in res78[:16])}")
    
    # 解析头部
    sample_start_offset = struct.unpack_from('<I', res78, 8)[0]   # 0x10 = 16
    sample_size = struct.unpack_from('<I', res78, 12)[0]          # 0x18d7 = 6359
    
    print(f"\n头部解析:")
    print(f"  样本起始偏移: +{sample_start_offset} (0x{sample_start_offset:x})")
    print(f"  样本大小: {sample_size} (0x{sample_size:x})")
    
    # 从正确位置提取样本
    sample_data = res78[sample_start_offset:sample_start_offset + sample_size]
    print(f"  实际样本数据: {len(sample_data)} bytes")
    print(f"  样本前16字节: {sample_data[:16].hex()}")
    
    # 计算时长
    sample_rates = [3906, 5512, 8000, 11025, 16000, 22050]
    print(f"\n时长分析:")
    for rate in sample_rates:
        duration_adpcm = (len(sample_data) * 2) / rate
        duration_8bit = len(sample_data) / rate
        duration_16bit = (len(sample_data) // 2) / rate
        print(f"  @{rate}Hz: ADPCM={duration_adpcm:.2f}s, 8bit={duration_8bit:.2f}s, 16bit={duration_16bit:.2f}s")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'sfx_wav', 'res078_ida_v4')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n生成WAV文件...")
    
    # IMA ADPCM @ 不同采样率
    pcm = ima_adpcm_decode(sample_data, 0, 0)
    for rate in sample_rates:
        wav = create_wav(pcm, rate)
        filename = f"adpcm_{rate}hz.wav"
        with open(os.path.join(output_dir, filename), 'wb') as f:
            f.write(wav)
        print(f"  生成: {filename} ({len(pcm)/rate:.2f}s)")
    
    # 8-bit PCM @ 不同采样率
    pcm8 = np.frombuffer(sample_data, dtype=np.uint8).astype(np.int16) - 128
    for rate in sample_rates:
        wav = create_wav(pcm8, rate, bits_per_sample=8)
        filename = f"pcm8_{rate}hz.wav"
        with open(os.path.join(output_dir, filename), 'wb') as f:
            f.write(wav)
        print(f"  生成: {filename} ({len(pcm8)/rate:.2f}s)")
    
    # 16-bit PCM @ 不同采样率
    pcm16 = np.frombuffer(sample_data[:len(sample_data)//2*2], dtype='<i2')
    for rate in sample_rates:
        wav = create_wav(pcm16, rate)
        filename = f"pcm16le_{rate}hz.wav"
        with open(os.path.join(output_dir, filename), 'wb') as f:
            f.write(wav)
        print(f"  生成: {filename} ({len(pcm16)/rate:.2f}s)")
    
    print(f"\n所有文件已保存到: {output_dir}")

if __name__ == '__main__':
    main()