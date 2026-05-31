#!/usr/bin/env python
"""
1:1复制sub_4E22A汇编代码
基于逐行分析汇编指令
"""

import struct
import os

def sub_4E22A_decode_exact(src_data, pitch=24):
    """
    1:1复制sub_4E22A汇编代码
    
    根据反编译代码：
    char __cdecl sub_4E22A(char *src, char *dst, int arg8)
    
    arg8 = pitch (行间距)
    """
    dst = bytearray(24 * 24)  # 固定24x24
    
    src_idx = 0
    dst_idx = 0
    
    # 4e23c: xor ecx, ecx -> count = 0
    count = 0
    # 4e23e: mov bl, 18h -> n24 = 24 (行数)
    n24 = 24
    
    # 外层循环：do...while(n24)
    while True:
        # 4e240: mov bh, 18h -> n24_1 = 24 (每行像素数)
        n24_1 = 24
        
        # 内层循环：do...while(n24_1)
        while True:
            # 4e242: lodsb -> value = *src++
            if src_idx >= len(src_data):
                break
            value = src_data[src_idx]
            src_idx += 1
            
            # 4e243: mov cl, al
            # 4e245: shl cl, 1
            cl = (value << 1) & 0xFF
            
            # 4e247: jb short loc_4E271
            # CF = value的bit7
            if value & 0x80:
                # bit7=1: 跳转到0x4E271
                
                # 4e271: shl cl, 1
                # CF = (value << 1)的bit7 = value的bit6
                cl = (cl << 1) & 0xFF
                
                # 4e273: jb short loc_4E284
                if value & 0x40:  # bit6=1
                    # bit6=1: 11xxxxxx - 跳过模式
                    # 4e284: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e287: inc cl
                    count = count + 1
                    
                    # 4e289: add edi, ecx -> dst += count
                    dst_idx += count
                    
                    # 4e28b: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e28d: or bh, bh
                    # 4e28f: jnz short loc_4E242
                    if n24_1 != 0:
                        continue
                    else:
                        break
                else:
                    # bit6=0: 10xxxxxx - 复制模式
                    # 4e275: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e278: inc cl
                    count = count + 1
                    
                    # 4e27a: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e27c: rep movsb
                    if src_idx + count <= len(src_data):
                        for i in range(count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = src_data[src_idx + i]
                            dst_idx += 1
                        src_idx += count
                    
                    # 4e27e: or bh, bh
                    # 4e280: jnz short loc_4E242
                    if n24_1 != 0:
                        continue
                    else:
                        break
            else:
                # bit7=0: 继续
                # 4e249: shl cl, 1
                # CF = (value << 1)的bit7 = value的bit6
                cl = (cl << 1) & 0xFF
                
                # 4e24b: jb short loc_4E25D
                if value & 0x40:  # bit6=1
                    # bit6=1: 01xxxxxx - 交替模式
                    # 4e25d: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e260: inc cl
                    count = count + 1
                    
                    # 4e262: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    # 4e264: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e266: lodsb -> value = *src++
                    if src_idx >= len(src_data):
                        break
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    
                    # 4e267-4e269: loop循环
                    # do {
                    #   4e267: inc edi -> dst++
                    #   4e268: stosb -> *dst++ = value
                    #   4e269: loop -> --count
                    # } while(count)
                    for _ in range(count):
                        dst_idx += 1  # inc edi
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1  # stosb
                    
                    # 4e26b: or bh, bh
                    # 4e26d: jnz short loc_4E242
                    if n24_1 != 0:
                        continue
                    else:
                        break
                else:
                    # bit6=0: 00xxxxxx - 填充模式
                    # 4e24d: shr cl, 2
                    count = (cl >> 2) & 0xFF
                    # 4e250: inc cl
                    count = count + 1
                    
                    # 4e252: sub bh, cl
                    n24_1 = (n24_1 - count) & 0xFF
                    
                    # 4e254: lodsb -> value = *src++
                    if src_idx >= len(src_data):
                        break
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    
                    # 4e255: rep stosb
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1
                    
                    # 4e257: or bh, bh
                    # 4e259: jnz short loc_4E242
                    if n24_1 != 0:
                        continue
                    else:
                        break
        
        # 行结束
        # 4e291: add edi, edx -> dst += (pitch - 24)
        # edx在函数开始时被设置为arg8 - 24
        dst_idx += (pitch - 24)
        
        # 4e293: dec bl
        n24 = (n24 - 1) & 0xFF
        
        # 4e295: jnz short loc_4E240
        if n24 == 0:
            break
    
    return bytes(dst)


def test_icon0():
    """测试图标0的解码"""
    fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
    
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    
    # 解析资源偏移表
    offsets = []
    pos = 6
    while pos + 4 <= file_size:
        off = struct.unpack('<I', data[pos:pos+4])[0]
        if off == 0 or off > file_size:
            break
        offsets.append(off)
        pos += 4
    offsets.append(file_size)
    
    # 获取索引1资源
    idx1_start = offsets[1]
    idx1_end = offsets[2]
    idx1_data = data[idx1_start:idx1_end]
    
    # 解析头部
    palette_window = idx1_data[4]
    
    # 解析图标偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(idx1_data):
        off = struct.unpack('<I', idx1_data[pos:pos+4])[0]
        if off == 0 or off > len(idx1_data):
            break
        icon_offsets.append(off)
        pos += 4
    
    # 获取图标0
    icon0_start = icon_offsets[0]
    icon0_end = icon_offsets[1] if len(icon_offsets) > 1 else len(idx1_data)
    icon0_data = idx1_data[icon0_start:icon0_end]
    
    print(f"图标0: offset=0x{icon0_start:X}, size={len(icon0_data)} bytes")
    print(f"palette_window: {palette_window}")
    print(f"前40字节: {' '.join(f'{b:02X}' for b in icon0_data[:40])}\n")
    
    # 手动解码前几个控制字节
    print("手动解码前10个控制字节:")
    src_idx = 0
    dst_idx = 0
    for i in range(10):
        if src_idx >= len(icon0_data):
            break
        value = icon0_data[src_idx]
        bit7 = (value >> 7) & 1
        bit6 = (value >> 6) & 1
        mode = f"{bit7}{bit6}"
        lower6 = value & 0x3F
        count = lower6 + 1
        
        if mode == "00":
            desc = f"填充模式 (count={count})"
        elif mode == "01":
            desc = f"交替模式 (count={count})"
        elif mode == "10":
            desc = f"复制模式 (count={count})"
        elif mode == "11":
            desc = f"跳过模式 (count={count})"
        
        print(f"  字节{i} @ src[{src_idx}]: 0x{value:02X} = {mode}xxxxxx -> {desc}")
        src_idx += 1
    
    # 解码图标0
    decoded = sub_4E22A_decode_exact(icon0_data, 24)
    
    # 输出解码结果
    print(f"\n解码后的24x24像素矩阵:")
    for row in range(24):
        row_data = decoded[row*24:(row+1)*24]
        hex_str = ' '.join(f'{v:02X}' for v in row_data)
        print(f"  行{row:2d}: {hex_str}")
    
    # 应用调色板窗口
    with_palette = bytearray(24*24)
    for i in range(24*24):
        with_palette[i] = (decoded[i] + palette_window) & 0xFF
    
    print(f"\n应用palette_window={palette_window}后:")
    for row in range(24):
        row_data = with_palette[row*24:(row+1)*24]
        hex_str = ' '.join(f'{v:02X}' for v in row_data)
        print(f"  行{row:2d}: {hex_str}")
    
    # 保存为文本文件
    output_path = r"d:\workspace\fd2_dat_freebuff\output\icon0_decoded.txt"
    with open(output_path, 'w') as f:
        f.write(f"图标0 - sub_4E22A解码结果\n")
        f.write(f"palette_window: {palette_window}\n")
        f.write(f"图标数据大小: {len(icon0_data)} bytes\n\n")
        
        f.write("原始像素值:\n")
        for row in range(24):
            row_data = decoded[row*24:(row+1)*24]
            chars = []
            for v in row_data:
                if v == 0:
                    chars.append('..')
                elif v < 16:
                    chars.append(f'0{v:X}')
                else:
                    chars.append(f'{v:X}')
            f.write(' '.join(chars) + '\n')
        
        f.write(f"\n应用palette_window={palette_window}后:\n")
        for row in range(24):
            row_data = with_palette[row*24:(row+1)*24]
            chars = []
            for v in row_data:
                if v == 0:
                    chars.append('..')
                elif v < 16:
                    chars.append(f'0{v:X}')
                else:
                    chars.append(f'{v:X}')
            f.write(' '.join(chars) + '\n')
    
    print(f"\n结果已保存到: {output_path}")


if __name__ == '__main__':
    test_icon0()
