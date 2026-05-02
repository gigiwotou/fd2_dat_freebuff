#!/usr/bin/env python3
"""
基于IDA分析结果提取res78闪电音效并生成WAV
关键发现:
1. sub_414E0 (AIL_init_sample) 设置采样率为 11025 Hz
2. res78头部结构:
   - 偏移0x0C: 样本大小 = 6359 (0x18D7)
   - 偏移0x10: 样本数据起始
3. Miles Sound System使用IMA ADPCM编码
"""
import struct
import os
import sys

def ima_adpcm_decode_16bit(adpcm_data, initial_predictor=0, initial_index=0):
    """
    IMA ADPCM 4-bit 解码 - 16位输出
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
            output.append(struct.pack('<h', predictor))
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return b''.join(output)

def ima_adpcm_decode_8bit(adpcm_data, initial_predictor=128, initial_index=0):
    """
    IMA ADPCM 4-bit 解码 - 8位输出
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
            
            predictor = max(0, min(255, predictor))
            output.append(struct.pack('B', predictor))
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return b''.join(output)

def create_wav(pcm_data, sample_rate=11025, channels=1, bits_per_sample=16):
    """创建WAV文件"""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(pcm_data),
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
        len(pcm_data)
    )
    
    return header + pcm_data

def main():
    # 读取FDOTHER.DAT
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT")
        sys.exit(1)
    
    print(f"使用文件: {fdother_path}")
    
    with open(fdother_path, 'rb') as f:
        # FDOTHER.DAT格式: [magic(6)][count(4)][offsets(N*4)][资源数据]
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        # 读取偏移表
        f.seek(10)
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # 获取res78
    idx = 78
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
    size = end - start
    
    print(f"res78:")
    print(f"  起始偏移: 0x{start:x} ({start})")
    print(f"  大小: {size} bytes")
    
    # 读取res78完整数据
    with open(fdother_path, 'rb') as f:
        f.seek(start)
        res78 = f.read(size)
    
    # 根据IDA分析提取样本
    # *(res78+0x0C) = 样本大小 = 6359
    # 样本数据从 res78+0x10 开始
    sample_size = struct.unpack_from('<I', res78, 0x0C)[0]
    sample_data_start = 0x10
    
    print(f"样本大小: {sample_size}")
    print(f"样本数据起始: 0x{sample_data_start:x}")
    
    if sample_data_start + sample_size > len(res78):
        print(f"警告: 样本超出范围，调整大小")
        sample_size = len(res78) - sample_data_start
    
    sample_data = res78[sample_data_start:sample_data_start + sample_size]
    print(f"实际样本数据: {len(sample_data)} bytes")
    print(f"样本数据前16字节: {sample_data[:16].hex()}")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'sfx_wav', 'res078_ida')
    os.makedirs(output_dir, exist_ok=True)
    
    # 尝试不同解码参数
    print(f"\n生成WAV文件...")
    
    # IMA ADPCM 16-bit @ 11025Hz
    for predictor in [0, 128, 1024, -128]:
        for index in [0, 1, 2]:
            pcm = ima_adpcm_decode_16bit(sample_data, predictor, index)
            wav_data = create_wav(pcm, 11025)
            filename = f"adpcm16_p{predictor}_i{index}_11025.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(wav_data)
            print(f"生成: {filename}")
    
    # IMA ADPCM 8-bit @ 11025Hz
    for predictor in [0, 128]:
        pcm = ima_adpcm_decode_8bit(sample_data, predictor, 0)
        wav_data = create_wav(pcm, 11025, bits_per_sample=8)
        filename = f"adpcm8_p{predictor}_11025.wav"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(wav_data)
        print(f"生成: {filename}")
    
    # 也尝试直接PCM格式（之前效果较好的格式）
    for skip in [0, 2, 4]:
        if skip > 0 and len(sample_data) <= skip:
            continue
        raw = sample_data[skip:]
        if len(raw) >= 2:
            # 16-bit big-endian
            samples_be = []
            for i in range(0, len(raw) - 1, 2):
                samples_be.append(struct.unpack_from('>h', raw, i)[0])
            pcm_be = struct.pack('<' + 'h' * len(samples_be), *samples_be)
            wav_be = create_wav(pcm_be, 11025)
            filename = f"pcm16be_skip{skip}_11025.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(wav_be)
            print(f"生成: {filename}")
            
            # 16-bit little-endian
            samples_le = []
            for i in range(0, len(raw) - 1, 2):
                samples_le.append(struct.unpack_from('<h', raw, i)[0])
            pcm_le = struct.pack('<' + 'h' * len(samples_le), *samples_le)
            wav_le = create_wav(pcm_le, 11025)
            filename = f"pcm16le_skip{skip}_11025.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(wav_le)
            print(f"生成: {filename}")
    
    # 尝试更低的采样率（用户之前反馈8000Hz更舒服）
    for sample_rate in [8000, 5512]:
        pcm = ima_adpcm_decode_16bit(sample_data, 128, 0)
        wav_data = create_wav(pcm, sample_rate)
        filename = f"adpcm16_p128_{sample_rate}hz.wav"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(wav_data)
        print(f"生成: {filename}")
    
    print(f"\n所有文件已保存到: {output_dir}")
    print(f"\n建议测试顺序:")
    print(f"1. adpcm16_p128_i0_11025.wav - 标准IMA ADPCM 16位")
    print(f"2. pcm16be_skip0_11025.wav - 16位大端PCM")
    print(f"3. adpcm16_p128_8000hz.wav - 8000Hz采样率")
    print(f"4. adpcm16_p128_5512hz.wav - 5512Hz采样率")

if __name__ == '__main__':
    main()