#!/usr/bin/env python3
"""
尝试Miles Sound System支持的多种音频格式

Miles AIL库常见支持的格式:
1. 8-bit unsigned PCM
2. 16-bit signed PCM (little-endian)
3. IMA ADPCM 4-bit
4. DSP ADPCM
"""
import struct
import os
import wave

# 加载样本
with open('output/sfx_wav/res078_lightning/sample_raw.bin', 'rb') as f:
    sample = f.read()

# 前16字节是头部
header = sample[:16]
data = sample[16:]

print(f"样本头部: {header.hex()}")
print(f"  *(0) = {struct.unpack_from('<I', header, 0)[0]}")  # 可能是样本数量
print(f"  *(4) = {struct.unpack_from('<I', header, 4)[0]}")  # 可能是保留
print(f"  *(8) = {struct.unpack_from('<I', header, 8)[0]}")  # 可能是第一个样本偏移
print(f"  *(12) = {struct.unpack_from('<I', header, 12)[0]}") # 可能是样本大小

# 尝试从偏移16开始作为样本数据
# 或者从偏移0x2C (44)开始，这是样本数据的实际位置

# 检查偏移0x2C之后的数据
print(f"\n偏移0x2C处的数据:")
offset_2c = sample[0x2C:0x2C+32]
print(f"  {offset_2c.hex()}")

# Miles Sound System的sample通常有特定的头部
# 让我们尝试不同的样本起始点

out_dir = 'output/sfx_wav/res078_miles'
os.makedirs(out_dir, exist_ok=True)

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

# 尝试不同的样本起始位置
sample_starts = [0, 4, 8, 16, 44]  # 44 = 0x2C

for start in sample_starts:
    if start >= len(sample):
        continue
    
    s_data = sample[start:]
    print(f"\n--- 样本起始偏移: {start} ---")
    print(f"  数据大小: {len(s_data)}")
    print(f"  前16字节: {s_data[:16].hex()}")
    
    # 8-bit PCM
    for sr in [5512, 8000, 11025]:
        pcm = bytes([b ^ 0x80 for b in s_data])
        save_wav(pcm, sr, f'{out_dir}/8bit_skip{start}_{sr}hz.wav')
    
    # IMA ADPCM
    for sr in [5512, 8000, 11025]:
        for pred in [0, 128, 1024]:
            pcm = ima_adpcm_decode(s_data, pred, 0)
            save_wav(pcm, sr, f'{out_dir}/adpcm_skip{start}_p{pred}_{sr}hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
