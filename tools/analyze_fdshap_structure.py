#!/usr/bin/env python3
"""Deep analyze FDSHAP.DAT structure"""

import struct
from PIL import Image

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

print(f"FDSHAP.DAT size: {len(fdshap)} bytes")
print(f"Magic: {fdshap[:6]}")

# Parse offset table
offset_table_start = 10
resource_count_32 = struct.unpack_from("<I", fdshap, 6)[0]
print(f"Value at offset 6 (as 32-bit): {resource_count_32}")

# Read first 20 resource offsets
offsets = []
for i in range(20):
    pos = 10 + i * 4
    if pos + 4 > len(fdshap):
        break
    offset = struct.unpack_from("<I", fdshap, pos)[0]
    offsets.append(offset)

print(f"\nFirst 20 resource offsets:")
for i, off in enumerate(offsets):
    next_off = offsets[i+1] if i+1 < len(offsets) else len(fdshap)
    size = next_off - off
    print(f"  Resource {i}: offset={off}, size={size}")

# Analyze resource 0 (supposed to be palette)
res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start

print(f"\n--- Resource 0 analysis ---")
print(f"Size: {res0_size} bytes")
print(f"First 50 bytes: {fdshap[res0_start:res0_start+50].hex()}")
print(f"First 20 bytes as values: {list(fdshap[res0_start:res0_start+20])}")

# If palette is 768 bytes (256 colors * 3)
if res0_size >= 768:
    palette_data = fdshap[res0_start:res0_start+768]
    print(f"\nFirst 10 palette entries (6-bit):")
    for i in range(10):
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        print(f"  Color {i}: 6bit=({r},{g},{b}), 8bit=({r8},{g8},{b8})")
    
    # Save palette as image to visualize
    palette_img = Image.new("RGB", (256, 1))
    for i in range(256):
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        palette_img.putpixel((i, 0), (r8, g8, b8))
    palette_img.save("output/maps/palette_0.png")
    palette_img.save("output/maps/palette_0_256x10.png")
    
    # Also save as 16x16 grid for better visualization
    palette_grid = Image.new("RGB", (16*16, 16))
    for i in range(256):
        x = i % 16
        y = i // 16
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        for px in range(16):
            for py in range(16):
                palette_grid.putpixel((x*16+px, y*16+py), (r8, g8, b8))
    palette_grid.save("output/maps/palette_0_grid.png")
    print(f"Saved palette visualization images")

# Analyze resource 1 (supposed to be tile images for terrain set 0)
res1_start = offsets[1]
res1_end = offsets[2]
res1_size = res1_end - res1_start

print(f"\n--- Resource 1 analysis ---")
print(f"Size: {res1_size} bytes")
print(f"First 4 bytes: {fdshap[res1_start:res1_start+4].hex()}")

w = struct.unpack_from("<H", fdshap, res1_start)[0]
h = struct.unpack_from("<H", fdshap, res1_start+2)[0]
print(f"Dimensions from header: {w}x{h}")

# Parse tile offset table (from offset 4, 2 bytes per entry)
tile_offsets = []
pos = res1_start + 4
while pos < res1_start + min(res1_size, 2000) - 2:
    offset_val = struct.unpack_from('<H', fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        if not tile_offsets or offset_val > tile_offsets[-1]:
            tile_offsets.append(offset_val)
    pos += 2

print(f"Found {len(tile_offsets)} tile offsets")
print(f"First 10 offsets: {tile_offsets[:10]}")

# Check if tile sizes are reasonable
if len(tile_offsets) > 1:
    print(f"\nFirst 5 tile sizes:")
    for i in range(min(5, len(tile_offsets)-1)):
        tile_size = tile_offsets[i+1] - tile_offsets[i]
        print(f"  Tile {i}: size={tile_size} bytes")
    
    # Decompress first tile and visualize
    from PIL import Image
    
    def rle_decompress(src: bytes, width: int, height: int):
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
    
    # Decompress first tile
    tile0_start = res1_start + tile_offsets[0]
    tile0_end = res1_start + tile_offsets[1]
    tile0_data = fdshap[tile0_start:tile0_end]
    
    pixels = rle_decompress(tile0_data, w, h)
    
    # Create image
    img = Image.new("P", (w, h))
    img.putdata(pixels)
    
    # Apply palette
    if res0_size >= 768:
        palette_data = fdshap[res0_start:res0_start+768]
        flat_palette = []
        for i in range(256):
            r = palette_data[i*3]
            g = palette_data[i*3+1]
            b = palette_data[i*3+2]
            r8 = (r << 2) | (r >> 4)
            g8 = (g << 2) | (g >> 4)
            b8 = (b << 2) | (b >> 4)
            flat_palette.extend([r8, g8, b8])
        img.putpalette(flat_palette)
    
    img.save("output/maps/tile_0_from_res1.png")
    print(f"Saved tile 0 from resource 1")
