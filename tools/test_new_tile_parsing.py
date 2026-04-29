import struct
from PIL import Image
from pathlib import Path

def rle_decompress(src: bytes, width: int, height: int) -> bytes:
    dst = bytearray(width * height)
    p = 0
    src_end = len(src)
    
    for row in range(height):
        row_dst = row * width
        count = width
        
        while count > 0 and p < src_end:
            value = src[p]
            p += 1
            count_1 = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 and bit6:
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count >= 2:
                            if row_dst + 1 < len(dst):
                                dst[row_dst + 1] = fill
                            row_dst += 2
                            count -= 2
                        else:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
            else:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count > 0:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
    
    return bytes(dst)

def palette_6bit_to_8bit(palette_6bit: bytes) -> list:
    palette_8bit = []
    for i in range(0, len(palette_6bit), 3):
        r = palette_6bit[i]
        g = palette_6bit[i + 1]
        b = palette_6bit[i + 2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        palette_8bit.append((min(255, max(0, r8)), min(255, max(0, g8)), min(255, max(0, b8))))
    return palette_8bit

# 加载FDSHAP.DAT
with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# 解析资源表
fdshap_rc = struct.unpack_from('<I', fdshap, 6)[0]
print(f"FDSHAP.DAT: {fdshap_rc} resources")

fdshap_offsets = []
for i in range(fdshap_rc):
    offset = struct.unpack_from('<I', fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# 资源0（调色板）
res0_start = fdshap_offsets[0]
res0_end = fdshap_offsets[1]
res0_size = res0_end - res0_start
print(f"\n资源0 (palette): start={res0_start}, size={res0_size}")

palette_data = fdshap[res0_start:res0_start + min(res0_size, 768)]
if len(palette_data) >= 768:
    palette = palette_6bit_to_8bit(palette_data[:768])
    print(f"调色板: {len(palette)} 色")
else:
    print(f"调色板数据不足: {len(palette_data)} 字节")
    palette = [(i, i, i) for i in range(256)]

# 资源1（瓦片集）
res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2] if 2 < len(fdshap_offsets) else len(fdshap)
res1_size = res1_end - res1_start
print(f"\n资源1 (tiles): start={res1_start}, size={res1_size}")

# 瓦片尺寸
tile_w, tile_h = struct.unpack_from('<HH', fdshap, res1_start)
print(f"Tile尺寸: {tile_w}x{tile_h}")

# 根据IDA分析，瓦片偏移表从byte 6开始，每个条目4字节（DWORD）
# 公式: FDSHAP_DAT + 4 * tile_index + 6
tile_offsets = []
pos = res1_start + 6
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from('<I', fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        tile_offsets.append(offset_val)
    else:
        # 如果连续多个无效值，停止
        if len(tile_offsets) > 0 and offset_val >= res1_size:
            break
    pos += 4

print(f"找到 {len(tile_offsets)} 个tile (使用4字节DWORD偏移表)")

# 解压前5个tile查看
output_dir = Path("output/maps")
output_dir.mkdir(parents=True, exist_ok=True)

for i in range(min(5, len(tile_offsets))):
    tile_offset = tile_offsets[i]
    if i + 1 < len(tile_offsets):
        tile_size = tile_offsets[i + 1] - tile_offset
    else:
        tile_size = res1_size - tile_offset
    
    try:
        tile_data_start = res1_start + tile_offset
        tile_data = fdshap[tile_data_start:tile_data_start + min(tile_size, 3000)]
        pixels = rle_decompress(tile_data, tile_w, tile_h)
        
        img = Image.new("P", (tile_w, tile_h))
        img.putdata(pixels)
        img.putpalette([c for rgb in palette for c in rgb])
        
        tile_path = output_dir / f"tile_new_{i}.png"
        img.save(str(tile_path))
        print(f"保存 tile_new_{i}.png - 文件存在: {tile_path.exists()}")
    except Exception as e:
        print(f"Tile {i} 解压失败: {e}")

print(f"\n完成！请检查output/maps/tile_new_*.png")
