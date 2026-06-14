#!/usr/bin/env python3
"""分析 FDOTHER.DAT 资源8的实际内容"""
import struct
import os
import sys

filepath = "d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"

if not os.path.exists(filepath):
    print(f"文件不存在: {filepath}")
    sys.exit(1)

with open(filepath, "rb") as f:
    data = f.read()

print(f"文件大小: {len(data)} 字节")
print(f"魔数: {data[0:6]}")

# 解析索引表 (从偏移6开始，每项4字节)
magic = data[0:6]
if magic != b"LLLLLL":
    print(f"魔数错误: {magic}")
    sys.exit(1)

# 解析所有资源
offsets = []
off = 6
while off + 4 <= len(data):
    val = struct.unpack_from("<I", data, off)[0]
    if val == 0 or val > len(data):
        break
    offsets.append(val)
    off += 4

print(f"资源数量: {len(offsets)}")
print(f"前10个资源偏移: {offsets[:10]}")

# 添加文件结束位置
all_offsets = offsets + [len(data)]

# 分析资源8
idx = 8
start = all_offsets[idx]
end = all_offsets[idx + 1]
res_data = data[start:end]
print(f"\n=== 资源{idx} ===")
print(f"偏移: 0x{start:04X} - 0x{end:04X}")
print(f"大小: {len(res_data)} 字节")
print(f"前32字节(hex): {res_data[:32].hex()}")
print(f"前32字节(raw): {res_data[:32]}")

# 检查调色板 (768字节)
print(f"\n=== 类型判断 ===")
print(f"大小 == 768? {len(res_data) == 768}")

# 检查LMI1头
print(f"前4字节 == 'LMI1'? {res_data[:4] == b'LMI1'}")

# 检查LLLLLL头
print(f"前6字节 == 'LLLLLL'? {res_data[:6] == b'LLLLLL'}")

# 检查是否是Tile
if len(res_data) >= 4:
    w, h = struct.unpack_from("<HH", res_data, 0)
    print(f"width={w}, height={h}")
    print(f"5字节头调色板窗口: {res_data[4] if len(res_data) > 4 else 'N/A'}")
    if w > 0 and w <= 640 and h > 0 and h <= 480:
        print(f"  -> 可能是TILE (4字节头w={w}, h={h})")
    if len(res_data) >= 5:
        # 5字节头 TILE 格式: w, h, window
        # 检查RLE大小: 4E 范围
        rle_size_calc = w * h
        print(f"  raw像素数据大小预期: {rle_size_calc} 字节")
        print(f"  实际数据大小减去5: {len(res_data) - 5}")
        if rle_size_calc + 5 == len(res_data):
            print(f"  -> 可能是raw像素 TILE: w={w}, h={h}, window={res_data[4]}")

# 与已知的调色板资源对比 - 资源0
print(f"\n=== 与资源0对比 ===")
res0_data = data[all_offsets[0]:all_offsets[1]]
print(f"资源0大小: {len(res0_data)} 字节 (期望768)")
print(f"资源0前16字节: {res0_data[:16].hex()}")
print(f"资源8前16字节: {res_data[:16].hex()}")
print(f"资源0 == 资源8? {res0_data == res_data}")

# 与57/76/99/101/102对比
for other_idx in [57, 76, 99, 101, 102]:
    if other_idx < len(offsets):
        other_data = data[all_offsets[other_idx]:all_offsets[other_idx+1]]
        print(f"资源{other_idx}大小: {len(other_data)}, == 资源8? {other_data == res_data}")
        print(f"  前16字节: {other_data[:16].hex()}")

# 如果大小是768, 打印所有颜色
print(f"\n=== 调色板分析 ===")
if len(res_data) == 768:
    print("是调色板! 打印所有颜色:")
    for i in range(256):
        r, g, b = res_data[i*3], res_data[i*3+1], res_data[i*3+2]
        # 6位颜色值
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        if i < 16 or i > 240:
            print(f"  [{i:3d}] RGB6=({r:2d},{g:2d},{b:2d}) RGB8=({r8:3d},{g8:3d},{b8:3d}) #{r8:02X}{g8:02X}{b8:02X}")

# 统计: 全部为0? 部分是0?
print(f"\n=== 数据统计 ===")
zero_count = sum(1 for b in res_data if b == 0)
print(f"0字节数: {zero_count} / {len(res_data)} ({100*zero_count/len(res_data):.1f}%)")

# 唯一字节数
unique_bytes = set(res_data)
print(f"唯一字节数: {len(unique_bytes)}")
print(f"唯一字节: {sorted(unique_bytes)[:32]}")
