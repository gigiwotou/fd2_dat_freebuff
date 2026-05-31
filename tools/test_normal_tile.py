#!/usr/bin/env python3
"""测试普通TILE资源的解码"""
import struct
import os
from PIL import Image

def main():
    dat_path = 'game/FDOTHER.DAT'
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # 解析索引表
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    offsets.append(len(data))
    
    print(f"总索引数: {len(offsets)-1}")
    
    # 检查索引11（全屏图像 320x200）
    idx = 11
    res_start = offsets[idx]
    res_end = offsets[idx+1]
    res_data = data[res_start:res_end]
    
    print(f"\n索引{idx}: 大小={len(res_data)}")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in res_data[:32])}")
    
    # 解析头部
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    
    print(f"宽高: {w}x{h}")
    
    if w > 640 or h > 480 or w == 0 or h == 0:
        print("宽高异常")
        return
    
    # 解析调色板窗口
    pal_window = res_data[4]
    header_size = 5
    if len(res_data) >= 8 and res_data[5] != 0:
        pal_window = struct.unpack_from('<H', res_data, 4)[0]
        header_size = 8
        print(f"8字节头，pal_window={pal_window}")
    else:
        print(f"5字节头，pal_window={pal_window}")
    
    # RLE数据
    rle_data = res_data[header_size:]
    print(f"RLE数据大小: {len(rle_data)}")
    print(f"RLE前32字节: {' '.join(f'{b:02X}' for b in rle_data[:32])}")
    
    # 预期像素数
    expected = w * h
    print(f"预期像素数: {expected}")
    
    # 解码EC66
    dst = []
    src_idx = 0
    ah = 0
    al = 0
    
    for i in range(expected):
        if ah > 0:
            ah -= 1
            # AL保持不变
        else:
            if src_idx >= len(rle_data):
                print(f"警告：源数据不足，解码了{i}个像素")
                break
            
            al = rle_data[src_idx]
            src_idx += 1
            
            if al > 0xC0:
                ah = al - 0xC1
                if src_idx < len(rle_data):
                    al = rle_data[src_idx]
                    src_idx += 1
            else:
                ah = 0
        
        # 应用调色板窗口
        pixel = (pal_window + al) & 0xFF
        dst.append(pixel)
    
    print(f"解码像素数: {len(dst)}, 源数据消耗: {src_idx}/{len(rle_data)}")
    
    # 保存图像
    if len(dst) == expected:
        # 加载调色板（索引0）
        pal_data = data[offsets[0]:offsets[1]]
        palette_rgb24 = []
        for i in range(256):
            r = (pal_data[i*3] << 2) | (pal_data[i*3] >> 4)
            g = (pal_data[i*3+1] << 2) | (pal_data[i*3+1] >> 4)
            b = (pal_data[i*3+2] << 2) | (pal_data[i*3+2] >> 4)
            palette_rgb24.append((r, g, b))
        
        img = Image.new('RGB', (w, h))
        pixels = img.load()
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                pal_idx = dst[idx]
                pixels[x, y] = palette_rgb24[pal_idx]
        
        out_path = f'output/test_index{idx}_tile.png'
        img.save(out_path)
        print(f"已保存到: {out_path}")
    else:
        print(f"像素数不匹配: {len(dst)} != {expected}")

if __name__ == '__main__':
    main()
