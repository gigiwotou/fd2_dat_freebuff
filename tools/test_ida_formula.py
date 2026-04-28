import struct
from pathlib import Path

data = Path("game/FDFIELD.DAT").read_bytes()

print("=== 按照IDA sub_111BA的实际行为分析 ===")
print(f"文件总大小: {len(data)} 字节")
print(f"前100字节(hex): {data[:100].hex()}")

# sub_111BA的索引计算: pos = 4*a7 + 6
# 从pos读取8字节: start, end
print("\n=== 测试前10个资源（按IDA公式 4*idx+6）===")

for idx in range(10):
    pos = 4 * idx + 6
    if pos + 8 > len(data):
        break
    
    start, end = struct.unpack_from("<II", data, pos)
    size = end - start
    
    print(f"\n资源 {idx} (pos={pos}):")
    print(f"  start={start}, end={end}, size={size}")
    
    if size > 0 and size < 10000 and start + size <= len(data):
        res_data = data[start:start+size]
        if size >= 4:
            w, h = struct.unpack_from("<HH", res_data, 0)
            print(f"  前4字节作为宽高: w={w}, h={h}")
            if 5 <= w <= 50 and 5 <= h <= 50:
                print(f"  *** 有效的地图尺寸! ***")
