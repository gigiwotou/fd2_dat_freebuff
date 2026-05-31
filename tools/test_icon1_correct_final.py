#!/usr/bin/env python3
"""1:1复现sub_4EC66 + sub_4EBFF，使用pitch=320渲染到屏幕缓冲区"""
import struct
from PIL import Image

def load_fdother(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    
    offsets.append(len(data))
    return data, offsets

def load_palette(data, offsets):
    pal_start = offsets[0]
    pal_data = data[pal_start:pal_start+768]
    palette = []
    for i in range(256):
        r = pal_data[i*3]
        g = pal_data[i*3+1]
        b = pal_data[i*3+2]
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette.append((r, g, b))
    return palette

def sub_4ec66_step(src_data):
    """sub_4EC66: 每次调用返回一个像素值"""
    global ec66_ah, ec66_src_pos, ec66_al
    
    # or ah, ah; jz loc_4EC6D
    if ec66_ah == 0:
        # loc_4EC6D: lodsb
        if ec66_src_pos >= len(src_data):
            return False
        
        ec66_al = src_data[ec66_src_pos]
        ec66_src_pos += 1
        
        # cmp al, 0C0h; ja loc_4EC75
        if ec66_al > 0xC0:
            # loc_4EC75: mov ah, al; sub ah, 0C1h
            ec66_ah = ec66_al - 0xC1
            
            # lodsb
            if ec66_src_pos >= len(src_data):
                return False
            ec66_al = src_data[ec66_src_pos]
            ec66_src_pos += 1
        else:
            # xor ah, ah
            ec66_ah = 0
    else:
        # dec ah
        ec66_ah -= 1
        # AL保持不变
    
    return True

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    palette = load_palette(data, offsets)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 解析相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"图标数量: {len(icon_offsets)}")
    
    # 测试图标0 - 1:1复现sub_4EBFF + sub_4EC66
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\n图标{icon_idx}: {len(icon_data)}字节")
    print(f"前16字节: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
    
    global ec66_ah, ec66_src_pos, ec66_al
    ec66_ah = 0
    ec66_src_pos = 0
    ec66_al = 0
    
    # 图标数据包含4字节宽高头
    tile_w = struct.unpack_from('<H', icon_data, 0)[0]
    tile_h = struct.unpack_from('<H', icon_data, 2)[0]
    print(f"图标内部宽高: {tile_w}x{tile_h}")
    
    if tile_w > 1000 or tile_h > 1000:
        print("⚠️ 宽高异常，图标数据可能不包含宽高头")
        # 使用外层宽高，跳过4字节
        width = outer_w
        height = outer_h
        pixel_data = icon_data[4:]
    else:
        width = tile_w
        height = tile_h
        pixel_data = icon_data[4:]  # 跳过4字节宽高头
    
    print(f"渲染尺寸: {width}x{height}")
    print(f"像素数据大小: {len(pixel_data)}字节")
    
    # 1:1复现sub_4EBFF
    # 创建320x200的屏幕缓冲区
    SCREEN_W, SCREEN_H = 320, 200
    screen_buf = [0] * (SCREEN_W * SCREEN_H)
    pitch = 320
    
    # sub_4EBFF: EDI = dst缓冲区 (从屏幕中间开始)
    dst_start = 0  # 简化：从屏幕左上角开始
    edi = dst_start
    
    # 外层循环: DX = height行
    for row in range(height):
        push_edi = edi  # push edi - 保存行起始
        
        # 内层循环: CX = width次
        for col in range(width):
            # call sub_4EC66
            if not sub_4ec66_step(pixel_data):
                break
            
            # stosb - 存储AL到[EDI]
            screen_buf[edi] = ec66_al
            edi += 1
        
        # pop edi + add edi, ebx
        edi = push_edi + pitch
    
    # 提取图标区域（sub_4EBFF不应用palette_window）
    pixels = []
    for row in range(height):
        for col in range(width):
            pixels.append(screen_buf[row * pitch + col])
    
    print(f"前24像素(原始): {' '.join(f'{p:02X}' for p in pixels[:24])}")
    
    # 渲染图像（应用palette_window）
    img = Image.new('RGB', (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            idx = (pixels[y * width + x] + pal_win) & 0xFF
            pix[x, y] = palette[idx]
    img.save('output/icon0_sub4ebff_correct.png')
    print(f"已保存: output/icon0_sub4ebff_correct.png")
    
    # 对比：不应用palette_window
    img2 = Image.new('RGB', (width, height))
    pix2 = img2.load()
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x] & 0xFF
            pix2[x, y] = palette[idx]
    img2.save('output/icon0_sub4ebff_no_pal.png')
    print(f"已保存: output/icon0_sub4ebff_no_pal.png")

ec66_ah = 0
ec66_src_pos = 0
ec66_al = 0

if __name__ == '__main__':
    main()
