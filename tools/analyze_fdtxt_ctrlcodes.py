#!/usr/bin/env python3
"""
FDTXT.DAT 控制码分析工具
读取第一个资源集(索引0)的第一个子文本(索引0)
打印所有遇到的控制码(负值)及其原始int16值
"""

import struct
import os

CONTROL_CODES = {
    -1: "TEXT_END",
    -2: "TEXT_NEWLINE",
    -3: "TEXT_NEWLINE2",
    -4: "TEXT_RECURSE1",
    -5: "TEXT_RECURSE2",
    -6: "TEXT_SHOW_NUM",
    -17: "TEXT_PORTRAIT_F",
    -18: "TEXT_PORTRAIT_S",
    -19: "TEXT_CHAR_F",
    -20: "TEXT_CHAR_S",
}

def load_resource(dat_data, index):
    count = struct.unpack_from('<I', dat_data, 6)[0]
    if index < 0 or index >= count - 1:
        return None
    offset_start = struct.unpack_from('<I', dat_data, 10 + index * 4)[0]
    offset_end = struct.unpack_from('<I', dat_data, 10 + (index + 1) * 4)[0]
    return dat_data[offset_start:offset_end]

def analyze_control_codes(resource_data):
    if len(resource_data) < 2:
        print("资源数据太小")
        return

    sub_count = struct.unpack_from('<h', resource_data, 0)[0]
    print(f"资源集包含 {sub_count} 个子项\n")

    if sub_count < 1:
        print("没有子项可分析")
        return

    offset_0 = struct.unpack_from('<h', resource_data, 2)[0]
    offset_1 = struct.unpack_from('<h', resource_data, 4)[0] if sub_count > 1 else len(resource_data)

    sub_data = resource_data[offset_0:offset_1]
    print(f"子项0: 起始偏移={offset_0}, 结束偏移={offset_1}, 大小={len(sub_data)}字节\n")

    print("=" * 60)
    print(f"{'位置':>6} | {'原始值(int16)':>14} | {'十六进制':>6} | {'类型':>20}")
    print("=" * 60)

    control_code_count = {}

    for i in range(0, len(sub_data), 2):
        if i + 1 >= len(sub_data):
            break

        word = struct.unpack_from('<h', sub_data, i)[0]
        raw_u16 = word & 0xFFFF
        hex_str = f"0x{raw_u16:04X}"

        if word < 0:
            code_name = CONTROL_CODES.get(word, "UNKNOWN_CONTROL")
            control_code_count[word] = control_code_count.get(word, 0) + 1
            print(f"{i:6d} | {word:14d} | {hex_str:>6} | {code_name}")

            if word == -1:
                break
        else:
            try:
                char = word.to_bytes(2, 'little', signed=False).decode('big5')
                print(f"{i:6d} | {word:14d} | {hex_str:>6} | 字符: {char}")
            except:
                print(f"{i:6d} | {word:14d} | {hex_str:>6} | [不可解码]")

    print("=" * 60)
    print("\n控制码统计:")
    print("-" * 40)
    for code, count in sorted(control_code_count.items()):
        name = CONTROL_CODES.get(code, "UNKNOWN")
        print(f"  {name:20s} (值={code:4d}): {count}次")

def main():
    fdtxt_path = os.path.join("game", "FDTXT.DAT")

    if not os.path.exists(fdtxt_path):
        print(f"错误: 找不到 {fdtxt_path}")
        return

    with open(fdtxt_path, 'rb') as f:
        fdtxt_data = f.read()

    resource_count = struct.unpack_from('<I', fdtxt_data, 6)[0]
    print(f"FDTXT.DAT 总资源集数: {resource_count}\n")

    resource_data = load_resource(fdtxt_data, 0)
    if resource_data is None:
        print("无法加载资源集0")
        return

    print(f"资源集0大小: {len(resource_data)}字节\n")
    analyze_control_codes(resource_data)

if __name__ == "__main__":
    main()
