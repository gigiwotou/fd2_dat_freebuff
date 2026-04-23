#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
RLE解压调试脚本 - 验证RLE算法是否正确
'''

import struct
import sys

def debug_rle_decompress(src_data, width, height):
    '''模拟C语言的RLE解压算法'''
    pixels = []
    count = width
    src_idx = 0
    
    for row in range(height):
        count = width  # 每行重新设置count
        
        while count > 0:
            if src_idx >= len(src_data):
                break
            
            value = src_data[src_idx]
            src_idx += 1
            
            cnt = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7:
                if bit6:  # SKIP (11)
                    # 跳过cnt个像素
                    count -= cnt
                    # SKIP不写入数据
                else:  # COPY (10)
                    # 复制cnt个字节
                    n = min(cnt, count)
                    if src_idx + n > len(src_data):
                        n = len(src_data) - src_idx
                    for i in range(n):
                        pixels.append(src_data[src_idx + i])
                        src_idx += 1
                    count -= n
            else:
                if bit6:  # FILL (01)
                    # 用下一个字节填充cnt个像素
                    if src_idx >= len(src_data):
                        break
                    fill = src_data[src_idx]
                    src_idx += 1
                    n = min(cnt, count)
                    for i in range(n):
                        pixels.append(fill)
                    count -= n
                else:  # SPARSE (00)
                    # 在奇数位置写入cnt个像素
                    if src_idx >= len(src_data):
                        break
                    fill = src_data[src_idx]
                    src_idx += 1
                    
                    remaining = cnt
                    while remaining > 0 and count >= 4:
                        # 跳过位置0
                        # 位置1写入
                        pixels.append(fill)
                        # 跳过位置2,3
                        count -= 4
                        remaining -= 1
                    
                    # 公式: count = count - cnt - cnt
                    count = count - cnt - cnt
                    if count < 0:
                        count = 0
    
    return pixels


def main():
    if len(sys.argv) < 2:
        # 测试内置示例
        test_data = bytes([
            0xC1, 0xFF,  # FILL 1 pixel with 0xFF
            0x81, 0xAA,  # COPY 1 byte: 0xAA
            0xC2,       # FILL 2 pixels with ...  (需要下一个字节)
            0x55, 0x55, # FILL内容
            0x41, 0x77, # SPARSE 1 pixel at position 1: fill=0x77
        ])
        result = debug_rle_decompress(test_data, 10, 1)
        print(f'Test: got {len(result)} pixels, expected some')
        return
    
    # 从FDOTHER.DAT读取资源
    dat_path = sys.argv[1]
    res_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 99
    palette_idx = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    
    with open(dat_path, 'rb') as f:
        f.seek(10)
        offsets = []
        for i in range(422):
            off = struct.unpack('<I', f.read(4))[0]
            offsets.append(off)
        
        start = offsets[res_idx]
        end = offsets[res_idx + 1] if res_idx + 1 < 422 else 3382481
        
        f.seek(start)
        header = f.read(4)
        w = struct.unpack('<H', header[0:2])[0]
        h = struct.unpack('<H', header[2:4])[0]
        
        comp_data = f.read(end - start - 4)
        
        print(f'=== 资源 {res_idx} 分析 ===')
        print(f'尺寸: {w}x{h} = {w*h} pixels')
        print(f'压缩数据: {len(comp_data)} bytes')
        print(f'压缩比: {len(comp_data) / (w * h) * 100:.1f}%')
        
        # 使用Python模拟解压
        pixels = debug_rle_decompress(comp_data, w, h)
        print(f'Python解压结果: {len(pixels)} pixels')
        
        # 统计像素分布
        from collections import Counter
        counts = Counter(pixels)
        top = counts.most_common(10)
        print(f'Top 10 颜色:')
        for val, cnt in top:
            pct = cnt * 100 / len(pixels)
            print(f'  {val:3d}: {cnt:6d} ({pct:.1f}%)')
        
        # 非零像素
        non_zero = sum(cnt for val, cnt in top if val != 0)
        print(f'非零像素: {non_zero} ({non_zero*100/len(pixels):.1f}%)')
        
        # 保存为原始数据供PIL使用
        output_path = f'/tmp/debug_res{res_idx}.raw'
        with open(output_path, 'wb') as out:
            out.write(struct.pack('<I', w))
            out.write(struct.pack('<I', h))
            # 添加调色板（使用FDOTHER[palette_idx]）
            f.seek(offsets[palette_idx])
            out.write(f.read(768))
            out.write(bytes(pixels))
        
        print(f'\\n保存到: {output_path}')
        print('用 python3 decode_to_png.py 保存为PNG')


if __name__ == '__main__':
    main()