#!/usr/bin/env python3
"""
提取res78第二个样本(闪电音效)并尝试多种解码方式
根据分析: 样本从res78偏移16开始, 大小6359字节
"""

import struct
import os
import wave

def extract_sample2(fdother_path, output_dir):
    """提取res78第二个样本"""
    with open(fdother_path, 'rb') as f:
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        # 读取偏移表
        f.seek(10)
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
        
        # 获取res78
        idx = 78
        res_start = offsets[idx]
        res_end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
        f.seek(res_start)
        res78 = f.read(res_end - res_start)
    
    print(f"res78大小: {len(res78)} 字节")
    print(f"头部16字节: {res78[:16].hex(' ')}")
    
    # 解析头部
    # 根据之前分析: int16数组: [2, 2, 0, 0, 16, 0, 6359, 0]
    sample1_offset = struct.unpack_from('<H', res78, 4)[0]  # 0
    sample1_size = struct.unpack_from('<H', res78, 6)[0]    # 0
    sample2_offset = struct.unpack_from('<H', res78, 8)[0]  # 16
    sample2_size = struct.unpack_from('<H', res78, 10)[0]   # 6359
    # 还有DWORD: [12:16] = 0x000018d7 = 6359
    
    print(f"样本1: 偏移={sample1_offset}, 大小={sample1_size}")
    print(f"样本2: 偏移={sample2_offset}, 大小={sample2_size}")
    
    # 提取样本2数据
    sample_data = res78[sample2_offset:sample2_offset + sample2_size]
    print(f"样本2数据大小: {len(sample_data)} 字节")
    print(f"样本2前32字节: {sample_data[:32].hex(' ')}")
    
    # 保存到文件
    sample_path = os.path.join(output_dir, 'lightning_sample.bin')
    with open(sample_path, 'wb') as f:
        f.write(sample_data)
    print(f"样本数据保存到: {sample_path}")
    
    return sample_data

def write_wav(filepath, sample_rate, data, sample_width=2):
    """写入WAV文件"""
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)

def decode_as_raw_pcm(data, output_dir):
    """尝试作为原始PCM解码"""
    # 8-bit unsigned
    write_wav(os.path.join(output_dir, 'raw_8bit_8000hz.wav'), 8000, data, 1)
    write_wav(os.path.join(output_dir, 'raw_8bit_11025hz.wav'), 11025, data, 1)
    write_wav(os.path.join(output_dir, 'raw_8bit_16000hz.wav'), 16000, data, 1)
    
    # 8-bit signed
    signed_data = bytes([(b - 128) % 256 for b in data])
    write_wav(os.path.join(output_dir, 'raw_8bit_signed_8000hz.wav'), 8000, signed_data, 1)
    
    # 16-bit little-endian
    if len(data) % 2 == 0:
        write_wav(os.path.join(output_dir, 'raw_16le_8000hz.wav'), 8000, data, 2)
        write_wav(os.path.join(output_dir, 'raw_16le_11025hz.wav'), 11025, data, 2)
    
    # 16-bit big-endian
    if len(data) % 2 == 0:
        be_data = b''
        for i in range(0, len(data), 2):
            be_data += data[i+1:i+2] + data[i:i+1]
        write_wav(os.path.join(output_dir, 'raw_16be_8000hz.wav'), 8000, be_data, 2)
    
    print("原始PCM解码完成")

def ima_adpcm_decode_4bit(data, initial_predictor=0, initial_index=0):
    """IMA ADPCM 4-bit解码"""
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

def decode_as_adpcm(data, output_dir):
    """尝试IMA ADPCM解码"""
    sample_rates = [5512, 8000, 11025, 16000, 22050]
    predictors = [0, 128, 1024, -128, -1024]
    
    for pred in predictors:
        for rate in sample_rates:
            decoded = ima_adpcm_decode_4bit(data, initial_predictor=pred)
            filename = f'adpcm_pred{pred}_{rate}hz.wav'
            write_wav(os.path.join(output_dir, filename), rate, decoded, 2)
            print(f"  生成: {filename}")
    
    print("IMA ADPCM解码完成")

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    if not os.path.exists(fdother_path):
        fdother_path = os.path.join(base_dir, 'FDOTHER.DAT')
    
    output_dir = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_final')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"使用文件: {fdother_path}")
    print(f"输出目录: {output_dir}")
    
    sample_data = extract_sample2(fdother_path, output_dir)
    
    print("\n--- 原始PCM解码 ---")
    decode_as_raw_pcm(sample_data, output_dir)
    
    print("\n--- IMA ADPCM解码 ---")
    decode_as_adpcm(sample_data, output_dir)
    
    print(f"\n所有文件已生成到: {output_dir}")

if __name__ == '__main__':
    main()
