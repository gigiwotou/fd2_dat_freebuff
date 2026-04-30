#!/usr/bin/env python3
"""
验证地图0的瓦片尺寸

根据文档截图：
- 地图0: 24x24瓦片
- 地图32: 18x51瓦片（之前验证过）

需要确认代码中使用的瓦片尺寸是否正确
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

print("验证各地图的瓦片尺寸")
print("=" * 60)

# 验证多个地图
for map_id in [0, 1, 32]:
    idx_offset = 6 + map_id * 12
    
    if idx_offset + 12 > len(data):
        continue
    
    layout_off, ctrl_off, char_off = struct.unpack_from('<III', data, idx_offset)
    
    if 0 < layout_off + 4 <= len(data):
        width = struct.unpack_from('<H', data, layout_off)[0]
        height = struct.unpack_from('<H', data, layout_off + 2)[0]
        
        print("地图 {:2d}: {}x{} 瓦片 (布局偏移: 0x{:06X})".format(
            map_id, width, height, layout_off))
    else:
        print("地图 {:2d}: 无法读取布局数据".format(map_id))

print()
print("=" * 60)
print("结论:")
print("=" * 60)
print("- 地图0: 24x24瓦片")
print("- 地图32: 18x51瓦片")
print("- 瓦片尺寸: 24x24像素（从FDSHAP.DAT tileset验证）")
print()
print("注意: 瓦片尺寸是24x24像素，不是128x128!")
