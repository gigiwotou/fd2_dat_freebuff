#!/usr/bin/env python3
"""
检查FDOTHER.DAT索引7的嵌套DAT文件
查找资源201和205（slot边框图形）
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def analyze_nested_dat_index7():
    """分析索引7的嵌套DAT结构"""
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    
    # 解析主DAT文件头
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: 共 {res_count} 个资源")
    
    # 解析索引表
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 获取索引7的资源
    if 7 >= len(offsets):
        print(f"错误: 索引7不存在")
        return
    
    res7_start = offsets[7]
    res7_end = offsets[8] if 8 < len(offsets) else len(data)
    res7_data = data[res7_start:res7_end]
    
    print(f"\n{'='*60}")
    print(f"索引7资源信息:")
    print(f"  起始偏移: {res7_start} (0x{res7_start:X})")
    print(f"  结束偏移: {res7_end} (0x{res7_end:X})")
    print(f"  大小: {len(res7_data)} 字节")
    print(f"  文件头: {res7_data[:6]}")
    
    # 检查是否是嵌套DAT
    if res7_data[:6] != DAT_MAGIC:
        print(f"  警告: 不是嵌套DAT格式")
        return
    
    # 解析嵌套DAT的索引表
    nested_count = struct.unpack_from("<I", res7_data, 6)[0]
    print(f"\n嵌套DAT信息:")
    print(f"  子资源数量: {nested_count}")
    
    # 解析嵌套DAT的索引表
    nested_offsets = []
    for i in range(nested_count):
        off = 10 + i * 4
        if off + 4 <= len(res7_data):
            nested_offsets.append(struct.unpack_from("<I", res7_data, off)[0])
    
    print(f"\n所有子资源的偏移信息:")
    print(f"{'索引':>4} {'偏移':>8} {'大小':>8} {'头16字节'} {'类型'}")
    print("-" * 80)
    
    # 检查所有资源
    for i in range(len(nested_offsets)):
        s = nested_offsets[i]
        e = nested_offsets[i+1] if i+1 < len(nested_offsets) else len(res7_data)
        sz = e - s
        
        if s < len(res7_data):
            header = res7_data[s:s+16].hex()
            
            # 判断类型
            type_info = ""
            if sz >= 4:
                w, h = struct.unpack_from("<HH", res7_data, s)
                if 0 < w <= 640 and 0 < h <= 480:
                    type_info = f"图像 {w}x{h}"
                elif sz < 100:
                    type_info = f"小数据块"
                else:
                    type_info = f"大数据块"
            
            # 特别标记资源201和205
            marker = ""
            if i == 201 or i == 205:
                marker = " <<< 目标资源"
            
            print(f"[{i:3}] {s:8} {sz:8} {header} {type_info}{marker}")
    
    # 详细分析资源201和205
    print(f"\n{'='*60}")
    print("资源201详细分析:")
    print(f"{'='*60}")
    analyze_resource(res7_data, nested_offsets, 201)
    
    print(f"\n{'='*60}")
    print("资源205详细分析:")
    print(f"{'='*60}")
    analyze_resource(res7_data, nested_offsets, 205)

def analyze_resource(res7_data, nested_offsets, index):
    """分析指定索引的资源"""
    if index >= len(nested_offsets):
        print(f"  资源{index}不存在（总共{len(nested_offsets)}个子资源）")
        return
    
    s = nested_offsets[index]
    e = nested_offsets[index+1] if index+1 < len(nested_offsets) else len(res7_data)
    sz = e - s
    
    print(f"  偏移: {s} (0x{s:X})")
    print(f"  大小: {sz} 字节")
    
    if sz < 4:
        print(f"  数据太小，无法解析")
        return
    
    # 尝试解析为图像
    w, h = struct.unpack_from("<HH", res7_data, s)
    print(f"  可能的图像尺寸: {w}x{h}")
    
    if 0 < w <= 640 and 0 < h <= 480:
        rle_data = res7_data[s+4:s+24]
        print(f"  RLE数据前20字节: {rle_data.hex()}")
        
        # 计算理论RLE大小
        theoretical_rle_size = sz - 4
        print(f"  RLE数据大小: {theoretical_rle_size} 字节")
        
        # 尝试简单分析RLE压缩率
        compressed = res7_data[s+4:e]
        uncompressed_size = w * h
        compression_ratio = uncompressed_size / len(compressed) if len(compressed) > 0 else 0
        print(f"  未压缩大小: {uncompressed_size} 字节")
        print(f"  压缩比: {compression_ratio:.2f}:1")

if __name__ == "__main__":
    analyze_nested_dat_index7()
