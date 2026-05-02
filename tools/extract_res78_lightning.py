#!/usr/bin/env python3
"""
精确解析res78闪电音效 - 基于IDA汇编分析

根据sub_25A96汇编：
  样本起始 = buffer + *(buffer+6)  = buffer + 0 = buffer
  样本大小 = *(buffer+10) - *(buffer+6) = 0x18d7 - 0 = 6359 bytes

所以样本数据从res78的第0字节开始，大小6359字节
"""
import struct
import os
import wave

def load_res78():
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
    return raw

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

def main():
    raw = load_res78()
    
    # 根据IDA汇编精确提取
    v6 = struct.unpack_from('<I', raw, 6)[0]
    v10 = struct.unpack_from('<I', raw, 10)[0]
    
    sample_start = v6
    sample_size = v10 - v6
    
    print(f"res78总大小: {len(raw)} bytes")
    print(f"样本起始: {sample_start}")
    print(f"样本大小: {sample_size}")
    print(f"样本数据前32字节: {raw[sample_start:sample_start+32].hex()}")
    
    sample_data = raw[sample_start:sample_start+sample_size]
    
    out_dir = 'output/sfx_wav/res078_final'
    os.makedirs(out_dir, exist_ok=True)
    
    # 保存原始样本
    with open(f'{out_dir}/sample0.bin', 'wb') as f:
        f.write(sample_data)
    
    # 1. 8-bit unsigned PCM (转换为signed)
    print(f"\n--- 8-bit PCM ---")
    for sr in [4000, 5512, 8000, 11025]:
        pcm = bytes([b ^ 0x80 for b in sample_data])
        save_wav(pcm, sr, f'{out_dir}/8bit_{sr}hz.wav')
        print(f"  8bit_{sr}hz.wav ({len(pcm)} bytes)")
    
    # 2. IMA ADPCM
    print(f"\n--- IMA ADPCM ---")
    for sr in [4000, 5512, 8000, 11025]:
        for pred in [0, 128, 1024]:
            pcm = ima_adpcm_decode(sample_data, pred, 0)
            save_wav(pcm, sr, f'{out_dir}/adpcm16_p{pred}_{sr}hz.wav')
            print(f"  adpcm16_p{pred}_{sr}hz.wav ({len(pcm)} bytes)")
    
    print(f"\n完成! 检查 {out_dir}/ 目录")
    print("\n请试听以下文件:")
    print("  - 8bit_8000hz.wav")
    print("  - adpcm16_p0_8000hz.wav")
    print("  - adpcm16_p128_8000hz.wav")
    print("  - adpcm16_p1024_8000hz.wav")

if __name__ == '__main__':
    main()
