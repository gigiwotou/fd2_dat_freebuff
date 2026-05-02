#!/usr/bin/env python3
"""
基于IDA分析结果，测试所有可能的编码格式和采样率组合
根据res78头部：样本从偏移0x10开始，大小6359字节
"""
import struct
import os
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
    if bits_per_sample == 16:
        pcm_bytes = pcm_data.astype(np.int16).tobytes()
    else:
        pcm_bytes = (pcm_data + 128).astype(np.uint8).tobytes()
    
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(pcm_bytes), b'WAVE', b'fmt ',
        16, 1, channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b'data', len(pcm_bytes))
    
    return header + pcm_bytes

def main():
    # 读取res78样本数据
    with open('game/FDOTHER.DAT', 'rb') as f:
        f.read(10)
        offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(200)]
        f.seek(offsets[78])
        res78 = f.read(6801)
    
    sample_size = struct.unpack_from('<I', res78, 12)[0]  # 6359
    sample_start = struct.unpack_from('<I', res78, 8)[0]  # 16
    sample_data = res78[sample_start:sample_start + sample_size]
    
    print(f"res78样本数据: {len(sample_data)} bytes")
    print(f"样本起始偏移: {sample_start}")
    print(f"样本大小: {sample_size}")
    
    # 创建输出目录
    output_dir = 'output/sfx_wav/res078_final_test'
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试多种采样率
    sample_rates = [5512, 8000, 11025, 16000, 22050]
    
    # 1. IMA ADPCM 4-bit
    print("\n1. IMA ADPCM 4-bit 解码:")
    pcm_adpcm = ima_adpcm_decode(sample_data, 0, 0)
    for rate in sample_rates:
        duration = len(pcm_adpcm) / rate
        wav = create_wav(pcm_adpcm, rate)
        filename = f'adpcm_{rate}hz.wav'
        with open(f'{output_dir}/{filename}', 'wb') as f:
            f.write(wav)
        print(f"   @{rate}Hz: {duration:.2f}s")
    
    # 2. 8-bit PCM
    print("\n2. 8-bit PCM:")
    pcm8 = np.frombuffer(sample_data, dtype=np.uint8).astype(np.int16) - 128
    for rate in sample_rates:
        duration = len(pcm8) / rate
        wav = create_wav(pcm8, rate, bits_per_sample=8)
        filename = f'pcm8_{rate}hz.wav'
        with open(f'{output_dir}/{filename}', 'wb') as f:
            f.write(wav)
        print(f"   @{rate}Hz: {duration:.2f}s")
    
    # 3. 16-bit PCM LE
    if len(sample_data) >= 2:
        print("\n3. 16-bit PCM Little-Endian:")
        pcm16 = np.frombuffer(sample_data[:len(sample_data)//2*2], dtype='<i2')
        for rate in sample_rates:
            duration = len(pcm16) / rate
            wav = create_wav(pcm16, rate)
            filename = f'pcm16le_{rate}hz.wav'
            with open(f'{output_dir}/{filename}', 'wb') as f:
                f.write(wav)
            print(f"   @{rate}Hz: {duration:.2f}s")
    
    # 4. 16-bit PCM BE
    if len(sample_data) >= 2:
        print("\n4. 16-bit PCM Big-Endian:")
        pcm16_be = np.frombuffer(sample_data[:len(sample_data)//2*2], dtype='>i2')
        for rate in sample_rates:
            duration = len(pcm16_be) / rate
            wav = create_wav(pcm16_be, rate)
            filename = f'pcm16be_{rate}hz.wav'
            with open(f'{output_dir}/{filename}', 'wb') as f:
                f.write(wav)
            print(f"   @{rate}Hz: {duration:.2f}s")
    
    print(f"\n所有文件已保存到: {output_dir}")
    print("\n建议优先测试:")
    print("  - adpcm_5512hz.wav (最低采样率，时长最长)")
    print("  - adpcm_8000hz.wav (之前用户反馈较舒服的采样率)")
    print("  - pcm8_5512hz.wav (8-bit PCM最低采样率)")

if __name__ == '__main__':
    main()