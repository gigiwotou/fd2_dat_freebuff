#!/usr/bin/env python
"""
1:1复制sub_4E22A汇编代码的Python实现
基于对汇编代码的逐行分析
"""

import struct
import os
import sys

def sub_4E22A_decode_assembly(src_data, width=24, height=24, pitch=24):
    """
    1:1复制sub_4E22A汇编代码
    参数：src=源数据, dst=目标缓冲区, arg8=pitch
    """
    dst = bytearray(width * height)
    
    # 4e23c: xor ecx, ecx
    count = 0
    # 4e23e: mov bl, 18h
    n24 = 24  # bl = 行数
    # 4e240: mov bh, 18h
    n24_1 = 24  # bh = 每行像素数
    
    src_idx = 0
    dst_idx = 0
    
    # 外层循环：do...while(n24)
    while True:
        # 4e240: mov bh, 18h
        n24_1 = 24
        
        # 内层循环：do...while(n24_1)
        while True:
            # 4e242: lodsb - al = *src++
            if src_idx >= len(src_data):
                break
            value = src_data[src_idx]
            src_idx += 1
            
            # 4e243: mov cl, al
            # 4e245: shl cl, 1
            cl = (value << 1) & 0xFF
            
            # 4e247: jb short loc_4E271 - 检查CF(bit7)
            if value & 0x80:
                # bit7=1: 跳转到0x4E271
                
                # 4e271: shl cl, 1
                cl = (cl << 1) & 0xFF  # 再次左移检查bit6
                
                # 4e273: jb short loc_4E284
                if cl & 0x100:  # bit6=1
                    # bit6=1: 11xxxxxx - 跳过模式
                    # 4e284: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e287: inc cl
                    count = count + 1
                    
                    # 4e289: add edi, ecx - dst += count
                    dst_idx += count
                    
                    # 4e28b: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e28d: or bh, bh
                    # 4e28f: jnz short loc_4E242
                    if n24_1 == 0:
                        break
                else:
                    # bit6=0: 10xxxxxx - 复制模式
                    # 4e275: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e278: inc cl
                    count = count + 1
                    
                    # 4e27a: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e27c: rep movsb - qmemcpy(dst, src, count); src+=count; dst+=count
                    if src_idx + count <= len(src_data):
                        dst[dst_idx:dst_idx+count] = src_data[src_idx:src_idx+count]
                        src_idx += count
                        dst_idx += count
                    
                    # 4e27e: or bh, bh
                    # 4e280: jnz short loc_4E242
                    if n24_1 == 0:
                        break
            else:
                # bit7=0: 继续检查
                # 4e249: shl cl, 1
                cl = (cl << 1) & 0xFF  # 检查bit6
                
                # 4e24b: jb short loc_4E25D
                if cl & 0x100:  # bit6=1
                    # bit6=1: 01xxxxxx - 交替模式（间隔2写入）
                    # 4e25d: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e260: inc cl
                    count = count + 1
                    
                    # 4e262: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    # 4e264: sub bh, cl - 注意：减了两次！
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e266: lodsb - value = *src++
                    if src_idx >= len(src_data):
                        break
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    
                    # 4e267-4e269: loop循环 - 间隔写入
                    # do {
                    #   4e267: inc edi - dst++
                    #   4e268: stosb - *dst++ = value
                    #   4e269: loop - --count
                    # } while(count)
                    for _ in range(count):
                        dst_idx += 1  # 4e267: inc edi
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1  # stosb后还会+1
                    
                    # 4e26b: or bh, bh
                    # 4e26d: jnz short loc_4E242
                    if n24_1 == 0:
                        break
                else:
                    # bit6=0: 00xxxxxx - 填充模式
                    # 4e24d: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e250: inc cl
                    count = count + 1
                    
                    # 4e252: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e254: lodsb - value = *src++
                    if src_idx >= len(src_data):
                        break
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    
                    # 4e255: rep stosb - memset(dst, value, count); dst+=count
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1
                    
                    # 4e257: or bh, bh
                    # 4e259: jnz short loc_4E242
                    if n24_1 == 0:
                        break
        
        # 4e291: add edi, edx - dst += (pitch - 24)
        dst_idx += (pitch - 24)
        
        # 4e293: dec bl
        n24 = (n24 - 1) & 0xFF
        
        # 4e295: jnz short loc_4E240
        if n24 == 0:
            break
    
    return bytes(dst)


