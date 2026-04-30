#!/usr/bin/env python3
"""
Export map 32 character portrait icons as PNG images.
Uses the exact same RLE decoding logic as fd2_icon_b24.c (IDA sub_4E98D)
"""
import struct
import os
from PIL import Image

# FDICON.B24 structure (from C code)
FDICON_SEGMENTS_PER_ICON = 12
FDICON_OFFSET_TABLE_SIZE = 6720  # 1680 DWORDs
FDICON_MAX_ICONS = 140

def load_fdicon(filepath):
    """Load FDICON.B24 and parse icon entries using C code logic."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"Loading {filepath}: {len(data)} bytes")
    
    # Read offset table: 6720 bytes starting at offset 6
    offset_table_start = 6
    offset_table_data = data[offset_table_start:offset_table_start + FDICON_OFFSET_TABLE_SIZE]
    
    # Parse 1680 DWORDs (140 icons * 12 segments each)
    file_offsets = []
    for i in range(FDICON_MAX_ICONS * FDICON_SEGMENTS_PER_ICON):
        pos = i * 4
        offset = struct.unpack_from('<I', offset_table_data, pos)[0]
        file_offsets.append(offset)
    
    # Calculate total icons
    total_icons = 0
    for i in range(FDICON_MAX_ICONS):
        first_offset = file_offsets[i * FDICON_SEGMENTS_PER_ICON]
        if first_offset < 6 or first_offset >= len(data):
            break
        total_icons += 1
    
    print(f"Found {total_icons} valid icons")
    
    return data, file_offsets, total_icons

def decode_rle_icon(icon_data, data_start, data_end, width=24, height=24):
    """
    Decode icon segment using exact IDA sub_4E98D algorithm.
    Matches fd2_icon_decode_segment() in fd2_icon_b24.c
    """
    # Extract icon data
    if data_start < 6 or data_end > len(icon_data):
        return None
    
    seg_data = icon_data[data_start:data_end]
    seg_data_len = len(seg_data)
    
    # Clear output buffer (0 = transparent)
    pixels = bytearray(width * height)
    
    src_ptr = 0
    
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

def export_icon(data, file_offsets, icon_id, width=24, height=24, output_dir='.'):
    """Export icon segment 0 (front, frame 0) as PNG."""
    if icon_id >= len(file_offsets) // FDICON_SEGMENTS_PER_ICON:
        print(f"  Icon {icon_id}: ID out of range")
        return False
    
    base_idx = icon_id * FDICON_SEGMENTS_PER_ICON
    
    # Get offsets for all 12 segments
    offsets = file_offsets[base_idx:base_idx + FDICON_SEGMENTS_PER_ICON + 1]  # Need 13th for size
    
    # Segment 0: front view, frame 0
    data_start = offsets[0]
    data_end = offsets[1]  # Next segment offset
    data_size = data_end - data_start
    
    print(f"\nIcon {icon_id} (segment 0): data_start={data_start}, data_end={data_end}, size={data_size}")
    
    if data_start < 6 or data_end > len(data) or data_size <= 0:
        print(f"  Icon {icon_id}: invalid offsets")
        return False
    
    # Decode using IDA algorithm
    pixels = decode_rle_icon(data, data_start, data_end, width, height)
    if pixels is None:
        print(f"  Icon {icon_id}: FAILED to decode")
        return False
    
    # Create RGBA image
    img = Image.new('RGBA', (width, height))
    pixel_list = []
    
    for p in pixels:
        if p == 0:
            pixel_list.append((0, 0, 0, 0))  # Transparent
        else:
            # Map palette index to visible color (bright)
            r = (p * 7) % 256
            g = (p * 13) % 256
            b = (p * 17) % 256
            pixel_list.append((r, g, b, 255))
    
    img.putdata(pixel_list)
    
    # Save
    filename = os.path.join(output_dir, f'icon_{icon_id:03d}_seg0.png')
    img.save(filename)
    
    # Count non-zero pixels
    non_zero = sum(1 for p in pixels if p != 0)
    print(f"  Icon {icon_id}: saved to {filename} ({non_zero} non-zero pixels out of {len(pixels)})")
    
    # Save grayscale version
    img_gray = Image.new('L', (width, height))
    img_gray.putdata(pixels)
    filename_gray = os.path.join(output_dir, f'icon_{icon_id:03d}_gray.png')
    img_gray.save(filename_gray)
    
    return non_zero > 0

def main():
    output_dir = 'map32_icons'
    os.makedirs(output_dir, exist_ok=True)
    
    # Load FDICON.B24
    data, file_offsets, total_icons = load_fdicon('game/FDICON.B24')
    
    # Map 32 portrait IDs from the log
    portrait_ids = [48, 66, 0, 4, 68, 69, 96]
    unique_ids = sorted(set(portrait_ids))
    
    # Show character positions
    print("\nMap 32 characters:")
    print("  Enemy 0: portrait 48 at tile (7,5)")
    print("  Enemy 1: portrait 66 at tile (10,5)")
    print("  Enemy 2-3: portrait 0 at tiles (8,42), (4,46)")
    print("  Enemy 4: portrait 4 at tile (13,47)")
    print("  Enemy 5-12: portrait 68")
    print("  Enemy 13-20: portrait 69")
    print("  Enemy 21-29: portrait 96 at (0,0)")
    
    print(f"\nTotal icons in file: {total_icons}")
    print(f"Exporting {len(unique_ids)} unique portrait IDs: {unique_ids}")
    
    # Export each portrait
    success_count = 0
    for portrait_id in unique_ids:
        if export_icon(data, file_offsets, portrait_id, output_dir=output_dir):
            success_count += 1
    
    print(f"\nSuccessfully exported {success_count}/{len(unique_ids)} icons")
    print(f"Check the {output_dir}/ folder for PNG files")
    
    # Create summary image
    print("\nCreating summary image...")
    try:
        summary = Image.new('RGBA', (24 * len(unique_ids), 24))
        for idx, portrait_id in enumerate(unique_ids):
            filename = os.path.join(output_dir, f'icon_{portrait_id:03d}_seg0.png')
            if os.path.exists(filename):
                img = Image.open(filename)
                summary.paste(img, (idx * 24, 0))
        
        summary_path = os.path.join(output_dir, 'map32_summary.png')
        summary.save(summary_path)
        print(f"Summary saved to {summary_path}")
    except Exception as e:
        print(f"Failed to create summary: {e}")

if __name__ == '__main__':
    main()
