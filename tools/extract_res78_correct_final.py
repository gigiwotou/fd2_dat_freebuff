#!/usr/bin/env python3
"""
res78闪电音效正确解码

res78头部结构:
- offset[0]: WORD = 2 (样本数量)
- offset[2]: WORD = 2 (未知)
- offset[4]: DWORD = 0 (保留)
- offset[8]: DWORD = 16 (第一个样本偏移)
- offset[12]: DWORD = 6359 (样本结束位置)

样本数据: raw[16:16+6359] = raw[16:6375]
"""
import struct
import os
import wave

dat_path = os.path.join('game', 'FDOTHER.DAT')

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offset_table_start = 0x0A
offsets = []
for i in range(count):
    offsets.append(struct.unpack_from('<I', data, offset_table_start + i*4)[0])

idx = 78
res78_start = offsets[idx]
res78_end = offsets[idx + 1] if idx + 1 < count else len(data)
res78 = data[res78_start:res78_end]

# 解析头部
sample_count = struct.unpack_from('<H', res78, 0)[0]
sample_offset = struct.unpack_from('<I', res78, 8)[0]
sample_end = struct.unpack_from('<I', res78, 12)[0]
sample_size = sample_end - sample_offset

print(f"res78: {len(res78)} bytes")
print(f"样本数量: {sample_count}")
print(f"样本偏移: {sample_offset}")
print(f"样本结束: {sample_end}")
print(f"样本大小: {sample_size}")

# 提取样本数据
sample_data = res78[sample_offset:sample_offset + sample_size]
print(f"实际提取样本大小: {len(sample_data)}")

# 保存原始样本
os.makedirs('output/sfx_wav/res078_correct', exist_ok=True)
with open(f'output/sfx_wav/res078_correct/sample0.bin', 'wb') as f:
    f.write(sample_data)

print(f"\n样本数据前32字节: {sample_data[:32].hex()}")

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)

def ima_adpcm_decode(data, initial_predictor=0, initial_index=0):
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
    
    for byte in data:
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
            output.append(struct.pack('<h', predictor))
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return b''.join(output)

print("\n=== 解码测试 ===")

# 1. 8-bit PCM
print("\n--- 8-bit PCM ---")
for sr in [4000, 5512, 8000, 11025, 16000, 22050]:
    pcm = bytes([b ^ 0x80 for b in sample_data])
    save_wav(pcm, sr, f'output/sfx_wav/res078_correct/8bit_{sr}hz.wav')
    print(f"  8bit_{sr}hz.wav")

# 2. IMA ADPCM
print("\n--- IMA ADPCM ---")
for sr in [4000, 5512, 8000, 11025, 16000, 22050]:
    for pred in [0, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]:
        for idx in [0, 16, 32, 48, 64]:
            pcm = ima_adpcm_decode(sample_data, pred, idx)
            save_wav(pcm, sr, f'output/sfx_wav/res078_correct/adpcm_p{pred}_i{idx}_{sr}hz.wav')

# 3. 16-bit PCM
print("\n--- 16-bit PCM ---")
for sr in [8000, 11025, 16000, 22050]:
    for endian in ['little', 'big']:
        raw_data = sample_data[:len(sample_data)//2*2]
        fmt = f'<{len(raw_data)//2}h' if endian == 'little' else f'>{len(raw_data)//2}h'
        samples = struct.unpack(fmt, raw_data)
        pcm = b''.join(struct.pack('<h', s) for s in samples)
        save_wav(pcm, sr, f'output/sfx_wav/res078_correct/16bit_{endian}_{sr}hz.wav')

print(f"\n完成! 文件保存到 output/sfx_wav/res078_correct/")
print("\n重点试听:")
print("  - 8bit_8000hz.wav")
print("  - 8bit_11025hz.wav")
print("  - adpcm_p0_i0_8000hz.wav")
print("  - adpcm_p0_i0_11025hz.wav")
print("  - 16bit_little_8000hz.wav")
print("  - 16bit_big_8000hz.wav")
