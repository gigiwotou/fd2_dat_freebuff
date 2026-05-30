#!/usr/bin/env python3
"""验证索引7和索引14的数据"""
import struct

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    print("="*70)
    print("索引表验证 (从偏移6开始，每项8字节)")
    print("="*70)
    
    for idx in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:
        f.seek(6 + idx * 8)
        data = f.read(8)
        if len(data) < 8:
            print(f"索引{idx}: 数据不足")
            continue
        
        start, end = struct.unpack('<II', data)
        size = end - start
        
        f.seek(start)
        header = f.read(min(size, 20))
        
        print(f"\n索引{idx}: 偏移=0x{start:08x}, 结束=0x{end:08x}, 大小={size}")
        print(f"  前20字节: {' '.join(f'{b:02x}' for b in header[:20])}")
        
        # 识别类型
        if size == 768:
            print(f"  -> PALETTE")
        elif header[:4] == b'LMI1':
            tile_count = struct.unpack('<H', header[4:6])[0]
            print(f"  -> LMI1, tile_count={tile_count}")
        elif header[:6] == b'LLLLLL':
            res_count = struct.unpack('<I', header[6:10])[0]
            print(f"  -> NESTED_DAT, resource_count={res_count}")
        elif size >= 4:
            w = struct.unpack('<H', header[0:2])[0]
            h = struct.unpack('<H', header[2:4])[0]
            if w > 0 and w <= 640 and h > 0 and h <= 480:
                pal_window = header[4] if size >= 5 else 0
                print(f"  -> TILE, {w}x{h}, palette_window={pal_window}")
            else:
                print(f"  -> RAW (width={w}, height={h}不合理)")
        else:
            print(f"  -> RAW")
