import struct
from pathlib import Path

fdfield = Path("game/FDFIELD.DAT").read_bytes()
fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 地图0的控制数据在资源 3*0+1 = 1
# 但根据之前的分析，资源1大小937字节，前4字节不是宽高

# 让我重新检查：按照正确的FDFIELD解析
count_fd = struct.unpack_from('<I', fdfield, 6)[0]
print(f"FDFIELD resource count: {count_fd}")

# 使用4*i+10的方式
for i in range(3):
    pos = 4 * i + 10
    offset = struct.unpack_from('<I', fdfield, pos)[0]
    next_offset = struct.unpack_from('<I', fdfield, 4 * (i + 1) + 10)[0]
    size = next_offset - offset
    print(f"\n资源 {i}: offset={offset}, size={size}")
    if size >= 4:
        first_bytes = fdfield[offset:offset+20]
        print(f"  前20字节: {first_bytes.hex()}")
        val0, val1 = struct.unpack_from('<HH', fdfield, offset)
        print(f"  前4字节(HH): {val0}, {val1}")
        val2 = fdfield[offset]
        print(f"  第一字节: {val2} -> FDSHAP资源索引 = {2*val2}, {2*val2+1}")
