#!/usr/bin/env python3
"""
FD2 Map Verification Tool

Exports tile images from FDSHAP.DAT and generates complete maps
from FDFIELD.DAT layout data.

Usage:
  python tools/map_verify.py --export-tiles    # Export all tiles
  python tools/map_verify.py --generate-map 0  # Generate map 0
"""

import struct
import json
import argparse
from pathlib import Path
from PIL import Image


def parse_fdshap(data: bytes):
    """Parse FDSHAP.DAT file structure (verified by IDA sub_111BA analysis).
    
    Structure:
    - Header: 6 bytes "LLLLLL"
    - Resource count: 4 bytes (offset 6)
    - Resource offsets: count * 4 bytes starting at offset 10
    - Resource i: start = offsets[i], end = offsets[i+1]
    
    Resources alternate: even=palette, odd=tile images
    Each odd resource (tile image):
    - First 4 bytes: width(2) + height(2) - tile dimensions
    - From offset 4: offset table (2 bytes per tile offset)
    - Rest: RLE compressed tile pixel data
    """
    magic = data[:6]
    if magic != b"LLLLLL":
        raise ValueError(f"Invalid DAT magic: {magic}")
    
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    # Read all resource offsets
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
        offsets.append(offset)
    
    # Build resource list
    resources = []
    for i in range(resource_count):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < resource_count else len(data)
        size = end - start
        resources.append({
            "index": i,
            "offset": start,
            "size": size,
            "data": data[start:end]
        })
    
    return {
        "resource_count": resource_count,
        "resources": resources
    }


def parse_fdfield(data: bytes):
    """Parse FDFIELD.DAT file structure.
    
    Structure (verified by analysis):
    - Header: 6 bytes "LLLLLL"
    - Offset table: starts at offset 6, each entry 4 bytes
    - Data: starts after the offset table
    
    Each map uses 3 consecutive resources:
    - Resource N*3: layout data (width 2 bytes + height 2 bytes + tile grid)
    - Resource N*3+1: control data
    - Resource N*3+2: spawn data
    
    Layout data format:
    - Width: 2 bytes (LE)
    - Height: 2 bytes (LE)
    - Tile data: width * height * 4 bytes (terrain_id + event_id per tile)
    """
    magic = data[:6]
    if magic != b"LLLLLL":
        raise ValueError(f"Invalid FDFIELD magic: {magic}")
    
    # Read all resource offsets from offset table (starts at 6)
    resource_offsets = []
    pos = 6
    while pos < len(data) - 4:
        offset = struct.unpack_from("<I", data, pos)[0]
        # Valid offset should point to data after the offset table
        # We'll validate by checking if it points to reasonable layout data
        if offset > pos and offset < len(data):
            resource_offsets.append(offset)
        else:
            break
        pos += 4
    
    resource_count = len(resource_offsets)
    max_maps = resource_count // 3
    
    print(f"  Found {resource_count} resource offsets")
    
    maps = []
    for map_id in range(max_maps):
        layout_res_idx = map_id * 3
        if layout_res_idx + 2 >= resource_count:
            break
        
        layout_start = resource_offsets[layout_res_idx]
        control_start = resource_offsets[layout_res_idx + 1]
        spawn_start = resource_offsets[layout_res_idx + 2]
        
        # Parse layout dimensions
        if layout_start >= len(data) - 4:
            break
            
        w = struct.unpack_from("<H", data, layout_start)[0]
        h = struct.unpack_from("<H", data, layout_start + 2)[0]
        
        # Validate dimensions
        if w <= 0 or w > 200 or h <= 0 or h > 200:
            continue
        
        # Calculate layout size
        layout_size = resource_offsets[layout_res_idx + 1] - layout_start if layout_res_idx + 1 < resource_count else len(data) - layout_start
        
        # Parse control data
        terrain_set_id = 0
        ally_max = 0
        enemy_total = 0
        if control_start < len(data) - 2:
            terrain_set_id = data[control_start]
            ally_max = data[control_start + 1]
            enemy_total = data[control_start + 2]
        
        maps.append({
            "map_id": map_id,
            "layout_start": layout_start,
            "layout_size": layout_size,
            "control_start": control_start,
            "spawn_start": spawn_start,
            "width": w,
            "height": h,
            "terrain_set_id": terrain_set_id,
            "ally_max": ally_max,
            "enemy_total": enemy_total
        })
    
    print(f"  Found {len(maps)} valid maps")
    
    return {
        "resource_count": resource_count,
        "map_count": len(maps),
        "maps": maps,
        "data": data
    }


