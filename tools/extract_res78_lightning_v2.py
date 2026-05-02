#!/usr/bin/env python3
"""
基于IDA分析精确提取res78闪电音效

根据sub_25A96汇编和Miles AIL函数调用链：
- sub_111BA加载FDOTHER.DAT资源#78
- sub_25A96调用AIL_init_sample, AIL_set_sample_address, AIL_start_sample播放
- 样本偏移: buffer + *(6) = buffer + 0
- 样本大小: *(10) - *(6) = 6359 - 0 = 6359字节
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
    
    print(f"res78 size: {len(raw)} bytes")
    print(f"First 20 bytes: {raw[:20].hex()}")
    
    sample_data = raw[:6359]
    print(f"Sample data size: {len(sample_data)} bytes")
    print(f"Sample first 32 bytes: {sample_data[:32].hex()}")
    
    out_dir = 'output/sfx_wav/res078_lightning'
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f'{out_dir}/sample_raw.bin', 'wb') as f:
        f.write(sample_data)
    
    # 1. 8-bit PCM (signed)
    for sr in [4000, 5512, 8000, 11025]:
        pcm = bytes([b ^ 0x80 for b in sample_data])
        save_wav(pcm, sr, f'{out_dir}/8bit_{sr}hz.wav')
    
    # 2. IMA ADPCM with different parameters
    for sr in [4000, 5512, 8000, 11025]:
        for pred in [0, 128, 256, 512, 1024]:
            for idx in [0, 16, 32, 48]:
                pcm = ima_adpcm_decode(sample_data, pred, idx)
                save_wav(pcm, sr, f'{out_dir}/adpcm_p{pred}_i{idx}_{sr}hz.wav')
    
    # 3. 16-bit PCM
    for sr in [8000, 11025]:
        for endian in ['little', 'big']:
            data = sample_data[:len(sample_data)//2*2]
            fmt = f'<{len(data)//2}h' if endian == 'little' else f'>{len(data)//2}h'
            samples = struct.unpack(fmt, data)
            pcm = b''.join(struct.pack('<h', s) for s in samples)
            save_wav(pcm, sr, f'{out_dir}/16bit_{endian}_{sr}hz.wav')
    
    print(f"\nDone! Files saved to {out_dir}/")

if __name__ == '__main__':
    main()
