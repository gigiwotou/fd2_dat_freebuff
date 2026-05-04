#!/usr/bin/env python3
"""
导出FDOTHER.DAT资源索引3中的地形UI图片
根据IDA sub_126F7汇编代码分析
"""

import struct
import os
from PIL import Image

def load_fdother_dat(filepath):
    """加载FDOTHER.DAT文件"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 验证魔数 LLLLLL
    if data[:6] != b'LLLLLL':
        raise ValueError("Invalid FDOTHER.DAT file")
    
    return data

def get_resource(data, index):
    """从DAT文件中提取指定索引的资源
    基于IDA sub_111BA逻辑:
    - fseek(fp, 4*index + 6, 0)
    - 读取8字节: offset(4), next_offset(4)
    """
    # 定位到偏移表位置: 4*index + 6
    table_pos = 4 * index + 6
    
    if table_pos + 8 > len(data):
        raise ValueError(f"Resource index {index} offset table out of range")
    
    offset, next_offset = struct.unpack_from('<II', data, table_pos)
    
    resource_size = next_offset - offset
    if offset >= len(data) or resource_size <= 0:
        raise ValueError(f"Invalid resource {index}: offset={offset}, next={next_offset}")
    
    return data[offset:offset + resource_size]

def decode_rle_terrain(src_data):
    """
    解码地形图像RLE数据
    基于IDA sub_4E22A
    图像尺寸: 24x24
    """
    dst = bytearray(24 * 24)
    src_ptr = 0
    dst_ptr = 0
    
    for row in range(24):
        bh = 24  # 每行剩余列数
        
        while bh > 0:
            if src_ptr >= len(src_data):
                break
                
            al = src_data[src_ptr]
            src_ptr += 1
            
            if al & 0x80:
                # bit 7 set
                if (al & 0x40) == 0:
                    # bit 6 = 0: copy mode (rep movsb)
                    count = (al >> 2) + 1
                    count = min(count, bh)
                    if src_ptr + count > len(src_data):
                        break
                    dst[dst_ptr:dst_ptr + count] = src_data[src_ptr:src_ptr + count]
                    src_ptr += count
                    dst_ptr += count
                    bh -= count
                else:
                    # bit 6 = 1: skip mode (dst += count)
                    count = (al >> 2) + 1
                    count = min(count, bh)
                    dst_ptr += count
                    bh -= count
            else:
                # bit 7 clear
                if (al & 0x40) == 0:
                    # bit 6 = 0: fill mode (rep stosb)
                    count = (al >> 2) + 1
                    count = min(count, bh)
                    if src_ptr >= len(src_data):
                        break
                    fill_color = src_data[src_ptr]
                    src_ptr += 1
                    dst[dst_ptr:dst_ptr + count] = bytes([fill_color] * count)
                    dst_ptr += count
                    bh -= count
                else:
                    # bit 6 = 1: interleave mode
                    # 4E262: sub bh, cl; 4E264: sub bh, cl -> bh -= 2*cl
                    count = (al >> 2) + 1
                    bh -= count
                    bh -= count
                    
                    if src_ptr >= len(src_data):
                        break
                    fill_color = src_data[src_ptr]
                    src_ptr += 1
                    # 4E267: inc edi; stosb; loop
                    # 每轮: dst++, *dst++=color -> 写入1字节，前进2字节
                    for _ in range(count):
                        dst_ptr += 1
                        if dst_ptr < len(dst):
                            dst[dst_ptr] = fill_color
                        dst_ptr += 1
        
        # 换行: dst += (stride - 24)，但这里是线性buffer，直接下一行起始位置
        dst_ptr = (row + 1) * 24
    
    return bytes(dst)

def parse_terrain_resource(resource_data):
    """
    解析资源索引3（地形UI图像集）
    基于IDA sub_126F7第12779-12783行:
    - edx = FDOTHER_DAT__3
    - edx += [edx + a7*4 + 6]
    格式：
    - 字节0-5: 头部
    - 偏移表从字节6开始: 每4字节一个地形ID的图像数据偏移（相对于resource_data起始位置）
    - 图像数据: RLE编码
    """
    # 解析偏移表，从字节6开始
    offset_table_start = 6
    
    # 读取所有偏移量直到遇到无效值
    offsets = []
    pos = offset_table_start
    
    while pos + 4 <= len(resource_data):
        offset = struct.unpack_from('<I', resource_data, pos)[0]
        # 偏移量应该指向resource_data内部的有效位置
        if offset < 6 or offset >= len(resource_data):
            break
        offsets.append(offset)
        pos += 4
    
    print(f"找到 {len(offsets)} 个地形图像偏移")
    if offsets:
        print(f"  前5个偏移: {offsets[:5]}")
        if len(offsets) >= 2:
            print(f"  间隔: {offsets[1] - offsets[0]} 字节")
    
    # 解码每个地形图像
    images = []
    for i, offset in enumerate(offsets):
        try:
            # 获取下一个偏移作为结束位置
            if i + 1 < len(offsets):
                end = offsets[i + 1]
            else:
                end = len(resource_data)
            
            rle_data = resource_data[offset:end]
            
            decoded = decode_rle_terrain(rle_data)
            img = Image.frombytes('P', (24, 24), decoded)
            images.append((i, img))
        except Exception as e:
            print(f"  地形ID {i} (offset={offset}) 解码失败: {e}")
    
    return images

def main():
    # FDOTHER.DAT路径
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'terrain_ui')
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"加载 {fdother_path}")
    data = load_fdother_dat(fdother_path)
    
    print("提取资源索引5（地形UI）")
    resource5 = get_resource(data, 5)
    print(f"资源大小: {len(resource5)} 字节")
    print(f"前32字节: {resource5[:32].hex()}")
    
    # 尝试分类资源类型
    # 检查是否是RLE图像
    if len(resource5) >= 4:
        w, h = struct.unpack_from('<HH', resource5, 0)
        print(f"可能的图像尺寸: {w}x{h}")
    
    print("解析地形图像")
    images = parse_terrain_resource(resource5)
    
    print(f"\n导出 {len(images)} 个地形UI图片到 {output_dir}")
    for terrain_id, img in images:
        output_path = os.path.join(output_dir, f"terrain_{terrain_id:04d}.png")
        img.save(output_path)
        print(f"  保存: {output_path}")
    
    print("\n完成!")

if __name__ == '__main__':
    main()