def rle_decompress(src: bytes, width: int, height: int) -> bytes:
    """
    Decompress FD2 RLE data (IDA sub_4E98D).
    Matches the exact behavior from fd2_decoder.c.
    Returns decompressed pixel data (width * height bytes).
    """
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
                # 11: skip (transparent) - advance dst pointer
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                # 10: copy from source - literal run
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                # 01: sparse fill - write at every 2nd position (odd offsets)
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
                # 00: regular fill - fill with single value
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


def decompress_tile(res_data: bytes):
    """Decompress a single tile from FDSHAP.DAT resource"""
    if len(res_data) < 4:
        return None
    
    width = struct.unpack_from("<H", res_data, 0)[0]
    height = struct.unpack_from("<H", res_data, 2)[0]
    
    if width <= 0 or width > 100 or height <= 0 or height > 100:
        return None
    
    compressed_data = res_data[4:]
    pixels = rle_decompress(compressed_data, width, height)
    
    return {
        "width": width,
        "height": height,
        "pixels": pixels
    }


def palette_6bit_to_8bit(palette_6bit: bytes) -> list:
    """Convert 6-bit VGA palette to 8-bit RGB"""
    palette_8bit = []
    for i in range(0, len(palette_6bit), 3):
        r = palette_6bit[i]
        g = palette_6bit[i + 1]
        b = palette_6bit[i + 2]
        
        # Convert 6-bit to 8-bit
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        
        # Ensure values are in 0-255 range
        r8 = min(255, max(0, r8))
        g8 = min(255, max(0, g8))
        b8 = min(255, max(0, b8))
        
        palette_8bit.append((r8, g8, b8))
    
    return palette_8bit


def export_tiles(fdshap_data: bytes, output_dir: Path, max_tiles: int = 100):
    """Export tile images from FDSHAP.DAT"""
    dat = parse_dat_file(fdshap_data)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"FDSHAP.DAT: {dat['resource_count']} resources")
    print(f"Exporting up to {max_tiles} tiles...\n")
    
    # Extract palette from first even resource
    palette_res = dat["resources"][0]
    if palette_res["size"] >= 768:
        palette_6bit = palette_res["data"][:768]
        palette = palette_6bit_to_8bit(palette_6bit)
        print(f"Extracted palette from resource 0")
    else:
        print("Warning: Could not extract palette")
        palette = [(i, i, i) for i in range(256)]  # Grayscale fallback
    
    # Export tiles (odd indices)
    tile_count = 0
    for res in dat["resources"]:
        if res["index"] % 2 == 0:
            continue  # Skip palette resources
        
        tile_data = decompress_tile(res["data"])
        if not tile_data:
            continue
        
        # Create image
        img = Image.new("P", (tile_data["width"], tile_data["height"]))
        img.putdata(tile_data["pixels"])
        img.putpalette([c for rgb in palette for c in rgb])
        
        # Save
        output_path = output_dir / f"tile_{res['index']:04d}.png"
        img.save(output_path)
        tile_count += 1
        
        if tile_count % 10 == 0:
            print(f"Exported {tile_count} tiles...")
        
        if tile_count >= max_tiles:
            break
    
    print(f"\nTotal tiles exported: {tile_count}")
    print(f"Tiles saved to {output_dir}/")
    
    return tile_count


