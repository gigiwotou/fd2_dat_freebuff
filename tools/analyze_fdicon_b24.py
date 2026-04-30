"""Analyze FDICON.B24 file structure based on IDA sub_11019 analysis.

FDICON.B24 format (from IDA analysis of sub_11019 at 0x11019):
- 6 bytes: header (unknown, skipped)
- Offset table: 12 DWORDs per icon entry
- Icon data: variable size per icon

Each icon has 12 segments/frames with their own offsets.
The function reads 6720 bytes from offset 6 = 1680 DWORDs.
1680 / 12 = 140 icons maximum.
"""

import struct
import sys
import os

def analyze_fdicon_b24(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        return

    data = open(filepath, 'rb').read()
    print(f"FDICON.B24 file size: {len(data)} bytes")
    print(f"Header (6 bytes): {data[:6].hex(' ')}")

    # Read offset table from byte 6
    offset_table_start = 6
    offset_table_size = 6720  # From IDA: malloc(6720)
    
    if len(data) < offset_table_start + offset_table_size:
        print(f"Warning: file too small for full offset table")
        offset_table_size = len(data) - offset_table_start

    # Parse as DWORDs
    num_dwords = offset_table_size // 4
    offsets = struct.unpack(f'<{num_dwords}I', data[offset_table_start:offset_table_start + offset_table_size])
    
    print(f"\nOffset table: {num_dwords} DWORDs ({num_dwords // 12} icons * 12 offsets)")
    
    num_icons = num_dwords // 12
    print(f"\nExpected icon count: {num_icons}")
    
    # Analyze first few icons
    print("\nIcon offset analysis (first 10 icons):")
    print(f"{'Icon':>4} {'Off[0]':>8} {'Off[1]':>8} ... {'Off[11]':>8} {'DataSize':>8}")
    print("-" * 60)
    
    for i in range(min(10, num_icons)):
        base = i * 12
        icon_offsets = offsets[base:base+12]
        # Data size is typically determined by the difference between last and first offset
        # But there are only 12 offsets, so we need to infer
        if i < num_icons - 1:
            next_base = (i + 1) * 12
            data_size = offsets[next_base] - icon_offsets[0]
        else:
            data_size = len(data) - icon_offsets[0]
        
        print(f"{i:4d} {icon_offsets[0]:8d} {icon_offsets[1]:8d} ... {icon_offsets[11]:8d} {data_size:8d}")
    
    # Calculate actual data region
    first_icon_offset = offsets[0]
    print(f"\nFirst icon data at offset: {first_icon_offset}")
    print(f"Data region starts at: {first_icon_offset}")
    print(f"File size minus data start: {len(data) - first_icon_offset} bytes")
    
    # Analyze icon 0 data size
    icon0_size = offsets[12] - offsets[0]
    print(f"Icon 0 data size: {icon0_size} bytes")
    
    # Check if icons are sequential
    print("\nChecking sequential icon layout:")
    for i in range(min(5, num_icons - 1)):
        base = i * 12
        next_base = (i + 1) * 12
        current_start = offsets[base]
        next_start = offsets[next_base]
        current_size = next_start - current_start
        print(f"  Icon {i}: start={current_start}, next={next_start}, size={current_size}")
    
    # Try to determine pixel format
    total_data_size = len(data) - first_icon_offset
    total_icons = num_icons
    avg_size = total_data_size // total_icons
    print(f"\nTotal icon data: {total_data_size} bytes")
    print(f"Average per icon: {avg_size} bytes")
    
    # Check if 24x24 tiles
    print("\nPossible tile sizes:")
    for w, h in [(16,16), (24,24), (32,32), (16,32), (32,16), (48,48)]:
        bytes_per_frame = w * h
        frames_per_icon = avg_size / bytes_per_frame
        if frames_per_icon > 0.5 and frames_per_icon < 25:
            print(f"  {w}x{h} = {bytes_per_frame} bytes/frame -> {frames_per_icon:.1f} frames/icon")

if __name__ == '__main__':
    filepath = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    analyze_fdicon_b24(filepath)
