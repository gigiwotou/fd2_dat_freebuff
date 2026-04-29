"""验证map0的不同瓦片索引映射方式"""
from pathlib import Path
import struct
from PIL import Image

OUTPUT_DIR = Path(r"d:\testworkspace\fd2_dat_freebuff\output")
DATA_DIR = Path(r"d:\testworkspace\fd2_dat_freebuff\data")

def load_dat_entries(path):
    """Load DAT entries (format 2: no count)"""
    with open(path, "rb") as f:
        magic = f.read(4)
        num_entries_raw = f.read(2)
    
    entries = []
    with open(path, "rb") as f:
        f.seek(6)
        idx = 0
        while True:
            off_bytes = f.read(4)
            if len(off_bytes) < 4:
                break
            offset = struct.unpack("<I", off_bytes)[0]
            if offset >= 0x100000000:
                break
            entries.append(offset)
            idx += 1
            if idx > 1000:
                break
    return entries

def read_rle(data, start):
    """RLE decompress"""
    result = []
    pos = start
    while pos < len(data):
        op = data[pos]; pos += 1
        count = data[pos]; pos += 1
        if op == 0:  # FILL
            val = data[pos]; pos += 1
            result.extend([val] * count)
        elif op == 1:  # COPY
            result.extend(data[pos:pos+count]); pos += count
        elif op == 2:  # ALTERNATE
            for _ in range(count):
                result.append(data[pos]); pos += 1
        elif op == 3:  # SKIP
            result.extend([0] * count)
        else:
            break
    return result

def decode_tile(data, width, height):
    """Decode a single tile"""
    pixels = read_rle(data, 0)
    if len(pixels) != width * height:
        return None
    img = Image.new("P", (width, height))
    img.putpalette([c for r in range(256) for c in (r, r, r)][:768])
    img.putdata(pixels)
    return img

def apply_palette(img, palette_data):
    """Apply 6-bit palette to image"""
    pal = []
    for i in range(0, len(palette_data), 3):
        r = (palette_data[i] << 2) | (palette_data[i] >> 4)
        g = (palette_data[i+1] << 2) | (palette_data[i+1] >> 4)
        b = (palette_data[i+2] << 2) | (palette_data[i+2] >> 4)
        pal.extend([r, g, b])
    img.putpalette(pal)
    return img

def load_map0_tiles():
    """Load map0 terrain IDs"""
    entries = load_dat_entries(DATA_DIR / "FDFIELD.DAT")
    with open(DATA_DIR / "FDFIELD.DAT", "rb") as f:
        f.seek(entries[0])
        layout = f.read(entries[1] - entries[0])
    
    width, height = layout[0], layout[1]
    tiles = []
    pos = 2
    for y in range(height):
        row = []
        for x in range(width):
            b0 = layout[pos]; b1 = layout[pos+1]; pos += 2
            terrain_id = b0 | ((b1 & 0x03) << 8)
            row.append(terrain_id)
        tiles.append(row)
    return width, height, tiles

def load_tile_set(terrain_set_id):
    """Load tile set with palette"""
    shape_entries = load_dat_entries(DATA_DIR / "FDSHAP.DAT")
    tile_res_idx = terrain_set_id * 2
    
    with open(DATA_DIR / "FDSHAP.DAT", "rb") as f:
        tile_start = shape_entries[tile_res_idx]
        tile_end = shape_entries[tile_res_idx + 1]
        tile_data = f.read(tile_end - tile_start)
    
    other_entries = load_dat_entries(DATA_DIR / "FDOTHER.DAT")
    with open(DATA_DIR / "FDOTHER.DAT", "rb") as f:
        f.seek(other_entries[0])
        palette = f.read(768)
    
    # Parse tile offsets (format 2)
    offsets = []
    pos = 0
    while pos + 4 <= len(tile_data):
        off = struct.unpack("<I", tile_data[pos:pos+4])[0]
        if off > len(tile_data):
            break
        offsets.append(off)
        pos += 4
        if len(offsets) > 500:
            break
    
    tile_images = {}
    tile_size = 64
    for i in range(len(offsets)):
        start = offsets[i]
        end = offsets[i+1] if i+1 < len(offsets) else len(tile_data)
        if end <= start:
            continue
        img = decode_tile(tile_data[start:end], tile_size, tile_size)
        if img:
            tile_images[i] = apply_palette(img, palette)
    
    return tile_images

def render_map(width, height, tiles, tile_images, mapping_func, name):
    """Render map with given mapping function"""
    img = Image.new("RGB", (width * 64, height * 64), (0, 0, 0))
    rendered = 0
    
    for y in range(height):
        for x in range(width):
            terrain_id = tiles[y][x]
            tile_idx = mapping_func(terrain_id)
            if tile_idx in tile_images:
                img.paste(tile_images[tile_idx], (x * 64, y * 64))
                rendered += 1
    
    output_path = OUTPUT_DIR / f"map_0_verify_{name}.png"
    img.save(output_path)
    print(f"  {name}: {rendered}/{width*height} -> {output_path}")

# Main
width, height, tiles = load_map0_tiles()
tile_images = load_tile_set(0)

print(f"Map0: {width}x{height}, {len(tile_images)} tiles loaded\n")

# Collect all terrain IDs
all_ids = set()
for row in tiles:
    all_ids.update(row)
print(f"Terrain ID range: {min(all_ids)}-{max(all_ids)}, unique: {len(all_ids)}\n")

# Test different mappings
mappings = {
    "direct": lambda tid: tid,
    "minus_1": lambda tid: tid - 1 if tid > 0 else 0,
    "minus_8": lambda tid: tid - 8,  # 偏移8（因为最小ID是8）
    "and_7F": lambda tid: tid & 0x7F,
    "and_FF": lambda tid: tid & 0xFF,
    "shr_1": lambda tid: tid >> 1,
}

print("Testing different mappings:")
for name, func in mappings.items():
    try:
        render_map(width, height, tiles, tile_images, func, name)
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

print("\nCheck the generated images to see which mapping is correct.")
