#!/usr/bin/env python3
"""
res78闪电音效最终测试 - 基于IDA精确分析

样本数据: raw[0:6359] (6359字节)
尝试所有合理的解码组合
"""
import struct
import os
import wave
import math

# 加载FDOTHER.DAT
dat_path = os.path.join('game', 'FDOTHER.DAT')
with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    f.seek(0x0A)
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    idx = 78
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
    f.seek(start)
    raw = f.read(end - start)

# 提取样本
sample_start = struct.unpack_from('<I', raw, 6)[0]
sample_size = struct.unpack_from('<I', raw, 10)[0] - sample_start

print(f"res78总大小: {len(raw)}")
print(f"样本起始: {sample_start}")
print(f"样本大小: {sample_size}")

# 直接使用整个res78数据作为测试（因为sample_start=0）
sample_data = raw[:sample_size] if sample_start == 0 else raw[sample_start:sample_start+sample_size]

out_dir = 'output/sfx_wav/res078_lightning_final'
os.makedirs(out_dir, exist_ok=True)

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename} ({len(pcm_data)} bytes, {sample_rate}Hz)")

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

def apply_lowpass_filter(pcm_data, cutoff_ratio=0.3):
    """简单的低通滤波器，减少高频噪音"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    filtered = list(samples)
    
    # 简单的移动平均滤波
    window = 3
    for i in range(window, len(samples) - window):
        filtered[i] = int(sum(samples[i-window:i+window+1]) / (2*window + 1))
    
    return b''.join(struct.pack('<h', s) for s in filtered)

def apply_envelope(pcm_data, attack_ms=50, release_ms=200, sample_rate=22050):
    """应用包络线，使声音更像闪电"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    attack_samples = int(attack_ms * sample_rate / 1000)
    release_samples = int(release_ms * sample_rate / 1000)
    
    enveloped = list(samples)
    for i in range(len(samples)):
        if i < attack_samples:
            envelope = i / attack_samples
        elif i > len(samples) - release_samples:
            envelope = (len(samples) - i) / release_samples
        else:
            envelope = 1.0
        enveloped[i] = int(samples[i] * envelope)
    
    return b''.join(struct.pack('<h', s) for s in enveloped)

print("\n=== 测试组合 ===")

# 1. 8-bit PCM
print("\n--- 8-bit PCM ---")
for sr in [4000, 5512, 8000, 11025, 16000, 22050]:
    pcm = bytes([b ^ 0x80 for b in sample_data])
    save_wav(pcm, sr, f'{out_dir}/8bit_{sr}hz.wav')

# 2. IMA ADPCM
print("\n--- IMA ADPCM ---")
for sr in [4000, 5512, 8000, 11025, 16000, 22050]:
    for pred in [0, 128, 256, 512, 1024]:
        pcm = ima_adpcm_decode(sample_data, pred, 0)
        save_wav(pcm, sr, f'{out_dir}/adpcm_p{pred}_{sr}hz.wav')

# 3. 带滤波的IMA ADPCM
print("\n--- IMA ADPCM + 低通滤波 ---")
for sr in [8000, 11025, 22050]:
    pcm = ima_adpcm_decode(sample_data, 0, 0)
    filtered = apply_lowpass_filter(pcm)
    save_wav(filtered, sr, f'{out_dir}/adpcm_filtered_{sr}hz.wav')

# 4. 带包络的IMA ADPCM
print("\n--- IMA ADPCM + 包络 ---")
for sr in [8000, 11025, 22050]:
    pcm = ima_adpcm_decode(sample_data, 0, 0)
    enveloped = apply_envelope(pcm, 50, 200, sr)
    save_wav(enveloped, sr, f'{out_dir}/adpcm_envelope_{sr}hz.wav')

# 5. 16-bit PCM
print("\n--- 16-bit PCM ---")
for sr in [8000, 11025, 16000, 22050]:
    for endian in ['little', 'big']:
        data = sample_data[:len(sample_data)//2*2]
        fmt = f'<{len(data)//2}h' if endian == 'little' else f'>{len(data)//2}h'
        samples = struct.unpack(fmt, data)
        pcm = b''.join(struct.pack('<h', s) for s in samples)
        save_wav(pcm, sr, f'{out_dir}/16bit_{endian}_{sr}hz.wav')

print(f"\n完成! 所有文件保存到 {out_dir}/")
print("\n建议试听顺序:")
print("1. adpcm_p0_8000hz.wav")
print("2. adpcm_p0_11025hz.wav") 
print("3. adpcm_filtered_8000hz.wav")
print("4. 8bit_8000hz.wav")
print("5. adpcm_envelope_8000hz.wav")
