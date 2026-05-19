#!/usr/bin/env python3
"""
详细分析FDOTHER.DAT中所有嵌套DAT的内部资源
输出每个嵌套DAT的资源数量、各资源的偏移/尺寸
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def identify_resource_type(data):
    """识别子资源类型"""
    if len(data) < 4:
        return f"小数据({len(data)}字节)"
    
    # RLE图片格式：前2字节是宽，后2字节是高
    width = struct.unpack_from("<H", data, 0)[0]
    height = struct.unpack_from("<H", data, 2)[0]
    
    if 0 < width <= 2000 and 0 < height <= 2000:
        return f"RLE图片({width}x{height})"
    
    # LMI音频
    if data[:4] in [b'LMI0', b'LMI1', b'LMI2', b'LMI3']:
        return f"{data[:4].decode('ascii', errors='replace')}音频"
    
    # 调色板
    if len(data) == 768:
        return "调色板"
    
    # 其他
    return f"二进制({data[:4].hex(' ')})"

def analyze_all_nested_dat():
    """分析所有嵌套DAT"""
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
    
    print(f"FDOTHER.DAT - 嵌套DAT完整分析")
    print(f"{'='*80}\n")
    
    # 查找所有嵌套DAT
    nested_indices = []
    for i, start in enumerate(offsets):
        end = offsets[i + 1] if (i + 1) < len(offsets) else file_size
        res_data = data[start:end]
        if res_data[:6] == DAT_MAGIC:
            nested_indices.append(i)
    
    print(f"共找到 {len(nested_indices)} 个嵌套DAT文件\n")
    
    # 分析每个嵌套DAT
    for idx in nested_indices:
        start = offsets[idx]
        end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
        res_data = data[start:end]
        
        nested_count = struct.unpack_from("<I", res_data, 6)[0]
        
        # 解析嵌套偏移表
        nested_offsets = []
        for j in range(nested_count):
            off_pos = 10 + j * 4
            if off_pos + 4 <= len(res_data):
                nested_offsets.append(struct.unpack_from("<I", res_data, off_pos)[0])
        
        print(f"{'='*80}")
        print(f"索引 {idx} (主文件偏移: 0x{start:X}, 大小: {len(res_data):,} 字节)")
        print(f"嵌套资源数量: {nested_count}")
        print(f"{'-'*80}")
        print(f"{'子索引':>6} {'嵌套偏移':>10} {'大小':>8} {'类型'}")
        print(f"{'-'*80}")
        
        # 分析每个子资源
        for j, n_offset in enumerate(nested_offsets):
            if j < len(nested_offsets) - 1:
                n_end = nested_offsets[j + 1]
            else:
                n_end = len(res_data)
            
            n_size = n_end - n_offset
            n_data = res_data[n_offset:n_end]
            n_type = identify_resource_type(n_data)
            
            print(f"[{j:>4}]  0x{n_offset:>7X} {n_size:>7,} {n_type}")
        
        print()

if __name__ == "__main__":
    analyze_all_nested_dat()
