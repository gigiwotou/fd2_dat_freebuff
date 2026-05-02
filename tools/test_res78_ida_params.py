#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据IDA分析结果提取res78闪电音效
关键发现:
- sub_414E0 (AIL_init_sample) 设置采样率为 11025 Hz
- sub_25A96 从 FDOTHER.DAT 的 res78 提取样本
- 样本起始: *(v8+6), 样本结束: *(v8+10)
- 样本大小 = *(v8+10) - *(v8+6)
"""

import struct
import os
import sys

def parse_res78_header(raw):
    """解析res78头部"""
    v6 = struct.unpack_from('<I', raw, 6)[0]
    v10 = struct.unpack_from('<I', raw, 10)[0]
    sample_start = v6
    sample_size = v10 - v6
    sample_end = v6 + sample_size
    
    print(f"--- IDA汇编解析 ---")
    print(f"*(6) = 0x{v6:x} ({v6})")
    print(f"*(10) = 0x{v10:x} ({v10})")
    print(f"样本起始: 0x{sample_start:x} ({sample_start})")
    print(f"样本大小: 0x{sample_size:x} ({sample_size})")
    print(f"样本结束: 0x{sample_end:x} ({sample_end})")
    
    return sample_start, sample_size, sample_end

def ima_adpcm_decode(adpcm_data, initial_predictor=0, initial_index=0, sample_rate=11025):
    """
    IMA ADPCM 4-bit 解码
    根据 Miles Sound System 的解码逻辑
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
    
    # 如果数据以2字节开始，可能是头部信息
    # 尝试跳过不同的头部大小
    for skip_header in [0, 2, 4]:
        if skip_header > 0 and len(adpcm_data) <= skip_header:
            continue
            
        data = adpcm_data[skip_header:]
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
        
        if len(output) > 0:
            return b''.join(output), skip_header
    
    return b''.join(output), 0

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
        1,  # PCM
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
    # 读取 FDOTHER.DAT (可能在根目录或game/目录)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    if not os.path.exists(fdother_path):
        fdother_path = os.path.join(base_dir, 'FDOTHER.DAT')
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT")
        print(f"尝试路径: {os.path.join(base_dir, 'game', 'FDOTHER.DAT')}")
        print(f"尝试路径: {os.path.join(base_dir, 'FDOTHER.DAT')}")
        sys.exit(1)
    
    print(f"使用文件: {fdother_path}")
    
    with open(fdother_path, 'rb') as f:
        dat_data = f.read()
    
    # 解析FDOTHER.DAT格式
    # 格式: [magic(6)][count(4)][offsets(N*4)][资源数据]
    magic = dat_data[:6]
    res_count = struct.unpack_from('<I', dat_data, 6)[0]
    print(f"Magic: {magic}")
    print(f"资源数量: {res_count}")
    
    # 找到res78 (索引78)
    if res_count <= 78:
        print(f"错误: 资源数量 {res_count} 小于 78")
        sys.exit(1)
    
    # 偏移表从字节10开始 (6+4)
    offset_table_start = 10
    res78_offset = struct.unpack_from('<I', dat_data, offset_table_start + 78 * 4)[0]
    res79_offset = struct.unpack_from('<I', dat_data, offset_table_start + 79 * 4)[0] if 79 < res_count else len(dat_data)
    res78_size = res79_offset - res78_offset
    
    print(f"res78 偏移: 0x{res78_offset:x} ({res78_offset})")
    print(f"res78 大小: {res78_size} 字节")
    
    # 读取res78
    res78_raw = dat_data[res78_offset:res78_offset + res78_size]
    print(f"res78 实际读取: {len(res78_raw)} 字节")
    print(f"res78 前16字节: {res78_raw[:16].hex()}")
    
    # 解析头部获取样本位置
    sample_start, sample_size, sample_end = parse_res78_header(res78_raw)
    
    # 提取样本数据
    if sample_start + sample_size <= len(res78_raw):
        sample_data = res78_raw[sample_start:sample_start + sample_size]
        print(f"样本数据: {len(sample_data)} 字节")
        
        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'sfx_wav', 'res078_final')
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用IDA发现的参数解码: 11025 Hz
        # 尝试不同的初始预测值
        for predictor in [0, 128, 1024, -128, -1024]:
            for skip in [0, 2, 4]:
                if skip > 0 and len(sample_data) <= skip:
                    continue
                    
                pcm, actual_skip = ima_adpcm_decode(sample_data, predictor, 0, 11025)
                if len(pcm) > 0:
                    wav_data = create_wav(pcm, 11025)
                    filename = f"adpcm11025_p{predictor}_skip{skip}.wav"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(wav_data)
                    print(f"生成: {filename} ({len(pcm)} 字节PCM)")
        
        # 也尝试16位大端PCM格式 (之前用户反馈较好的格式)
        # 但以11025 Hz采样率
        for skip in [0, 2, 4, 8]:
            if skip > 0 and len(sample_data) <= skip:
                continue
            raw_pcm = sample_data[skip:]
            if len(raw_pcm) >= 2:
                # 16-bit big-endian
                samples = []
                for i in range(0, len(raw_pcm) - 1, 2):
                    sample = struct.unpack_from('>h', raw_pcm, i)[0]
                    samples.append(sample)
                
                pcm_data = struct.pack('<' + 'h' * len(samples), *samples)
                wav_data = create_wav(pcm_data, 11025)
                filename = f"pcm16be_11025_skip{skip}.wav"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(wav_data)
                print(f"生成: {filename} ({len(samples)} 采样)")
        
        print(f"\n所有文件已保存到: {output_dir}")
    else:
        print(f"错误: 样本超出数据范围")

if __name__ == "__main__":
    main()
