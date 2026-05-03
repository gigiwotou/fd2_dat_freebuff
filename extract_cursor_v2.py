#!/usr/bin/env python3
"""解析FDOTHER.DAT资源1的内部结构（每8字节一个索引条目）"""

import struct
import sys
from pathlib import Path


def analyze_resource1(data: bytes):
    """分析资源1的内部结构"""
    print(f"资源1大小: {len(data)} 字节")
    print(f"前64字节: {' '.join(f'{b:02X}' for b in data[:64])}")

    # 假设每8字节是一个条目（起始4字节 + 结束4字节）
    entry_size = 8
    num_entries = len(data) // entry_size
    print(f"\n假设每8字节一个条目，共有 {num_entries} 个条目")

    entries = []
    for i in range(min(num_entries, 50)):
        start_off = i * 8
        s = struct.unpack_from("<I", data, start_off)[0]
        e = struct.unpack_from("<I", data, start_off + 4)[0]
        size = e - s
        entries.append((s, e, size))
        if i < 20:
            print(f"  条目{i}: 起始={s} (0x{s:04X}), 结束={e} (0x{e:04X}), 大小={size}")

    return entries


def extract_sub_resource(data: bytes, idx: int) -> bytes:
    """提取指定索引的子资源"""
    entry_size = 8
    if idx * entry_size + 8 > len(data):
        return None

    s = struct.unpack_from("<I", data, idx * entry_size)[0]
    e = struct.unpack_from("<I", data, idx * entry_size + 4)[0]
    return data[s:e]


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


def apply_palette(pixels: bytes) -> bytes:
    """应用调色板"""
    rgb = bytearray(len(pixels) * 3)
    for i, idx in enumerate(pixels):
        if idx == 0:
            rgb[i * 3:i * 3 + 3] = [0, 0, 0]
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

    # 读取FDOTHER.DAT
    data = fdother_path.read_bytes()

    # 解析LLLLLL头部获取资源偏移表
    if data[:6] != b'LLLLLL':
        print("错误: FDOTHER.DAT 缺少LLLLLL头部")
        return 1

    resource_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from("<I", data, 10 + i * 4)[0]
        offsets.append(off)

    print(f"FDOTHER.DAT: {resource_count} 资源")

    # 获取资源1
    if len(offsets) <= 1:
        print("错误: 资源不足")
        return 1

    res1_start = offsets[1]
    res1_end = offsets[2] if len(offsets) > 2 else len(data)
    res1 = data[res1_start:res1_end]

    print(f"\n=== 资源1 (索引1) ===")
    entries = analyze_resource1(res1)

    # 提取子资源0
    print(f"\n=== 提取子资源0（光标）===")
    sub0 = extract_sub_resource(res1, 0)

    if sub0 is None:
        print("错误: 无法提取子资源0")
        return 1

    print(f"子资源0大小: {len(sub0)} 字节")
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

            # 打印像素网格
            print(f"\n像素网格:")
            for row in range(min(h, 24)):
                row_pixels = pixels[row*w:(row+1)*w]
                print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")

            # 保存图像
            rgb = apply_palette(pixels)
            from PIL import Image
            img = Image.frombytes('RGB', (w, h), rgb)
            img.save(output_dir / f"cursor_{w}x{h}.png")
            print(f"\n保存: {output_dir / f'cursor_{w}x{h}.png'}")
        else:
            print(f"尺寸 {w}x{h} 无效")

    # 尝试其他子资源
    print(f"\n=== 尝试提取前几个子资源 ===")
    for i in range(min(10, len(entries))):
        sub = extract_sub_resource(res1, i)
        if sub and len(sub) >= 4:
            w = struct.unpack_from("<H", sub, 0)[0]
            h = struct.unpack_from("<H", sub, 2)[0]
            print(f"子资源{i}: 大小={len(sub)}, 头={w}x{h}", end="")

            if 0 < w <= 64 and 0 < h <= 64 and len(sub) >= 4 + w * h:
                try:
                    rle = sub[4:]
                    pixels = decompress_rle(rle, w, h)
                    rgb = apply_palette(pixels)
                    from PIL import Image
                    img = Image.frombytes('RGB', (w, h), rgb)
                    img.save(output_dir / f"sub{i}_{w}x{h}.png")
                    print(f" -> 保存 {output_dir / f'sub{i}_{w}x{h}.png'}")
                except:
                    print()
            else:
                print()

    print("\n完成!")
    return 0


if __name__ == "__main__":
    exit(main())
