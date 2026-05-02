#!/usr/bin/env python3
"""
根据IDA汇编分析精确解析res78样本数据

sub_25A96 关键逻辑:
  a5 = buffer pointer (FDOTHER.DAT资源数据)
  a6 = sample index (0 for first sample)
  
  v13 = *(a5 + 6 + 4*a6) + a5  // sample start offset
  v12 = *(a5 + 10 + 4*a6) - *(a5 + 6 + 4*a6)  // sample size
  
  所以样本数据位于: buffer + *(6) 到 buffer + *(10)
"""
import struct
import os
import wave

def load_res78():
    dat_path = os.path.join('game', 'FDOTHER.DAT')
    with open(dat_path, 'rb') as f:
        # 解析文件头
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        # 读取offset table
        f.seek(0x0A)
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
        
        # res78
        idx = 78
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
        size = end - start
        
        f.seek(start)
        raw = f.read(size)
    
    return raw, size

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)

def ima_adpcm_decode(data, initial_predictor=0, initial_index=0):
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

def delta_decode_8bit(data, initial_value=128):
    """8-bit delta encoding解码"""
    output = []
    current = initial_value
    
    for byte in data:
        # byte是差值(有符号)
        if byte > 127:
            byte = byte - 256  # 转为有符号
        current = max(0, min(255, current + byte))
        output.append(current)
    
    return bytes(output)

def main():
    raw, size = load_res78()
    
    print("="*60)
    print("基于IDA汇编精确解析res78")
    print("="*60)
    print(f"\nres78总大小: {size} bytes")
    
    # 根据IDA: a5指向资源数据, a6=0 (第一个样本)
    # v13 = *(a5 + 6 + 4*0) + a5 = *(a5+6) + a5
    # v12 = *(a5 + 10 + 4*0) - *(a5 + 6 + 4*0) = *(a5+10) - *(a5+6)
    
    v6 = struct.unpack_from('<I', raw, 6)[0]  # *(6)
    v10 = struct.unpack_from('<I', raw, 10)[0]  # *(10)
    
    print(f"\n根据IDA汇编:")
    print(f"  *(6)  = 0x{v6:x} ({v6})")
    print(f"  *(10) = 0x{v10:x} ({v10})")
    
    # 样本起始和大小
    sample_start = v6
    sample_size = v10 - v6
    sample_end = sample_start + sample_size
    
    print(f"\n样本数据:")
    print(f"  起始偏移: {sample_start} (0x{sample_start:x})")
    print(f"  大小: {sample_size} bytes")
    print(f"  结束偏移: {sample_end} (0x{sample_end:x})")
    
    # 提取样本
    if sample_start < len(raw) and sample_end <= len(raw):
        sample_data = raw[sample_start:sample_end]
        print(f"\n样本数据前64字节:")
        for i in range(0, min(64, len(sample_data)), 16):
            hex_str = ' '.join(f'{b:02x}' for b in sample_data[i:i+16])
            print(f"  {i:04x}: {hex_str}")
        
        # 保存原始样本
        os.makedirs('output/sfx_wav/res078_exact', exist_ok=True)
        with open('output/sfx_wav/res078_exact/sample0_raw.bin', 'wb') as f:
            f.write(sample_data)
        
        # 尝试不同解码方式
        
        # 1. 8-bit PCM (signed)
        print(f"\n--- 8-bit PCM ---")
        for sr in [4000, 5512, 8000, 11025]:
            pcm = bytes([b ^ 0x80 for b in sample_data])
            save_wav(pcm, sr, f'output/sfx_wav/res078_exact/8bit_{sr}hz.wav')
            print(f"  保存: 8bit_{sr}hz.wav")
        
        # 2. 8-bit delta encoding
        print(f"\n--- 8-bit Delta Encoding ---")
        for init_val in [0, 64, 128, 192]:
            for sr in [4000, 5512, 8000, 11025]:
                pcm8 = delta_decode_8bit(sample_data, init_val)
                pcm16 = bytes([b ^ 0x80 for b in pcm8])
                save_wav(pcm16, sr, f'output/sfx_wav/res078_exact/delta_init{init_val}_{sr}hz.wav')
        
        # 3. IMA ADPCM
        print(f"\n--- IMA ADPCM ---")
        for sr in [4000, 5512, 8000, 11025]:
            for pred in [0, 128, 1024]:
                pcm = ima_adpcm_decode(sample_data, pred, 0)
                save_wav(pcm, sr, f'output/sfx_wav/res078_exact/adpcm_p{pred}_{sr}hz.wav')
        
        print(f"\n完成! 所有文件保存到 output/sfx_wav/res078_exact/")
    else:
        print(f"\n错误: 样本偏移超出范围!")
        print(f"  sample_start={sample_start}, sample_end={sample_end}")
        print(f"  raw_size={len(raw)}")

if __name__ == '__main__':
    main()
