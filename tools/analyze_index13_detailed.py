#!/usr/bin/env python3
"""
详细分析FDOTHER.DAT索引13的数据结构
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def analyze_index13():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    file_size = len(data)
    
    print(f"FDOTHER.DAT 文件分析")
    print(f"文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")
    
    # 解析主索引表
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])
    
    print(f"资源数量: {res_count}")
    print(f"解析到偏移数: {len(offsets)}")
    
    # 分析索引13
    print(f"\n{'='*60}")
    print(f"索引13详细分析:")
    print(f"{'='*60}")
    
    idx = 13
    if idx < len(offsets):
        start = offsets[idx]
        end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
        size = end - start
        res_data = data[start:end]
        
        print(f"偏移位置: 0x{start:X} ({start:,} 字节)")
        print(f"结束位置: 0x{end:X} ({end:,} 字节)")
        print(f"资源大小: {size:,} 字节 ({size/1024:.1f} KB)")
        print(f"\n文件头 (前32字节):")
        print(f"  {res_data[:32].hex(' ')}")
        print(f"  ASCII: {res_data[:32]}")
        
        # 检查是否是嵌套DAT
        if res_data[:6] == DAT_MAGIC:
            print(f"\n[嵌套DAT文件!]")
            nested_count = struct.unpack_from("<I", res_data, 6)[0]
            print(f"  嵌套资源数量: {nested_count}")
            
            # 解析嵌套资源
            nested_offsets = []
            for j in range(nested_count):
                off_pos = 10 + j * 4
                if off_pos + 4 <= len(res_data):
                    nested_offsets.append(struct.unpack_from("<I", res_data, off_pos)[0])
            
            print(f"\n  嵌套资源列表:")
            print(f"  {'索引':>6} {'偏移':>10} {'大小':>10} {'类型'}")
            print(f"  {'-'*60}")
            
            for j, n_offset in enumerate(nested_offsets):
                if j < len(nested_offsets) - 1:
                    n_end = nested_offsets[j + 1]
                else:
                    n_end = len(res_data)
                n_size = n_end - n_offset
                n_data = res_data[n_offset:n_end]
                
                # 尝试识别类型
                n_type = "未知"
                if n_size >= 4:
                    width = struct.unpack_from("<H", n_data, 0)[0]
                    height = struct.unpack_from("<H", n_data, 2)[0]
                    if 0 < width <= 2000 and 0 < height <= 2000:
                        n_type = f"RLE图片({width}x{height})"
                    elif n_data[:4] in [b'LMI0', b'LMI1', b'LMI2']:
                        n_type = f"{n_data[:4].decode()}音频"
                
                print(f"  [{j:>4}]  0x{n_offset:>7X} {n_size:>10,} {n_type}")
        
        elif res_data[:4] == b'LMI1':
            print(f"\n[LMI1 音频格式]")
            print(f"  这是一个音频文件，不是嵌套DAT")
            
            # 分析LMI1结构
            print(f"\n  LMI1数据样本 (前64字节):")
            for i in range(0, min(64, len(res_data)), 16):
                chunk = res_data[i:i+16]
                print(f"    +{i:04X}: {chunk.hex(' ')}")
        
        else:
            print(f"\n[未知格式]")
            print(f"  前4字节: {res_data[:4].hex(' ')}")

if __name__ == "__main__":
    analyze_index13()
