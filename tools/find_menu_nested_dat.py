#!/usr/bin/env python3
"""
查找FDOTHER.DAT中所有嵌套DAT结构
定位包含125个子资源的嵌套DAT（用户说这是菜单资源）
"""

import struct
from pathlib import Path

DAT_MAGIC = b"LLLLLL"
GAME_DIR = Path("game")

def find_all_nested_dat():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    data = fdother_path.read_bytes()
    
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: {res_count} 资源\n")
    
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    nested_resources = []
    
    for i in range(res_count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[start:end]
        
        if res_data[:6] == DAT_MAGIC:
            inner_count = struct.unpack_from("<I", res_data, 6)[0]
            
            # 验证偏移表是否合理
            valid = True
            if inner_count > 0 and inner_count < 500:  # 合理范围
                inner_offsets = []
                for j in range(inner_count):
                    off = 10 + j * 4
                    if off + 4 > len(res_data):
                        valid = False
                        break
                    inner_offsets.append(struct.unpack_from("<I", res_data, off)[0])
                
                # 检查偏移是否都在资源范围内
                for off in inner_offsets:
                    if off >= len(res_data):
                        valid = False
                        break
                
                if valid:
                    nested_resources.append((i, inner_count, inner_offsets, len(res_data)))
                    print(f"资源 {i:3}: 嵌套DAT, {inner_count:3} 个子资源, 总大小={len(res_data):8}")
    
    print(f"\n共找到 {len(nested_resources)} 个有效的嵌套DAT资源")
    
    # 详细检查包含>50个子资源的嵌套DAT
    for idx, count, inner_offsets, size in nested_resources:
        if count > 50:
            print(f"\n{'='*60}")
            print(f"资源 {idx} ({count} 个子资源, 大小 {size} 字节)")
            print(f"{'='*60}")
            print(f"前15个子资源:")
            for i in range(min(15, count)):
                s = inner_offsets[i]
                e = inner_offsets[i+1] if i+1 < count else size
                sz = e - s
                header = data[offsets[idx]+s:offsets[idx]+s+4].hex() if s < size else ""
                print(f"  [{i:3}] 偏移={s:8}, 大小={sz:8}, 头={header}")
            
            if count > 15:
                print(f"  ... (共{count}个)")
            
            # 尝试提取前7个为PNG（使用资源7调色板）
            res7_start = offsets[7]
            res7_end = offsets[8] if 8 < len(offsets) else len(data)
            palette_data = data[res7_start:res7_end]
            
            if len(palette_data) == 768:
                pal_8bit = bytearray(768)
                for p in range(256):
                    for c in range(3):
                        v6 = palette_data[p*3+c] & 0x3F
                        pal_8bit[p*3+c] = (v6 << 2) | (v6 >> 4)
                
                res_data = data[offsets[idx]:offsets[idx]+size]
                print(f"\n提取前7个子资源:")
                for i in range(min(7, count)):
                    s = inner_offsets[i]
                    e = inner_offsets[i+1] if i+1 < count else size
                    sub_data = res_data[s:e]
                    
                    if len(sub_data) >= 4:
                        w, h = struct.unpack_from("<HH", sub_data, 0)
                        if 0 < w <= 320 and 0 < h <= 200:
                            print(f"  [{i}] {w}x{h}, 大小={len(sub_data)}")
                            
                            out_dir = Path("output/menu_verify")
                            out_dir.mkdir(parents=True, exist_ok=True)
                            
                            compressed = sub_data[4:]
                            pixels = decompress_rle(compressed, w, h)
                            rgb = apply_palette(pixels, bytes(pal_8bit))
                            
                            try:
                                from PIL import Image
                                img = Image.frombytes('RGB', (w, h), rgb)
                                png_path = out_dir / f"res{idx}_sub{i}_{w}x{h}.png"
                                img.save(png_path)
                                print(f"    -> {png_path}")
                            except Exception as e:
                                print(f"    PNG失败: {e}")

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
    find_all_nested_dat()
