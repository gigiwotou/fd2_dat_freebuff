#!/usr/bin/env python3
"""
根据汇编调用约定精确验证RLE解码

从sub_10652汇编分析:
- arg0指向一个结构: {width: 2字节, height: 2字节, RLE数据...}
- value_1始终是-1 (0xFFFFFFFF)
- 所以RLE解码器使用最简单的模式: 直接输出像素值，无palette变换
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_rle_exact(rle_data, w, h):
    """精确按照sub_4E98D value_1=-1分支实现"""
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
                    # FILL (0x4E9EE)
                    # bit7=0, bit6=0: 从0x4e9e3读取value，在0x4e9f6读取fill值
                    # 注意: 汇编中FILL的逻辑在0x4e9f1之后
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
                    # COPY_SPEC (0x4EA00)
                    # bit7=0, bit6=1: 间隔写入
                    total_consume = count * 2
                    actual_count = count
                    if total_consume > remaining:
                        actual_count = remaining // 2
                        total_consume = actual_count * 2
                    if src_idx < len(rle_data):
                        val = rle_data[src_idx]
                        src_idx += 1
                        # do-while循环: *v14 = value; dst = v14 + 1; --count_1
                        # 每次循环dst前进2 (dst+1然后v14+1)
                        for i in range(actual_count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = val
                                dst_idx += 2
                    remaining -= total_consume
            else:
                if bit6 == 0:
                    # COPY_STD (0x4EA17)
                    # bit7=1, bit6=0: 从src复制
                    # qmemcpy(dst, src, count_1)
                    actual_count = min(count, remaining, len(rle_data) - src_idx)
                    for i in range(actual_count):
                        if dst_idx < len(dst) and src_idx < len(rle_data):
                            dst[dst_idx] = rle_data[src_idx]
                            src_idx += 1
                            dst_idx += 1
                    remaining -= actual_count
                    
                else:
                    # SKIP (0x4EA2C)
                    # bit7=1, bit6=1: 跳过
                    actual_count = min(count, remaining)
                    dst_idx += actual_count
                    remaining -= actual_count
        
        # 行结束: dst += v8 (v8 = arg10 - width = stride - width)
        # 游戏中stride通常等于width，所以不需要额外前进
    
    return dst

def analyze_caller_structures():
    """分析调用sub_4E98D时传递的结构"""
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
    
    # 索引1数据 (TILE: width:2 + height:2 + palette_window:1 + RLE)
    idx1_data = data[offsets[1]:offsets[2]]
    
    # 解析结构: {width:2, height:2, palette_window:1, RLE...}
    w = struct.unpack_from('<H', idx1_data, 0)[0]
    h = struct.unpack_from('<H', idx1_data, 2)[0]
    pw = idx1_data[4]
    
    print(f"索引1 TILE结构:")
    print(f"  宽度: {w}")
    print(f"  高度: {h}")  
    print(f"  palette_window: {pw}")
    print(f"  总大小: {len(idx1_data)}")
    print(f"  RLE数据起始偏移: 5")
    print(f"  RLE数据大小: {len(idx1_data) - 5}")
    
    # RLE数据
    rle_data = idx1_data[5:]
    
    print(f"\nRLE数据前64字节:")
    for i in range(0, min(64, len(rle_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in rle_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in rle_data[i:i+16])
        print(f"  {i:03d}: {hex_str:<48} {ascii_str}")
    
    # 解码
    decoded = decode_rle_exact(rle_data, w, h)
    
    # 统计
    non_zero = sum(1 for p in decoded if p != 0)
    unique_vals = sorted(set(decoded))
    
    print(f"\n解码结果:")
    print(f"  非零像素: {non_zero}/{w*h}")
    print(f"  唯一值数量: {len(unique_vals)}")
    print(f"  唯一值: {unique_vals[:30]}")
    
    # 使用索引0调色板渲染 (palette_window=20)
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            pal_idx = decoded[idx]
            r = idx0_data[pal_idx * 3]
            g = idx0_data[pal_idx * 3 + 1]
            b = idx0_data[pal_idx * 3 + 2]
            img.putpixel((x, y), (r, g, b))
    
    img.save('output/idx1_exact_decode.png')
    print(f"\n已保存: output/idx1_exact_decode.png")
    print(f"请用你提供的正确图像对比这张图片")

if __name__ == '__main__':
    analyze_caller_structures()
