#!/usr/bin/env python3
"""验证FDSHAP资源1是否包含多个帧，每个帧有4字节header"""

import struct
from pathlib import Path

fdshap = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', fdshap, 6)[0]

# 获取资源1
pos = 4 * 1 + 10
offset = struct.unpack_from('<I', fdshap, pos)[0]
next_pos = 4 * 2 + 10
next_offset = struct.unpack_from('<I', fdshap, next_pos)[0]
size = next_offset - offset

print(f"资源1: offset={offset}, size={size}")

# 尝试解析多个帧，每个帧有4字节header (w, h) + RLE数据
pos = offset
frame_count = 0
frame_info = []

while pos < offset + size - 4:
    w, h = struct.unpack_from('<HH', fdshap, pos)
    print(f"Frame {frame_count} at pos={pos-offset}: w={w}, h={h}")
    
    if w == 0 or h == 0 or w > 100 or h > 100:
        print(f"  无效的帧尺寸，停止解析")
        break
    
    frame_pixels = w * h
    # RLE压缩数据大小大约是原始数据的1/3到1/2
    # 但我们不知道确切大小，所以需要找下一个帧的header
    
    # 尝试从当前位置+4开始找下一个有效的w,h
    found_next = False
    for search_pos in range(pos + 4, min(pos + 4 + frame_pixels * 2, offset + size - 4)):
        next_w, next_h = struct.unpack_from('<HH', fdshap, search_pos)
        if next_w > 0 and next_w <= 100 and next_h > 0 and next_h <= 100:
            # 可能是下一个帧
            print(f"  找到下一帧在偏移{search_pos-pos}: w={next_w}, h={next_h}")
            frame_size = search_pos - pos
            frame_info.append({
                'frame': frame_count,
                'offset': pos - offset,
                'size': frame_size,
                'w': w,
                'h': h
            })
            pos = search_pos
            frame_count += 1
            found_next = True
            break
    
    if not found_next:
        print(f"  未找到下一帧，这是最后一帧")
        frame_size = offset + size - pos
        frame_info.append({
            'frame': frame_count,
            'offset': pos - offset,
            'size': frame_size,
            'w': w,
            'h': h
        })
        break
    
    if frame_count > 20:
        print("超过20帧，停止")
        break

print(f"\n总共找到 {len(frame_info)} 帧")
for fi in frame_info[:10]:
    print(f"  Frame {fi['frame']}: offset={fi['offset']}, size={fi['size']}, dims={fi['w']}x{fi['h']}")
