#!/usr/bin/env python3
"""
基于IDA分析结果提取res78闪电音效
关键发现 (case 1u):
- 采样率 = 0xF4240 / (256 - res78[4]) = 1000000 / (256 - 61) = 5128 Hz
- 样本数据从 res78+6 开始
- 样本大小 = 总长度 - 2
- IMA ADPCM 4-bit 编码
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
    print(f"res78前16字节: {res78[:16].hex()}")
    
    # 根据IDA case 1u解析
    # 采样率 = 0xF4240 / (256 - res78[4])
    byte_at_4 = res78[4]
    sample_rate = 1000000 // (256 - byte_at_4)
    
    print(f"\n根据IDA case 1u解析:")
    print(f"  res78[4] = {byte_at_4} (0x{byte_at_4:02x})")
    print(f"  采样率 = 1000000 / (256 - {byte_at_4}) = 1000000 / {256 - byte_at_4} = {sample_rate} Hz")
    
    # 样本数据从偏移6开始，大小 = 总大小 - 6 (或根据头部计算)
    # 根据之前分析，样本大小在0x0C处 = 6359
    sample_size_from_header = struct.unpack_from('<I', res78, 0x0C)[0]
    sample_data = res78[6:6 + sample_size_from_header]
    
    print(f"  样本大小 (从0x0C): {sample_size_from_header} bytes")
    print(f"  样本数据起始: 偏移6")
    print(f"  实际样本数据: {len(sample_data)} bytes")
    
    # 计算时长
    sample_count = len(sample_data) * 2  # IMA ADPCM 4-bit
    duration = sample_count / sample_rate
    print(f"  采样点数 (ADPCM): {sample_count}")
    print(f"  预估时长: {duration:.3f} 秒")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'sfx_wav', 'res078_ida_v3')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n生成WAV文件...")
    
    # IMA ADPCM解码 @ 计算出的采样率
    for predictor in [0, 128, -128, 1024]:
        pcm = ima_adpcm_decode(sample_data, predictor, 0)
        wav = create_wav(pcm, sample_rate)
        filename = f"adpcm_p{predictor}_{sample_rate}hz.wav"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(wav)
        print(f"  生成: {filename} (时长: {len(pcm)/sample_rate:.3f}s)")
    
    # 也尝试附近采样率
    for rate_offset in [-100, -50, 0, 50, 100]:
        rate = sample_rate + rate_offset
        if rate <= 0: continue
        pcm = ima_adpcm_decode(sample_data, 0, 0)
        wav = create_wav(pcm, rate)
        filename = f"adpcm_{rate}hz.wav"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(wav)
        print(f"  生成: {filename} (时长: {len(pcm)/rate:.3f}s)")
    
    print(f"\n所有文件已保存到: {output_dir}")
    print(f"\n建议测试: adpcm_0_{sample_rate}hz.wav")

if __name__ == '__main__':
    main()