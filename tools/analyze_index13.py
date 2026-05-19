#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引13的数据结构，检查是否包含嵌套DAT文件
重点关注边框、背景等资源
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def analyze_fdother_index13():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    file_size = len(data)
    
    print(f"FDOTHER.DAT 文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)")
    
    # 解析文件头
    magic = data[0:6]
    res_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"文件头: {magic}")
    print(f"资源数量: {res_count}")
    
    # 解析所有资源的偏移
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])
    
    print(f"\n实际解析到 {len(offsets)} 个资源的偏移")
    
    # 分析索引13的位置和大小
    index = 13
    if index < len(offsets):
        start_offset = offsets[index]
        end_offset = offsets[index + 1] if (index + 1) < len(offsets) else file_size
        res_size = end_offset - start_offset
        
        print(f"\n{'='*60}")
        print(f"索引 {index} 的信息:")
        print(f"  偏移位置: 0x{start_offset:X} ({start_offset})")
        print(f"  结束位置: 0x{end_offset:X} ({end_offset})")
        print(f"  资源大小: {res_size} 字节 ({res_size/1024:.1f} KB)")
        
        # 读取资源数据
        res_data = data[start_offset:end_offset]
        
        # 检查是否是嵌套DAT
        if res_data[:6] == DAT_MAGIC:
            print(f"\n{'='*60}")
            print(f"[是嵌套DAT文件]")
            print(f"  魔术头: {res_data[:6]}")
            
            nested_count = struct.unpack_from("<I", res_data, 6)[0]
            print(f"  嵌套资源数量: {nested_count}")
            
            # 解析嵌套DAT的索引表
            nested_offsets = []
            for j in range(nested_count):
                off_pos = 10 + j * 4
                if off_pos + 4 <= len(res_data):
                    nested_offsets.append(struct.unpack_from("<I", res_data, off_pos)[0])
            
            print(f"  解析到 {len(nested_offsets)} 个嵌套资源偏移")
            
            # 显示所有嵌套资源的偏移
            print(f"\n  嵌套资源偏移列表:")
            for j, offset in enumerate(nested_offsets):
                if j < len(nested_offsets) - 1:
                    next_offset = nested_offsets[j + 1]
                else:
                    next_offset = len(res_data)
                
                sub_size = next_offset - offset
                print(f"    [{j}] 偏移: 0x{offset:X} ({offset}), 大小: {sub_size} 字节")
            
            # 分析每个嵌套资源的内容
            print(f"\n{'='*60}")
            print(f"嵌套资源详细分析:")
            for j, offset in enumerate(nested_offsets):
                if j < len(nested_offsets) - 1:
                    next_offset = nested_offsets[j + 1]
                else:
                    next_offset = len(res_data)
                
                sub_size = next_offset - offset
                sub_data = res_data[offset:next_offset]
                
                print(f"\n  嵌套资源 [{j}]:")
                print(f"    偏移: 0x{offset:X}, 大小: {sub_size} 字节")
                print(f"    前16字节: {sub_data[:16].hex(' ')}")
                
                # 检查是否是图片
                if sub_size > 4:
                    width = struct.unpack_from("<H", sub_data, 0)[0]
                    height = struct.unpack_from("<H", sub_data, 2)[0]
                    if 0 < width <= 2000 and 0 < height <= 2000:
                        print(f"    可能是图片: {width}x{height}")
                        if sub_size > width * height:
                            print(f"    警告: 数据大小大于宽高乘积，可能是压缩格式")
                
                # 检查是否是另一个嵌套DAT
                if sub_data[:6] == DAT_MAGIC:
                    print(f"    [又是嵌套DAT!]")
                    inner_count = struct.unpack_from("<I", sub_data, 6)[0]
                    print(f"    内部资源数量: {inner_count}")
                
                # 检查常见文件头
                if sub_data[:2] == b'BM':
                    print(f"    [BMP图片]")
                elif sub_data[:4] == b'RIFF':
                    print(f"    [RIFF格式]")
        
        else:
            print(f"\n{'='*60}")
            print(f"[不是嵌套DAT文件]")
            print(f"  前32字节: {res_data[:32].hex(' ')}")
            
            # 尝试解析为图片
            if res_size > 4:
                width = struct.unpack_from("<H", res_data, 0)[0]
                height = struct.unpack_from("<H", res_data, 2)[0]
                if 0 < width <= 2000 and 0 < height <= 2000:
                    print(f"  可能是图片: {width}x{height}")
    
    # 对比相邻资源
    print(f"\n{'='*60}")
    print(f"索引12-14的对比:")
    for idx in range(12, 15):
        if idx < len(offsets):
            start = offsets[idx]
            end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
            size = end - start
            res_data = data[start:end]
            is_dat = "是嵌套DAT" if res_data[:6] == DAT_MAGIC else "普通资源"
            print(f"  索引{idx}: 偏移0x{start:X}, 大小{size}字节, {is_dat}")

if __name__ == "__main__":
    analyze_fdother_index13()
