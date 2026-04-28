#!/usr/bin/env python3
"""
FD2 开始菜单资源最终验证工具

根据IDA分析：
- sub_111BA(..., 7) 返回的是整个DAT文件加载后的资源7数据
- sub_16886(..., _FDOTHER.DAT__2, 0) 是从资源7中提取子资源0
- sub_1FF79中n2_1(1或2)作为索引从资源7中提取子资源

但FDOTHER[7]只有768字节，说明资源7可能不是嵌套DAT，
而是FDOTHER[8]才是菜单资源容器（3999字节，LMI1格式）。

此工具验证并提取正确的菜单资源。
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

def get_resource(data, offsets, idx):
    if idx >= len(offsets):
        return None
    start = offsets[idx]
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    return data[start:end]

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
        rgb[i * 3 + 0] = palette_8bit[idx * 3 + 0]
        rgb[i * 3 + 1] = palette_8bit[idx * 3 + 1]
        rgb[i * 3 + 2] = palette_8bit[idx * 3 + 2]
    return bytes(rgb)

def decompress_rle(data, width, height):
    """解压FD2 RLE数据（IDA sub_4E98D）"""
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

def save_png(path, width, height, rgb_pixels):
    img = Image.frombytes('RGB', (width, height), rgb_pixels)
    img.save(path)
    print(f"  保存: {path} ({width}x{height})")

def try_extract_rle_image(data, pal_8bit, name, output_dir, sizes=None):
    """尝试从数据中提取RLE图像"""
    if len(data) < 4:
        return False
    
    if sizes is None:
        sizes = [(320, 200), (320, 147), (160, 100), (128, 64), (64, 32), (32, 32), 
                 (61, 7), (62, 7), (61, 8), (62, 8), (24, 24)]
    
    for w, h in sizes:
        compressed = data[4:] if len(data) > 4 else data
        # 检查是否有宽高头
        if len(data) >= 4:
            hdr_w, hdr_h = struct.unpack_from("<HH", data, 0)
            if hdr_w == w and hdr_h == h:
                compressed = data[4:]
        
        try:
            pixels = decompress_rle(compressed, w, h)
            non_zero = sum(1 for p in pixels if p != 0)
            if non_zero > w * h * 0.05:
                rgb = apply_palette(pixels, pal_8bit)
                path = output_dir / f"{name}_{w}x{h}.png"
                save_png(path, w, h, rgb)
                return True
        except:
            pass
    return False

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return 1
    
    print("=" * 60)
    print("FD2 开始菜单资源最终验证")
    print("=" * 60)
    
    fdother_data = fdother_path.read_bytes()
    fdother_offsets = read_dat_offsets(fdother_data)
    if not fdother_offsets:
        print("FDOTHER.DAT 格式无效")
        return 1
    
    # 获取调色板（资源7）
    res7 = get_resource(fdother_data, fdother_offsets, 7)
    if res7 and len(res7) == 768:
        pal_8bit = palette_6bit_to_8bit(res7)
        print("调色板(资源7): 6-bit -> 8-bit 转换完成\n")
    else:
        pal_8bit = bytes([i for i in range(256) for _ in range(3)])
        print("警告: 使用默认调色板")
    
    pal_path = OUTPUT_DIR / "palette_7_8bit.bin"
    pal_path.write_bytes(pal_8bit)
    
    # 提取资源6子资源0-5（TITLE.DAT内容 - 1P/VS/Demo文字）
    print("=" * 60)
    print("资源6（嵌套DAT - TITLE.DAT内容）:")
    res6 = get_resource(fdother_data, fdother_offsets, 6)
    if res6:
        inner_offsets = read_dat_offsets(res6)
        if inner_offsets:
            print(f"  子资源数: {len(inner_offsets)}")
            for i in range(min(6, len(inner_offsets))):
                sub_res = get_resource(res6, inner_offsets, i)
                if sub_res:
                    print(f"  [{i}] {len(sub_res)} 字节, 头: {sub_res[:4].hex()}")
                    (OUTPUT_DIR / f"res6_sub{i}.bin").write_bytes(sub_res)
                    w, h = struct.unpack_from("<HH", sub_res, 0)
                    if 0 < w <= 100 and 0 < h <= 100:
                        pixels = decompress_rle(sub_res[4:], w, h)
                        rgb = apply_palette(pixels, pal_8bit)
                        path = OUTPUT_DIR / f"res6_sub{i}_{w}x{h}.png"
                        save_png(path, w, h, rgb)
    
    # 提取资源8（3999字节，可能是菜单背景/容器）
    print("\n" + "=" * 60)
    print("资源8（3999字节）:")
    res8 = get_resource(fdother_data, fdother_offsets, 8)
    if res8:
        print(f"  大小: {len(res8)} 字节")
        print(f"  头4字节: {res8[:4]}")
        (OUTPUT_DIR / "res8.bin").write_bytes(res8)
        
        # 尝试不同尺寸
        try_extract_rle_image(res8, pal_8bit, "res8", OUTPUT_DIR,
                             [(320, 200), (160, 100), (128, 64), (64, 32)])
    
    # 提取资源101
    print("\n" + "=" * 60)
    print("资源101:")
    res101 = get_resource(fdother_data, fdother_offsets, 101)
    if res101:
        print(f"  大小: {len(res101)} 字节")
        (OUTPUT_DIR / "res101.bin").write_bytes(res101)
        try_extract_rle_image(res101, pal_8bit, "res101", OUTPUT_DIR)
    
    # 提取资源74（标题画面）
    print("\n" + "=" * 60)
    print("资源74（标题画面）:")
    res74 = get_resource(fdother_data, fdother_offsets, 74)
    if res74:
        print(f"  大小: {len(res74)} 字节")
        (OUTPUT_DIR / "res74_title.bin").write_bytes(res74)
        try_extract_rle_image(res74, pal_8bit, "res74_title", OUTPUT_DIR)
    
    # 提取资源75（调色板）
    print("\n" + "=" * 60)
    print("资源75（调色板）:")
    res75 = get_resource(fdother_data, fdother_offsets, 75)
    if res75:
        print(f"  大小: {len(res75)} 字节")
        (OUTPUT_DIR / "res75_palette.bin").write_bytes(res75)
    
    print("\n完成！输出:", OUTPUT_DIR)
    return 0

if __name__ == "__main__":
    sys.exit(main())
