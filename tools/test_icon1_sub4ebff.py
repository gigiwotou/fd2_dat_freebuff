#!/usr/bin/env python3
"""根据sub_4EBFF汇编精确实现索引1解码 - 图标数据包含宽高头"""
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
    """
    sub_4EC66: 获取下一个像素值
    使用全局状态: ah (运行计数器), prev_al (上次像素值)
    返回: 像素值
    """
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

def sub_4ebff_render(dst, dst_pitch, src_data, src_size):
    """
    sub_4EBFF: 精确按照MCP汇编实现
    4ec0c  lodsw        ; 从src读取width (ESI+=2)
    4ec0e  mov  bp, ax  ; BP = width
    4ec11  lodsw        ; 从src读取height (ESI+=2)
    4ec13  mov  dx, ax  ; DX = height
    4ec16  xor  ecx, ecx ; ECX = 0
    4ec18  xor  ax, ax   ; AX = 0
    4ec1b  push edi     ; 保存行起始
    4ec1c  mov  cx, bp  ; CX = width
    4ec1f  call sub_4EC66 ; 获取像素值
    4ec24  stosb        ; 存储到dst[EDI], EDI++
    4ec25  loop loc_4EC1F ; CX--，如果!=0继续
    4ec27  pop edi      ; 恢复行起始
    4ec28  add  edi, ebx ; EDI += pitch
    4ec2a  dec  dx      ; DX-- (height--)
    4ec2c  jnz  loc_4EC1B ; 如果height!=0，继续下一行
    """
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    # 重置EC66状态
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 从src_data读取宽高 (lodsw两次)
    width = struct.unpack_from('<H', src_data, 0)[0]
    height = struct.unpack_from('<H', src_data, 2)[0]
    
    # 像素数据从偏移4开始 (ESI已经前进了4字节)
    pixel_data = src_data[4:]
    pixel_data_size = src_size - 4
    
    print(f"  sub_4EBFF: width={width}, height={height}")
    print(f"  像素数据: {pixel_data_size} 字节")
    
    if width <= 0 or width > 320 or height <= 0 or height > 200:
        print(f"  宽高不合理，无法渲染")
        return False, 0, 0
    
    # 模拟EDI (目标缓冲区位置)
    dst_pos = 0
    
    # 外层循环: DX = height行
    for row in range(height):
        row_start = dst_pos  # push edi
        
        # 内层循环: CX = width次
        for col in range(width):
            # call sub_4EC66
            pixel = sub_4ec66_step(pixel_data, pixel_data_size)
            
            # stosb: 存储到dst[EDI], EDI++
            dst[dst_pos] = pixel
            dst_pos += 1
        
        # pop edi (恢复行起始)
        dst_pos = row_start
        
        # add edi, ebx (移动到下一行)
        dst_pos += dst_pitch
        
        # 打印前3行
        if row < 3:
            row_pixels = dst[row_start:row_start+width]
            hex_str = ' '.join(f'{p:02X}' for p in row_pixels[:24])
            print(f"  行{row}: {hex_str}")
    
    return True, width, height

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print("=== 索引1 精确sub_4EBFF解码 ===")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 外头
    w_outer = struct.unpack_from('<H', res_data, 0)[0]
    h_outer = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"外头: {w_outer}x{h_outer}, pal_window={pal_win}")
    
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
    
    print(f"找到 {len(icon_offsets)} 个图标")
    
    # 渲染前5个图标
    print(f"\n渲染前5个图标:")
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\n{'='*60}")
        print(f"图标{icon_idx}: 0x{rel_off:X} - 0x{next_rel:X}, {len(icon_data)}字节")
        print(f"前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
        
        # 渲染到320x200缓冲区
        dst_buffer = bytearray(320 * 200)
        pitch = 320  # 行间距
        
        success, width, height = sub_4ebff_render(dst_buffer, pitch, icon_data, len(icon_data))
        
        if success:
            # 提取渲染区域
            icon_pixels = []
            for row in range(height):
                row_start = row * pitch
                for col in range(width):
                    icon_pixels.append(dst_buffer[row_start + col])
            
            # 统计
            non_zero = sum(1 for p in icon_pixels if p != 0)
            unique = len(set(icon_pixels))
            print(f"  非零像素: {non_zero}/{width*height}")
            print(f"  唯一值: {unique}")
            
            # 渲染到图像 (应用调色板窗口)
            img = Image.new('RGB', (width, height))
            pixels = img.load()
            
            # 简单调色板 (灰度)
            for y in range(height):
                for x in range(width):
                    idx = icon_pixels[y * width + x]
                    # 应用调色板窗口
                    idx = (idx + pal_win) & 0xFF
                    gray = idx
                    pixels[x, y] = (gray, gray, gray)
            
            output_path = f'output/icon1_sub4ebff_{icon_idx}.png'
            img.save(output_path)
            print(f"  保存到: {output_path}")

# 全局EC66状态
ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
