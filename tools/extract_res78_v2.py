#!/usr/bin/env python3
"""
基于IDA分析结果，使用正确的样本大小和多种采样率生成WAV
关键发现:
1. 样本大小 = 6359字节 (从res78头部0x0C或0x10处读取)
2. 样本数据从res78偏移0x10开始
3. 需要尝试不同的采样率找到正确的时长
"""
import struct
import os
import sys
import numpy as np

def ima_adpcm_decode(adpcm_data, initial_predictor=0, initial_index=0):
    """
    IMA ADPCM 4-bit 解码 - 输出16-bit PCM
    """
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

def create_wav(pcm_data, sample_rate=11025, channels=1, bits_per_sample=16):
    """创建WAV文件"""
    if bits_per_sample == 16:
        pcm_bytes = pcm_data.astype(np.int16).tobytes()
    else:
        pcm_bytes = (pcm_data + 128).astype(np.uint8).tobytes()
    
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(pcm_bytes),
        b'WAVE',
        b'fmt ',
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        len(pcm_bytes)
    )
    
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
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
    
    idx = 78
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
    size = end - start
    
    with open(fdother_path, 'rb') as f:
        f.seek(start)
        res78 = f.read(size)
    
    # 样本大小从0x0C读取
    sample_size = struct.unpack_from('<I', res78, 0x0C)[0]
    sample_data_start = 0x10
    
    print(f"res78总大小: {size} bytes")
    print(f"样本大小: {sample_size} bytes")
    print(f"样本数据起始: 0x{sample_data_start:x}")
    
    sample_data = res78[sample_data_start:sample_data_start + sample_size]
    print(f"实际样本数据: {len(sample_data)} bytes")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'sfx_wav', 'res078_ida_v2')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n生成不同采样率的WAV文件...")
    print(f"样本大小: {sample_size} bytes")
    print(f"如果是IMA ADPCM 4-bit: {sample_size * 2} 个采样点")
    print(f"如果是8-bit PCM: {sample_size} 个采样点")
    print(f"如果是16-bit PCM: {sample_size // 2} 个采样点")
    print()
    
    # 计算不同采样率下的时长
    sample_count_adpcm = sample_size * 2  # IMA ADPCM
    sample_count_8bit = sample_size        # 8-bit PCM
    sample_count_16bit = sample_size // 2  # 16-bit PCM
    
    sample_rates = [5512, 8000, 11025, 16000, 22050]
    
    print("时长分析:")
    for rate in sample_rates:
        duration_adpcm = sample_count_adpcm / rate
        duration_8bit = sample_count_8bit / rate
        duration_16bit = sample_count_16bit / rate
        print(f"  @{rate}Hz: ADPCM={duration_adpcm:.3f}s, 8bit={duration_8bit:.3f}s, 16bit={duration_16bit:.3f}s")
    print()
    
    # IMA ADPCM解码 @ 不同采样率
    pcm_adpcm = ima_adpcm_decode(sample_data, 0, 0)
    
    for rate in sample_rates:
        duration = len(pcm_adpcm) / rate
        print(f"生成: adpcm11025_{rate}hz.wav (时长: {duration:.3f}s)")
        wav_data = create_wav(pcm_adpcm, rate)
        filename = f"adpcm_{rate}hz.wav"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(wav_data)
    
    # 8-bit PCM @ 不同采样率
    pcm_8bit = np.frombuffer(sample_data, dtype=np.uint8).astype(np.int16) - 128
    for rate in sample_rates:
        duration = len(pcm_8bit) / rate
        print(f"生成: pcm8_{rate}hz.wav (时长: {duration:.3f}s)")
        wav_data = create_wav(pcm_8bit, rate, bits_per_sample=8)
        filename = f"pcm8_{rate}hz.wav"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(wav_data)
    
    # 16-bit PCM (little-endian) @ 不同采样率
    if sample_size >= 2:
        pcm_16bit = np.frombuffer(sample_data[:sample_size - (sample_size % 2)], dtype='<i2')
        for rate in sample_rates:
            duration = len(pcm_16bit) / rate
            print(f"生成: pcm16le_{rate}hz.wav (时长: {duration:.3f}s)")
            wav_data = create_wav(pcm_16bit, rate)
            filename = f"pcm16le_{rate}hz.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(wav_data)
    
    # 16-bit PCM (big-endian) @ 不同采样率
    if sample_size >= 2:
        pcm_16bit_be = np.frombuffer(sample_data[:sample_size - (sample_size % 2)], dtype='>i2')
        for rate in sample_rates:
            duration = len(pcm_16bit_be) / rate
            print(f"生成: pcm16be_{rate}hz.wav (时长: {duration:.3f}s)")
            wav_data = create_wav(pcm_16bit_be, rate)
            filename = f"pcm16be_{rate}hz.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(wav_data)
    
    print(f"\n所有文件已保存到: {output_dir}")
    print(f"\n建议优先测试:")
    print(f"1. adpcm_5512hz.wav - 最低采样率，时长最长")
    print(f"2. adpcm_8000hz.wav - 8000Hz，之前用户反馈较舒服")
    print(f"3. pcm8_5512hz.wav - 8-bit PCM最低采样率")

if __name__ == '__main__':
    main()