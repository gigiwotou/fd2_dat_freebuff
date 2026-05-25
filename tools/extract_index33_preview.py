# 提取索引33的tile图片并生成预览图
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother13_tiles_index33_preview")
os.makedirs(OUTPUT_DIR, exist_ok=True)

fdother_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")
with open(fdother_path, 'rb') as f:
    fdother_data = f.read()

index_count = struct.unpack_from('<I', fdother_data, 6)[0]
offsets_start = 10
sizes_start = 10 + index_count * 4

idx33_offset = struct.unpack_from('<I', fdother_data, offsets_start + 33 * 4)[0]
idx33_size = struct.unpack_from('<I', fdother_data, sizes_start + 33 * 4)[0]
res_data = fdother_data[idx33_offset:idx33_offset + idx33_size]

tile_count = struct.unpack_from('<H', res_data, 0)[0]
offset_table_start = 8
tile_offsets = []
for i in range(tile_count):
    offset = struct.unpack_from('<I', res_data, offset_table_start + i * 4)[0]
    if offset < len(res_data):
        tile_offsets.append(offset)
    else:
        break

def decompress_rle(src_data, width, height):
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    dst_pos = 0
    
    while dst_pos < dst_size and src_pos < len(src_data):
        byte = src_data[src_pos]
        src_pos += 1
        
        if byte & 0x80:
            if byte & 0x40:
                count = ((byte & 0x3F) + 1)
                dst_pos += count
            else:
                count = ((byte & 0x3F) + 1)
                for i in range(count):
                    if dst_pos < dst_size and src_pos < len(src_data):
                        dst[dst_pos] = src_data[src_pos]
                        src_pos += 1
                        dst_pos += 1
        else:
            count = byte + 1
            if src_pos < len(src_data):
                fill_value = src_data[src_pos]
                src_pos += 1
                for i in range(count):
                    if dst_pos < dst_size:
                        dst[dst_pos] = fill_value
                        dst_pos += 1
    
    return bytes(dst)

# 创建调色板 (256色)
palette = []
for i in range(256):
    palette.extend([i, i, i])

# 提取所有tile并保存
tile_images = []
for tile_idx, tile_offset in enumerate(tile_offsets):
    if tile_idx + 1 < len(tile_offsets):
        tile_size = tile_offsets[tile_idx + 1] - tile_offset
    else:
        tile_size = len(res_data) - tile_offset
    
    tile_data = res_data[tile_offset:tile_offset + tile_size]
    
    if len(tile_data) < 9:
        continue
    
    tile_width = struct.unpack_from('<H', tile_data, 0)[0]
    tile_height = struct.unpack_from('<H', tile_data, 2)[0]
    
    if tile_width == 0 or tile_height == 0 or tile_width > 1024 or tile_height > 1024:
        continue
    
    rle_data = tile_data[9:]
    
    try:
        pixels = decompress_rle(rle_data, tile_width, tile_height)
        
        img = Image.new('P', (tile_width, tile_height))
        img.putdata(pixels)
        img.putpalette(palette)
        
        # 保存单个tile
        img_path = os.path.join(OUTPUT_DIR, f"tile_{tile_idx:04d}_{tile_width}x{tile_height}.png")
        img.save(img_path)
        tile_images.append((tile_idx, img, tile_width, tile_height))
        
    except Exception as e:
        print(f"Tile {tile_idx} 解压缩失败: {e}")

print(f"总计提取: {len(tile_images)} 个tile")

# 创建预览大图 (排列所有tile)
# 计算最大宽度，按行排列
max_width = max(w for _, _, w, _ in tile_images) if tile_images else 0
total_height = sum(h for _, _, _, h in tile_images) if tile_images else 0

# 按行排列，每行宽度不超过1024
preview_width = 1024
preview_height = 0
current_y = 0
current_x = 0
row_height = 0

# 计算总高度
preview_height = 0
current_y = 0
row_height = 0
for _, _, w, h in tile_images:
    if current_x + w > preview_width:
        preview_height += row_height
        current_y += row_height
        current_x = 0
        row_height = 0
    current_x += w
    row_height = max(row_height, h)
preview_height += row_height

# 创建预览图
preview = Image.new('P', (preview_width, preview_height))
preview.putpalette(palette)

current_x = 0
current_y = 0
row_height = 0

for tile_idx, img, w, h in tile_images:
    if current_x + w > preview_width:
        current_y += row_height
        current_x = 0
        row_height = 0
    
    preview.paste(img, (current_x, current_y))
    current_x += w
    row_height = max(row_height, h)

preview_path = os.path.join(OUTPUT_DIR, "preview_all_tiles.png")
preview.save(preview_path)
print(f"预览图已保存: {preview_path} ({preview_width}x{preview_height})")
