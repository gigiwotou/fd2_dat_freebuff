#!/usr/bin/env python3
"""验证RLE解码和调色板应用"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_rle_complete(rle_data, w, h):
    """完整RLE解码"""
    dst = bytearray(w * h)
    dst_idx = 0
    src_idx = 0
    
    for row in range(h):
        remaining = w
        
        while remaining > 0 and src_idx < len(rle_data):
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    actual_count = min(count, remaining)
                    if src_idx < len(rle_data):
                        fill_val = rle_data[src_idx]
                        src_idx += 1
                        for i in range(actual_count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                    remaining -= actual_count
                else:
                    # COPY_SPEC
                    total_consume = count * 2
                    actual_count = count
                    if total_consume > remaining:
                        actual_count = remaining // 2
                        total_consume = actual_count * 2
                    if src_idx < len(rle_data):
                        val = rle_data[src_idx]
                        src_idx += 1
                        for i in range(actual_count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = val
                                dst_idx += 2
                    remaining -= total_consume
            else:
                if bit6 == 0:
                    # COPY_STD
                    actual_count = min(count, remaining, len(rle_data) - src_idx)
                    for i in range(actual_count):
                        if dst_idx < len(dst) and src_idx < len(rle_data):
                            dst[dst_idx] = rle_data[src_idx]
                            src_idx += 1
                            dst_idx += 1
                    remaining -= actual_count
                else:
                    # SKIP
                    actual_count = min(count, remaining)
                    dst_idx += actual_count
                    remaining -= actual_count
    
    return dst

def main():
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引0调色板
    idx0_data = data[offsets[0]:offsets[1]]
    
    # 索引1数据
    idx1_data = data[offsets[1]:offsets[2]]
    w = struct.unpack_from('<H', idx1_data, 0)[0]
    h = struct.unpack_from('<H', idx1_data, 2)[0]
    pw = idx1_data[4]
    
    print(f"索引1: {w}x{h}, palette_window={pw}")
    
    # RLE数据 (5字节头后)
    rle_data = idx1_data[5:]
    
    # 解码
    decoded = decode_rle_complete(rle_data, w, h)
    
    # 打印解码结果的前100个像素
    print(f"\n解码结果前100像素:")
    print(' '.join(f'{decoded[i]:3d}' for i in range(min(100, len(decoded)))))
    
    # 统计
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"\n非零像素: {non_zero}/{w*h}")
    print(f"唯一值: {sorted(set(decoded))}")
    
    # 渲染测试 - 不使用palette_window
    img1 = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            pal_idx = decoded[idx]
            r = idx0_data[pal_idx * 3]
            g = idx0_data[pal_idx * 3 + 1]
            b = idx0_data[pal_idx * 3 + 2]
            img1.putpixel((x, y), (r, g, b))
    
    img1.save('output/idx1_no_pw.png')
    print(f"已保存: output/idx1_no_pw.png (不应用palette_window)")
    
    # 渲染测试 - 使用palette_window
    img2 = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            pal_idx = (pw + decoded[idx]) & 0xFF
            r = idx0_data[pal_idx * 3]
            g = idx0_data[pal_idx * 3 + 1]
            b = idx0_data[pal_idx * 3 + 2]
            img2.putpixel((x, y), (r, g, b))
    
    img2.save('output/idx1_with_pw.png')
    print(f"已保存: output/idx1_with_pw.png (应用palette_window={pw})")
    
    # 尝试其他palette_window值
    for test_pw in [0, 16, 32, 48, 64, 96, 128, 160, 192, 224]:
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                pal_idx = (test_pw + decoded[idx]) & 0xFF
                r = idx0_data[pal_idx * 3]
                g = idx0_data[pal_idx * 3 + 1]
                b = idx0_data[pal_idx * 3 + 2]
                img.putpixel((x, y), (r, g, b))
        
        filename = f'output/idx1_pw{test_pw}.png'
        img.save(filename)

if __name__ == '__main__':
    main()
