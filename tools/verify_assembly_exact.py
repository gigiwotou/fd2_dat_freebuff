#!/usr/bin/env python3
"""
按照sub_4E98D汇编代码1:1实现RLE解码 (value_1 == -1分支)

关键发现：
1. 内层循环读取控制字节value
2. bit7=0时break到0x4e9e8
3. 在0x4e9e8检查bit6:
   - bit6=0: FILL (使用刚才读取的value计算count，再读取一个fill值)
   - bit6=1: break到0x4ea13执行COPY_SPEC (使用刚才读取的value计算count)
4. bit7=1时继续内层循环:
   - bit6=0: COPY_STD
   - bit6=1: SKIP
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_rle_assembly_exact(rle_data, w, h):
    """按照MCP反编译代码1:1实现"""
    dst = bytearray(w * h)
    dst_idx = 0
    src_idx = 0
    
    row = 0
    while row < h:  # do-while (arg8)
        remaining = w  # count = width
        count_1 = 0
        
        while True:  # do-while (count)
            # 内层while循环 (0x4e9e3)
            while True:
                # 0x4e9e3: 读取控制字节
                if src_idx >= len(rle_data):
                    break
                value = rle_data[src_idx]
                src_idx += 1
                
                # 0x4e9e6: v12 = 2 * value (左移1位)
                # 0x4e9e8: 检查CF=bit7
                bit7 = (value >> 7) & 1
                
                if bit7 == 0:
                    # bit7=0: break到0x4e9e8
                    break
                
                # bit7=1: 继续内层处理
                # 0x4e9ea: v13 = CF of (v12 << 1) = bit6
                bit6 = (value >> 6) & 1
                
                # 0x4e9ea: count_1 = 4 * value (这里value是整个控制字节)
                count_1 = (value & 0x3F) + 1
                
                if bit6 == 1:
                    # 0x4ea19: SKIP
                    actual_count = min(count_1, remaining)
                    dst_idx += actual_count
                    remaining -= actual_count
                    count_1 = 0  # 0x4ea23
                    if remaining == 0:
                        break
                else:
                    # 0x4ea1e: COPY_STD
                    actual_count = min(count_1, remaining, len(rle_data) - src_idx)
                    for i in range(actual_count):
                        if dst_idx < len(dst) and src_idx < len(rle_data):
                            dst[dst_idx] = rle_data[src_idx]
                            src_idx += 1
                            dst_idx += 1
                    remaining -= actual_count
                    count_1 = 0  # 0x4ea23
                    if remaining == 0:
                        break
            
            if remaining == 0:
                break
            
            # 0x4e9e8: bit7=0时到达这里
            bit6 = (value >> 6) & 1
            count_1 = (value & 0x3F) + 1
            
            if bit6 == 1:
                # 0x4e9ec: bit6=1, break到外层0x4ea13
                break
            
            # 0x4e9f1: bit6=0, FILL
            count_1 = min(count_1, remaining)
            remaining -= count_1
            
            if src_idx < len(rle_data):
                fill_val = rle_data[src_idx]
                src_idx += 1
                for i in range(count_1):
                    if dst_idx < len(dst):
                        dst[dst_idx] = fill_val
                        dst_idx += 1
            
            count_1 = 0  # 0x4e9f7
            if remaining == 0:
                break
        
        if remaining > 0:
            # 0x4ea03: COPY_SPEC (使用上一次的控制字节value)
            count_1 = (value & 0x3F) + 1
            total_consume = count_1 * 2
            actual_count = count_1
            
            if total_consume > remaining:
                actual_count = remaining // 2
                total_consume = actual_count * 2
            
            remaining -= total_consume
            
            if src_idx < len(rle_data):
                spec_val = rle_data[src_idx]
                src_idx += 1
                for i in range(actual_count):
                    if dst_idx < len(dst):
                        dst[dst_idx] = spec_val
                        dst_idx += 2
        
        # 行结束
        row += 1
        # dst += v8 (stride - width)，这里假设stride=width，所以不需要
    
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
    decoded = decode_rle_assembly_exact(rle_data, w, h)
    
    # 统计
    non_zero = sum(1 for p in decoded if p != 0)
    unique_vals = sorted(set(decoded))
    
    print(f"解码结果: {non_zero} 非零像素, {len(unique_vals)} 唯一值")
    print(f"唯一值: {unique_vals[:20]}")
    
    # 使用索引0调色板渲染
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            pal_idx = decoded[idx]
            r = idx0_data[pal_idx * 3]
            g = idx0_data[pal_idx * 3 + 1]
            b = idx0_data[pal_idx * 3 + 2]
            img.putpixel((x, y), (r, g, b))
    
    img.save('output/idx1_assembly_exact.png')
    print(f"已保存: output/idx1_assembly_exact.png")

if __name__ == '__main__':
    main()
