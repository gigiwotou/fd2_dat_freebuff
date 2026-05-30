#!/usr/bin/env python3
"""详细对比查看器解码和Python解码的差异"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_rle_python(rle_data, w, h):
    """Python版RLE解码（与查看器逻辑一致）"""
    dst = bytearray(w * h)
    dst_idx = 0
    src_idx = 0
    
    # 按行处理
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
                    # COPY_SPEC (间隔写入)
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

def analyze_idx1_detailed():
    """详细分析索引1"""
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
    idx1_size = len(idx1_data)
    
    w = 24
    h = 24
    
    print(f"=== 索引1 详细分析 ===")
    print(f"数据大小: {idx1_size} 字节")
    print(f"前8字节: {' '.join(f'{b:02X}' for b in idx1_data[:8])}")
    print(f"字节4: 0x{idx1_data[4]:02X} ({idx1_data[4]})")
    print(f"字节5: 0x{idx1_data[5]:02X} ({idx1_data[5]})")
    
    # 检查头格式
    if idx1_data[5] == 0:
        print("=> 5字节头 (width=24, height=24, palette_window=20)")
        rle_data = idx1_data[5:]
    else:
        print("=> 8字节头")
        rle_data = idx1_data[8:]
    
    print(f"RLE数据大小: {len(rle_data)} 字节")
    print(f"RLE前32字节: {' '.join(f'{b:02X}' for b in rle_data[:32])}")
    
    # 解码
    decoded = decode_rle_python(rle_data, w, h)
    
    # 统计解码后的像素
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"\n解码结果: {w}x{h} = {w*h} 像素")
    print(f"非零像素: {non_zero}")
    print(f"唯一值: {sorted(set(decoded))}")
    
    # 尝试不同的调色板索引
    for pw in [0, 20, 32, 48, 64]:
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                pal_idx = (pw + decoded[idx]) & 0xFF
                r = idx0_data[pal_idx * 3]
                g = idx0_data[pal_idx * 3 + 1]
                b = idx0_data[pal_idx * 3 + 2]
                img.putpixel((x, y), (r, g, b))
        
        filename = f'output/idx1_detailed_pw{pw}.png'
        img.save(filename)
        print(f"已保存: {filename}")

if __name__ == '__main__':
    analyze_idx1_detailed()
