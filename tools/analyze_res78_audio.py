#!/usr/bin/env python3
"""
分析res78中6359字节样本数据的内部结构
根据之前的分析，样本数据从res78偏移16开始，大小6359字节
样本前16字节看起来像元数据: 45 00 3d 00 00 00 02 00 00 b5 00 4b 00 ff ca 81
"""

import struct
import os
import wave

def write_wav(filepath, sample_rate, data, sample_width=2):
    """写入WAV文件"""
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)

def ima_adpcm_decode_4bit(data, initial_predictor=0, initial_index=0):
    """IMA ADPCM 4-bit解码（标准实现）"""
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
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sample_path = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_correct', 'lightning_6359.bin')
    
    if not os.path.exists(sample_path):
        print(f"找不到样本文件: {sample_path}")
        return
    
    with open(sample_path, 'rb') as f:
        sample_data = f.read()
    
    print(f"样本数据大小: {len(sample_data)} 字节")
    print(f"样本前64字节: {sample_data[:64].hex(' ')}")
    print(f"样本后32字节: {sample_data[-32:].hex(' ')}")
    
    # 尝试解析头部
    # 样本前16字节可能是:
    # 45 00 = 0x0045 = 69
    # 3d 00 = 0x003d = 61
    # 00 00 = 0
    # 02 00 = 2
    # 00 b5 = 0xb500 = 46336 (大端) 或 0x00b5 = 181 (小端)
    # 00 4b = 0x4b00 = 19200 (大端) 或 0x004b = 75 (小端)
    # 00 ff = 0xff00 = 65280 (大端) 或 0x00ff = 255 (小端)
    # ca 81 = 0x81ca = 33226 (大端) 或 0x81ca (小端有符号 = -32310)
    
    print(f"\n--- 尝试解析样本头部 ---")
    h = struct.unpack_from('<8H', sample_data, 0)
    print(f"WORD数组: {[f'0x{x:04x}={x}' for x in h]}")
    
    # 可能的采样率字段？
    # 0xb500 大端 = 46336, 不太像采样率
    # 但如果样本数据从偏移16开始...
    
    audio_data = sample_data[16:]
    print(f"\n音频数据偏移16后大小: {len(audio_data)} 字节")
    print(f"音频数据前32字节: {audio_data[:32].hex(' ')}")
    
    output_dir = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_v2')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n--- 尝试不同解码方式 ---")
    
    # 方案1: 整个样本作为8-bit unsigned PCM
    for rate in [5512, 8000, 11025, 16000, 22050]:
        write_wav(os.path.join(output_dir, f'full_8bit_{rate}hz.wav'), rate, sample_data, 1)
    
    # 方案2: 跳过16字节头，剩余作为8-bit PCM
    for rate in [5512, 8000, 11025, 16000, 22050]:
        write_wav(os.path.join(output_dir, f'skip16_8bit_{rate}hz.wav'), rate, audio_data, 1)
    
    # 方案3: 跳过16字节头，剩余作为16-bit LE PCM
    if len(audio_data) % 2 == 0:
        for rate in [5512, 8000, 11025, 16000, 22050]:
            write_wav(os.path.join(output_dir, f'skip16_16le_{rate}hz.wav'), rate, audio_data, 2)
    
    # 方案4: IMA ADPCM 解码
    # 跳过前16字节头部
    for rate in [5512, 8000, 11025, 16000, 22050]:
        for pred in [0, 128, 1024, -128, 2048]:
            decoded = ima_adpcm_decode_4bit(audio_data, initial_predictor=pred)
            write_wav(os.path.join(output_dir, f'adpcm_skip16_p{pred}_{rate}hz.wav'), rate, decoded, 2)
    
    # 方案5: 尝试整个样本作为IMA ADPCM（无头）
    for rate in [5512, 8000, 11025, 16000, 22050]:
        for pred in [0, 128, 1024]:
            decoded = ima_adpcm_decode_4bit(sample_data, initial_predictor=pred)
            write_wav(os.path.join(output_dir, f'adpcm_full_p{pred}_{rate}hz.wav'), rate, decoded, 2)
    
    # 方案6: 尝试不同的初始index
    # 标准IMA ADPCM使用初始index=0，但某些实现可能使用不同的初始值
    for rate in [5512, 8000, 11025]:
        for pred in [0, 128]:
            for idx in [0, 10, 20, 30, 40]:
                decoded = ima_adpcm_decode_4bit(audio_data, initial_predictor=pred, initial_index=idx)
                write_wav(os.path.join(output_dir, f'adpcm_skip16_p{pred}_idx{idx}_{rate}hz.wav'), rate, decoded, 2)
    
    print(f"\n所有WAV文件已生成到: {output_dir}")
    print("\n推荐试听文件:")
    print("  1. skip16_8bit_11025hz.wav - 跳过16字节头，8-bit PCM，11025Hz")
    print("  2. skip16_8bit_8000hz.wav - 跳过16字节头，8-bit PCM，8000Hz")
    print("  3. skip16_16le_11025hz.wav - 跳过16字节头，16-bit LE PCM，11025Hz")
    print("  4. adpcm_skip16_p0_11025hz.wav - IMA ADPCM，预测器0，11025Hz")
    print("  5. adpcm_skip16_p0_8000hz.wav - IMA ADPCM，预测器0，8000Hz")

if __name__ == '__main__':
    main()
