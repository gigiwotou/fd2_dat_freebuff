#!/usr/bin/env python3
"""查看嵌套DAT资源6的实际子资源"""
import struct
from pathlib import Path

data = Path("game/FDOTHER.DAT").read_bytes()
res_count = struct.unpack_from("<I", data, 6)[0]
offsets = [struct.unpack_from("<I", data, 10 + i*4)[0] for i in range(res_count)]

# 资源6是嵌套DAT
res6_start = offsets[6]
res6_end = offsets[7]
res6 = data[res6_start:res6_end]

print(f"资源6: 偏移={res6_start}, 大小={res6_end-res6_start}")
print(f"嵌套DAT头: {res6[:6]}")
inner_count = struct.unpack_from("<I", res6, 6)[0]
print(f"子资源数: {inner_count}")

inner_offsets = []
for i in range(inner_count):
    off = 10 + i * 4
    if off + 4 > len(res6):
        break
    inner_offsets.append(struct.unpack_from("<I", res6, off)[0])

print(f"\n所有 {inner_count} 个子资源:")
for i in range(inner_count):
    start = inner_offsets[i]
    end = inner_offsets[i+1] if i+1 < len(inner_offsets) else len(res6)
    size = end - start
    hdr = res6[start:start+6] if start < len(res6) else b""
    
    if size < 4:
        print(f"  [{i:3}] 偏移={start:8}, 大小={size:6} (太小)")
        continue
    
    w, h = struct.unpack_from("<HH", res6, start)
    rle_size = size - 4
    print(f"  [{i:3}] 偏移={start:8}, 大小={size:6}, {w}x{h}, RLE={rle_size}")

# 资源7是调色板
res7_start = offsets[7]
res7_end = offsets[8] if 8 < len(offsets) else len(data)
res7 = data[res7_start:res7_end]
print(f"\n资源7: 大小={len(res7)}")
if len(res7) == 768:
    print("  是768字节调色板")
