"""
根据IDA 4E98D.c分析光标RLE数据

IDA 4E98D.c第35行调用:
sub_4E98D((__int16 *)(*(_DWORD *)(dword_53A81 + 526) + dword_53A81), 0, 0, v6, n456, -1);

从IDA反编译4E98D.c看:
- arg0[0] = width
- arg0[1] = height  
- arg0+2 = RLE数据

4E98D是RLE解压缩函数，value_1=-1表示直接模式
"""

import struct

def analyze_cursor_rle():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)} 字节")
    
    # 根据IDA分析，资源表结构:
    # - 偏移0-5: 文件头(6字节)
    # - 偏移6开始: 资源偏移表(每项4字节)
    
    print("\n=== 分析前200字节资源表 ===")
    
    # 打印前6字节头
    print(f"文件头(0-5): {' '.join(f'{b:02X}' for b in data[0:6])}")
    
    # 打印资源偏移表
    resources = []
    for idx in range(0, 200):
        offset = 6 + idx * 4
        if offset + 4 > len(data):
            break
        
        rel_offset = struct.unpack('<I', data[offset:offset+4])[0]
        
        if rel_offset > 0 and rel_offset < len(data) - 4:
            w = struct.unpack('<H', data[rel_offset:rel_offset+2])[0]
            h = struct.unpack('<H', data[rel_offset+2:rel_offset+4])[0]
            
            if w > 0 and w < 256 and h > 0 and h < 256:
                print(f"索引{idx:3d} (偏移{offset:4d}): rel_offset={rel_offset:8d}, 尺寸={w}x{h}")
                resources.append((idx, offset, rel_offset, w, h))
    
    print(f"\n找到 {len(resources)} 个有效图像资源")
    
    # 分析可能的候选
    if resources:
        print("\n=== 分析候选资源 ===")
        for idx, tbl_off, rel_off, w, h in resources[:5]:
            print(f"\n索引{idx}, 偏移{rel_off}:")
            print(f"  宽x高: {w}x{h}")
            rle_data = data[rel_off+4:rel_off+64]
            print(f"  RLE前32字节: {' '.join(f'{b:02X}' for b in rle_data[:32])}")

if __name__ == '__main__':
    analyze_cursor_rle()
