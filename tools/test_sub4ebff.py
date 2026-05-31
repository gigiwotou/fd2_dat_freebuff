#!/usr/bin/env python3
"""精确模拟sub_4EBFF + sub_4EC66的渲染流程"""
import struct

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

def sub_4ec66(src_data, src_size):
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
        return 0  # 数据不足
    
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

def sub_4ebff(dst, dst_pitch, src_data, src_size):
    """
    sub_4EBFF: 渲染像素数据到屏幕缓冲区
    根据MCP汇编1:1实现:
    
    4ec0c  lodsw        ; 读取width到AX
    4ec0e  mov  bp, ax  ; BP = width
    4ec11  lodsw        ; 读取height到AX
    4ec13  mov  dx, ax  ; DX = height
    4ec1b  push edi     ; 保存行起始位置
    4ec1c  mov  cx, bp  ; CX = width (loop计数器)
    4ec1f  call sub_4EC66 ; 获取像素值
    4ec24  stosb        ; 存储像素
    4ec25  loop loc_4EC1F ; 循环width次
    4ec27  pop edi      ; 恢复行起始
    4ec28  add  edi, ebx ; 移动到下一行 (edi += pitch)
    4ec2a  dec  dx      ; height--
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
    
    print(f"  sub_4EBFF: width={width}, height={height}")
    print(f"  src_size={src_size}, 像素数据从偏移4开始")
    
    # 像素数据从偏移4开始 (跳过宽高头)
    pixel_data = src_data[4:]
    pixel_data_size = src_size - 4
    
    if width <= 0 or width > 320 or height <= 0 or height > 200:
        print(f"  宽高不合理，无法渲染")
        return False
    
    dst_pos = 0  # 模拟edi
    
    # 外层循环: DX = height行
    for row in range(height):
        row_start = dst_pos  # push edi
        
        # 内层循环: CX = width次
        for col in range(width):
            # call sub_4EC66
            pixel = sub_4ec66(pixel_data, pixel_data_size)
            
            # stosb: 存储到dst[edi]
            dst[dst_pos] = pixel
            dst_pos += 1
        
        # pop edi (恢复行起始)
        dst_pos = row_start
        
        # add edi, ebx (移动到下一行)
        dst_pos += dst_pitch
        
        # 打印前3行的前20个像素
        if row < 3:
            row_pixels = dst[row_start:row_start+width]
            hex_str = ' '.join(f'{p:02X}' for p in row_pixels[:20])
            print(f"  行{row}: {hex_str}")
    
    return True

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print("=== 索引1 模拟sub_4EBFF ===")
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
    
    # 分析图标0
    if len(icon_offsets) > 0:
        rel_off = icon_offsets[0]
        next_rel = icon_offsets[1] if len(icon_offsets) > 1 else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\n=== 图标0 ===")
        print(f"相对偏移: 0x{rel_off:X} - 0x{next_rel:X}")
        print(f"大小: {len(icon_data)} 字节")
        print(f"前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
        
        # 模拟sub_4EBFF
        # 假设pitch = 320 (游戏屏幕宽度)
        dst_buffer = bytearray(320 * 200)
        pitch = 320
        
        success = sub_4ebff(dst_buffer, pitch, icon_data, len(icon_data))
        
        if success:
            # 统计渲染的像素
            non_zero = sum(1 for b in dst_buffer if b != 0)
            unique = len(set(dst_buffer))
            print(f"\n渲染结果:")
            print(f"  非零像素: {non_zero}")
            print(f"  唯一值: {unique}")

# 全局EC66状态
ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
