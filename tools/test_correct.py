import struct
from pathlib import Path

data = Path("game/FDFIELD.DAT").read_bytes()

print("=== 正确的FDFIELD.DAT结构 ===")
print(f"Magic (0-6): {data[0:6]}")

count = struct.unpack_from('<I', data, 6)[0]
print(f"Resource count (offset 6): {count}")

# 测试：从偏移10开始，每4字节一个偏移值
print(f"\n=== 从偏移10开始读取偏移表 ===")
for i in range(min(15, count)):
    pos = 10 + i * 4
    if pos + 4 > len(data):
        break
    
    offset = struct.unpack_from('<I', data, pos)[0]
    
    # 计算大小（下一个偏移 - 当前偏移，或文件末尾）
    next_pos = 10 + (i + 1) * 4
    if next_pos + 4 <= len(data):
        next_offset = struct.unpack_from('<I', data, next_pos)[0]
        size = next_offset - offset
    else:
        size = len(data) - offset
    
    print(f"资源 {i}: offset={offset}, size={size}")
    
    if offset < len(data) and size >= 4:
        w, h = struct.unpack_from('<HH', data, offset)
        print(f"  前4字节: w={w}, h={h}")
