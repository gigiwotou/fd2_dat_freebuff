#!/usr/bin/env python3
"""
FD2 开始菜单资源提取工具

提取 FDOTHER.DAT 资源7（嵌套DAT）中的菜单资源并保存为PNG：
  - 子资源0: 菜单背景图
  - 子资源1-2: 1P 未选中/选中
  - 子资源3-4: VS 未选中/选中
  - 子资源5-6: Demo 未选中/选中

同时提取资源8（调色板）用于着色。

用法:
    python extract_menu_resources.py --game game --output output/menu
"""

import argparse
import struct
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要PIL库 (pip install Pillow)")
    exit(1)

DAT_MAGIC = b"LLLLLL"
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 200


def read_dat_header(data: bytes):
    """Parse DAT file header, return None if not a valid DAT."""
    if len(data) < 10 or data[:6] != DAT_MAGIC:
        return None
    resource_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(resource_count):
        offset = 10 + i * 4
        if offset + 4 > len(data):
            break
        offsets.append(struct.unpack_from("<I", data, offset)[0])
    return {"resource_count": resource_count, "offsets": offsets}


def get_resource_data(data: bytes, offsets: list, idx: int) -> bytes:
    """Extract raw resource data by index."""
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
    return data[start:end]


def decompress_rle(data: bytes, width: int, height: int) -> bytes:
    """
    Decompress FD2 RLE data (IDA sub_4E98D).
    Returns pixel index buffer (width * height bytes).
    """
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
                # 11: skip (transparent)
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
                # 00: sparse fill - write at positions 1, 3, 5, ...
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


def palette_6bit_to_8bit(palette_6bit: bytes) -> bytes:
    """Convert 6-bit VGA palette to 8-bit RGB."""
    palette_8bit = bytearray(768)
    for i in range(256):
        for c in range(3):
            v6 = palette_6bit[i * 3 + c] & 0x3F
            palette_8bit[i * 3 + c] = (v6 << 2) | (v6 >> 4)
    return bytes(palette_8bit)


def apply_palette(pixels: bytes, palette_8bit: bytes) -> bytes:
    """Apply palette to indexed pixels, return RGB data."""
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        rgb[i * 3 + 0] = palette_8bit[idx * 3 + 0]
        rgb[i * 3 + 1] = palette_8bit[idx * 3 + 1]
        rgb[i * 3 + 2] = palette_8bit[idx * 3 + 2]
    return bytes(rgb)


def save_png(path: Path, width: int, height: int, rgb_pixels: bytes):
    """Save RGB pixels as PNG."""
    img = Image.frombytes('RGB', (width, height), rgb_pixels)
    img.save(path)
    print(f"  保存: {path} ({width}x{height})")


def extract_menu_resources(game_dir: Path, output_dir: Path):
    """Extract menu resources from FDOTHER.DAT."""
    fdother_path = game_dir / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    # Read FDOTHER.DAT
    data = fdother_path.read_bytes()
    header = read_dat_header(data)
    if not header:
        print("错误: FDOTHER.DAT 格式无效")
        return False

    offsets = header["offsets"]
    print(f"FDOTHER.DAT: {header['resource_count']} 资源")

    # Extract resource 7 (nested DAT containing menu images)
    if len(offsets) <= 7:
        print("错误: FDOTHER.DAT 资源不足")
        return False

    res7_data = get_resource_data(data, offsets, 7)
    print(f"资源7大小: {len(res7_data)} 字节")

    # Parse nested DAT
    nested_header = read_dat_header(res7_data)
    if not nested_header:
        print("错误: 资源7不是有效的嵌套DAT")
        return False

    nested_offsets = nested_header["offsets"]
    nested_count = nested_header["resource_count"]
    print(f"资源7内嵌资源数: {nested_count}")

    # Extract resource 8 (palette)
    if len(offsets) <= 8:
        print("错误: FDOTHER.DAT 没有资源8（调色板）")
        return False

    res8_data = get_resource_data(data, offsets, 8)
    print(f"资源8（调色板）大小: {len(res8_data)} 字节")

    if len(res8_data) == 768:
        palette_8bit = palette_6bit_to_8bit(res8_data)
        print("调色板: 6-bit -> 8-bit 转换完成")
    else:
        print(f"警告: 资源8大小不是768字节，使用灰度调色板")
        palette_8bit = bytes([i for i in range(256) for _ in range(3)])

    # Menu resource names
    menu_names = [
        "menu_background",      # 0
        "1p_unselected",        # 1
        "1p_selected",          # 2
        "vs_unselected",        # 3
        "vs_selected",          # 4
        "demo_unselected",      # 5
        "demo_selected",        # 6
    ]

    extracted = []

    for idx in range(min(len(menu_names), nested_count)):
        sub_res = get_resource_data(res7_data, nested_offsets, idx)
        print(f"\n子资源 {idx} ({menu_names[idx]}): {len(sub_res)} 字节")

        if len(sub_res) < 4:
            print(f"  跳过: 数据太小")
            continue

        # Try to read RLE header
        w, h = struct.unpack_from("<HH", sub_res, 0)
        if 0 < w <= 640 and 0 < h <= 480:
            print(f"  尺寸: {w}x{h}")
            compressed = sub_res[4:]
            pixels = decompress_rle(compressed, w, h)
            print(f"  解压后: {len(pixels)} 像素")

            # Apply palette and save as PNG
            rgb = apply_palette(pixels, palette_8bit)
            png_path = output_dir / f"{menu_names[idx]}_{w}x{h}.png"
            save_png(png_path, w, h, rgb)
            extracted.append({
                "index": idx,
                "name": menu_names[idx],
                "width": w,
                "height": h,
                "path": str(png_path),
            })
        else:
            # Try as raw/palette data
            print(f"  不是RLE图像 (头: {w}x{h})")
            if len(sub_res) == 768:
                print(f"  可能是调色板数据")
                # Save as palette reference
                pal_path = output_dir / f"{menu_names[idx]}_palette.bin"
                pal_path.write_bytes(sub_res)
                print(f"  保存原始调色板: {pal_path}")
            else:
                # Save raw
                raw_path = output_dir / f"{menu_names[idx]}_raw.bin"
                raw_path.write_bytes(sub_res)
                print(f"  保存原始数据: {raw_path}")

    # Also save the nested DAT for reference
    nested_dat_path = output_dir / "resource7_nested.dat"
    nested_dat_path.write_bytes(res7_data)
    print(f"\n嵌套DAT已保存: {nested_dat_path}")

    # Save palette for reference
    pal_ref_path = output_dir / "palette_8bit.bin"
    pal_ref_path.write_bytes(palette_8bit)
    print(f"调色板已保存: {pal_ref_path}")

    print(f"\n提取完成! 共 {len(extracted)} 个图像")
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract FD2 menu resources as PNG")
    parser.add_argument("--game", type=Path, default=Path("game"), help="Game directory")
    parser.add_argument("--output", type=Path, default=Path("output/menu"), help="Output directory")
    args = parser.parse_args()

    game_dir = args.game.resolve()
    output_dir = args.output.resolve()

    if not game_dir.exists():
        print(f"错误: 游戏目录不存在: {game_dir}")
        return 1

    print("=" * 50)
    print("FD2 开始菜单资源提取工具")
    print("=" * 50)
    print(f"游戏目录: {game_dir}")
    print(f"输出目录: {output_dir}")
    print()

    if extract_menu_resources(game_dir, output_dir):
        print("\n成功!")
        return 0
    else:
        print("\n失败!")
        return 1


if __name__ == "__main__":
    exit(main())
