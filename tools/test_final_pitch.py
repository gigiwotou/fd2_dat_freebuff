#!/usr/bin/env python3
"""测试：使用外头宽高+pitch=320渲染索引1图标"""
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

def sub_4ec66_step(src_data, src_size):
    """sub_4EC66: 精确按照MCP汇编实现"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    if ec66_ah > 0:
        ec66_ah -= 1
        return ec66_prev_al
    
    if ec66_src_pos >= src_size:
        return 0
    
    al = src_data[ec66_src_pos]
    ec66_src_pos += 1
    
    if al > 0xC0:
        ec66_ah = al - 0xC1
        if ec66_src_pos < src_size:
            al = src_data[ec66_src_pos]
            ec66_src_pos += 1
        ec66_prev_al = al
        return al
    else:
        ec66_ah = 0
        ec66_prev_al = al
        return al

def render_with_pitch(src_data, src_size, width, height, pitch, palette_window):
    """
    使用外头宽高+pitch渲染，类似sub_4EBFF但不读取宽高头
    
    这模拟调用sub_4EBFF时，宽高作为参数传入的情况
    """
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    # 重置EC66状态
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 创建pitch*height的缓冲区
    dst_size = pitch * height
    dst_buffer = [0] * dst_size
    
    # 外层循环: height行
    dst_pos = 0  # EDI = 0
    
    for row in range(height):
        row_start = dst_pos  # push edi
        
        # 内层循环: width次
        for col in range(width):
            # call sub_4EC66
            if ec66_src_pos < src_size:
                pixel = sub_4ec66_step(src_data, src_size)
            else:
                pixel = 0
            
            # stosb: 存储到dst[EDI], EDI++
            dst_buffer[dst_pos] = pixel
            dst_pos += 1
        
        # pop edi (恢复行起始)
        dst_pos = row_start
        
        # add edi, ebx (移动到下一行，使用pitch)
        dst_pos += pitch
    
    # 应用调色板窗口
    for i in range(len(dst_buffer)):
        dst_buffer[i] = (dst_buffer[i] + palette_window) & 0xFF
    
    return dst_buffer

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

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    palette = load_palette(data, offsets)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    # 外头宽高
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
        if len(icon_offsets) >= 20:
            break
    
    print(f"图标数量: {len(icon_offsets)}\n")
    
    # 测试：使用外头宽高+pitch=320
    PITCH = 320
    
    print(f"=== 测试：外头宽高{outer_w}x{outer_h} + pitch={PITCH} ===")
    
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        icon_size = next_rel - rel_off
        
        print(f"\n图标{icon_idx}: {icon_size}字节")
        print(f"  前16字节: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
        
        # 使用外头宽高+pitch渲染
        dst_buffer = render_with_pitch(icon_data, icon_size, outer_w, outer_h, PITCH, pal_win)
        
        # 渲染图像
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        
        for y in range(outer_h):
            for x in range(outer_w):
                pal_idx = dst_buffer[y * PITCH + x]
                if pal_idx < 256:
                    pix[x, y] = palette[pal_idx]
                else:
                    pix[x, y] = (255, 0, 0)
        
        output_path = f'output/icon1_outer_wh_pitch320_{icon_idx}.png'
        img.save(output_path)
        print(f"  保存到: {output_path}")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
