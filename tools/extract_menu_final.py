#!/usr/bin/env python3
"""
FD2 开始菜单资源完整提取工具

关键发现：
- 资源6 = 嵌套DAT，包含TITLE.DAT的内容（38子资源）
- 资源2 = LMI1格式（1P按钮选中/未选中）
- 资源4 = LMI1格式（VS按钮选中/未选中）  
- 资源5 = LMI1格式（Demo按钮选中/未选中）
- 资源7 = 调色板（768字节）
- 资源8 = LMI1格式（3999字节，可能是菜单背景/容器）

提取所有菜单相关资源为PNG进行验证
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
                # 11: skip
                skip = min(count_1, count, expected - dst)
                dst += skip
                count -= skip
            elif bit7 and not bit6:
                # 10: copy from source
                for _ in range(count_1):
                    if count <= 0 or p >= len(data):
                        break
                    if dst < expected:
                        img[dst] = data[p]
                    p += 1
                    dst += 1
                    count -= 1
            elif not bit7 and bit6:
                # 01: fill
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
                # 00: sparse fill (write at positions 1, 3, 5, ...)
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

def try_extract_rle_image(data, pal_8bit, name, output_dir):
    """尝试从数据中提取RLE图像"""
    if len(data) < 4:
        return False
    
    # 检查宽高头
    w, h = struct.unpack_from("<HH", data, 0)
    if 0 < w <= 640 and 0 < h <= 480:
        compressed = data[4:]
        pixels = decompress_rle(compressed, w, h)
        # 检查有效性
        non_zero = sum(1 for p in pixels if p != 0)
        if non_zero > w * h * 0.05:
            rgb = apply_palette(pixels, pal_8bit)
            path = output_dir / f"{name}_{w}x{h}.png"
            save_png(path, w, h, rgb)
            return True
    return False

def parse_lmi1(data, pal_8bit, name, output_dir):
    """解析LMI1格式资源"""
    if len(data) < 8 or data[:4] != b"LMI1":
        return False
    
    print(f"  LMI1格式，尝试解析...")
    
    # LMI1结构分析
    # 字节4-5: 未知
    # 字节6-7: 未知
    # 可能是: [LMI1][entry_count?][...][offsets][...]
    
    # 方法1: 尝试作为简单RLE（跳过LMI1头）
    for w, h in [(320, 200), (160, 100), (128, 64), (64, 32), (32, 32), (61, 7), (62, 8)]:
        try:
            pixels = decompress_rle(data[8:], w, h)
            non_zero = sum(1 for p in pixels if p != 0)
            if non_zero > w * h * 0.05:
                rgb = apply_palette(pixels, pal_8bit)
                path = output_dir / f"{name}_lmi1_{w}x{h}.png"
                save_png(path, w, h, rgb)
                return True
        except:
            pass
    
    # 方法2: LMI1可能包含多个图像偏移
    # 检查字节8-11是否有类似偏移表的结构
    if len(data) > 12:
        potential_offset_count = data[4]  # 可能是条目数
        print(f"  可能的条目数: {potential_offset_count}")
        
        # 尝试从字节8开始读取偏移表
        offset_table_start = 8
        for i in range(min(10, potential_offset_count)):
            off_pos = offset_table_start + i * 4
            if off_pos + 4 <= len(data):
                offset = struct.unpack_from("<I", data, off_pos)[0]
                if 0 < offset < len(data):
                    print(f"    偏移[{i}] = {offset}")
    
    return False

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return 1
    
    print("=" * 60)
    print("FD2 开始菜单资源完整提取")
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
    
    # 提取资源6（嵌套DAT，包含TITLE.DAT的内容）
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
                    # 尝试作为RLE图像解压
                    w, h = struct.unpack_from("<HH", sub_res, 0)
                    if 0 < w <= 100 and 0 < h <= 100:
                        pixels = decompress_rle(sub_res[4:], w, h)
                        rgb = apply_palette(pixels, pal_8bit)
                        path = OUTPUT_DIR / f"res6_sub{i}_{w}x{h}.png"
                        save_png(path, w, h, rgb)
                        print(f"    -> {w}x{h}")
    
    # 提取资源8（LMI1，可能是菜单背景）
    print("\n" + "=" * 60)
    print("资源8（LMI1 - 3999字节）:")
    res8 = get_resource(fdother_data, fdother_offsets, 8)
    if res8:
        (OUTPUT_DIR / "res8_lmi1.bin").write_bytes(res8)
        parse_lmi1(res8, pal_8bit, "res8_menu", OUTPUT_DIR)
    
    # 提取资源2（LMI1 - 5990字节）
    print("\n" + "=" * 60)
    print("资源2（LMI1 - 5990字节）:")
    res2 = get_resource(fdother_data, fdother_offsets, 2)
    if res2:
        (OUTPUT_DIR / "res2_lmi1.bin").write_bytes(res2)
        parse_lmi1(res2, pal_8bit, "res2_button", OUTPUT_DIR)
    
    # 提取资源4（LMI1 - 44181字节）
    print("\n" + "=" * 60)
    print("资源4（LMI1 - 44181字节）:")
    res4 = get_resource(fdother_data, fdother_offsets, 4)
    if res4:
        (OUTPUT_DIR / "res4_lmi1.bin").write_bytes(res4)
        parse_lmi1(res4, pal_8bit, "res4_button", OUTPUT_DIR)
    
    # 提取资源5（LMI1 - 33415字节）
    print("\n" + "=" * 60)
    print("资源5（LMI1 - 33415字节）:")
    res5 = get_resource(fdother_data, fdother_offsets, 5)
    if res5:
        (OUTPUT_DIR / "res5_lmi1.bin").write_bytes(res5)
        parse_lmi1(res5, pal_8bit, "res5_button", OUTPUT_DIR)
    
    # 提取资源101
    print("\n" + "=" * 60)
    print("资源101:")
    res101 = get_resource(fdother_data, fdother_offsets, 101)
    if res101:
        (OUTPUT_DIR / "res101.bin").write_bytes(res101)
        try_extract_rle_image(res101, pal_8bit, "res101", OUTPUT_DIR)
    
    print("\n完成！输出:", OUTPUT_DIR)
    return 0

if __name__ == "__main__":
    sys.exit(main())
