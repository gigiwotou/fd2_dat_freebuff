"""
分析 FDOTHER.DAT 索引2的原始数据
1. 解析 422 个索引表获取索引2的偏移和大小
2. 转储索引2的全部数据
3. 分析索引2的子结构
"""
import struct
import os

FDOTHER_PATH = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"

with open(FDOTHER_PATH, "rb") as f:
    data = f.read()

# 解析主索引表
assert data[:6] == b"LLLLLL"
offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack_from("<I", data, pos)[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4

print(f"Total resources: {len(offsets)}")
print(f"Index 2 offset: 0x{offsets[2]:08X}")
end = offsets[3] if len(offsets) > 3 else len(data)
print(f"Index 2 size: {end - offsets[2]} bytes")

idx2_data = data[offsets[2]:end]
print(f"\nIndex 2 头 64 字节:")
for i in range(0, 64, 16):
    hex_bytes = " ".join(f"{b:02X}" for b in idx2_data[i:i+16])
    print(f"  {i:04X}: {hex_bytes}")

# 假设索引2是偏移表结构
# 检查前 4 字节作为可能宽度
w = struct.unpack_from("<H", idx2_data, 0)[0]
h = struct.unpack_from("<H", idx2_data, 2)[0]
print(f"\nIf 4字节头: w={w}, h={h}")

# 假设是78个dword偏移表 (312字节)
print(f"\n假设78个dword偏移表 (312字节):")
print(f"  - 起始 78个偏移: ")
for i in range(min(10, 78)):
    off = struct.unpack_from("<I", idx2_data, i*4)[0]
    print(f"    [{i}] = 0x{off:08X} ({off})")

# 子资源0: 312 -> offsets[1] - 312
sub0_off = struct.unpack_from("<I", idx2_data, 0)[0]
sub1_off = struct.unpack_from("<I", idx2_data, 4)[0]
print(f"\n子资源 0: 起始 {sub0_off} (0x{sub0_off:X})")
print(f"  头 32 字节: " + " ".join(f"{b:02X}" for b in idx2_data[sub0_off:sub0_off+32]))
print(f"子资源 1: 起始 {sub1_off} (0x{sub1_off:X}), 大小 {sub1_off - sub0_off}")
print(f"  头 32 字节: " + " ".join(f"{b:02X}" for b in idx2_data[sub1_off:sub1_off+32]))
