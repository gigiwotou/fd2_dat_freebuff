#!/usr/bin/env python3
"""重新分析资源6的实际内容"""

import struct

def analyze_resource6_content():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    # 资源6
    resource6_offset = struct.unpack('<I', data[30:34])[0]  # 6 + 6*4 = 30
    resource7_offset = struct.unpack('<I', data[34:38])[0]  # 6 + 7*4 = 34
    resource6_size = resource7_offset - resource6_offset
    
    print(f"\n资源6: 偏移={resource6_offset}, 大小={resource6_size}")
    
    resource6_data = data[resource6_offset:resource6_offset+resource6_size]
    
    # 打印前100字节
    print(f"\n资源6前100字节:")
    for i in range(0, 100, 16):
        hex_str = ' '.join(f'{b:02X}' for b in resource6_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in resource6_data[i:i+16])
        print(f"  {i:04d} (0x{i:04X}): {hex_str}  {ascii_str}")
    
    # 尝试查找类似"LLLLLL"的头部
    lll_pattern = b'\x4C\x4C\x4C\x4C\x4C\x4C'
    pos = resource6_data.find(lll_pattern)
    if pos >= 0:
        print(f"\n找到'LLLLLL'模式在偏移: {pos}")
    
    # 分析是否是RLE图像数据（没有头部）
    # 根据4E98D: [宽度2字节][高度2字节][RLE数据]
    print(f"\n=== 尝试解析为RLE图像 ===")
    
    # 直接尝试作为RLE数据解码
    print(f"前4字节: {struct.unpack('<H', resource6_data[0:2])[0]} x {struct.unpack('<H', resource6_data[2:4])[0]}")
    
    # 也许资源6本身就是RLE图像，不需要内部表？
    w = struct.unpack('<H', resource6_data[0:2])[0]
    h = struct.unpack('<H', resource6_data[2:4])[0]
    
    if w > 0 and w < 500 and h > 0 and h < 500:
        print(f"可能是图像: {w}x{h}")
        print(f"RLE前32字节: {' '.join(f'{b:02X}' for b in resource6_data[4:36])}")
        
        # 尝试简单的RLE解码
        rle_data = resource6_data[4:]
        pixels = []
        p = 0
        while p < min(len(rle_data), 200):
            opcode = rle_data[p]
            p += 1
            
            bit7 = (opcode >> 7) & 1
            bit6 = (opcode >> 6) & 1
            count = (opcode & 0x3F) + 1
            
            mode = "SKIP" if (bit7 and bit6) else "COPY" if (bit7 and not bit6) else "FILL" if (not bit7 and bit6) else "ALT"
            print(f"  操作码 0x{opcode:02X}: {mode}, count={count}")
            
            if mode == "COPY" or (mode == "FILL") or (mode == "ALT"):
                if p < len(rle_data):
                    print(f"    颜色/数据: 0x{rle_data[p]:02X}")
                    if mode == "COPY":
                        p += count
                    else:
                        p += 1
            
            if len(pixels) > 10:
                break

if __name__ == '__main__':
    analyze_resource6_content()
