#!/usr/bin/env python3
"""
正确分析FDOTHER.DAT结构，找到资源201和205
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def main():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    file_size = len(data)
    
    print(f"FDOTHER.DAT 文件大小: {file_size} 字节 ({file_size/1024/1024:.2f} MB)")
    
    # 解析文件头
    magic = data[0:6]
    res_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"文件头: {magic}")
    print(f"资源数量: {res_count}")
    
    # 验证资源数量是否合理
    # 索引表大小 = 6 + 4*res_count
    # 如果res_count=422，索引表大小 = 6 + 4*422 = 1694 字节
    # 这意味着第一个资源应该从约1694字节开始
    
    if res_count > 10000:
        print(f"警告: 资源数量异常大({res_count})，可能解析错误")
        print(f"尝试其他解析方式...")
        
        # 可能字节6-9不是资源数量，而是第一个偏移
        first_offset = struct.unpack_from("<I", data, 6)[0]
        print(f"如果字节6是第一个偏移: {first_offset}")
        
        # 尝试从不同位置解析资源数量
        # 某些DAT格式可能在偏移0有4字节，然后才是数量
        for test_offset in [0, 4, 6]:
            val = struct.unpack_from("<I", data, test_offset)[0]
            print(f"偏移{test_offset}处的值: {val} (0x{val:X})")
    
    # 按照之前的分析，res_count=422是正确的
    # 重新解析索引表
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            print(f"警告: 索引{i}的偏移位置{off_pos}超出文件")
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])
    
    print(f"\n实际解析到 {len(offsets)} 个资源的偏移")
    
    # 检查前10个偏移
    print(f"\n前10个偏移:")
    for i in range(min(10, len(offsets))):
        print(f"  [{i}] {offsets[i]} (0x{offsets[i]:X})")
    
    # 检查最后几个偏移
    print(f"\n最后10个偏移:")
    for i in range(max(0, len(offsets)-10), len(offsets)):
        print(f"  [{i}] {offsets[i]} (0x{offsets[i]:X})")
    
    # 检查资源6的嵌套DAT（已知有38个子资源）
    if 6 < len(offsets):
        s = offsets[6]
        e = offsets[7] if 7 < len(offsets) else file_size
        res6_data = data[s:e]
        
        print(f"\n{'='*60}")
        print(f"资源6（嵌套DAT）:")
        print(f"  大小: {len(res6_data)} 字节")
        print(f"  文件头: {res6_data[:6]}")
        
        if res6_data[:6] == DAT_MAGIC:
            nested_count = struct.unpack_from("<I", res6_data, 6)[0]
            print(f"  子资源数: {nested_count}")
            
            # 解析嵌套DAT的索引表
            nested_offsets = []
            for j in range(nested_count):
                off_pos = 10 + j * 4
                if off_pos + 4 <= len(res6_data):
                    nested_offsets.append(struct.unpack_from("<I", res6_data, off_pos)[0])
            
            print(f"  实际解析到 {len(nested_offsets)} 个偏移")
            print(f"  嵌套索引表结构:")
            print(f"    字节0-5: 魔术头 LLLLLL")
            print(f"    字节6-9: 子资源数量 = {nested_count}")
            print(f"    字节10+: 偏移表")
            
            # 计算嵌套DAT的实际可用数据
            table_size = 10 + nested_count * 4
            actual_data_start = table_size
            
            # 但偏移值是相对于嵌套DAT开头的绝对偏移
            # 需要检查这些偏移是否有效
            valid_offsets = [off for off in nested_offsets if off < len(res6_data)]
            print(f"  有效偏移数: {len(valid_offsets)}/{len(nested_offsets)}")
            
            if valid_offsets:
                print(f"  偏移范围: {min(valid_offsets)} - {max(valid_offsets)}")

if __name__ == "__main__":
    main()
