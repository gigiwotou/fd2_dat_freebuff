#!/usr/bin/env python3
"""
验证FDOTHER.DAT资源6和7的嵌套结构
检查是否有索引偏移问题（IDA的"资源7"对应Python的"资源6"）
"""

import struct
from pathlib import Path

DAT_MAGIC = b"LLLLLL"
GAME_DIR = Path("game")

def check_resource(data, name):
    """检查一个资源是否是嵌套DAT"""
    print(f"\n{'='*60}")
    print(f"检查 {name}")
    print(f"{'='*60}")
    print(f"前16字节(hex): {data[:16].hex()}")
    print(f"前6字节: {data[:6]}")
    
    if data[:6] == DAT_MAGIC:
        count = struct.unpack_from("<I", data, 6)[0]
        print(f"[OK] 是嵌套DAT! 资源数: {count}")
        
        offsets = []
        for i in range(count):
            off = 10 + i * 4
            if off + 4 > len(data):
                break
            offsets.append(struct.unpack_from("<I", data, off)[0])
        
        print(f"\n前20个子资源:")
        for i in range(min(20, len(offsets))):
            start = offsets[i]
            end = offsets[i+1] if i+1 < len(offsets) else len(data)
            size = end - start
            header = data[start:start+4].hex() if start < len(data) else ""
            print(f"  [{i:3}] 偏移={start:8}, 大小={size:8}, 头={header}")
        
        if count > 20:
            print(f"  ... 还有 {count-20} 个子资源")
            # 打印最后几个
            for i in range(max(20, count-5), count):
                if i < len(offsets):
                    start = offsets[i]
                    end = offsets[i+1] if i+1 < len(offsets) else len(data)
                    size = end - start
                    print(f"  [{i:3}] 偏移={start:8}, 大小={size:8}")
        
        return True, count, offsets
    else:
        print(f"✗ 不是嵌套DAT")
        return False, 0, []

def main():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    data = fdother_path.read_bytes()
    
    # 读取FDOTHER.DAT偏移表
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: {res_count} 资源\n")
    
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 获取资源6和7
    for idx in [6, 7]:
        start = offsets[idx]
        end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
        res_data = data[start:end]
        print(f"资源{idx}: 偏移={start}, 大小={end-start}")
        
        is_nested, count, inner_offsets = check_resource(res_data, f"资源{idx}")
        
        if is_nested:
            print(f"\n{'='*60}")
            print(f"资源{idx}包含 {count} 个子资源")
            print(f"{'='*60}")
            
            # 提取前7个子资源为PNG（使用资源7的调色板）
            res7_start = offsets[7]
            res7_end = offsets[8] if 8 < len(offsets) else len(data)
            palette_data = data[res7_start:res7_end]
            
            if len(palette_data) == 768:
                pal_8bit = bytearray(768)
                for i in range(256):
                    for c in range(3):
                        v6 = palette_data[i*3+c] & 0x3F
                        pal_8bit[i*3+c] = (v6 << 2) | (v6 >> 4)
                
                print(f"\n使用资源7调色板提取资源{idx}的前7个子资源:")
                for i in range(min(7, count)):
                    sub_start = inner_offsets[i]
                    sub_end = inner_offsets[i+1] if i+1 < len(inner_offsets) else len(res_data)
                    sub_data = res_data[sub_start:sub_end]
                    
                    if len(sub_data) >= 4:
                        w, h = struct.unpack_from("<HH", sub_data, 0)
                        if 0 < w <= 320 and 0 < h <= 200:
                            print(f"  [{i}] {w}x{h}, 大小={len(sub_data)}")
                            
                            # 保存为bin
                            out_dir = Path("output/menu_verify")
                            out_dir.mkdir(parents=True, exist_ok=True)
                            bin_path = out_dir / f"res{idx}_sub{i}_{w}x{h}.bin"
                            bin_path.write_bytes(sub_data)
                            
                            # 尝试解压RLE
                            compressed = sub_data[4:]
                            pixels = decompress_rle(compressed, w, h)
                            rgb = apply_palette(pixels, bytes(pal_8bit))
                            
                            try:
                                from PIL import Image
                                img = Image.frombytes('RGB', (w, h), rgb)
                                png_path = out_dir / f"res{idx}_sub{i}_{w}x{h}.png"
                                img.save(png_path)
                                print(f"    保存: {png_path}")
                            except Exception as e:
                                print(f"    PNG保存失败: {e}")
            else:
                print(f"  资源7不是768字节，无法使用调色板")
        
        print()

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
