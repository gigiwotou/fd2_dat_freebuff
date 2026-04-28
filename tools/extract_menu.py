#!/usr/bin/env python3
"""
FD2 开始菜单资源提取和验证工具

分析并提取:
- FDOTHER.DAT 资源8（可能是嵌套菜单资源，3999字节，头"LMI1"）
- FDOTHER.DAT 资源1-6（菜单项按钮）
- FDOTHER.DAT 资源7（调色板，768字节）
- FDOTHER.DAT 资源101（菜单背景，768字节）
- TITLE.DAT 资源0-5（标题文字元素）
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
    """读取DAT文件偏移表，返回offsets列表"""
    if len(data) < 10 or data[:6] != DAT_MAGIC:
        return None
    count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    return offsets

def get_resource(data, offsets, idx):
    """获取指定索引的资源数据"""
    if idx >= len(offsets):
        return None
    start = offsets[idx]
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    return data[start:end]

def decompress_rle(data, width, height):
    """解压FD2 RLE数据"""
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
    """6位调色板转8位RGB"""
    palette_8bit = bytearray(768)
    for i in range(256):
        for c in range(3):
            v6 = palette_6bit[i * 3 + c] & 0x3F
            palette_8bit[i * 3 + c] = (v6 << 2) | (v6 >> 4)
    return bytes(palette_8bit)

def apply_palette(pixels, palette_8bit):
    """应用调色板到索引像素"""
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        rgb[i * 3 + 0] = palette_8bit[idx * 3 + 0]
        rgb[i * 3 + 1] = palette_8bit[idx * 3 + 1]
        rgb[i * 3 + 2] = palette_8bit[idx * 3 + 2]
    return bytes(rgb)

def save_png(path, width, height, rgb_pixels):
    """保存RGB像素为PNG"""
    img = Image.frombytes('RGB', (width, height), rgb_pixels)
    img.save(path)
    print(f"  保存: {path} ({width}x{height})")

def try_decompress_image(data, pal_8bit, name_prefix, output_dir):
    """尝试将数据作为RLE图像解压并保存"""
    if len(data) < 4:
        return False
    
    # 尝试常见尺寸
    for w, h in [(320, 200), (320, 147), (62, 8), (62, 7), (61, 7), (24, 24), (64, 64), (128, 128)]:
        compressed_size = w * h + 100  # 预估
        if len(data) >= 4 and len(data) < compressed_size * 2:
            # 尝试读取宽高头
            hdr_w, hdr_h = struct.unpack_from("<HH", data, 0)
            if hdr_w == w and hdr_h == h:
                pixels = decompress_rle(data[4:], w, h)
                rgb = apply_palette(pixels, pal_8bit)
                path = output_dir / f"{name_prefix}_{w}x{h}.png"
                save_png(path, w, h, rgb)
                return True
            
            # 尝试无头直接解压
            try:
                pixels = decompress_rle(data, w, h)
                # 检查是否有有效像素
                non_zero = sum(1 for p in pixels if p != 0)
                if non_zero > w * h * 0.1:  # 至少10%非零像素
                    rgb = apply_palette(pixels, pal_8bit)
                    path = output_dir / f"{name_prefix}_{w}x{h}.png"
                    save_png(path, w, h, rgb)
                    return True
            except:
                pass
    return False

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    title_path = GAME_DIR / "TITLE.DAT"
    
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return 1
    
    print("=" * 60)
    print("FD2 开始菜单资源提取验证工具")
    print("=" * 60)
    
    # 读取FDOTHER.DAT
    fdother_data = fdother_path.read_bytes()
    fdother_offsets = read_dat_offsets(fdother_data)
    if not fdother_offsets:
        print("FDOTHER.DAT 格式无效")
        return 1
    
    print(f"FDOTHER.DAT: {len(fdother_offsets)} 资源\n")
    
    # 获取调色板（资源7）
    res7 = get_resource(fdother_data, fdother_offsets, 7)
    print(f"资源7: {len(res7)} 字节")
    if len(res7) == 768:
        pal_8bit = palette_6bit_to_8bit(res7)
        print("  调色板已转换（6-bit -> 8-bit）")
    else:
        pal_8bit = bytes([i for i in range(256) for _ in range(3)])
        print("  使用默认灰度调色板")
    
    # 保存调色板
    pal_path = OUTPUT_DIR / "palette_7_8bit.bin"
    pal_path.write_bytes(pal_8bit)
    print(f"  调色板已保存: {pal_path}")
    
    # 提取资源1-6（菜单按钮项）
    print("\n资源1-6（菜单项按钮）:")
    for i in range(1, 7):
        res = get_resource(fdother_data, fdother_offsets, i)
        if res:
            print(f"  资源{i}: {len(res)} 字节, 头: {res[:8].hex()}")
            # 保存原始数据
            (OUTPUT_DIR / f"res{i}_menu_item_raw.bin").write_bytes(res)
            # 尝试解压为图像
            names = {
                1: "1p_unselected",
                2: "1p_selected",
                3: "vs_unselected",
                4: "vs_selected",
                5: "demo_unselected",
                6: "demo_selected"
            }
            try_decompress_image(res, pal_8bit, names[i], OUTPUT_DIR)
    
    # 提取资源8（可能的嵌套菜单资源）
    print("\n资源8（3999字节，可能是LMI1格式）:")
    res8 = get_resource(fdother_data, fdother_offsets, 8)
    if res8:
        print(f"  大小: {len(res8)} 字节")
        print(f"  头4字节: {res8[:4]} ({res8[:4].hex()})")
        (OUTPUT_DIR / "res8_menu_raw.bin").write_bytes(res8)
        
        if res8[:4] == b"LMI1":
            print("  格式: LMI1")
            # LMI1可能有特殊结构，尝试解析
            if len(res8) > 8:
                w, h = struct.unpack_from("<HH", res8, 4)
                print(f"  可能尺寸: {w}x{h}")
                # 尝试作为RLE图像
                try_decompress_image(res8[8:], pal_8bit, "res8_lmi1", OUTPUT_DIR)
    
    # 提取资源101（菜单背景）
    print("\n资源101（菜单背景）:")
    res101 = get_resource(fdother_data, fdother_offsets, 101)
    if res101:
        print(f"  大小: {len(res101)} 字节")
        (OUTPUT_DIR / "res101_menu_bg_raw.bin").write_bytes(res101)
        try_decompress_image(res101, pal_8bit, "res101_menu_bg", OUTPUT_DIR)
    
    # 提取TITLE.DAT资源0-5
    print("\nTITLE.DAT 资源0-5:")
    if title_path.exists():
        title_data = title_path.read_bytes()
        title_offsets = read_dat_offsets(title_data)
        if title_offsets:
            print(f"  TITLE.DAT: {len(title_offsets)} 资源")
            for i in range(min(6, len(title_offsets))):
                res = get_resource(title_data, title_offsets, i)
                if res:
                    print(f"  资源{i}: {len(res)} 字节, 头: {res[:4].hex()}")
                    (OUTPUT_DIR / f"title_res{i}_raw.bin").write_bytes(res)
                    # TITLE.DAT资源有宽高头
                    if len(res) >= 4:
                        w, h = struct.unpack_from("<HH", res, 0)
                        if 0 < w <= 100 and 0 < h <= 100:
                            print(f"    尺寸: {w}x{h}")
                            pixels = decompress_rle(res[4:], w, h)
                            rgb = apply_palette(pixels, pal_8bit)
                            path = OUTPUT_DIR / f"title_res{i}_{w}x{h}.png"
                            save_png(path, w, h, rgb)
    else:
        print("  TITLE.DAT 不存在")
    
    print("\n完成！输出目录:", OUTPUT_DIR)
    return 0

if __name__ == "__main__":
    sys.exit(main())
