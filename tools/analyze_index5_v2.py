import struct
import os

# 查找FDOTHER.DAT文件
possible_paths = [
    'bin/FDOTHER.DAT',
    'data/FDOTHER.DAT',
    'output/FDOTHER.DAT',
    '../data/FDOTHER.DAT',
    'FDOTHER.DAT'
]

dat_path = None
for p in possible_paths:
    if os.path.exists(p):
        dat_path = p
        break

if not dat_path:
    print("未找到FDOTHER.DAT文件")
    exit(1)

print(f"使用文件: {dat_path}")

with open(dat_path, 'rb') as f:
    # 读取文件头
    magic = f.read(4)
    print(f"文件魔术字节: {magic}")
    
    tile_count = struct.unpack('<H', f.read(2))[0]
    print(f"文件tile总数: {tile_count}")
    
    # 读取所有偏移
    offsets = []
    for i in range(tile_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    print(f"\n索引5的文件偏移: 0x{offsets[5]:X}")
    print(f"索引6的文件偏移: 0x{offsets[6]:X}")
    print(f"索引5的大小: {offsets[6] - offsets[5]} 字节")
    
    # 跳转到索引5
    f.seek(offsets[5])
    
    # 读取整个索引5资源
    res_size = offsets[6] - offsets[5]
    res_data = f.read(res_size)
    
    print(f"\n索引5资源大小: {res_size} 字节")
    print(f"\n前64字节（十六进制）:")
    for i in range(0, min(64, len(res_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # 解析为LMI1 tile集格式
    print("\n" + "="*60)
    print("解析为LMI1 tile集格式")
    print("="*60)
    
    if res_data[:4] == b'LMI1':
        print("  找到LMI1魔术字节")
        inner_count = struct.unpack('<H', res_data[4:6])[0]
        print(f"  Tile数量: {inner_count}")
        
        # 读取前20个tile
        for i in range(min(20, inner_count)):
            offset = struct.unpack('<I', res_data[6 + i*4:10 + i*4])[0]
            if offset < res_size and offset >= 6 + inner_count*4:
                w = struct.unpack('<H', res_data[offset:offset+2])[0]
                h = struct.unpack('<H', res_data[offset+2:offset+4])[0]
                if w < 500 and h < 500:
                    print(f"  Tile {i}: {w}x{h} (偏移: 0x{offset:X})")
                else:
                    print(f"  Tile {i}: 尺寸异常 {w}x{h}")
            else:
                print(f"  Tile {i}: 偏移0x{offset:X} 异常")
    else:
        print(f"  前4字节: {res_data[:4]}，不是LMI1格式")
        
        # 尝试作为简单tile集（WORD数量 + DWORD偏移表）
        print("\n  尝试作为简单tile集（WORD数量 + DWORD偏移表）:")
        if len(res_data) >= 2:
            count = struct.unpack('<H', res_data[0:2])[0]
            print(f"  WORD[0-1] = {count}")
            
            if count < 1000 and 6 + count*4 <= res_size:
                print(f"  偏移表从字节6开始，共{count}个tile")
                for i in range(min(20, count)):
                    offset = struct.unpack('<I', res_data[6 + i*4:10 + i*4])[0]
                    if offset < res_size and offset >= 6 + count*4:
                        w = struct.unpack('<H', res_data[offset:offset+2])[0]
                        h = struct.unpack('<H', res_data[offset+2:offset+4])[0]
                        if w < 500 and h < 500:
                            print(f"  Tile {i}: {w}x{h} (偏移: 0x{offset:X})")
                        else:
                            print(f"  Tile {i}: 尺寸异常 {w}x{h}")
                    else:
                        print(f"  Tile {i}: 偏移0x{offset:X} 异常")
