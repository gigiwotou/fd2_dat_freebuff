#!/usr/bin/env python3
"""
深度分析res78原始数据
尝试所有可能的音频编码格式
"""
import struct
import os
import wave
import numpy as np

def load_res78():
    dat_path = os.path.join('game', 'FDOTHER.DAT')
    with open(dat_path, 'rb') as f:
        f.seek(0x10)  # header offset
        table_offset = struct.unpack_from('<I', f.read(4), 0)[0]
        
        f.seek(table_offset + 78 * 8)
        res_offset = struct.unpack_from('<I', f.read(4), 0)[0]
        res_size = struct.unpack_from('<I', f.read(4), 0)[0]
        
        f.seek(res_offset)
        raw = f.read(res_size)
    
    return raw, res_size

def save_wav(filename, pcm_data, sample_rate=22050, sample_width=2):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename} ({len(pcm_data)} bytes, {sample_rate}Hz)")

def analyze_byte_distribution(data, name="data"):
    print(f"\n=== {name} 字节分布分析 ===")
    print(f"总大小: {len(data)} bytes")
    
    if len(data) == 0:
        return
    
    # 前64字节
    print(f"前64字节 (hex):")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # 统计信息
    byte_values = list(data)
    print(f"\n统计信息:")
    print(f"  最小值: {min(byte_values)} (0x{min(byte_values):02x})")
    print(f"  最大值: {max(byte_values)} (0x{max(byte_values):02x})")
    print(f"  平均值: {sum(byte_values)/len(byte_values):.1f}")
    print(f"  中位数: {sorted(byte_values)[len(byte_values)//2]}")
    
    # 高位/低位分析（针对4-bit ADPCM）
    high_nibbles = [(b >> 4) & 0x0F for b in data]
    low_nibbles = [b & 0x0F for b in data]
    
    print(f"\nNibble分布:")
    print(f"  高4位范围: {min(high_nibbles)} - {max(high_nibbles)}")
    print(f"  低4位范围: {min(low_nibbles)} - {max(low_nibbles)}")
    
    # 检查是否像8-bit PCM
    zero_crossings = sum(1 for i in range(1, len(data)) if (data[i] > 128) != (data[i-1] > 128))
    print(f"  8-bit PCM零交叉率: {zero_crossings/len(data)*100:.1f}%")
    
    # 检查相邻字节差值（针对16-bit PCM）
    if len(data) >= 4:
        # 尝试16-bit LE
        samples_le = struct.unpack_from(f'<{len(data)//2}h', data, 0)
        diffs_le = [abs(samples_le[i] - samples_le[i-1]) for i in range(1, min(1000, len(samples_le)))]
        avg_diff_le = sum(diffs_le) / len(diffs_le) if diffs_le else 0
        
        # 尝试16-bit BE
        samples_be = struct.unpack_from(f'>{len(data)//2}h', data, 0)
        diffs_be = [abs(samples_be[i] - samples_be[i-1]) for i in range(1, min(1000, len(samples_be)))]
        avg_diff_be = sum(diffs_be) / len(diffs_be) if diffs_be else 0
        
        print(f"\n16-bit PCM分析:")
        print(f"  LE平均差值: {avg_diff_le:.1f}")
        print(f"  BE平均差值: {avg_diff_be:.1f}")

def decode_8bit_pcm(data, sample_rate=11025, offset=0, size=None):
    """8-bit unsigned PCM"""
    if size is None:
        size = len(data) - offset
    raw = data[offset:offset+size]
    pcm = bytes([b ^ 0x80 for b in raw])  # unsigned to signed
    return pcm

def decode_16bit_pcm(data, sample_rate=22050, offset=0, size=None, endian='little'):
    """16-bit PCM"""
    if size is None:
        size = len(data) - offset
    raw = data[offset:offset+size]
    count = len(raw) // 2
    fmt = f'<{count}h' if endian == 'little' else f'>{count}h'
    samples = struct.unpack(fmt, raw[:count*2])
    pcm = b''.join(struct.pack('<h', s) for s in samples)
    return pcm

def decode_ima_adpcm(data, initial_predictor=0, initial_index=0, sample_rate=22050):
    """IMA ADPCM解码"""
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

def main():
    raw, res_size = load_res78()
    
    print("="*60)
    print("res78 深度分析")
    print("="*60)
    
    analyze_byte_distribution(raw, "res78完整数据")
    analyze_byte_distribution(raw[:100], "res78前100字节")
    analyze_byte_distribution(raw[100:], "res78第100字节后")
    
    # 创建输出目录
    out_dir = 'output/sfx_wav/res078_deep'
    os.makedirs(out_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("尝试不同解码方式")
    print("="*60)
    
    # 1. 8-bit PCM (各种采样率)
    print("\n--- 8-bit PCM ---")
    for sr in [5512, 8000, 11025, 16000, 22050]:
        pcm = decode_8bit_pcm(raw, sr)
        save_wav(f"{out_dir}/8bit_{sr}hz.wav", pcm, sr)
    
    # 2. 跳过前几个字节后的8-bit PCM
    print("\n--- 8-bit PCM (skip header) ---")
    for skip in [2, 4, 6, 8]:
        pcm = decode_8bit_pcm(raw, 11025, offset=skip)
        save_wav(f"{out_dir}/8bit_skip{skip}.wav", pcm, 11025)
    
    # 3. 16-bit PCM (各种配置)
    print("\n--- 16-bit PCM ---")
    for sr in [8000, 11025, 16000, 22050]:
        for endian in ['little', 'big']:
            pcm = decode_16bit_pcm(raw, sr, endian=endian)
            save_wav(f"{out_dir}/16bit_{endian}_{sr}hz.wav", pcm, sr)
    
    # 4. 跳过header后的16-bit PCM
    print("\n--- 16-bit PCM (skip header) ---")
    for skip in [2, 4, 6, 8]:
        for sr in [8000, 11025, 16000]:
            pcm = decode_16bit_pcm(raw, sr, offset=skip)
            save_wav(f"{out_dir}/16bit_skip{skip}_{sr}hz.wav", pcm, sr)
    
    # 5. IMA ADPCM (各种初始值)
    print("\n--- IMA ADPCM ---")
    for pred in [0, 128, 256, 512, 1024, 2048]:
        for idx in [0, 16, 32, 48, 64]:
            pcm = decode_ima_adpcm(raw, pred, idx, 22050)
            save_wav(f"{out_dir}/adpcm_p{pred}_i{idx}.wav", pcm, 22050)
    
    # 6. IMA ADPCM (不同采样率)
    print("\n--- IMA ADPCM (不同采样率) ---")
    for sr in [5512, 8000, 11025, 16000, 22050]:
        pcm = decode_ima_adpcm(raw, 0, 0, sr)
        save_wav(f"{out_dir}/adpcm_{sr}hz.wav", pcm, sr)
    
    # 7. 从不同偏移开始的IMA ADPCM
    print("\n--- IMA ADPCM (不同偏移) ---")
    for offset in [2, 4, 6, 8, 10]:
        pcm = decode_ima_adpcm(raw[offset:], 0, 0, 22050)
        save_wav(f"{out_dir}/adpcm_offset{offset}.wav", pcm, 22050)
    
    print(f"\n所有测试文件已保存到: {out_dir}/")
    print("请试听这些文件，找到最接近闪电效果的版本")

if __name__ == '__main__':
    main()
