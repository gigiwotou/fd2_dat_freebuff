#!/usr/bin/env python3
"""
FD2 FDOTHER.DAT 资源列表和大小分析
输出所有资源的偏移和大小，用于分析菜单资源
"""

import struct
from pathlib import Path

DAT_MAGIC = b"LLLLLL"
GAME_DIR = Path("game")

def analyze_fdother():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return

    data = fdother_path.read_bytes()
    if data[:6] != DAT_MAGIC:
        print("错误: 不是有效的DAT文件")
        return

    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: {res_count} 资源\n")
    print(f"{'索引':>4} {'偏移':>10} {'大小':>10} {'说明'}")
    print("-" * 70)

    offsets = []
    for i in range(res_count):
        offset = 10 + i * 4
        offsets.append(struct.unpack_from("<I", data, offset)[0])

    res_info = {}
    for i in range(res_count):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < len(offsets) else len(data)
        size = end - start
        res_info[i] = (start, size)

        # Print key resources (0-15, 69-77, 99-102)
        if i <= 15 or (69 <= i <= 77) or i in (99, 100, 101, 102):
            desc = ""
            if i <= 6:
                desc = "UI元素"
            elif i == 7:
                desc = "调色板/菜单资源"
            elif i == 8:
                desc = "菜单资源"
            elif i == 9:
                desc = "菜单元素"
            elif 10 <= i <= 15:
                desc = "开场/UI"
            elif 69 <= i <= 73:
                desc = "动画帧"
            elif i == 74:
                desc = "标题画面"
            elif i == 75:
                desc = "调色板"
            elif i == 76:
                desc = "背景(原始)"
            elif i == 77:
                desc = "动画数据"
            elif i == 99:
                desc = "特效"
            elif i == 100:
                desc = "菜单覆盖层"
            elif i == 101:
                desc = "菜单背景"
            elif i == 102:
                desc = "菜单资源"

            print(f"{i:4} {start:10} {size:10} {desc}")

    # Check if resource 8 is a nested DAT
    print("\n" + "=" * 70)
    print("检查资源8（菜单资源）...")
    if 8 in res_info:
        start, size = res_info[8]
        res8_data = data[start:start+size]
        if res8_data[:6] == DAT_MAGIC:
            inner_count = struct.unpack_from("<I", res8_data, 6)[0]
            print(f"  资源8是嵌套DAT! 包含 {inner_count} 个子资源")
            inner_offsets = []
            for i in range(inner_count):
                inner_offsets.append(struct.unpack_from("<I", res8_data, 10 + i*4)[0])
            for i in range(inner_count):
                s = inner_offsets[i]
                e = inner_offsets[i+1] if i+1 < len(inner_offsets) else size
                sz = e - s
                desc = ""
                if i == 0: desc = "菜单背景"
                elif i == 1: desc = "1P未选中"
                elif i == 2: desc = "1P选中"
                elif i == 3: desc = "VS未选中"
                elif i == 4: desc = "VS选中"
                elif i == 5: desc = "Demo未选中"
                elif i == 6: desc = "Demo选中"
                print(f"  子资源 {i}: 偏移={s}, 大小={sz} {desc}")
        else:
            print(f"  资源8不是嵌套DAT (头: {res8_data[:4].hex()})")

    # Also check resource 7
    print("\n" + "=" * 70)
    print("检查资源7...")
    if 7 in res_info:
        start, size = res_info[7]
        res7_data = data[start:start+size]
        print(f"  大小: {size} 字节")
        if res7_data[:6] == DAT_MAGIC:
            inner_count = struct.unpack_from("<I", res7_data, 6)[0]
            print(f"  是嵌套DAT! 包含 {inner_count} 个子资源")
        else:
            print(f"  不是嵌套DAT")
            if size == 768:
                print(f"  可能是调色板 (768字节)")

    # Check resource 102
    print("\n" + "=" * 70)
    print("检查资源102...")
    if 102 in res_info:
        start, size = res_info[102]
        res102_data = data[start:start+min(size, 20)]
        print(f"  大小: {size} 字节")
        if data[start:start+6] == DAT_MAGIC:
            inner_count = struct.unpack_from("<I", data, start+6)[0]
            print(f"  是嵌套DAT! 包含 {inner_count} 个子资源")

if __name__ == "__main__":
    analyze_fdother()
