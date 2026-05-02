#!/usr/bin/env python3
"""
根据用户反馈"低沉轰鸣，1秒"生成正确的闪电音效
- 采样率: ~12718 Hz (精确匹配1秒)
- 简单低通滤波: 平滑处理去除高频沙沙声
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

def simple_lowpass_filter(data, window_size=5):
    """简单的移动平均低通滤波"""
    if window_size <= 1:
        return data
    kernel = np.ones(window_size) / window_size
    # 使用卷积实现平滑
    filtered = np.convolve(data.astype(np.float64), kernel, mode='same')
    return np.clip(filtered, -32768, 32767).astype(np.int16)

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
    print(f"IMA ADPCM采样点数: {len(sample_data) * 2}")
    
    # 创建输出目录
    output_dir = 'output/sfx_wav/res078_thunder'
    os.makedirs(output_dir, exist_ok=True)
    
    # 解码IMA ADPCM
    pcm = ima_adpcm_decode(sample_data, 0, 0)
    print(f"解码后PCM数据: {len(pcm)} 采样点")
    
    # 计算精确采样率
    exact_rate = len(pcm)  # 1秒时长
    print(f"精确采样率 (1秒): {exact_rate} Hz")
    
    # 生成不同采样率的WAV
    print("\n生成不同采样率版本:")
    for rate in [exact_rate, 12000, 11025, 10000, 8000]:
        # 原始
        wav = create_wav(pcm, rate)
        filename = f'thunder_{rate}hz_raw.wav'
        with open(f'{output_dir}/{filename}', 'wb') as f:
            f.write(wav)
        print(f"  {filename} ({len(pcm)/rate:.3f}s)")
        
        # 低通滤波版本 (不同窗口大小)
        for window in [3, 5, 7]:
            filtered = simple_lowpass_filter(pcm, window)
            wav_filtered = create_wav(filtered, rate)
            filename = f'thunder_{rate}hz_smooth{window}.wav'
            with open(f'{output_dir}/{filename}', 'wb') as f:
                f.write(wav_filtered)
            print(f"  {filename}")
    
    print(f"\n所有文件已保存到: {output_dir}")
    print("\n推荐测试顺序:")
    print("1. thunder_12718hz_smooth5.wav - 1秒 + 中度平滑")
    print("2. thunder_12718hz_smooth3.wav - 1秒 + 轻度平滑")
    print("3. thunder_12718hz_smooth7.wav - 1秒 + 重度平滑")
    print("4. thunder_12718hz_raw.wav - 1秒无滤波")

if __name__ == '__main__':
    main()