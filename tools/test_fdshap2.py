import struct
from pathlib import Path

# 测试FDSHAP.DAT使用与FDFIELD相同的解析方式
data = Path("game/FDSHAP.DAT").read_bytes()

print("=== FDSHAP.DAT 分析 ===")
count = struct.unpack_from('<I', data, 6)[0]
print(f"资源数量: {count}")

print("\n=== 前20个资源 ===")
for i in range(min(20, count)):
    pos = 4 * i + 10
    offset = struct.unpack_from('<I', data, pos)[0]
    next_pos = 4 * (i + 1) + 10
    next_offset = struct.unpack_from('<I', data, next_pos)[0] if i + 1 < count else len(data)
    size = next_offset - offset
    
    print(f"\n资源 {i}: offset={offset}, size={size}")
    if size > 0 and size < 5000:
        # 尝试解析前几个字节
        first_bytes = data[offset:offset+min(20, size)]
        print(f"  前20字节: {first_bytes.hex()}")
        if size >= 4:
            val0, val1 = struct.unpack_from('<HH', data, offset)
            print(f"  前4字节 as HH: {val0}, {val1}")
