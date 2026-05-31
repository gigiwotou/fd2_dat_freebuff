#!/usr/bin/env python3
"""1:1复现sub_4EC66 + sub_4EBFF的完整逻辑"""
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

def sub_4ec66_1to1(src_data):
    """1:1复现sub_4EC66汇编逻辑
    4ec66  or      ah, ah
    4ec68  jz      short loc_4EC6D
    4ec6a  dec     ah
    4ec6c  retn
    
    4ec6d  lodsb
    4ec6e  cmp     al, 0C0h
    4ec70  ja      short loc_4EC75
    4ec72  xor     ah, ah
    4ec74  retn
    
    4ec75  mov     ah, al
    4ec77  sub     ah, 0C1h
    4ec7a  lodsb
    4ec7b  retn
    """
    global ec66_ah, ec66_src_pos, ec66_al
    
    # or ah, ah; jz loc_4EC6D
    if ec66_ah == 0:
        # loc_4EC6D: lodsb (读取新字节到AL)
        if ec66_src_pos >= len(src_data):
            return False  # 数据不足
        
        ec66_al = src_data[ec66_src_pos]
        ec66_src_pos += 1
        
        # cmp al, 0C0h; ja loc_4EC75
        if ec66_al > 0xC0:
            # loc_4EC75: mov ah, al; sub ah, 0C1h
            ec66_ah = ec66_al - 0xC1
            
            # lodsb (再读取一个字节到AL)
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
        # AL保持上次的值不变
    
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
    
    # 1:1复现sub_4EBFF
    # 4ebff  push    ebp
    # 4ec00  mov     ebp, esp
    # 4ec02  pusha
    # 4ec03  mov     edi, [ebp+arg_0]  ; dst缓冲区
    # 4ec06  mov     esi, [ebp+arg_4]  ; src数据
    # 4ec09  mov     ebx, [ebp+arg_8]  ; pitch
    
    # 创建320x200的屏幕缓冲区
    SCREEN_W, SCREEN_H = 320, 200
    screen_buf = [0] * (SCREEN_W * SCREEN_H)
    pitch = 320
    
    # 图标数据直接就是像素数据（没有4字节宽高头）
    src_data = icon_data
    
    # 使用外层头部的宽高
    width = outer_w
    height = outer_h
    
    print(f"渲染: {width}x{height}, pitch={pitch}")
    
    # 4ec0c  lodsw  ; 读取width (但我们已经知道宽高，跳过)
    # 4ec11  lodsw  ; 读取height
    # 实际sub_4EBFF从src读取宽高，但图标数据没有宽高头，所以直接使用外层宽高
    
    # 4ec16  xor     ecx, ecx
    # 4ec18  xor     ax, ax
    
    # 4ec1b  push    edi  ; 保存行起始位置
    # 4ec1c  mov     cx, bp  ; CX = width
    # 4ec1f  call    sub_4EC66
    # 4ec24  stosb  ; 存储AL到[EDI], EDI++
    # 4ec25  loop    loc_4EC1F
    # 4ec27  pop     edi
    # 4ec28  add     edi, ebx
    # 4ec2a  dec     dx
    # 4ec2c  jnz     short loc_4EC1B
    
    dst_pos = 0  # EDI初始位置
    
    for row in range(height):
        row_start = dst_pos  # push edi
        
        for col in range(width):
            # call sub_4EC66
            if not sub_4ec66_1to1(src_data):
                break
            
            # stosb - 存储AL到屏幕缓冲区
            screen_buf[dst_pos] = ec66_al
            dst_pos += 1
        
        # pop edi + add edi, ebx
        dst_pos = row_start + pitch
    
    # 提取图标区域（不应用palette_window）
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
    img.save('output/icon0_sub4ebff_1to1.png')
    print(f"已保存: output/icon0_sub4ebff_1to1.png")
    
    # 对比：不应用palette_window
    img2 = Image.new('RGB', (width, height))
    pix2 = img2.load()
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x] & 0xFF
            pix2[x, y] = palette[idx]
    img2.save('output/icon0_sub4ebff_no_palwin.png')
    print(f"已保存: output/icon0_sub4ebff_no_palwin.png")

ec66_ah = 0
ec66_src_pos = 0
ec66_al = 0

if __name__ == '__main__':
    main()
