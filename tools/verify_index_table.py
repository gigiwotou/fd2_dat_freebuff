#!/usr/bin/env python3
"""
验证索引表解析和资源读取是否正确
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def verify_index_table():
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    print(f"文件大小: {len(data)} 字节")
    print(f"文件头: {' '.join(f'{b:02X}' for b in data[:10])}")
    
    # 读取索引表（从偏移6开始，每项4字节）
    offsets = []
    table_offset = 6
    
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    print(f"\n索引表:")
    print(f"索引表起始: 偏移6")
    print(f"索引表结束: 偏移{table_offset}")
    print(f"索引表大小: {table_offset - 6} 字节")
    print(f"资源数量: {len(offsets)}")
    
    # 打印前20个资源
    print(f"\n前20个资源:")
    for i, offset in enumerate(offsets[:20]):
        size = offsets[i + 1] - offset if i + 1 < len(offsets) else len(data) - offset
        print(f"  [{i:2d}] 偏移={offset:6d} (0x{offset:04X}), 大小={size:6d}")
    
    # 详细分析索引0和索引1
    print(f"\n{'='*60}")
    print(f"索引0 (调色板):")
    idx0_start = offsets[0]
    idx0_end = offsets[1]
    idx0_size = idx0_end - idx0_start
    print(f"  偏移: {idx0_start} - {idx0_end}")
    print(f"  大小: {idx0_size}")
    print(f"  前10字节: {' '.join(f'{b:02X}' for b in data[idx0_start:idx0_start+10])}")
    
    print(f"\n{'='*60}")
    print(f"索引1 (TILE):")
    idx1_start = offsets[1]
    idx1_end = offsets[2]
    idx1_size = idx1_end - idx1_start
    print(f"  偏移: {idx1_start} - {idx1_end}")
    print(f"  大小: {idx1_size}")
    print(f"  前20字节: {' '.join(f'{b:02X}' for b in data[idx1_start:idx1_start+20])}")
    
    # 解析TILE头
    w = struct.unpack_from('<H', data, idx1_start)[0]
    h = struct.unpack_from('<H', data, idx1_start + 2)[0]
    pw = data[idx1_start + 4]
    print(f"  宽度: {w}")
    print(f"  高度: {h}")
    print(f"  palette_window: {pw}")
    print(f"  预期RLE数据大小: {w*h} 像素")
    
    # RLE数据
    rle_data = data[idx1_start + 5:idx1_end]
    print(f"  实际RLE数据大小: {len(rle_data)}")
    print(f"  压缩率: {len(rle_data) / (w*h):.2f}x")
    
    # 尝试使用不同的调色板
    for pal_idx in [0, 57, 76]:
        pal_start = offsets[pal_idx]
        pal_end = offsets[pal_idx + 1] if pal_idx + 1 < len(offsets) else len(data)
        pal_data = data[pal_start:pal_end]
        
        if len(pal_data) != 768:
            print(f"\n索引{pal_idx}不是调色板 (大小={len(pal_data)})")
            continue
        
        # 简单RLE解码
        decoded = bytearray(w * h)
        dst_idx = 0
        src_idx = 0
        
        while src_idx < len(rle_data) and dst_idx < w * h:
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    actual = min(count, w*h - dst_idx)
                    if src_idx < len(rle_data):
                        val = rle_data[src_idx]
                        src_idx += 1
                        for i in range(actual):
                            decoded[dst_idx] = val
                            dst_idx += 1
                else:
                    # COPY_SPEC
                    actual = count
                    total = count * 2
                    if total > w*h - dst_idx:
                        actual = (w*h - dst_idx) // 2
                        total = actual * 2
                    if src_idx < len(rle_data):
                        val = rle_data[src_idx]
                        src_idx += 1
                        for i in range(actual):
                            if dst_idx < len(decoded):
                                decoded[dst_idx] = val
                                dst_idx += 2
            else:
                if bit6 == 0:
                    # COPY_STD
                    actual = min(count, w*h - dst_idx, len(rle_data) - src_idx)
                    for i in range(actual):
                        if dst_idx < len(decoded) and src_idx < len(rle_data):
                            decoded[dst_idx] = rle_data[src_idx]
                            src_idx += 1
                            dst_idx += 1
                else:
                    # SKIP
                    actual = min(count, w*h - dst_idx)
                    dst_idx += actual
        
        # 渲染 - 不使用palette_window
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                pal_entry = decoded[idx]
                r = pal_data[pal_entry * 3]
                g = pal_data[pal_entry * 3 + 1]
                b = pal_data[pal_entry * 3 + 2]
                img.putpixel((x, y), (r, g, b))
        
        img.save(f'output/idx1_verify_pal{pal_idx}.png')
        print(f"\n已保存: output/idx1_verify_pal{pal_idx}.png (使用调色板索引{pal_idx})")

if __name__ == '__main__':
    verify_index_table()
