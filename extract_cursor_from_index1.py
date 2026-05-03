#!/usr/bin/env python3
"""提取FDOTHER.DAT索引1中的0号子资源（光标）"""

import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要PIL库 (pip install Pillow)")
    exit(1)


def read_dat_header(data: bytes):
    """Parse DAT file header"""
    if len(data) < 10 or data[:6] != b"LLLLLL":
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
    """Extract raw resource data by index"""
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
    return data[start:end]


def decompress_rle(data: bytes, width: int, height: int) -> bytes:
    """RLE解压（IDA sub_4E98D）"""
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


def apply_palette(pixels: bytes) -> bytes:
    """应用默认调色板"""
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        if idx < 10:
            r = (idx * 25) % 256
            g = (idx * 50) % 256
            b = (idx * 75) % 256
        elif idx < 20:
            r = (idx * 30 + 50) % 256
            g = (idx * 40 + 30) % 256
            b = (idx * 60 + 70) % 256
        else:
            r = (idx * 7) % 256
            g = (idx * 13) % 256
            b = (idx * 17) % 256
        rgb[i * 3 + 0] = r
        rgb[i * 3 + 1] = g
        rgb[i * 3 + 2] = b
    return bytes(rgb)


def extract_cursor_from_fdother(game_dir: Path, output_dir: Path):
    """从FDOTHER.DAT索引1提取0号子资源作为光标"""
    fdother_path = game_dir / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    data = fdother_path.read_bytes()
    header = read_dat_header(data)

    if not header:
        print("错误: FDOTHER.DAT 格式无效 (缺少LLLLLL头)")
        return False

    offsets = header["offsets"]
    print(f"FDOTHER.DAT: {header['resource_count']} 资源")
    print(f"资源偏移表: {offsets[:10]}...")

    if len(offsets) <= 1:
        print("错误: FDOTHER.DAT 资源不足（需要索引1）")
        return False

    res1_data = get_resource_data(data, offsets, 1)
    print(f"\n资源1大小: {len(res1_data)} 字节")
    print(f"资源1前32字节: {' '.join(f'{b:02X}' for b in res1_data[:32])}")

    nested_header = read_dat_header(res1_data)
    if not nested_header:
        print("错误: 资源1不是嵌套DAT（可能光标数据直接在资源1位置）")

        if len(res1_data) >= 4:
            w, h = struct.unpack_from("<HH", res1_data, 0)
            print(f"\n尝试直接作为RLE图像: {w}x{h}")
            if 0 < w <= 256 and 0 < h <= 256:
                compressed = res1_data[4:]
                pixels = decompress_rle(compressed, w, h)
                rgb = apply_palette(pixels)
                img = Image.frombytes('RGB', (w, h), rgb)
                img.save(output_dir / f"cursor_direct_{w}x{h}.png")
                print(f"保存: output/cursor_direct_{w}x{h}.png")
        return False

    nested_offsets = nested_header["offsets"]
    nested_count = nested_header["resource_count"]
    print(f"\n资源1是嵌套DAT，包含 {nested_count} 个子资源")
    print(f"子资源偏移: {nested_offsets[:10]}...")

    for i in range(min(5, nested_count)):
        sub_res = get_resource_data(res1_data, nested_offsets, i)
        print(f"\n子资源{i}: {len(sub_res)} 字节")
        if len(sub_res) >= 4:
            w, h = struct.unpack_from("<HH", sub_res, 0)
            print(f"  头部: {w}x{h}")
            if 0 < w <= 256 and 0 < h <= 256:
                compressed = sub_res[4:]
                pixels = decompress_rle(compressed, w, h)
                rgb = apply_palette(pixels)
                img = Image.frombytes('RGB', (w, h), rgb)
                img.save(output_dir / f"cursor_sub{i}_{w}x{h}.png")
                print(f"  保存: output/cursor_sub{i}_{w}x{h}.png")

                print(f"  像素网格 (前{h}行，每行{w}像素):")
                for row in range(min(h, 24)):
                    row_pixels = pixels[row*w:(row+1)*w]
                    print(f"    {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels[:min(w,32)])}")

    print(f"\n完成!")
    return True


if __name__ == "__main__":
    game_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "game")
    output_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "output/cursor")

    print("=" * 50)
    print("FDOTHER.DAT 索引1 光标提取工具")
    print("=" * 50)
    print(f"游戏目录: {game_dir}")
    print(f"输出目录: {output_dir}")
    print()

    if not game_dir.exists():
        print(f"错误: 游戏目录不存在: {game_dir}")
        exit(1)

    extract_cursor_from_fdother(game_dir, output_dir)
