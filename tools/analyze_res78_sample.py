#!/usr/bin/env python3
"""
根据IDA分析结果深度解析res78样本结构
重点查找样本头部的采样率信息
"""
import struct
import os
import sys

def analyze_res78():
    # 读取FDOTHER.DAT
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        fdother_path = os.path.join(base_dir, 'FDOTHER.DAT')
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT")
        sys.exit(1)
    
    print(f"使用文件: {fdother_path}")
    
    with open(fdother_path, 'rb') as f:
        # FDOTHER.DAT格式: [magic(6)][count(4)][offsets(N*4)][资源数据]
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        print(f"Magic: {magic}")
        print(f"资源数量: {count}")
        
        # 读取偏移表
        f.seek(10)  # 6 + 4
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # 获取res78
    idx = 78
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
    size = end - start
    
    print(f"\nres78:")
    print(f"  起始偏移: 0x{start:x} ({start})")
    print(f"  结束偏移: 0x{end:x} ({end})")
    print(f"  大小: {size} bytes (0x{size:x})")
    
    # 读取res78完整数据
    with open(fdother_path, 'rb') as f:
        f.seek(start)
        res78 = f.read(size)
    
    print(f"\nres78头部详细分析 (前256字节):")
    print("=" * 80)
    for i in range(0, min(256, len(res78)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in res78[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res78[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    print(f"\n关键位置值分析:")
    print("=" * 80)
    for offset in range(0, 64, 2):
        if offset + 2 <= len(res78):
            val_w = struct.unpack_from('<H', res78, offset)[0]
            print(f"  WORD +{offset:02x}: {val_w:5d} (0x{val_w:04x})")
        if offset + 4 <= len(res78):
            val_d = struct.unpack_from('<I', res78, offset)[0]
            print(f"  DWORD+{offset:02x}: {val_d:10d} (0x{val_d:08x})")
    
    # 根据IDA汇编sub_25A96解析样本位置
    print(f"\n根据IDA sub_25A96解析样本:")
    print("=" * 80)
    v6 = struct.unpack_from('<I', res78, 6)[0]
    v10 = struct.unpack_from('<I', res78, 10)[0]
    sample_start = v6
    sample_size = v10 - v6
    
    print(f"  *(res78+6)  = {v6} (0x{v6:x})")
    print(f"  *(res78+10) = {v10} (0x{v10:x})")
    print(f"  样本起始位置: {sample_start}")
    print(f"  样本大小: {sample_size}")
    print(f"  样本结束: {sample_start + sample_size}")
    
    # 提取样本数据
    if sample_start + sample_size <= len(res78):
        sample_data = res78[sample_start:sample_start + sample_size]
        
        print(f"\n样本数据前64字节:")
        hex_str = ' '.join(f'{b:02x}' for b in sample_data[:64])
        print(f"  {hex_str}")
        
        # 分析样本头部的可能采样率信息
        print(f"\n样本头部可能的采样率字段:")
        print("=" * 80)
        for offset in [0, 2, 4, 6, 8, 10, 12, 14]:
            if offset + 4 <= len(sample_data):
                val = struct.unpack_from('<I', sample_data, offset)[0]
                # 检查是否是常见采样率
                if val in [5512, 8000, 11025, 16000, 22050, 44100]:
                    print(f"  *({offset}) = {val} - **常见采样率!**")
        
        # 检查样本前几个字节作为头部
        print(f"\n样本前16字节作为可能头部:")
        for i in range(0, 16, 2):
            if i + 2 <= len(sample_data):
                val_w = struct.unpack_from('<H', sample_data, i)[0]
                print(f"  偏移{i}: WORD = {val_w} (0x{val_w:04x})")
        
        # 保存样本原始数据用于进一步分析
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'sfx_analysis')
        os.makedirs(output_dir, exist_ok=True)
        
        sample_file = os.path.join(output_dir, 'res78_sample.bin')
        with open(sample_file, 'wb') as f:
            f.write(sample_data)
        print(f"\n样本数据已保存到: {sample_file}")
        
        # 同时保存完整res78
        res78_file = os.path.join(output_dir, 'res78_full.bin')
        with open(res78_file, 'wb') as f:
            f.write(res78)
        print(f"完整res78已保存到: {res78_file}")

if __name__ == '__main__':
    analyze_res78()