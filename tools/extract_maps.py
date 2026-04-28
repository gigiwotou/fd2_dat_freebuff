#!/usr/bin/env python3
"""
FD2 Map Resource Extractor

Extracts map tile images from FDSHAP.DAT and map layout data from FDFIELD.DAT.

Based on IDA analysis:
- FDSHAP.DAT: Contains map tile images (RLE compressed)
- FDFIELD.DAT: Contains map layout/composition data
"""

import argparse
import struct
import json
import os
from pathlib import Path


def parse_dat_file(data: bytes):
    """Parse DAT file format (header + resource index table)"""
    if len(data) < 10:
        return None
    
    # Check magic "LLLLLL"
    magic = data[:6]
    if magic != b"LLLLLL":
        print(f"Warning: Unexpected magic: {magic}")
        return None
    
    # Resource count (little-endian 32-bit)
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    # Parse offset table
    offsets = []
    for i in range(resource_count):
        offset_pos = 10 + i * 4
        if offset_pos + 4 > len(data):
            break
        offset = struct.unpack_from("<I", data, offset_pos)[0]
        offsets.append(offset)
    
    # Calculate sizes
    resources = []
    for i in range(len(offsets)):
        start = offsets[i]
        if i + 1 < len(offsets):
            end = offsets[i + 1]
        else:
            end = len(data)
        
        size = end - start
        resources.append({
            "index": i,
            "offset": start,
            "size": size,
            "data": data[start:end]
        })
    
    return {
        "magic": magic.decode("ascii"),
        "resource_count": resource_count,
        "resources": resources
    }


def read_rle_header(res_data: bytes):
    """Read RLE image header (4 bytes: width, height as 16-bit LE)"""
    if len(res_data) < 4:
        return 0, 0
    width = struct.unpack_from("<H", res_data, 0)[0]
    height = struct.unpack_from("<H", res_data, 2)[0]
    return width, height


def decompress_rle_image(res_data: bytes, palette: bytes = None):
    """
    Decompress RLE image data.
    Returns (width, height, pixels) or None on failure.
    """
    if len(res_data) < 4:
        return None
    
    width, height = read_rle_header(res_data)
    if width <= 0 or width > 640 or height <= 0 or height > 480:
        return None
    
    expected_size = width * height
    compressed_data = res_data[4:]
    
    # RLE decompression
    pixels = bytearray()
    pos = 0
    
    while pos < len(compressed_data) and len(pixels) < expected_size:
        cmd = compressed_data[pos]
        pos += 1
        
        if cmd >= 192:
            # Skip transparent pixels
            count = cmd - 192 + 1
            pixels.extend([0] * count)
        elif cmd >= 128:
            # Literal run
            count = cmd - 128 + 1
            if pos + count <= len(compressed_data):
                pixels.extend(compressed_data[pos:pos + count])
                pos += count
        elif cmd >= 64:
            # Fill run
            count = cmd - 64
            if pos < len(compressed_data):
                color = compressed_data[pos]
                pos += 1
                pixels.extend([color] * count)
        else:
            # Small fill run
            count = cmd
            if pos < len(compressed_data):
                color = compressed_data[pos]
                pos += 1
                pixels.extend([color] * count)
    
    if len(pixels) < expected_size:
        pixels.extend([0] * (expected_size - len(pixels)))
    
    return width, height, bytes(pixels[:expected_size])


def analyze_map_resources(fdfield_data, fdshap_data, output_dir: Path):
    """Analyze and extract map data from both DAT files"""
    
    fdfield = parse_dat_file(fdfield_data)
    fdshap = parse_dat_file(fdshap_data)
    
    if not fdfield or not fdshap:
        print("Error: Failed to parse DAT files")
        return
    
    print(f"\n{'='*60}")
    print(f"FDFIELD.DAT: {fdfield['resource_count']} resources")
    print(f"FDSHAP.DAT: {fdshap['resource_count']} resources")
    print(f"{'='*60}\n")
    
    # Export FDSHAP.DAT summary
    fdshap_summary = []
    for res in fdshap["resources"][:100]:  # First 100 resources
        res_data = res["data"]
        info = {
            "index": res["index"],
            "offset": res["offset"],
            "size": res["size"]
        }
        
        # Try to read as RLE image
        if len(res_data) >= 4:
            width, height = read_rle_header(res_data)
            if width > 0 and width <= 640 and height > 0 and height <= 480:
                info["type"] = "tile_image"
                info["width"] = width
                info["height"] = height
                info["is_rle"] = True
        
        fdshap_summary.append(info)
    
    # Export FDFIELD.DAT summary  
    fdfield_summary = []
    for res in fdfield["resources"][:100]:  # First 100 resources
        res_data = res["data"]
        info = {
            "index": res["index"],
            "offset": res["offset"],
            "size": res["size"]
        }
        
        # Analyze map layout data structure
        if len(res_data) > 0:
            # Try to detect if it's a tile map (grid of tile indices)
            info["type"] = "map_layout"
            info["byte_count"] = len(res_data)
            
            # Check if data could be a tile grid
            # Common map sizes: 20x15=300, 16x12=192, 32x32=1024
            byte_count = len(res_data)
            possible_dims = []
            for w in range(10, 50):
                if byte_count % w == 0:
                    h = byte_count // w
                    if 10 <= h <= 50:
                        possible_dims.append(f"{w}x{h}")
            
            if possible_dims:
                info["possible_dimensions"] = possible_dims[:5]
        
        fdfield_summary.append(info)
    
    # Save analysis results
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "fdshap_analysis.json", "w") as f:
        json.dump({
            "file": "FDSHAP.DAT",
            "resource_count": fdshap["resource_count"],
            "resources": fdshap_summary
        }, f, indent=2)
    
    with open(output_dir / "fdfield_analysis.json", "w") as f:
        json.dump({
            "file": "FDFIELD.DAT",
            "resource_count": fdfield["resource_count"],
            "resources": fdfield_summary
        }, f, indent=2)
    
    print(f"Analysis saved to {output_dir}/")
    print(f"  - fdshap_analysis.json")
    print(f"  - fdfield_analysis.json")
    
    # Show map 97 info specifically
    if fdfield["resource_count"] > 97:
        map97 = fdfield["resources"][97]
        print(f"\nMap 97 (from FDFIELD.DAT):")
        print(f"  Offset: {map97['offset']}")
        print(f"  Size: {map97['size']} bytes")
        print(f"  Data preview: {map97['data'][:50].hex()}")
    
    if fdshap["resource_count"] > 97:
        tile97 = fdshap["resources"][97]
        print(f"\nTile set 97 (from FDSHAP.DAT):")
        print(f"  Offset: {tile97['offset']}")
        print(f"  Size: {tile97['size']} bytes")


