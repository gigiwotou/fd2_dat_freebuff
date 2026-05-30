#!/usr/bin/env python3
"""
按照sub_4EBFF + sub_4EC66游戏实际渲染逻辑解码图像
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_pixel_ec66(src_data, src_pos, ah):
    """
    sub_4EC66: 像素解码函数
    参数: src_data=源数据, src_pos=当前读取位置, ah=运行长度计数器
    返回: (pixel_value, new_src_pos, new_ah)
    """
    if ah > 0:
        # AH > 0: 重复之前的像素值
        ah -= 1
        # 注意: pixel值应该从之前读取的al获得，但这里用全局状态
        # 实际上al是从之前lodsb得到的值
        return None, src_pos, ah  # 需要跟踪之前的al值
    
    # AH == 0: 读取新字节
    if src_pos >= len(src_data):
        return None, src_pos, ah
    
    al = src_data[src_pos]
    src_pos += 1
    
    if al > 0xC0:
        # AL > 0xC0: 运行长度编码
        ah = al - 0xC1
        # 再读取下一个字节作为像素值
        if src_pos >= len(src_data):
            return None, src_pos, ah
        al = src_data[src_pos]
        src_pos += 1
        # ah > 0, 所以下次调用会返回相同的al
        return al, src_pos, ah
    else:
        # AL <= 0xC0: 直接像素值
        return al, src_pos, 0

def decode_image_4ebff_4ec66(src_data, dst_buffer, pitch):
    """
    sub_4EBFF: 按照游戏实际渲染逻辑解码图像到目标缓冲区
    参数: src_data=源数据(包含4字节宽高头), dst_buffer=目标缓冲区, pitch=行间距
    """
    if len(src_data) < 4:
        return
    
    # 读取宽高
    width = struct.unpack_from('<H', src_data, 0)[0]
    height = struct.unpack_from('<H', src_data, 2)[0]
    
    if width == 0 or height == 0:
        return
    
    # 像素数据从偏移4开始
    pixel_data = src_data[4:]
    
    src_pos = 0
    ah = 0
    prev_al = 0
    
    for row in range(height):
        for col in range(width):
            if ah > 0:
                # 重复之前的像素值
                ah -= 1
                pixel = prev_al
            else:
                # 读取新像素
                if src_pos >= len(pixel_data):
                    break
                al = pixel_data[src_pos]
                src_pos += 1
                
                if al > 0xC0:
                    # 运行长度编码
                    ah = al - 0xC1
                    if src_pos >= len(pixel_data):
                        break
                    al = pixel_data[src_pos]
                    src_pos += 1
                    prev_al = al
                    pixel = al
                else:
                    # 直接像素值
                    prev_al = al
                    pixel = al
            
            dst_buffer[row * pitch + col] = pixel

def test_4ec66_decoding():
    """测试sub_4EC66解码方式"""
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引0调色板
    idx0_data = data[offsets[0]:offsets[1]]
    
    # 索引1数据
    idx1_data = data[offsets[1]:offsets[2]]
    
    print(f"索引1数据:")
    print(f"  大小: {len(idx1_data)} 字节")
    print(f"  前10字节: {' '.join(f'{b:02X}' for b in idx1_data[:10])}")
    
    # 尝试sub_4EC66解码
    width = struct.unpack_from('<H', idx1_data, 0)[0]
    height = struct.unpack_from('<H', idx1_data, 2)[0]
    
    print(f"  宽度: {width}, 高度: {height}")
    print(f"  预期像素数: {width * height}")
    
    if width > 0 and height > 0 and width * height <= 10000:
        # 解码
        dst_buffer = bytearray(width * height)
        decode_image_4ebff_4ec66(idx1_data, dst_buffer, width)
        
        # 统计
        non_zero = sum(1 for p in dst_buffer if p != 0)
        unique_vals = sorted(set(dst_buffer))
        print(f"\n解码结果:")
        print(f"  非零像素: {non_zero}/{width*height}")
        print(f"  唯一值数量: {len(unique_vals)}")
        print(f"  唯一值: {unique_vals[:20]}")
        
        # 渲染 - 直接使用解码值作为调色板索引
        img = Image.new('RGB', (width, height))
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                pal_idx = dst_buffer[idx]
                if pal_idx < 256:
                    r = idx0_data[pal_idx * 3]
                    g = idx0_data[pal_idx * 3 + 1]
                    b = idx0_data[pal_idx * 3 + 2]
                    img.putpixel((x, y), (r, g, b))
        
        img.save('output/idx1_4ec66_decode.png')
        print(f"\n已保存: output/idx1_4ec66_decode.png")
        
        # 也尝试RLE解码对比
        rle_data = idx1_data[5:]  # 跳过5字节头
        
        print(f"\n{'='*60}")
        print(f"对比: 使用sub_4E98D RLE解码")
        print(f"RLE数据大小: {len(rle_data)}")
        
        # RLE解码 (简单版本)
        rle_dst = bytearray(width * height)
        rle_src_pos = 0
        rle_dst_pos = 0
        
        while rle_src_pos < len(rle_data) and rle_dst_pos < width * height:
            ctrl = rle_data[rle_src_pos]
            rle_src_pos += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    actual = min(count, width*height - rle_dst_pos)
                    if rle_src_pos < len(rle_data):
                        val = rle_data[rle_src_pos]
                        rle_src_pos += 1
                        for i in range(actual):
                            rle_dst[rle_dst_pos] = val
                            rle_dst_pos += 1
                else:
                    # COPY_SPEC
                    actual = count
                    total = count * 2
                    if total > width*height - rle_dst_pos:
                        actual = (width*height - rle_dst_pos) // 2
                        total = actual * 2
                    if rle_src_pos < len(rle_data):
                        val = rle_data[rle_src_pos]
                        rle_src_pos += 1
                        for i in range(actual):
                            if rle_dst_pos < len(rle_dst):
                                rle_dst[rle_dst_pos] = val
                                rle_dst_pos += 2
            else:
                if bit6 == 0:
                    # COPY_STD
                    actual = min(count, width*height - rle_dst_pos, len(rle_data) - rle_src_pos)
                    for i in range(actual):
                        if rle_dst_pos < len(rle_dst) and rle_src_pos < len(rle_data):
                            rle_dst[rle_dst_pos] = rle_data[rle_src_pos]
                            rle_src_pos += 1
                            rle_dst_pos += 1
                else:
                    # SKIP
                    actual = min(count, width*height - rle_dst_pos)
                    rle_dst_pos += actual
        
        # 渲染RLE结果
        img_rle = Image.new('RGB', (width, height))
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                pal_idx = rle_dst[idx]
                if pal_idx < 256:
                    r = idx0_data[pal_idx * 3]
                    g = idx0_data[pal_idx * 3 + 1]
                    b = idx0_data[pal_idx * 3 + 2]
                    img_rle.putpixel((x, y), (r, g, b))
        
        img_rle.save('output/idx1_rle_decode.png')
        print(f"已保存: output/idx1_rle_decode.png (RLE解码)")

if __name__ == '__main__':
    test_4ec66_decoding()
