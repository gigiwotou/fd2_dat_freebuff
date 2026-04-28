#!/usr/bin/env python3
"""
FD2 开始菜单资源提取验证工具 v3

根据用户说明：资源6有125个资源（从0开始），0是背景图，1-6是按钮
但工具解析发现只有6个有效子资源（61x7到62x8）

此工具将：
1. 提取资源6的6个有效子资源为PNG
2. 尝试查找包含125个子资源的嵌套DAT
3. 检查是否在其他DAT文件中
"""

import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("需要PIL库: pip install Pillow")
    exit(1)

GAME_DIR = Path("game")
OUTPUT_DIR = Path("output/menu_verify")
DAT_MAGIC = b"LLLLLL"

def read_dat_offsets(data):
    if len(data) < 10 or data[:6] != DAT_MAGIC:
        return None
    count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    return offsets

def decompress_rle(data, width, height):
    expected = width * height
    img = bytearray(expected)
    p = 0
    dst = 0
    
    for row in range(height):
        count = width
        while count > 0 and p < len(data):
            value = data[p]
            p += 1
            count_1 = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 and bit6:
                skip = min(count_1, count, expected - dst)
                dst += skip
                count -= skip
            elif bit7 and not bit6:
                for _ in range(count_1):
                    if count <= 0 or p >= len(data):
                        break
                    if dst < expected:
                        img[dst] = data[p]
                    p += 1
                    dst += 1
                    count -= 1
            elif not bit7 and bit6:
                if p < len(data):
                    fill = data[p]
                    p += 1
                    for _ in range(count_1):
                        if count <= 0:
                            break
                        if dst < expected:
                            img[dst] = fill
                        dst += 1
                        count -= 1
            else:
                if p < len(data):
                    fill = data[p]
                    p += 1
                    written = 0
                    while written < count_1 and count > 0:
                        if count >= 2:
                            if dst + 1 < expected:
                                img[dst + 1] = fill
                            dst += 2
                            count -= 2
                            written += 1
                        elif count == 1:
                            if dst < expected:
                                img[dst] = fill
                            dst += 1
                            count -= 1
                            written += 1
                        else:
                            break
    return bytes(img[:expected])

def palette_6bit_to_8bit(palette_6bit):
    palette_8bit = bytearray(768)
    for i in range(256):
        for c in range(3):
            v6 = palette_6bit[i * 3 + c] & 0x3F
            palette_8bit[i * 3 + c] = (v6 << 2) | (v6 >> 4)
    return bytes(palette_8bit)

def apply_palette(pixels, palette_8bit):
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        rgb[i*3+0] = palette_8bit[idx*3+0]
        rgb[i*3+1] = palette_8bit[idx*3+1]
        rgb[i*3+2] = palette_8bit[idx*3+2]
    return bytes(rgb)

def save_png(path, width, height, rgb_pixels):
    img = Image.frombytes('RGB', (width, height), rgb_pixels)
    img.save(path)
    print(f"  保存: {path} ({width}x{height})")

def find_all_nested_dat_with_count(min_count=50):
    """查找所有包含>=min_count个子资源的嵌套DAT"""
    print(f"\n查找包含>={min_count}个子资源的嵌套DAT:")
    
    dat_files = list(GAME_DIR.glob("*.DAT"))
    
    for dat_file in dat_files:
        data = dat_file.read_bytes()
        offsets = read_dat_offsets(data)
        if not offsets:
            continue
        
        print(f"\n{dat_file.name}: {len(offsets)} 顶级资源")
        
        for i in range(len(offsets)):
            s = offsets[i]
            e = offsets[i+1] if i+1 < len(offsets) else len(data)
            res_data = data[s:e]
            
            if res_data[:6] == DAT_MAGIC:
                nested_count = struct.unpack_from("<I", res_data, 6)[0]
                if nested_count >= min_count:
                    print(f"  资源{i}: 嵌套DAT, {nested_count} 个子资源, 大小={len(res_data)}")
                    
                    # 检查前7个子资源
                    nested_offsets = []
                    for j in range(min(7, nested_count)):
                        off_pos = 10 + j*4
                        if off_pos + 4 <= len(res_data):
                            nested_offsets.append(struct.unpack_from("<I", res_data, off_pos)[0])
                    
                    for j, off in enumerate(nested_offsets):
                        if off < len(res_data):
                            next_off = nested_offsets[j+1] if j+1 < len(nested_offsets) else len(res_data)
                            sz = next_off - off
                            header = res_data[off:off+4].hex()
                            print(f"    [{j}] 偏移={off}, 大小={sz}, 头={header}")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("FD2 菜单资源查找 v3")
    print("=" * 60)
    
    # 先查找包含>50个子资源的嵌套DAT
    find_all_nested_dat_with_count(50)
    
    # 也提取资源6的6个子资源
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        return 1
    
    fdother_data = fdother_path.read_bytes()
    fdother_offsets = read_dat_offsets(fdother_data)
    
    # 使用资源7作为调色板
    res7_start = fdother_offsets[7]
    res7_end = fdother_offsets[8] if 8 < len(fdother_offsets) else len(fdother_data)
    palette_data = fdother_data[res7_start:res7_end]
    pal_8bit = palette_6bit_to_8bit(palette_data)
    
    print(f"\n提取资源6的子资源:")
    res6_start = fdother_offsets[6]
    res6_end = fdother_offsets[7]
    res6_data = fdother_data[res6_start:res6_end]
    
    nested_offsets = read_dat_offsets(res6_data)
    if nested_offsets:
        for i in range(min(6, len(nested_offsets))):
            s = nested_offsets[i]
            e = nested_offsets[i+1] if i+1 < len(nested_offsets) else len(res6_data)
            sub_data = res6_data[s:e]
            
            if len(sub_data) >= 4:
                w, h = struct.unpack_from("<HH", sub_data, 0)
                if 0 < w <= 100 and 0 < h <= 100:
                    pixels = decompress_rle(sub_data[4:], w, h)
                    rgb = apply_palette(pixels, pal_8bit)
                    png_path = OUTPUT_DIR / f"res6_sub{i}_{w}x{h}.png"
                    save_png(png_path, w, h, rgb)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