def export_map_97(fdfield_data, output_dir: Path):
    """Export map 97 data in editable JSON format"""
    
    fdfield = parse_dat_file(fdfield_data)
    if not fdfield or fdfield["resource_count"] <= 97:
        print("Error: Map 97 not found in FDFIELD.DAT")
        return
    
    map_data = fdfield["resources"][97]["data"]
    byte_count = len(map_data)
    
    # Try to interpret as tile map
    # First bytes might be header (width, height, etc.)
    map_info = {
        "map_id": 97,
        "description": "Battlefield map - First story level",
        "raw_size": byte_count,
        "format": "fdfield_map_layout",
        "format_note": "Map layout data from FDFIELD.DAT resource 97"
    }
    
    # Try different interpretations
    if byte_count >= 4:
        # Check for header
        w16 = struct.unpack_from("<H", map_data, 0)[0]
        h16 = struct.unpack_from("<H", map_data, 2)[0]
        
        if w16 > 0 and w16 <= 64 and h16 > 0 and h16 <= 64:
            map_info["header_width"] = w16
            map_info["header_height"] = h16
            tile_data = map_data[4:]
        else:
            # No header, try to infer dimensions
            tile_data = map_data
    
    # Export tile indices as 2D array
    if len(tile_data) > 0:
        # Try common dimensions
        for w, h in [(20, 15), (16, 12), (32, 20), (40, 25)]:
            if w * h == len(tile_data):
                tiles_2d = []
                for y in range(h):
                    row = []
                    for x in range(w):
                        tile_idx = tile_data[y * w + x]
                        row.append(tile_idx)
                    tiles_2d.append(row)
                
                map_info["width"] = w
                map_info["height"] = h
                map_info["tile_size"] = 16
                map_info["tiles"] = tiles_2d
                break
    
    # Save as raw bytes if not matched
    if "tiles" not in map_info:
        map_info["raw_bytes"] = [b for b in tile_data[:200]]
        map_info["byte_count"] = len(tile_data)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "map_97.json", "w") as f:
        json.dump(map_info, f, indent=2)
    
    print(f"\nMap 97 exported to {output_dir}/map_97.json")
    print(f"  Size: {byte_count} bytes")
    if "width" in map_info:
        print(f"  Dimensions: {map_info['width']}x{map_info['height']} tiles")


def main():
    parser = argparse.ArgumentParser(description="FD2 Map Resource Extractor")
    parser.add_argument("--source", type=Path, default=Path("game"),
                       help="Game directory containing DAT files")
    parser.add_argument("--output", type=Path, default=Path("output/maps"),
                       help="Output directory for extracted data")
    parser.add_argument("--analyze", action="store_true",
                       help="Analyze DAT file structure")
    parser.add_argument("--export-map", type=int,
                       help="Export specific map (e.g., 97)")
    
    args = parser.parse_args()
    
    source = args.source.resolve()
    output = args.output.resolve()
    
    if not source.exists():
        print(f"Error: Source directory not found: {source}")
        return 1
    
    fdfield_path = source / "FDFIELD.DAT"
    fdshap_path = source / "FDSHAP.DAT"
    
    if not fdfield_path.exists() or not fdshap_path.exists():
        print(f"Error: DAT files not found in {source}")
        print(f"  FDFIELD.DAT: {'found' if fdfield_path.exists() else 'missing'}")
        print(f"  FDSHAP.DAT: {'found' if fdshap_path.exists() else 'missing'}")
        return 1
    
    # Load DAT files
    print(f"Loading FDFIELD.DAT...")
    fdfield_data = fdfield_path.read_bytes()
    print(f"  Size: {len(fdfield_data)} bytes")
    
    print(f"Loading FDSHAP.DAT...")
    fdshap_data = fdshap_path.read_bytes()
    print(f"  Size: {len(fdshap_data)} bytes")
    
    if args.analyze:
        analyze_map_resources(fdfield_data, fdshap_data, output)
    
    if args.export_map is not None:
        export_map_97(fdfield_data, output)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
