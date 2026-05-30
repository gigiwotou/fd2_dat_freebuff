#!/usr/bin/env python3
"""测试所有可能的RLE映射组合"""

import struct
from pathlib import Path
from PIL import Image
import itertools

FDOTHER_PATH = Path("game/FDOTHER.DAT")

# 定义4种操作
OP_FILL = 0
OP_COPY_SPEC = 1
OP_COPY_STD = 2
OP_SKIP = 3

OP_NAMES = {
    OP_FILL: "FILL",
    OP_COPY_SPEC: "COPY_SPEC",
    OP_COPY_STD: "COPY_STD",
    OP_SKIP: "SKIP"
}

def decode_rle_with_mapping(rle_data, w, h, mapping):
    """使用指定映射解码RLE"""
    # mapping是4位组合到操作的映射字典
    # key: (bit7, bit6), value: operation
    
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
            
            op = mapping.get((bit7, bit6), OP_FILL)
            
            if op == OP_FILL:
                actual_count = min(count, remaining)
                if src_idx < len(rle_data):
                    fill_val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual_count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = fill_val
                            dst_idx += 1
                remaining -= actual_count
                
            elif op == OP_COPY_SPEC:
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
                
            elif op == OP_COPY_STD:
                actual_count = min(count, remaining, len(rle_data) - src_idx)
                for i in range(actual_count):
                    if dst_idx < len(dst) and src_idx < len(rle_data):
                        dst[dst_idx] = rle_data[src_idx]
                        src_idx += 1
                        dst_idx += 1
                remaining -= actual_count
                
            elif op == OP_SKIP:
                actual_count = min(count, remaining)
                dst_idx += actual_count
                remaining -= actual_count
    
    return dst

def test_all_mappings():
    """测试所有可能的映射组合"""
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
    
    # RLE数据
    rle_data = idx1_data[5:]
    
    # 所有可能的映射组合 (4^4 = 256种)
    ops = [OP_FILL, OP_COPY_SPEC, OP_COPY_STD, OP_SKIP]
    
    # 测试几种常见的映射组合
    test_mappings = [
        # 映射1: bit7高位
        {(0,0): OP_FILL, (0,1): OP_COPY_SPEC, (1,0): OP_COPY_STD, (1,1): OP_SKIP},
        # 映射2: bit7低位
        {(0,0): OP_SKIP, (0,1): OP_COPY_STD, (1,0): OP_COPY_SPEC, (1,1): OP_FILL},
        # 映射3: 另一种常见组合
        {(0,0): OP_FILL, (0,1): OP_COPY_STD, (1,0): OP_COPY_SPEC, (1,1): OP_SKIP},
        # 映射4: 反转
        {(0,0): OP_SKIP, (0,1): OP_COPY_SPEC, (1,0): OP_COPY_STD, (1,1): OP_FILL},
        # 映射5: 交叉
        {(0,0): OP_COPY_STD, (0,1): OP_FILL, (1,0): OP_SKIP, (1,1): OP_COPY_SPEC},
        # 映射6: 另一种交叉
        {(0,0): OP_COPY_SPEC, (0,1): OP_FILL, (1,0): OP_SKIP, (1,1): OP_COPY_STD},
    ]
    
    for i, mapping in enumerate(test_mappings):
        print(f"\n测试映射 {i+1}:")
        for bits, op in sorted(mapping.items()):
            print(f"  bit7={bits[0]}, bit6={bits[1]} -> {OP_NAMES[op]}")
        
        decoded = decode_rle_with_mapping(rle_data, w, h, mapping)
        
        # 统计
        non_zero = sum(1 for p in decoded if p != 0)
        unique_vals = sorted(set(decoded))
        print(f"  非零像素: {non_zero}/{w*h}")
        print(f"  唯一值: {unique_vals[:20]}{'...' if len(unique_vals) > 20 else ''}")
        
        # 渲染 - 不应用palette_window
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                pal_idx = decoded[idx]
                if pal_idx < 256:
                    r = idx0_data[pal_idx * 3]
                    g = idx0_data[pal_idx * 3 + 1]
                    b = idx0_data[pal_idx * 3 + 2]
                    img.putpixel((x, y), (r, g, b))
                else:
                    img.putpixel((x, y), (255, 0, 255))  # 错误颜色
        
        filename = f'output/idx1_mapping{i+1}.png'
        img.save(filename)
        print(f"  已保存: {filename}")

if __name__ == '__main__':
    test_all_mappings()
