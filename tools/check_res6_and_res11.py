#!/usr/bin/env python3
"""
详细分析FDOTHER.DAT索引6和索引11的嵌套DAT
检查是否包含资源201和205（slot边框图形）
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def analyze_nested_dat(res_data, res_index):
    """分析嵌套DAT结构"""
    if res_data[:6] != DAT_MAGIC:
        print(f"资源{res_index}不是嵌套DAT格式")
        return
    
    nested_count = struct.unpack_from("<I", res_data, 6)[0]
    print(f"\n{'='*80}")
    print(f"资源 {res_index} 嵌套DAT分析:")
    print(f"  总大小: {len(res_data)} 字节")
    print(f"  子资源数量: {nested_count}")
    print(f"{'='*80}")
    
    # 解析所有偏移
    nested_offsets = []
    for i in range(nested_count):
        off = 10 + i * 4
        if off + 4 <= len(res_data):
            nested_offsets.append(struct.unpack_from("<I", res_data, off)[0])
        else:
            nested_offsets.append(None)
    
    # 输出所有资源信息
    print(f"\n{'索引':>4} {'偏移':>8} {'大小':>8} {'尺寸':>10} {'头16字节'} {'类型'}")
    print("-" * 100)
    
    for i in range(len(nested_offsets)):
        if nested_offsets[i] is None:
            print(f"[{i:3}] 偏移表超出范围")
            continue
        
        s = nested_offsets[i]
        e = nested_offsets[i+1] if i+1 < len(nested_offsets) and nested_offsets[i+1] is not None else len(res_data)
        sz = e - s
        
        if s >= len(res_data):
            print(f"[{i:3}] 偏移超出数据范围")
            continue
        
        header = res_data[s:s+16].hex()
        
        # 尝试解析为图像
        type_info = "未知"
        dimensions = "N/A"
        if sz >= 4:
            w, h = struct.unpack_from("<HH", res_data, s)
            dimensions = f"{w}x{h}"
            if 0 < w <= 640 and 0 < h <= 480:
                type_info = "RLE图像"
            elif sz < 100:
                type_info = "小数据块"
            else:
                type_info = "数据块"
        
        # 特别标记201和205
        marker = ""
        if i in [201, 205]:
            marker = " <<< 目标"
        
        print(f"[{i:3}] {s:8} {sz:8} {dimensions:>10} {header} {type_info}{marker}")
    
    # 检查是否有201和205
    print(f"\n{'='*80}")
    if nested_count > 205:
        print(f"*** 资源{res_index} 包含资源201和205 ***")
        
        for idx in [201, 205]:
            if nested_offsets[idx] is not None and nested_offsets[idx] < len(res_data):
                s = nested_offsets[idx]
                e = nested_offsets[idx+1] if idx+1 < len(nested_offsets) and nested_offsets[idx+1] is not None else len(res_data)
                sz = e - s
                
                print(f"\n资源 {idx} 详情:")
                print(f"  偏移: {s} (0x{s:X})")
                print(f"  大小: {sz} 字节")
                
                if sz >= 4:
                    w, h = struct.unpack_from("<HH", res_data, s)
                    print(f"  尺寸: {w}x{h}")
                    
                    # RLE数据分析
                    rle_data = res_data[s+4:s+24]
                    print(f"  RLE前20字节: {rle_data.hex()}")
                    
                    uncompressed = w * h
                    compressed = sz - 4
                    ratio = uncompressed / compressed if compressed > 0 else 0
                    print(f"  压缩前: {uncompressed} 字节")
                    print(f"  压缩后: {compressed} 字节")
                    print(f"  压缩比: {ratio:.2f}:1")
    else:
        print(f"资源{res_index}只有{nested_count}个子资源，不包含201和205")

def main():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    res_count = struct.unpack_from("<I", data, 6)[0]
    
    # 解析索引表
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 分析索引6的嵌套DAT
    if 6 < len(offsets):
        s = offsets[6]
        e = offsets[7] if 7 < len(offsets) else len(data)
        res6_data = data[s:e]
        analyze_nested_dat(res6_data, 6)
    
    # 分析索引11的嵌套DAT
    if 11 < len(offsets):
        s = offsets[11]
        e = offsets[12] if 12 < len(offsets) else len(data)
        res11_data = data[s:e]
        analyze_nested_dat(res11_data, 11)
    
    # 也检查一下其他可能有200+子资源的嵌套DAT
    print(f"\n{'='*80}")
    print("查找所有可能包含201和205的嵌套DAT:")
    print(f"{'='*80}")
    
    for i in range(res_count):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[s:e]
        
        if res_data[:6] == DAT_MAGIC:
            nested_count = struct.unpack_from("<I", res_data, 6)[0]
            if nested_count > 205:
                print(f"资源 {i}: {nested_count} 个子资源 - 包含201和205")

if __name__ == "__main__":
    main()
