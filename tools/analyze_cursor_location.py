#!/usr/bin/env python3
"""分析FDOTHER.DAT的索引结构和光标位置"""

import struct
import sys
from pathlib import Path


def analyze_fdother(fdother_path: Path):
    """分析FDOTHER.DAT结构"""
    data = fdother_path.read_bytes()
    print(f"文件大小: {len(data)} 字节")

    print(f"\n前64字节:")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

    # 检查是否以LLLLLL开头
    if data[:6] == b'LLLLLL':
        print("\n检测到 'LLLLLL' 头部")
        print("这是嵌套DAT格式（前6字节魔数 + 4字节资源数 + 4字节偏移表）")

        resource_count = struct.unpack_from("<I", data, 6)[0]
        print(f"资源数量: {resource_count}")

        # 读取偏移表
        offsets = []
        for i in range(min(resource_count, 20)):
            offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
            offsets.append(offset)
        print(f"前20个偏移: {offsets}")

        return

    # 如果不是LLLLLL格式，检查sub_111BA的读取方式
    print("\n不是LLLLLL格式，检查索引结构...")
    print("sub_111BA(..., a7=0) 从偏移6读取8字节作为索引")

    if len(data) >= 14:
        val1 = struct.unpack_from("<I", data, 6)[0]
        val2 = struct.unpack_from("<I", data, 10)[0]
        print(f"偏移6处的DWORD: {val1} (0x{val1:04X})")
        print(f"偏移10处的DWORD: {val2} (0x{val2:04X})")
        print(f"数据大小: {val2 - val1} 字节")

        # 检查索引表位置（偏移6 + 8 = 14之后的结构）
        print(f"\n偏移14后的数据:")
        for i in range(14, min(60, len(data)), 16):
            hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
            print(f"  {i:04X}: {hex_str}")

        # 根据IDA: dword_53A81 + 526处存储的是光标偏移
        # 这意味着索引表从dword_53A81开始，光标偏移在526处
        # 526 / 8 = 65.75，说明526是某个资源条目的偏移

        print(f"\n--- 分析偏移526处的光标指针 ---")
        if len(data) >= 530:
            cursor_rel_offset = struct.unpack_from("<I", data, 526)[0]
            print(f"偏移526处的相对偏移: {cursor_rel_offset} (0x{cursor_rel_offset:04X})")

            if cursor_rel_offset > 0 and cursor_rel_offset < len(data):
                cursor_abs = cursor_rel_offset  # 如果是相对偏移则+14或其他值
                print(f"光标数据可能位置: 0x{cursor_abs:04X}")

                # 尝试读取光标图像头
                if cursor_abs + 4 <= len(data):
                    w = struct.unpack_from("<H", data, cursor_abs)[0]
                    h = struct.unpack_from("<H", data, cursor_abs + 2)[0]
                    print(f"光标尺寸: {w}x{h}")

                    # 打印光标数据前32字节
                    print(f"光标数据前32字节: {' '.join(f'{b:02X}' for b in data[cursor_abs:cursor_abs+32])}")

    # 分析索引表结构
    print("\n--- 分析索引表结构 ---")
    print("假设: 每个索引条目8字节 (起始4字节 + 结束4字节)")

    entry_size = 8
    num_entries = (len(data) - 6) // entry_size
    print(f"可能的索引条目数: {num_entries}")

    print(f"\n前20个索引条目:")
    for i in range(min(20, num_entries)):
        start = 6 + i * 8
        end = start + 8
        if end <= len(data):
            s = struct.unpack_from("<I", data, start)[0]
            e = struct.unpack_from("<I", data, start + 4)[0]
            size = e - s
            print(f"  索引{i}: 起始={s} (0x{s:04X}), 结束={e} (0x{e:04X}), 大小={size}")


def extract_cursor(fdother_path: Path, output_dir: Path):
    """提取光标数据"""
    data = fdother_path.read_bytes()

    # 假设偏移526处的DWORD是相对于数据起始（偏移6之后）的偏移
    cursor_rel = struct.unpack_from("<I", data, 526)[0]
    print(f"偏移526处的相对偏移: {cursor_rel} (0x{cursor_rel:04X})")

    # 计算光标绝对位置 - 需要确定基准点
    # 根据sub_111BA，数据加载从偏移6开始（跳过LLLLLL头）
    # 但dword_53A81指向的是整个文件数据

    # 如果526处的偏移是相对于文件起始的绝对偏移
    cursor_offset = cursor_rel

    if cursor_offset + 4 < len(data):
        w = struct.unpack_from("<H", data, cursor_offset)[0]
        h = struct.unpack_from("<H", data, cursor_offset + 2)[0]
        print(f"光标尺寸: {w}x{h}")

        if 0 < w <= 64 and 0 < h <= 64:
            rle_data = data[cursor_offset + 4:cursor_offset + 4 + w * h * 2]
            print(f"RLE数据长度: {len(rle_data)}")

            # 尝试解压
            try:
                from PIL import Image
                pixels = decompress_rle(rle_data, w, h)

                # 创建图像
                img = Image.new('RGBA', (w, h))
                rgba = []
                for px in pixels:
                    if px == 0:
                        rgba.append((0, 0, 0, 0))
                    else:
                        r = (px * 7) % 256
                        g = (px * 13) % 256
                        b = (px * 17) % 256
                        rgba.append((r, g, b, 255))
                img.putdata(rgba)
                img.save(output_dir / "cursor_526.png")
                print(f"保存: {output_dir / 'cursor_526.png'}")

                # 打印像素网格
                print(f"\n像素网格:")
                for row in range(min(h, 24)):
                    row_pixels = pixels[row*w:(row+1)*w]
                    print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels[:min(w, 32)])}")

            except Exception as e:
                print(f"解压失败: {e}")


def decompress_rle(data: bytes, width: int, height: int) -> bytes:
    """RLE解压"""
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


if __name__ == "__main__":
    fdother_path = Path(sys.argv[1] if len(sys.argv) > 1 else "game/FDOTHER.DAT")
    output_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "output")

    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        exit(1)

    print("=" * 60)
    print("FDOTHER.DAT 结构分析工具")
    print("=" * 60)
    print()

    analyze_fdother(fdother_path)
    print()
    extract_cursor(fdother_path, output_dir)
