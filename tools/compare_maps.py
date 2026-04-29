#!/usr/bin/env python3
"""对比原始工具和新工具生成的地图差异"""
from PIL import Image
import json

orig = Image.open('output/maps/map_0_final.png')
ida = Image.open('output/map_0_ida_verified.png')

# 找出哪些位置不同
diff_positions = []
for y in range(orig.height):
    for x in range(orig.width):
        if orig.getpixel((x,y)) != ida.getpixel((x,y)):
            diff_positions.append((x,y))

# 分析差异瓦片
tile_w = 24
tile_h = 24
map_w = 24
diff_tiles = set()
for x,y in diff_positions:
    tile_x = x // tile_w
    tile_y = y // tile_h
    diff_tiles.add((tile_x, tile_y))

print(f'总差异像素: {len(diff_positions)}')
print(f'差异瓦片数: {len(diff_tiles)}/{map_w*24}')

# 检查这些瓦片的地形ID
layout = json.load(open('output/maps/map_0_layout.json'))
tids = layout['terrain_ids']
print('\n差异瓦片的地形ID:')
for tx, ty in sorted(list(diff_tiles))[:20]:
    tid = tids[ty][tx]
    status = 'out_of_range' if tid >= 192 else 'in_range'
    print(f'  ({tx},{ty}): tid={tid} [{status}]')
