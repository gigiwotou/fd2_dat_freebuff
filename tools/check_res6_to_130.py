#!/usr/bin/env python3
"""
检查FDOTHER.DAT资源6-130（共125个资源）
用户说"索引6的嵌套资源有125个资源，0是背景，1-6是按钮"
可能是指从索引6开始的125个连续资源
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")

def main():
    data = (GAME_DIR / "FDOTHER.DAT").read_bytes()
    res_count = struct.unpack_from("<I", data, 6)[0]
    
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    print("FDOTHER.DAT 资源6-130（共125个资源）:")
    print(f"{'索引':>4} {'偏移':>10} {'大小':>10} {'头8字节'} {'说明'}")
    print("-" * 80)
    
    # 获取调色板
    res7_start = offsets[7]
    res7_end = offsets[8] if 8 < len(offsets) else len(data)
    palette_data = data[res7_start:res7_end]
    
    pal_8bit = bytearray(768)
    for i in range(256):
        for c in range(3):
            v6 = palette_data[i*3+c] & 0x3F
            pal_8bit[i*3+c] = (v6 << 2) | (v6 >> 4)
    
    out_dir = Path("output/menu_verify")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(6, min(131, res_count)):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        sz = e - s
        header = data[s:s+8].hex() if s < len(data) else ""
        
        # 判断是否是嵌套DAT
        is_nested = ""
        if data[s:s+6] == b"LLLLLL":
            nested_count = struct.unpack_from("<I", data, s+6)[0]
            is_nested = f"[嵌套DAT:{nested_count}]"
        
        # 判断是否是RLE图像
        is_rle = ""
        if sz > 4 and sz < 100000:
            w, h = struct.unpack_from("<HH", data, s)
            if 0 < w <= 320 and 0 < h <= 200:
                is_rle = f"[RLE:{w}x{h}]"
                # 尝试解压并保存为PNG
                try:
                    compressed = data[s+4:e]
                    pixels = decompress_rle(compressed, w, h)
                    rgb = apply_palette(pixels, bytes(pal_8bit))
                    from PIL import Image
                    img = Image.frombytes('RGB', (w, h), rgb)
                    png_path = out_dir / f"res{i}_{w}x{h}.png"
                    img.save(png_path)
                    is_rle += f"->PNG"
                except:
                    pass
        
        print(f"{i:4} {s:10} {sz:10} {header} {is_nested}{is_rle}")

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

def apply_palette(pixels, palette_8bit):
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        rgb[i*3+0] = palette_8bit[idx*3+0]
        rgb[i*3+1] = palette_8bit[idx*3+1]
        rgb[i*3+2] = palette_8bit[idx*3+2]
    return bytes(rgb)

if __name__ == "__main__":
    main()
