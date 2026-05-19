#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引13的LMI1音频格式内部结构
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")

def analyze_lmi1_index13():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    file_size = len(data)
    
    # 解析主索引表
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])
    
    print(f"FDOTHER.DAT - 索引13详细分析")
    print(f"{'='*80}")
    
    idx = 13
    if idx >= len(offsets):
        print(f"索引13不存在")
        return
    
    start = offsets[idx]
    end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
    res_data = data[start:end]
    
    print(f"\n基本信息:")
    print(f"  主文件偏移: 0x{start:X} ({start:,} 字节)")
    print(f"  结束偏移: 0x{end:X} ({end:,} 字节)")
    print(f"  资源大小: {len(res_data):,} 字节 ({len(res_data)/1024:.1f} KB)")
    print(f"  格式: LMI1 (音频)")
    
    # LMI1头分析
    print(f"\nLMI1头 (前16字节):")
    print(f"  魔术头: {res_data[:4]}")
    print(f"  字节4-7: {res_data[4:8].hex(' ')}")
    print(f"  字节8-15: {res_data[8:16].hex(' ')}")
    
    # 尝试解析为3字节偏移表
    print(f"\n尝试解析为3字节偏移表 (从字节4开始):")
    three_byte_offsets = []
    for i in range(20):
        pos = 4 + i * 3
        if pos + 3 <= len(res_data):
            val = res_data[pos] | (res_data[pos+1] << 8) | (res_data[pos+2] << 16)
            three_byte_offsets.append(val)
            if val < len(res_data):
                print(f"  [{i}] 0x{val:06X} ({val:,}) [有效]")
            else:
                print(f"  [{i}] 0x{val:06X} ({val:,}) [超出范围]")
    
    # 尝试解析为4字节偏移表 (小端序)
    print(f"\n尝试解析为4字节偏移表 (从字节8开始，小端序):")
    four_byte_offsets_le = []
    for i in range(20):
        pos = 8 + i * 4
        if pos + 4 <= len(res_data):
            val = struct.unpack_from("<I", res_data, pos)[0]
            four_byte_offsets_le.append(val)
            if val < len(res_data) and val > 0:
                print(f"  [{i}] 0x{val:08X} ({val:,}) [有效]")
            else:
                print(f"  [{i}] 0x{val:08X} ({val:,}) [无效]")
    
    # 尝试解析为4字节偏移表 (大端序)
    print(f"\n尝试解析为4字节偏移表 (从字节8开始，大端序):")
    for i in range(20):
        pos = 8 + i * 4
        if pos + 4 <= len(res_data):
            val = struct.unpack_from(">I", res_data, pos)[0]
            if val < len(res_data) and val > 0:
                print(f"  [{i}] 0x{val:08X} ({val:,}) [有效]")

if __name__ == "__main__":
    analyze_lmi1_index13()
