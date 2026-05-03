#!/usr/bin/env python3
"""分析FDOTHER.DAT的文件格式"""

import struct

def analyze_fdother_format():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    # 打印前100字节
    print(f"\n文件前100字节:")
    for i in range(0, 100, 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04d} (0x{i:04X}): {hex_str}  {ascii_str}")
    
    # 尝试解析为不同的格式
    
    # 格式1: 偏移6是资源数量
    print(f"\n=== 格式1: 偏移6是资源数量 ===")
    resource_count = struct.unpack('<I', data[6:10])[0]
    print(f"资源数量: {resource_count}")
    
    if resource_count > 0 and resource_count < 10000:
        print(f"偏移10开始的前10个资源偏移:")
        for i in range(10):
            offset = 10 + i * 4
            if offset + 4 > len(data):
                break
            res_offset = struct.unpack('<I', data[offset:offset+4])[0]
            print(f"  资源{i}: 偏移={res_offset} (0x{res_offset:08X})")
    
    # 格式2: 偏移6开始是资源表（每个4字节）
    print(f"\n=== 格式2: 偏移6开始是资源偏移表 ===")
    print(f"前10个资源偏移:")
    for i in range(10):
        offset = 6 + i * 4
        if offset + 4 > len(data):
            break
        res_offset = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"  资源{i}: 偏移={res_offset} (0x{res_offset:08X})")
        
        # 检查该偏移的数据
        if res_offset > 0 and res_offset < len(data) - 4:
            w = struct.unpack('<H', data[res_offset:res_offset+2])[0]
            h = struct.unpack('<H', data[res_offset+2:res_offset+4])[0]
            if w > 0 and w < 256 and h > 0 and h < 256:
                print(f"    -> 可能图像: {w}x{h}")
    
    # 检查索引6的资源
    print(f"\n=== 资源6 ===")
    res6_offset_format1 = struct.unpack('<I', data[10+6*4:10+6*4+4])[0] if resource_count > 6 else 0
    res6_offset_format2 = struct.unpack('<I', data[6+6*4:6+6*4+4])[0]
    
    print(f"格式1（偏移34）: {res6_offset_format1}")
    print(f"格式2（偏移30）: {res6_offset_format2}")
    
    if res6_offset_format2 > 0 and res6_offset_format2 < len(data):
        print(f"\n资源6数据前50字节:")
        for i in range(0, 50, 16):
            pos = res6_offset_format2 + i
            if pos + 16 > len(data):
                break
            hex_str = ' '.join(f'{b:02X}' for b in data[pos:pos+16])
            print(f"  {i:04d}: {hex_str}")

if __name__ == '__main__':
    analyze_fdother_format()
