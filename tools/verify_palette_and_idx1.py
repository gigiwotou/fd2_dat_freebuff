#!/usr/bin/env python3
"""分析索引0调色板是否正确"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def analyze_palette():
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
    
    # 索引0的数据（调色板）
    idx0_start = offsets[0]
    idx0_end = offsets[1] if len(offsets) > 1 else len(data)
    idx0_data = data[idx0_start:idx0_end]
    idx0_size = len(idx0_data)
    
    print(f"索引0大小: {idx0_size} 字节")
    
    if idx0_size == 768:
        print("大小=768，确认是调色板资源")
        print(f"\n前16个颜色 (RGB):")
        for i in range(min(16, 256)):
            r = idx0_data[i*3]
            g = idx0_data[i*3+1]
            b = idx0_data[i*3+2]
            print(f"  [{i:3d}] RGB({r:3d}, {g:3d}, {b:3d})")
        
        # 创建调色板预览图
        img = Image.new('RGB', (16, 16))
        for i in range(256):
            r = idx0_data[i*3]
            g = idx0_data[i*3+1]
            b = idx0_data[i*3+2]
            img.putpixel((i % 16, i // 16), (r, g, b))
        
        img.save('output/palette_0.png')
        print(f"\n调色板预览图已保存: output/palette_0.png")

def analyze_idx1_with_palette():
    """分析索引1图像与调色板的关系"""
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
    idx1_size = len(idx1_data)
    
    print(f"\n=== 索引1 分析 ===")
    print(f"大小: {idx1_size} 字节")
    print(f"前10字节: {' '.join(f'{b:02X}' for b in idx1_data[:10])}")
    
    # 解析为TILE
    if idx1_size >= 5:
        w = struct.unpack_from('<H', idx1_data, 0)[0]
        h = struct.unpack_from('<H', idx1_data, 2)[0]
        pw = idx1_data[4]
        print(f"如果是TILE: {w}x{h}, palette_window={pw}")
        
        # 检查是5字节头还是8字节头
        if idx1_size >= 8 and idx1_data[5] != 0:
            pw_16 = struct.unpack_from('<H', idx1_data, 4)[0]
            extra = struct.unpack_from('<H', idx1_data, 6)[0]
            rle_start = 8
            print(f"8字节头: palette_window={pw_16}, extra={extra}")
        else:
            rle_start = 5
            print(f"5字节头: palette_window={pw}")
        
        # RLE数据
        rle_data = idx1_data[rle_start:]
        rle_size = idx1_size - rle_start
        print(f"RLE数据大小: {rle_size} 字节")
        print(f"RLE前32字节: {' '.join(f'{b:02X}' for b in rle_data[:32])}")
        
        # 简单解码RLE（不使用调色板窗口）
        dst = bytearray(w * h)
        dst_idx = 0
        src_idx = 0
        
        while src_idx < rle_size and dst_idx < w * h:
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    val = rle_data[src_idx]
                    src_idx += 1
                    for _ in range(min(count, w*h - dst_idx)):
                        dst[dst_idx] = val
                        dst_idx += 1
                else:
                    # COPY_SPEC (间隔写入)
                    val = rle_data[src_idx]
                    src_idx += 1
                    for _ in range(count):
                        if dst_idx < w * h:
                            dst[dst_idx] = val
                            dst_idx += 2
            else:
                if bit6 == 0:
                    # COPY_STD
                    for _ in range(count):
                        if src_idx < rle_size and dst_idx < w * h:
                            dst[dst_idx] = rle_data[src_idx]
                            src_idx += 1
                            dst_idx += 1
                else:
                    # SKIP
                    dst_idx += count
        
        # 使用调色板渲染（尝试不同palette_window）
        for test_pw in [0, pw]:
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    idx = y * w + x
                    if idx < len(dst):
                        pal_idx = (test_pw + dst[idx]) & 0xFF
                        r = idx0_data[pal_idx * 3]
                        g = idx0_data[pal_idx * 3 + 1]
                        b = idx0_data[pal_idx * 3 + 2]
                        img.putpixel((x, y), (r, g, b))
            
            filename = f'output/idx1_pw{test_pw}.png'
            img.save(filename)
            print(f"已保存: {filename} (palette_window={test_pw})")

if __name__ == '__main__':
    analyze_palette()
    analyze_idx1_with_palette()
