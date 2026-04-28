#!/usr/bin/env python3
"""验证FDSHAP资源1的实际tile数量"""

import struct
from pathlib import Path

def rle_decompress(src: bytes, width: int, height: int) -> bytes:
    dst = bytearray(width * height)
    p = 0
    src_end = len(src)
    
    for row in range(height):
        row_dst = row * width
        count = width
        
        while count > 0 and p < src_end:
            value = src[p]
            p += 1
            count_1 = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 and bit6:
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count >= 2:
                            if row_dst + 1 < len(dst):
                                dst[row_dst + 1] = fill
                            row_dst += 2
                            count -= 2
                        else:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
            else:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count > 0:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
    
    return bytes(dst)

fdshap = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', fdshap, 6)[0]
print(f"FDSHAP资源数量: {count}")

# 测试前5个tile资源
for res_idx in [1, 3, 5, 7, 9]:
    if res_idx >= count:
        break
    
    pos = 4 * res_idx + 10
    offset = struct.unpack_from('<I', fdshap, pos)[0]
    next_pos = 4 * (res_idx + 1) + 10
    next_offset = struct.unpack_from('<I', fdshap, next_pos)[0] if res_idx + 1 < count else len(fdshap)
    size = next_offset - offset
    
    print(f"\n=== 资源 {res_idx}: size={size} ===")
    
    if size >= 4:
        w, h = struct.unpack_from('<HH', fdshap, offset)
        print(f"  头部: w={w}, h={h}")
        print(f"  前20字节: {fdshap[offset:offset+20].hex()}")
        
        # 如果w=24, h=24是单个tile尺寸
        if w == 24 and h == 24:
            print(f"  单个tile，像素数={w*h}")
            print(f"  压缩数据大小={size-4}字节")
            print(f"  压缩比={(size-4)/(w*h):.2f}")
        else:
            # 可能是tileset
            tiles_per_row = w // 24
            tiles_per_col = h // 24
            total_tiles = tiles_per_row * tiles_per_col
            print(f"  可能是tileset: {tiles_per_row}x{tiles_per_col} = {total_tiles} tiles")
            
            # 尝试解压
            pixels = rle_decompress(fdshap[offset+4:offset+size], w, h)
            non_zero = sum(1 for p in pixels if p != 0)
            print(f"  解压后: {len(pixels)}像素, 非零={non_zero}")
