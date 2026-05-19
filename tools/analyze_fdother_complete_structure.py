#!/usr/bin/env python3
"""
全面分析FDOTHER.DAT文件：
1. 找出所有嵌套DAT文件
2. 详细分析索引13的数据结构（LMI音频格式）
3. 分析所有资源类型分布
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def parse_resource_type(data):
    """识别资源类型"""
    if len(data) < 6:
        return "太小的数据"
    
    # 检查是否是嵌套DAT
    if data[:6] == DAT_MAGIC:
        count = struct.unpack_from("<I", data, 6)[0]
        return f"嵌套DAT (子资源数: {count})"
    
    # 检查常见文件头
    if data[:4] == b'LMI1':
        return "LMI1 音频"
    if data[:4] == b'LMI2':
        return "LMI2 音频"
    if data[:4] == b'LMI0':
        return "LMI0 音频"
    if data[:4] == b'AFM1':
        return "AFM1 动画"
    if data[:4] == b'AFM2':
        return "AFM2 动画"
    if data[:2] == b'BM':
        return "BMP 图片"
    if data[:4] == b'RIFF':
        return "RIFF/WAV 音频"
    if data[:4] == b'\x89PNG':
        return "PNG 图片"
    if data[:3] == b'\xFF\xD8\xFF':
        return "JPEG 图片"
    
    # 尝试解析为RLE图片
    if len(data) >= 4:
        width = struct.unpack_from("<H", data, 0)[0]
        height = struct.unpack_from("<H", data, 2)[0]
        if 0 < width <= 2000 and 0 < height <= 2000:
            return f"RLE图片 ({width}x{height})"
    
    # 检查是否是调色板
    if len(data) == 768:
        return "调色板 (256色)"
    
    return "二进制数据"

def analyze_all_resources():
    """分析所有资源，找出嵌套DAT"""
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    file_size = len(data)
    
    res_count = struct.unpack_from("<I", data, 6)[0]
    
    # 解析所有资源的偏移
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])
    
    print(f"FDOTHER.DAT 分析:")
    print(f"  文件大小: {file_size} 字节")
    print(f"  资源数量: {res_count}")
    print(f"  解析到偏移数: {len(offsets)}")
    
    # 分析每个资源
    nested_dat_indices = []
    lmi_audio_indices = []
    image_indices = []
    palette_indices = []
    other_indices = []
    
    print(f"\n{'='*80}")
    print(f"所有资源类型分析:")
    print(f"{'索引':>5} {'偏移':>10} {'大小':>10} {'类型':<30}")
    print(f"{'='*80}")
    
    for i, start in enumerate(offsets):
        end = offsets[i + 1] if (i + 1) < len(offsets) else file_size
        size = end - start
        res_data = data[start:end]
        res_type = parse_resource_type(res_data)
        
        print(f"[{i:>3}] 0x{start:>8X} {size:>10} {res_type}")
        
        # 分类
        if "嵌套DAT" in res_type:
            nested_dat_indices.append(i)
        elif "LMI" in res_type:
            lmi_audio_indices.append(i)
        elif "RLE图片" in res_type or "BMP" in res_type or "PNG" in res_type or "JPEG" in res_type:
            image_indices.append(i)
        elif "调色板" in res_type:
            palette_indices.append(i)
        else:
            other_indices.append(i)
    
    print(f"\n{'='*80}")
    print(f"资源分类统计:")
    print(f"  嵌套DAT: {len(nested_dat_indices)} 个 - 索引: {nested_dat_indices}")
    print(f"  LMI音频: {len(lmi_audio_indices)} 个 - 索引: {lmi_audio_indices}")
    print(f"  图片:    {len(image_indices)} 个")
    print(f"  调色板:  {len(palette_indices)} 个 - 索引: {palette_indices}")
    print(f"  其他:    {len(other_indices)} 个")
    
    # 详细分析嵌套DAT
    if nested_dat_indices:
        print(f"\n{'='*80}")
        print(f"嵌套DAT详细分析:")
        for idx in nested_dat_indices:
            start = offsets[idx]
            end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
            res_data = data[start:end]
            
            nested_count = struct.unpack_from("<I", res_data, 6)[0]
            print(f"\n  索引 {idx} (偏移0x{start:X}, 大小{len(res_data)}字节):")
            print(f"    子资源数量: {nested_count}")
            
            # 解析嵌套资源
            nested_offsets = []
            for j in range(nested_count):
                off_pos = 10 + j * 4
                if off_pos + 4 <= len(res_data):
                    nested_offsets.append(struct.unpack_from("<I", res_data, off_pos)[0])
            
            print(f"    嵌套资源列表:")
            for j, n_offset in enumerate(nested_offsets):
                if j < len(nested_offsets) - 1:
                    n_end = nested_offsets[j + 1]
                else:
                    n_end = len(res_data)
                n_size = n_end - n_offset
                n_data = res_data[n_offset:n_end]
                n_type = parse_resource_type(n_data)
                print(f"      [{j}] 偏移0x{n_offset:X}, 大小{n_size}字节, 类型:{n_type}")
    
    # 详细分析索引13
    print(f"\n{'='*80}")
    print(f"索引13详细分析:")
    idx = 13
    if idx < len(offsets):
        start = offsets[idx]
        end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
        res_data = data[start:end]
        
        print(f"  偏移: 0x{start:X} ({start})")
        print(f"  大小: {len(res_data)} 字节")
        print(f"  文件头: {res_data[:4]} ({res_data[:4].hex(' ')})")
        
        # LMI格式分析
        if res_data[:4] == b'LMI1':
            print(f"\n  [LMI1 音频格式]")
            # 跳过LMI1头
            if len(res_data) >= 8:
                # 可能包含音频块信息
                print(f"  字节4-7: {res_data[4:8].hex(' ')}")
            
            # 分析内部结构
            print(f"\n  数据分布:")
            # 查找重复模式
            for i in range(0, min(100, len(res_data)), 16):
                chunk = res_data[i:i+16]
                print(f"    +{i:04X}: {chunk.hex(' ')}")
    
    # 列出LMI音频资源
    print(f"\n{'='*80}")
    print(f"LMI音频资源列表:")
    for idx in lmi_audio_indices:
        start = offsets[idx]
        end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
        size = end - start
        print(f"  索引{idx}: 偏移0x{start:X}, 大小{size}字节")

if __name__ == "__main__":
    analyze_all_resources()
