#!/usr/bin/env python3
"""验证FDSHAP.DAT的资源偏移表结构"""
import struct

fdshap = open('game/FDSHAP.DAT', 'rb').read()

print('Testing FDSHAP.DAT resource offset table structure...')
print()

# 方法1: byte 6是计数，偏移从byte 10开始（旧假设）
count_v1 = struct.unpack_from('<I', fdshap, 6)[0]
print(f'Method 1 (count at byte 6):')
print(f'  Count: {count_v1}')
if count_v1 < 500:
    offsets_v1 = []
    for i in range(count_v1):
        off = struct.unpack_from('<I', fdshap, 10 + i*4)[0]
        offsets_v1.append(off)
    print(f'  First 3 offsets: {offsets_v1[:3]}')
    if len(offsets_v1) > 1:
        res0_size = offsets_v1[1] - offsets_v1[0]
        print(f'  Resource 0 size: {res0_size}')
else:
    print(f'  Count too large, probably wrong')

print()

# 方法2: 偏移直接从byte 6开始，没有计数（根据IDA代码）
print('Method 2 (offsets from byte 6, per IDA):')
offsets_v2 = []
for i in range(50):
    off = struct.unpack_from('<I', fdshap, 6 + i*4)[0]
    if off > 0 and off < len(fdshap):
        offsets_v2.append(off)
    else:
        break
print(f'  Valid offsets found: {len(offsets_v2)}')
if len(offsets_v2) > 2:
    print(f'  First 3 offsets: {offsets_v2[:3]}')
    res0_size = offsets_v2[1] - offsets_v2[0]
    print(f'  Resource 0 size (by difference): {res0_size}')
    res1_size = offsets_v2[2] - offsets_v2[1]
    print(f'  Resource 1 size (by difference): {res1_size}')
    
    # 验证资源0数据
    res0_data = fdshap[offsets_v2[0]:offsets_v2[1]]
    print(f'  Resource 0 actual size: {len(res0_data)}')
    print(f'  Resource 0 first 20 bytes: {res0_data[:20].hex(chr(32))}')
    
    # 验证资源1数据（瓦片集）
    res1_data = fdshap[offsets_v2[1]:offsets_v2[2]]
    print(f'  Resource 1 actual size: {len(res1_data)}')
    tile_w = struct.unpack_from('<H', res1_data, 0)[0]
    tile_h = struct.unpack_from('<H', res1_data, 2)[0]
    tile_count = struct.unpack_from('<H', res1_data, 4)[0]
    print(f'  Resource 1: tile {tile_w}x{tile_h}, count={tile_count}')
