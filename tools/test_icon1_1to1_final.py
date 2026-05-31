#!/usr/bin/env python3
"""1:1复制sub_4EC66 + sub_4EBFF解码逻辑 - 使用FDOTHER索引0的调色板"""
import struct
import os
from PIL import Image

def load_palette_from_fdother():
    """从FDOTHER.DAT索引0加载调色板"""
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
    
    # 索引0是调色板（256字节 * 3通道？或者256字节直接是索引？）
    pal_data = data[offsets[0]:offsets[1]]
    print(f"索引0大小: {len(pal_data)}")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in pal_data[:32])}")
    
    # 假设是256色调色板，每个颜色3字节（RGB）
    palette_rgb24 = []
    if len(pal_data) == 768:
        # 256 * 3 = 768
        for i in range(256):
            r = (pal_data[i*3] << 2) | (pal_data[i*3] >> 4)
            g = (pal_data[i*3+1] << 2) | (pal_data[i*3+1] >> 4)
            b = (pal_data[i*3+2] << 2) | (pal_data[i*3+2] >> 4)
            palette_rgb24.append((r, g, b))
    elif len(pal_data) == 256:
        # 256字节，需要转换
        for i in range(256):
            val = pal_data[i]
            r = (val << 2) | (val >> 4)
            g = (val << 2) | (val >> 4)
            b = (val << 2) | (val >> 4)
            palette_rgb24.append((r, g, b))
    else:
        print(f"警告：调色板大小异常: {len(pal_data)}")
        return None
    
    return palette_rgb24

def main():
    dat_path = 'game/FDOTHER.DAT'
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    palette_rgb24 = load_palette_from_fdother()
    if not palette_rgb24:
        print("调色板加载失败")
        return
    
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
    
    # 解析索引1（MULTI_TILE）
    res_start = offsets[1]
    res_data = data[res_start:]
    
    # 头部：宽(2) + 高(2) + 调色板窗口(2) = 6字节
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = struct.unpack_from('<H', res_data, 4)[0]
    
    print(f"\n索引1: {outer_w}x{outer_h}, pal_window={pal_window}")
    
    # 解析偏移表（从偏移6开始）
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"图标数量: {len(icon_offsets)}")
    print(f"偏移表: {[hex(o) for o in icon_offsets[:5]]}")
    
    # 测试图标0
    if len(icon_offsets) > 0:
        start = icon_offsets[0]
        end = icon_offsets[1] if len(icon_offsets) > 1 else len(res_data)
        icon_data = res_data[start:end]
        
        print(f"\n图标0: 偏移={start}, 大小={end-start}")
        print(f"前32字节: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
        
        # 使用外层宽高
        width, height = outer_w, outer_h
        pixel_data = icon_data
        print(f"使用外层宽高: {width}x{height}")
        
        # 1:1复制sub_4EC66逻辑
        dst = []
        src_idx = 0
        ah = 0
        al = 0  # 像素值
        
        for i in range(width * height):
            # sub_4EC66逻辑
            if ah > 0:
                # AH > 0: 重复之前的像素值
                ah -= 1
                # AL保持不变
            else:
                # AH == 0: 读取新字节
                if src_idx >= len(pixel_data):
                    break
                
                al = pixel_data[src_idx]
                src_idx += 1
                
                if al > 0xC0:
                    # AL > 0xC0: 运行长度编码
                    ah = al - 0xC1
                    if src_idx < len(pixel_data):
                        al = pixel_data[src_idx]
                        src_idx += 1
                    # AL现在是像素值
                else:
                    # AL <= 0xC0: 直接像素值
                    ah = 0
                    # AL已经是像素值
            
            # sub_4EC66结束，AL是像素值
            # 应用调色板窗口
            pixel = (pal_window + al) & 0xFF
            dst.append(pixel)
        
        print(f"解码像素数: {len(dst)}, 源数据消耗: {src_idx}/{len(pixel_data)}")
        
        # 保存图像
        if len(dst) == width * height:
            img = Image.new('RGB', (width, height))
            pixels = img.load()
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx < len(dst):
                        pal_idx = dst[idx]
                        pixels[x, y] = palette_rgb24[pal_idx]
            
            out_path = 'output/test_icon0_final.png'
            img.save(out_path)
            print(f"已保存到: {out_path}")
        else:
            print(f"像素数不匹配: {len(dst)} != {width*height}")

if __name__ == '__main__':
    main()
