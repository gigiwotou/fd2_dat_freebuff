#!/usr/bin/env python3
"""直接从FDOTHER.DAT索引1的0号子资源提取光标"""

import struct
import sys
from pathlib import Path


def read_ll_header(data: bytes):
    """读取LLLLLL格式的DAT头部"""
    if data[:6] != b'LLLLLL':
        return None
    resource_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from("<I", data, 10 + i * 4)[0]
        offsets.append(off)
    return {"count": resource_count, "offsets": offsets}


def get_resource(data: bytes, offsets: list, idx: int) -> bytes:
    """获取指定索引的资源数据"""
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
                # 11: skip
                skip = min(count_1, count, expected - dst)
                dst += skip
                count -= skip
            elif bit7 and not bit6:
                # 10: copy
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
                # 00: sparse fill
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


def apply_palette(pixels: bytes, palette_hint: int = 0) -> bytes:
    """应用调色板（简单的颜色映射）"""
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        # 简单的颜色映射
        if idx == 0:
            rgb[i * 3:i * 3 + 3] = [0, 0, 0]  # 黑色
        else:
            rgb[i * 3] = (idx * 7 + 50) % 256
            rgb[i * 3 + 1] = (idx * 13 + 30) % 256
            rgb[i * 3 + 2] = (idx * 17 + 70) % 256
    return bytes(rgb)


def main():
    fdother_path = Path("game/FDOTHER.DAT")
    output_dir = Path("output/cursor_index1_0")

    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    data = fdother_path.read_bytes()
    header = read_ll_header(data)

    if not header:
        print("错误: FDOTHER.DAT 不是有效的LLLLLL格式")
        return 1

    print(f"FDOTHER.DAT: {header['count']} 资源")
    offsets = header["offsets"]

    if len(offsets) <= 1:
        print("错误: 资源不足")
        return 1

    # 获取索引1的资源
    res1 = get_resource(data, offsets, 1)
    print(f"\n资源1大小: {len(res1)} 字节")
    print(f"资源1前32字节: {' '.join(f'{b:02X}' for b in res1[:32])}")

    # 检查资源1是否是嵌套的LLLLLL DAT
    res1_header = read_ll_header(res1)

    if res1_header:
        print(f"\n资源1是嵌套DAT，包含 {res1_header['count']} 个子资源")
        sub_offsets = res1_header["offsets"]

        # 提取子资源0（光标）
        if len(sub_offsets) > 0:
            sub0 = get_resource(res1, sub_offsets, 0)
            print(f"\n子资源0大小: {len(sub0)} 字节")
            print(f"子资源0前32字节: {' '.join(f'{b:02X}' for b in sub0[:32])}")

            if len(sub0) >= 4:
                w = struct.unpack_from("<H", sub0, 0)[0]
                h = struct.unpack_from("<H", sub0, 2)[0]
                print(f"子资源0尺寸: {w}x{h}")

                if 0 < w <= 64 and 0 < h <= 64:
                    rle = sub0[4:]
                    print(f"RLE数据长度: {len(rle)}")

                    pixels = decompress_rle(rle, w, h)
                    print(f"解压后像素: {len(pixels)}")

                    rgb = apply_palette(pixels)
                    from PIL import Image
                    img = Image.frombytes('RGB', (w, h), rgb)
                    img.save(output_dir / f"cursor_index1_0_{w}x{h}.png")
                    print(f"保存: {output_dir / f'cursor_index1_0_{w}x{h}.png'}")

                    # 打印像素网格
                    print(f"\n像素网格 (每行前{w}像素):")
                    for row in range(min(h, 24)):
                        row_pixels = pixels[row*w:(row+1)*w]
                        print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
                else:
                    print(f"尺寸无效: {w}x{h}")
        else:
            print("子资源数量为0")
    else:
        print("\n资源1不是嵌套DAT，尝试直接作为图像解析")

        # 资源1可能直接就是图像数据
        if len(res1) >= 4:
            w = struct.unpack_from("<H", res1, 0)[0]
            h = struct.unpack_from("<H", res1, 2)[0]
            print(f"尝试作为图像: {w}x{h}")

            if 0 < w <= 64 and 0 < h <= 64:
                rle = res1[4:]
                pixels = decompress_rle(rle, w, h)
                rgb = apply_palette(pixels)
                from PIL import Image
                img = Image.frombytes('RGB', (w, h), rgb)
                img.save(output_dir / f"cursor_direct_{w}x{h}.png")
                print(f"保存: {output_dir / f'cursor_direct_{w}x{h}.png'}")
            else:
                print(f"尺寸{w}x{h}无效")

    print("\n完成!")
    return 0


if __name__ == "__main__":
    exit(main())
