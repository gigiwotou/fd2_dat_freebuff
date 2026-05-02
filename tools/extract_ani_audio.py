#!/usr/bin/env python3
"""
从ANI.DAT中提取闪电音效的音频样本数据
根据IDA分析 sub_20421 和 sub_25A96:
- 闪电音效样本嵌入在ANI.DAT的AFM帧数据中
- 帧头8字节: [size(2)][param(2)][sample_offset(2)][sample_end(2)]
- 样本数据从帧数据的 sample_offset 开始，大小为 sample_end - sample_offset
"""

import struct
import os
import wave

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ani_path = os.path.join(base_dir, 'game', 'ANI.DAT')
    if not os.path.exists(ani_path):
        ani_path = os.path.join(base_dir, 'ANI.DAT')
        if not os.path.exists(ani_path):
            print("错误: 找不到 ANI.DAT")
            return
    
    print(f"使用文件: {ani_path}")
    
    with open(ani_path, 'rb') as f:
        ani_data = f.read()
    
    print(f"ANI.DAT大小: {len(ani_data)} 字节")
    
    # 验证魔数
    magic = ani_data[:6]
    print(f"Magic: {magic}")
    if magic != b'LLLLLL':
        print("警告: 魔数不匹配")
    
    # 解析索引表
    print(f"\n--- 索引表 ---")
    index_table = []
    for index in range(100):
        offset = 4 * index + 6
        if offset + 4 > len(ani_data):
            break
        
        value = struct.unpack('<I', ani_data[offset:offset+4])[0]
        
        if value == 0 or value >= len(ani_data) - 100:
            continue
        
        # 检查是否是 AFM
        if b'AFM - Animation' in ani_data[value:value+50] or b'AFM' in ani_data[value:value+50]:
            index_table.append((index, value))
            print(f"  索引{index}: 偏移 0x{value:x} ({value})")
    
    print(f"\n找到 {len(index_table)} 个AFM资源")
    
    # 分析第一个AFM (闪电效果可能是索引0)
    for afm_idx, afm_offset in index_table[:3]:  # 分析前3个
        print(f"\n{'='*60}")
        print(f"分析 AFM 索引 {afm_idx} (偏移 0x{afm_offset:x})")
        print(f"{'='*60}")
        
        # 读取AFM头
        # 帧数在偏移0xA5处
        frame_count = struct.unpack('<H', ani_data[afm_offset + 0xA5:afm_offset + 0xA7])[0]
        title = ani_data[afm_offset + 0x51:afm_offset + 0x70].rstrip(b'\x00').decode('ascii', errors='replace')
        print(f"  帧数: {frame_count}")
        print(f"  标题: {title}")
        
        # 读取帧
        pos = afm_offset + 0xAA  # 帧数据起始位置
        for frame_i in range(min(frame_count, 10)):  # 只分析前10帧
            if pos + 8 > len(ani_data):
                break
            
            # 读取帧头 (8字节)
            frame_header = ani_data[pos:pos+8]
            size = struct.unpack('<H', frame_header[0:2])[0]
            param = struct.unpack('<H', frame_header[2:4])[0]
            sample_off = struct.unpack('<H', frame_header[4:6])[0]
            sample_end = struct.unpack('<H', frame_header[6:8])[0]
            
            print(f"\n  帧 {frame_i}: size={size}, param={param}, sample_off={sample_off}, sample_end={sample_end}")
            
            pos += 8
            
            if pos + size > len(ani_data):
                print(f"    帧数据超出文件范围")
                break
            
            frame_data = ani_data[pos:pos+size]
            print(f"    帧数据前32字节: {frame_data[:32].hex(' ')}")
            
            # 检查是否有嵌入的音频样本
            if sample_off > 0 and sample_end > sample_off and sample_end <= size:
                sample_size = sample_end - sample_off
                sample_data = frame_data[sample_off:sample_end]
                print(f"    *** 发现音频样本: 偏移={sample_off}, 大小={sample_size}")
                print(f"    样本前32字节: {sample_data[:32].hex(' ')}")
                
                # 保存到文件
                output_dir = os.path.join(base_dir, 'output', 'sfx_wav', 'ani_extracted')
                os.makedirs(output_dir, exist_ok=True)
                
                sample_file = os.path.join(output_dir, f'afm{afm_idx}_frame{frame_i}_sample_{sample_size}.bin')
                with open(sample_file, 'wb') as f:
                    f.write(sample_data)
                print(f"    样本保存到: {sample_file}")
                
                # 尝试解码为WAV
                # 根据IDA: 默认采样率11025Hz
                # 尝试作为16-bit little-endian PCM
                if sample_size % 2 == 0:
                    wav_file = os.path.join(output_dir, f'afm{afm_idx}_frame{frame_i}_16le_11025hz.wav')
                    with wave.open(wav_file, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(11025)
                        wf.writeframes(sample_data)
                    print(f"    WAV (16le 11025hz): {wav_file}")
                
                # 尝试作为8-bit unsigned PCM
                wav_file = os.path.join(output_dir, f'afm{afm_idx}_frame{frame_i}_8bit_11025hz.wav')
                with wave.open(wav_file, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(1)
                    wf.setframerate(11025)
                    wf.writeframes(sample_data)
                print(f"    WAV (8bit 11025hz): {wav_file}")
                
            pos += size

if __name__ == '__main__':
    main()