def test_with_real_data():
    """使用真实数据测试"""
    fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
    
    if not os.path.exists(fdother_path):
        print(f"文件不存在: {fdother_path}")
        return
    
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    # 解析索引1的资源
    index1_offset = data[0x14] | (data[0x15] << 8) | (data[0x16] << 16) | (data[0x17] << 24)
    index1_size = data[0x18] | (data[0x19] << 8) | (data[0x1A] << 16) | (data[0x1B] << 24)
    
    print(f"索引1: offset=0x{index1_offset:X}, size=0x{index1_size:X}")
    
    res_data = data[index1_offset:index1_offset + index1_size]
    
    # 解析头部
    width = res_data[0] | (res_data[1] << 8)
    height = res_data[2] | (res_data[3] << 8)
    palette_window = res_data[4]
    padding = res_data[5]
    
    print(f"头部: width={width}, height={height}, palette_window={palette_window}, padding={padding}")
    
    # 解析偏移表（从偏移6开始）
    offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        off = res_data[pos] | (res_data[pos+1] << 8) | (res_data[pos+2] << 16) | (res_data[pos+3] << 24)
        if off == 0 or off > index1_size:
            break
        offsets.append(off)
        pos += 4
        if len(offsets) > 100:
            break
    
    print(f"图标数量: {len(offsets)}")
    print(f"前10个偏移: {[hex(o) for o in offsets[:10]]}")
    
    # 测试解码第一个图标
    if len(offsets) > 0:
        icon_offset = offsets[0]
        next_offset = offsets[1] if len(offsets) > 1 else len(res_data)
        icon_size = next_offset - icon_offset
        
        print(f"\n图标0: offset=0x{icon_offset:X}, size={icon_size}")
        print(f"前20字节: {' '.join(f'{b:02X}' for b in res_data[icon_offset:icon_offset+20])}")
        
        # 使用sub_4E22A解码
        icon_data = res_data[icon_offset:icon_offset+icon_size]
        decoded = sub_4E22A_decode_assembly(icon_data, 24, 24, 24)
        
        # 输出解码后的像素值（前100个）
        print(f"\n解码后的前100个像素值:")
        for i in range(0, min(100, len(decoded)), 24):
            row = decoded[i:min(i+24, len(decoded))]
            print(f"  行{i//24}: {' '.join(f'{v:3d}' for v in row)}")
        
        # 保存为可视化的TXT文件
        output_path = r"d:\workspace\fd2_dat_freebuff\output\icon0_sub_4E22A.txt"
        with open(output_path, 'w') as f:
            f.write(f"图标0 - 使用sub_4E22A解码\n")
            f.write(f"尺寸: 24x24\n")
            f.write(f"palette_window: {palette_window}\n\n")
            
            for row in range(24):
                row_data = decoded[row*24:(row+1)*24]
                # 将像素值映射为字符
                chars = []
                for v in row_data:
                    if v == 0:
                        chars.append('  ')  # 透明
                    elif v < 16:
                        chars.append(f'0{v:X}')
                    else:
                        chars.append(f'{v:X}')
                f.write(' '.join(chars) + '\n')
        
        print(f"\n结果已保存到: {output_path}")
        
        # 也保存一个应用调色板窗口的版本
        with_palette = bytearray(24*24)
        for i in range(24*24):
            with_palette[i] = decoded[i]
            # 应用调色板窗口
            with_palette[i] = (decoded[i] + palette_window) & 0xFF
        
        output_path2 = r"d:\workspace\fd2_dat_freebuff\output\icon0_sub_4E22A_with_palette.txt"
        with open(output_path2, 'w') as f:
            f.write(f"图标0 - 使用sub_4E22A解码 + 应用palette_window\n")
            f.write(f"尺寸: 24x24\n")
            f.write(f"palette_window: {palette_window}\n\n")
            
            for row in range(24):
                row_data = with_palette[row*24:(row+1)*24]
                chars = []
                for v in row_data:
                    if v == 0:
                        chars.append('  ')
                    elif v < 16:
                        chars.append(f'0{v:X}')
                    else:
                        chars.append(f'{v:X}')
                f.write(' '.join(chars) + '\n')
        
        print(f"应用调色板的结果已保存到: {output_path2}")


if __name__ == '__main__':
    test_with_real_data()
