#!/usr/bin/env python3
"""
Export map 32 character portrait icons from FDICON.B24 to verify pixel data.
Uses the exact same RLE decoding logic as fd2_icon_decode_segment() in C code.
"""

import struct
import os
from PIL import Image

# FDICON.B24 structure constants (from C code)
FDICON_SEGMENTS_PER_ICON = 12
FDICON_OFFSET_TABLE_SIZE = 6720  # 1680 DWORDs
FDICON_MAX_ICONS = 140
FDICON_HEADER_RESERVE = 1920

def load_fdicon(filepath):
    """Load FDICON.B24 and parse offset table like C code does."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"Loading {filepath}: {len(data)} bytes")
    
    # Read offset table: 6720 bytes starting at offset 6
    offset_table_start = 6
    offset_table_data = data[offset_table_start:offset_table_start + FDICON_OFFSET_TABLE_SIZE]
    
    # Parse 1680 DWORDs (140 icons * 12 segments)
    offsets = []
    for i in range(FDICON_MAX_ICONS * FDICON_SEGMENTS_PER_ICON):
        pos = i * 4
        offset = struct.unpack_from('<I', offset_table_data, pos)[0]
        offsets.append(offset)
    
    # Count valid icons
    total_icons = 0
    for i in range(FDICON_MAX_ICONS):
        first_offset = offsets[i * FDICON_SEGMENTS_PER_ICON]
        if first_offset < 6 or first_offset >= len(data):
            break
        total_icons += 1
    
    print(f"Found {total_icons} valid icons")
    return data, offsets, total_icons

def decode_rle_segment(seg_data, width=24, height=24):
    """
    Decode RLE compressed icon segment using IDA sub_4E98D algorithm.
    Exact match to fd2_icon_decode_segment() in C code.
    """
    if not seg_data or len(seg_data) < 2:
        return None
    
    pixels = bytearray(width * height)
    src_ptr = 0
    seg_data_len = len(seg_data)
    
    for y in range(height):
        width_remaining = width
        dst_ptr = y * width
        
        while width_remaining > 0 and src_ptr < seg_data_len:
            value = seg_data[src_ptr]
            src_ptr += 1
            
            # Extract bits 7 and 6 for command type
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            count = (value & 0x3F) + 1
            
            if count > width_remaining:
                count = width_remaining
            
            if bit7 and bit6:
                # 0xC0+: SKIP pixels (transparent)
                dst_ptr += count
                width_remaining -= count
            elif bit7 and not bit6:
                # 0x80-0xBF: COPY raw bytes from source
                if src_ptr + count > seg_data_len:
                    break
                for i in range(count):
                    pixels[dst_ptr] = seg_data[src_ptr]
                    dst_ptr += 1
                    src_ptr += 1
                width_remaining -= count
            elif not bit7 and bit6:
                # 0x40-0x7F: FILL with next byte
                if src_ptr >= seg_data_len:
                    break
                fill_value = seg_data[src_ptr]
                src_ptr += 1
                
                for i in range(count):
                    if dst_ptr < width * height:
                        pixels[dst_ptr] = fill_value
                        dst_ptr += 1
                width_remaining -= count
            else:
                # 0x00-0x3F: FILL with next byte
                if src_ptr >= seg_data_len:
                    break
                fill_value = seg_data[src_ptr]
                src_ptr += 1
                
                for i in range(count):
                    if dst_ptr < width * height:
                        pixels[dst_ptr] = fill_value
                        dst_ptr += 1
                width_remaining -= count
    
    return bytes(pixels)

def export_icon(data, offsets, icon_id, output_dir):
    """Export icon segment 0 (front, frame 0) as PNG."""
    if icon_id >= FDICON_MAX_ICONS:
        print(f"  X Icon {icon_id}: ID out of range")
        return False
    
    base_idx = icon_id * FDICON_SEGMENTS_PER_ICON
    
    # Get offsets for segment 0 and 1
    data_start = offsets[base_idx]
    data_end = offsets[base_idx + 1]  # Next segment offset
    data_size = data_end - data_start
    
    print(f"\nIcon {icon_id} (segment 0): data_start={data_start}, data_end={data_end}, size={data_size}")
    
    if data_start < 6 or data_end > len(data) or data_size <= 0:
        print(f"  X Icon {icon_id}: invalid offsets")
        return False
    
    # Extract segment data
    seg_data = data[data_start:data_end]
    
    # Decode RLE
    pixels = decode_rle_segment(seg_data)
    if pixels is None:
        print(f"  X Icon {icon_id}: decode failed")
        return False
    
    # Count non-zero pixels
    non_zero = sum(1 for p in pixels if p != 0)
    print(f"  Non-zero pixels: {non_zero}/576")
    
    # Create grayscale image (palette index visualization)
    img_gray = Image.new('L', (24, 24))
    img_gray.putdata(pixels)
    
    # Save grayscale version
    filename_gray = os.path.join(output_dir, f'icon_{icon_id:03d}_seg0_gray.png')
    img_gray.save(filename_gray)
    print(f"  Saved: {filename_gray}")
    
    # Create RGB version with color mapping
    img_rgb = Image.new('RGB', (24, 24))
    pixel_list = []
    for p in pixels:
        if p == 0:
            pixel_list.append((0, 0, 0))  # Transparent
        else:
            # Map palette index to visible color
            r = (p * 37) % 256
            g = (p * 71) % 256
            b = (p * 103) % 256
            pixel_list.append((r, g, b))
    img_rgb.putdata(pixel_list)
    
    filename_rgb = os.path.join(output_dir, f'icon_{icon_id:03d}_seg0_rgb.png')
    img_rgb.save(filename_rgb)
    print(f"  Saved: {filename_rgb}")
    
    return non_zero > 0

def main():
    output_dir = 'output/map32_icons'
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("Map 32 Sprite Export Tool")
    print("=" * 60)
    
    # Load FDICON.B24
    data, offsets, total_icons = load_fdicon('game/FDICON.B24')
    
    # Map 32 uses these portrait IDs
    portrait_ids = [0, 4, 48, 66, 68, 69, 96]
    
    print(f"\nMap 32 characters:")
    print(f"  Portrait IDs used: {portrait_ids}")
    print(f"  Exporting icons...")
    
    success_count = 0
    for pid in portrait_ids:
        if export_icon(data, offsets, pid, output_dir):
            success_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"Successfully exported {success_count}/{len(portrait_ids)} icons")
    print(f"Output directory: {output_dir}/")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
