#!/usr/bin/env python3
"""重新分析索引1 - 检查数据模式"""
import struct

def load_fdother(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    
    offsets.append(len(data))
    return data, offsets

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    print("=== 索引1 详细数据 ===")
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    print(f"总大小: {len(res_data)} 字节")
    print(f"完整十六进制转储 (前500字节):")
    
    for i in range(0, min(500, len(res_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} |{ascii_str}|")
    
    # 尝试不同的解析方式
    print(f"\n\n尝试1: 2字节偏移表")
    pos = 5
    offsets_2byte = []
    while pos + 2 <= min(100, len(res_data)):
        off = struct.unpack_from('<H', res_data, pos)[0]
        if off > len(res_data):
            break
        offsets_2byte.append((pos - 5, off))
        pos += 2
        if len(offsets_2byte) > 50:
            break
    
    print(f"前10个2字节偏移:")
    for i, (p, off) in enumerate(offsets_2byte[:10]):
        print(f"  偏移{p}: 0x{off:04X} = {off}")
    
    # 检查是否有规律的间隔
    if len(offsets_2byte) > 1:
        diffs = [offsets_2byte[i+1][1] - offsets_2byte[i][1] for i in range(min(10, len(offsets_2byte)-1))]
        print(f"\n偏移差值: {diffs}")
    
    print(f"\n\n尝试2: 直接查看数据模式")
    # 24x24 = 576, 2230 / 576 = 3.87
    # 也许每个图标大小不同？
    print(f"数据区: {len(res_data) - 5} 字节")
    print(f"如果是24x24图标 (576像素): {len(res_data) - 5} / 576 = {(len(res_data) - 5) / 576:.2f}")
    
    # 检查前几个字节作为偏移值
    print(f"\n前20字节作为可能的偏移值:")
    for i in range(0, 20, 4):
        val_4byte = struct.unpack_from('<I', res_data, 5 + i)[0]
        val_2byte = struct.unpack_from('<H', res_data, 5 + i)[0]
        print(f"  偏移{5+i}: 4字节={val_4byte}, 2字节={val_2byte}")

if __name__ == '__main__':
    main()
