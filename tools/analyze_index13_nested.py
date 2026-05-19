#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引13的LMI1音频格式内部结构
字节4-5小端=32，可能是子资源数量
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")

def main():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return

    data = fdother_path.read_bytes()
    file_size = len(data)

    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])

    idx = 13
    start = offsets[idx]
    end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
    res_data = data[start:end]

    print(f"索引13: 偏移0x{start:X}, 大小{len(res_data)}字节\n")

    # 尝试: 字节4-5小端=32是子资源数量，从字节8开始是32个4字节小端偏移
    sub_count = struct.unpack_from("<H", res_data, 4)[0]
    print(f"假设: 字节4-5小端={sub_count}是子资源数量")
    print(f"从字节8开始解析{sub_count}个4字节小端偏移:\n")

    internal_offsets = []
    for i in range(sub_count):
        pos = 8 + i * 4
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from("<I", res_data, pos)[0]
        internal_offsets.append(val)
        status = "有效" if (val < len(res_data) and val > 0) else "无效"
        print(f"  [{i:>3}] @+{pos:03X}: 0x{val:08X} ({val}) [{status}]")

    print(f"\n有效偏移数: {sum(1 for v in internal_offsets if v < len(res_data) and v > 0)}")

    # 尝试: 字节8开始，每4字节大端序
    print(f"\n{'='*60}")
    print(f"从字节8开始的4字节大端序偏移 (前32个):")
    internal_offsets_be = []
    for i in range(32):
        pos = 8 + i * 4
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from(">I", res_data, pos)[0]
        internal_offsets_be.append(val)
        status = "有效" if (val < len(res_data) and val > 0) else "无效"
        print(f"  [{i:>3}] @+{pos:03X}: 0x{val:08X} ({val}) [{status}]")

    # 尝试: 字节8开始，每4字节，取低2字节作为偏移 (小端)
    print(f"\n{'='*60}")
    print(f"从字节8开始，每4字节取低2字节 (小端) 作为偏移:")
    for i in range(32):
        pos = 8 + i * 4
        if pos + 4 > len(res_data):
            break
        low2 = struct.unpack_from("<H", res_data, pos)[0]
        status = "有效" if (low2 < len(res_data) and low2 > 0) else "无效"
        print(f"  [{i:>3}] @+{pos:03X}: 0x{low2:04X} ({low2}) [{status}]")

    # 尝试: 字节8开始，每4字节，取高2字节作为偏移 (大端)
    print(f"\n{'='*60}")
    print(f"从字节8开始，每4字节取高2字节 (大端) 作为偏移:")
    for i in range(32):
        pos = 8 + i * 4
        if pos + 4 > len(res_data):
            break
        high2 = struct.unpack_from(">H", res_data, pos)[0]
        status = "有效" if (high2 < len(res_data) and high2 > 0) else "无效"
        print(f"  [{i:>3}] @+{pos:03X}: 0x{high2:04X} ({high2}) [{status}]")

    # 尝试: 每2字节直接作为偏移 (小端)
    print(f"\n{'='*60}")
    print(f"从字节8开始，每2字节小端作为偏移:")
    offsets_2byte = []
    for i in range(100):
        pos = 8 + i * 2
        if pos + 2 > len(res_data):
            break
        val = struct.unpack_from("<H", res_data, pos)[0]
        if val < len(res_data) and val > 0:
            offsets_2byte.append(val)
            if i < 32:
                print(f"  [{i:>3}] @+{pos:03X}: 0x{val:04X} ({val}) [有效]")

    print(f"\n共找到 {len(offsets_2byte)} 个有效2字节偏移")
    
    if len(offsets_2byte) > 5:
        # 排序并去重
        offsets_2byte_sorted = sorted(set(offsets_2byte))
        print(f"\n排序去重后 (前32个):")
        for j, off in enumerate(offsets_2byte_sorted[:32]):
            idx_in_sorted = offsets_2byte.index(off)
            print(f"  [{j:>3}] 0x{off:04X} ({off})  原始索引:{idx_in_sorted}")

if __name__ == "__main__":
    main()
