#!/usr/bin/env python3
"""分析FDOTHER.DAT资源6的实际结构"""

import struct

def analyze_resource6():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    # FDOTHER.DAT的资源表结构：
    # 偏移0-5: 文件头
    # 偏移6开始: 资源偏移表（每项4字节）
    
    # 先读取资源6的表项
    resource6_table_offset = 6 + 6 * 4  # 6 + 24 = 30
    if resource6_table_offset + 4 > len(data):
        print(f"错误: 资源6表项超出文件范围")
        return
    
    resource6_offset = struct.unpack('<I', data[resource6_table_offset:resource6_table_offset+4])[0]
    print(f"\n资源6:")
    print(f"  表项位置: {resource6_table_offset} (0x{resource6_table_offset:04X})")
    print(f"  资源偏移: {resource6_offset} (0x{resource6_offset:04X})")
    
    if resource6_offset == 0 or resource6_offset >= len(data):
        print(f"  错误: 无效偏移")
        return
    
    # 读取下一个资源的偏移，计算资源6的大小
    resource7_table_offset = 6 + 7 * 4  # 6 + 28 = 34
    if resource7_table_offset + 4 <= len(data):
        resource7_offset = struct.unpack('<I', data[resource7_table_offset:resource7_table_offset+4])[0]
        if resource7_offset > resource6_offset:
            resource6_size = resource7_offset - resource6_offset
            print(f"  资源7偏移: {resource7_offset}")
            print(f"  资源6大小: {resource6_size}")
    
    # 分析资源6的数据
    resource6_data = data[resource6_offset:resource6_offset+530]  # 读取前530字节
    print(f"\n  资源6前6字节 (头部): {' '.join(f'{b:02X}' for b in resource6_data[0:6])}")
    
    # 尝试解析为资源表
    print(f"\n  资源6的前50个表项 (从偏移6开始):")
    for idx in range(0, 50):
        table_offset = 6 + idx * 4
        if table_offset + 4 > len(resource6_data):
            print(f"    索引{idx}: 超出数据范围")
            break
        
        rel_offset = struct.unpack('<I', resource6_data[table_offset:table_offset+4])[0]
        
        # 检查是否是有效的图像偏移
        if rel_offset > 0 and rel_offset < len(resource6_data):
            w = struct.unpack('<H', resource6_data[rel_offset:rel_offset+2])[0]
            h = struct.unpack('<H', resource6_data[rel_offset+2:rel_offset+4])[0]
            
            if w > 0 and w < 256 and h > 0 and h < 256:
                print(f"    索引{idx:3d} (偏移{table_offset:4d}): 相对偏移={rel_offset:6d} -> 图像 {w}x{h}")
            elif idx == 130 or idx <= 5:
                print(f"    索引{idx:3d} (偏移{table_offset:4d}): 相对偏移={rel_offset:6d} (0x{rel_offset:04X})")
                if idx == 130:
                    print(f"      前32字节: {' '.join(f'{b:02X}' for b in resource6_data[rel_offset:rel_offset+32])}")
        elif idx == 130:
            print(f"    索引{idx:3d} (偏移{table_offset:4d}): 相对偏移={rel_offset:6d} (0x{rel_offset:04X})")

if __name__ == '__main__':
    analyze_resource6()
