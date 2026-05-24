#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""分析索引0的实际数据结构"""

import struct
from pathlib import Path

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    data = fdother_path.read_bytes()
    
    resource_count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    idx = 0
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
    size = end - start
    idx0_data = data[start:end]
    
    print(f"索引0: 大小={size}字节")
    print(f"\n前100字节十六进制:")
    for i in range(0, min(100, len(idx0_data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in idx0_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in idx0_data[i:i+16])
        print(f"  {i:4d} (0x{i:04X}): {hex_str:<48s} {ascii_str}")
    
    # 检查是否是LMI1
    if idx0_data[:4] == b'LMI1':
        print(f"\n✓ 是LMI1格式")
        tile_count = struct.unpack_from('<H', idx0_data, 4)[0]
        print(f"  Tile数量: {tile_count}")
        
        # 读取tile偏移表
        for i in range(min(10, tile_count)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(idx0_data):
                break
            tile_offset = struct.unpack_from('<I', idx0_data, offset_addr)[0]
            print(f"  Tile {i}: 偏移={tile_offset}")
    else:
        print(f"\n✗ 不是LMI1格式，前4字节: {idx0_data[:4]}")
        
        # 尝试其他解析
        # 可能是直接的偏移表
        print(f"\n尝试解析为偏移表:")
        offset_count = len(idx0_data) // 4
        print(f"  可能的偏移数量: {offset_count}")
        
        for i in range(min(20, offset_count)):
            offset = struct.unpack_from('<I', idx0_data, i * 4)[0]
            print(f"  偏移{i}: {offset}")

if __name__ == "__main__":
    main()