def generate_map(map_id: int, fdfield_data: bytes, fdshap_data: bytes, 
                 output_dir: Path, tile_cache: dict = None):
    """Generate complete map image from FDFIELD.DAT layout and FDSHAP.DAT tiles"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse FDFIELD.DAT
    fdfield = parse_fdfield(fdfield_data)
    
    print(f"FDFIELD.DAT: {fdfield['map_count']} maps")
    
    if map_id >= fdfield["map_count"]:
        print(f"Error: Map {map_id} not found (valid maps: 0-{fdfield['map_count']-1})")
        return None
    
    map_info = fdfield["maps"][map_id]
    
    # Get layout data
    layout_start = map_info["layout_start"]
    width = map_info["width"]
    height = map_info["height"]
    
    print(f"Map {map_id}: {width}x{height} tiles")
    print(f"  Terrain set ID: {map_info['terrain_set_id']}")
    print(f"  Ally max: {map_info['ally_max']}, Enemy total: {map_info['enemy_total']}")
    
    # Layout data format:
    # Offset 0: width (2 bytes)
    # Offset 2: height (2 bytes)  
    # Offset 4+: tile data (4 bytes per tile: terrain_id + event_id)
    tile_data = fdfield_data[layout_start + 4:layout_start + map_info["layout_size"]]
    
    # Verify we have enough tile data
    expected_size = width * height * 4
    if len(tile_data) < expected_size:
        print(f"Warning: Tile data size ({len(tile_data)}) < expected ({expected_size})")
    
    tiles = []
    pos = 0
    for y in range(height):
        row = []
        for x in range(width):
            if pos + 4 > len(tile_data):
                row.append({"terrain": 0, "event": 0})
            else:
                terrain_id = struct.unpack_from("<H", tile_data, pos)[0]
                event_id = struct.unpack_from("<H", tile_data, pos + 2)[0]
                pos += 4
                row.append({"terrain": terrain_id, "event": event_id})
        tiles.append(row)
    
    # Get terrain set ID from map info
    terrain_set_id = map_info["terrain_set_id"]
    print(f"Using terrain set {terrain_set_id}")
    
    # Parse FDSHAP.DAT for tile images
    fdshap = parse_fdshap(fdshap_data)
    
    # Each terrain set uses 2 resources: palette (even) and tiles (odd)
    # Resource index = terrain_set_id * 2 (palette) and terrain_set_id * 2 + 1 (tiles)
    palette_res_idx = terrain_set_id * 2
    tile_set_res_idx = terrain_set_id * 2 + 1
    
    # Extract palette
    if palette_res_idx < fdshap["resource_count"]:
        palette_res = fdshap["resources"][palette_res_idx]["data"]
        print(f"Using palette from FDSHAP resource {palette_res_idx} (size={len(palette_res)})")
        if len(palette_res) >= 768:
            palette = palette_6bit_to_8bit(palette_res[:768])
        else:
            palette = [(i, i, i) for i in range(256)]
    else:
        print(f"Warning: Palette resource {palette_res_idx} not found")
        palette = [(i, i, i) for i in range(256)]
    
    # Load tile images from tile set resource
    tile_images = {}
    tile_size = 24  # Default tile size
    
    print(f"Loading tile images from FDSHAP resource {tile_set_res_idx}...")
    
    if tile_set_res_idx < fdshap["resource_count"]:
        tile_set_data = fdshap["resources"][tile_set_res_idx]["data"]
        print(f"Tile set resource size: {len(tile_set_data)} bytes")
        
        if len(tile_set_data) >= 6:
            tile_w = struct.unpack_from("<H", tile_set_data, 0)[0]
            tile_h = struct.unpack_from("<H", tile_set_data, 2)[0]
            print(f"Tile dimensions: {tile_w}x{tile_h}")
            
            # Tile offset table:
            # - Byte 4: first tile data offset
            # - Byte 6+: offset entries every 4 bytes (offset + 2 zero bytes)
            # Stop when we hit a non-zero "zero" field or offset exceeds resource size
            tile_offsets = []
            
            # First offset at byte 4
            first_offset = struct.unpack_from("<H", tile_set_data, 4)[0]
            if first_offset > 0 and first_offset < len(tile_set_data):
                tile_offsets.append(first_offset)
            
            # Additional offsets at byte 6, 10, 14, ...
            # Each entry is 4 bytes: [offset(2), zero(2)]
            pos = 6
            consecutive_invalid = 0
            while pos + 4 <= len(tile_set_data):
                offset_val = struct.unpack_from("<H", tile_set_data, pos)[0]
                zero_val = struct.unpack_from("<H", tile_set_data, pos + 2)[0]
                
                if zero_val == 0 and offset_val > 0 and offset_val < len(tile_set_data):
                    tile_offsets.append(offset_val)
                    consecutive_invalid = 0
                else:
                    consecutive_invalid += 1
                    # Stop after 2 consecutive invalid entries
                    if consecutive_invalid >= 2:
                        break
                
                pos += 4
            
            print(f"Found {len(tile_offsets)} tiles in tile set")
            
            # Decompress tiles
            for i in range(len(tile_offsets)):
                tile_offset = tile_offsets[i]
                if i + 1 < len(tile_offsets):
                    next_offset = tile_offsets[i + 1]
                else:
                    next_offset = len(tile_set_data)
                
                compressed_size = next_offset - tile_offset
                if compressed_size <= 0 or compressed_size > 5000:
                    continue
                
                compressed_data = tile_set_data[tile_offset:next_offset]
                pixels = rle_decompress(compressed_data, tile_w, tile_h)
                
                img = Image.new("P", (tile_w, tile_h))
                img.putdata(pixels)
                img.putpalette([c for rgb in palette for c in rgb])
                tile_images[i] = img
            
            tile_size = tile_w
            print(f"Extracted {len(tile_images)} tiles")
    
    if not tile_images:
        print("Warning: No tiles extracted")
    
    # Create map image
    map_width = width * tile_size
    map_height = height * tile_size
    map_img = Image.new("RGB", (map_width, map_height), (0, 0, 0))
    
    # Composite tiles
    print(f"Generating map image ({map_width}x{map_height})...")
    tiles_rendered = 0
    for y in range(height):
        for x in range(width):
            terrain_id = tiles[y][x]["terrain"]
            
            # Map terrain_id to tile index using low 7 bits
            tile_index = terrain_id & 0x7F
            
            if tile_index in tile_images:
                tile_img = tile_images[tile_index].convert("RGB")
                map_img.paste(tile_img, (x * tile_size, y * tile_size))
                tiles_rendered += 1
    
    print(f"Rendered {tiles_rendered}/{width*height} tiles")
    
    # Save map
    output_path = output_dir / f"map_{map_id}.png"
    try:
        map_img.save(str(output_path))
        print(f"Map saved to {output_path}")
    except Exception as e:
        print(f"Error saving map: {e}")
        return None
    
    # Also save tile layout as JSON for reference
    layout_json = {
        "map_id": map_id,
        "width": width,
        "height": height,
        "tile_size": tile_size,
        "terrain_set_id": terrain_set_id,
        "terrain_ids": [[tiles[y][x]["terrain"] for x in range(width)] for y in range(height)]
    }
    
    layout_path = output_dir / f"map_{map_id}_layout.json"
    layout_path.write_text(json.dumps(layout_json, indent=2))
    print(f"Layout saved to {layout_path}")
    
    return {
        "width": width,
        "height": height,
        "tile_size": tile_size,
        "unique_tiles": len(tile_images)
    }


def main():
    parser = argparse.ArgumentParser(description="FD2 Map Verification Tool")
    parser.add_argument("--source", type=Path, default=Path("game"),
                       help="Game directory")
    parser.add_argument("--output", type=Path, default=Path("output/maps"),
                       help="Output directory")
    parser.add_argument("--export-tiles", action="store_true",
                       help="Export tile images from FDSHAP.DAT")
    parser.add_argument("--max-tiles", type=int, default=100,
                       help="Maximum number of tiles to export")
    parser.add_argument("--generate-map", type=int,
                       help="Generate complete map (specify map ID)")
    
    args = parser.parse_args()
    
    source = args.source.resolve()
    output = args.output.resolve()
    
    # Load DAT files
    fdfield_path = source / "FDFIELD.DAT"
    fdshap_path = source / "FDSHAP.DAT"
    
    if not fdfield_path.exists() or not fdshap_path.exists():
        print(f"Error: DAT files not found in {source}")
        return 1
    
    fdfield_data = fdfield_path.read_bytes()
    fdshap_data = fdshap_path.read_bytes()
    
    print(f"Loaded FDFIELD.DAT ({len(fdfield_data)} bytes)")
    print(f"Loaded FDSHAP.DAT ({len(fdshap_data)} bytes)\n")
    
    if args.export_tiles:
        tile_dir = output / "tiles"
        export_tiles(fdshap_data, tile_dir, args.max_tiles)
    
    if args.generate_map is not None:
        tile_dir = output / "tiles"
        result = generate_map(args.generate_map, fdfield_data, fdshap_data, output)
        
        if result:
            print(f"\nMap {args.generate_map} generated successfully:")
            print(f"  Dimensions: {result['width']}x{result['height']} tiles")
            print(f"  Tile size: {result['tile_size']}x{result['tile_size']} pixels")
            print(f"  Unique tiles used: {result['unique_tiles']}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
