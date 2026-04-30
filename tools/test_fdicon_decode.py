#!/usr/bin/env python3
"""Test FDICON.B24 decoding for all 4 directions of icon 0"""

import struct
import sys

def decode_segment(data, width=24, height=24):
    """Decode one segment using RLE algorithm from IDA sub_4E98D"""
    pixels = [0] * (width * height)
    src_ptr = 0
    seg_data_len = len(data)
    
    for y in range(height):
        dst_ptr = y * width
        width_remaining = width
        
        while width_remaining > 0 and src_ptr < seg_data_len:
            value = data[src_ptr]
            src_ptr += 1
            
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            count = (value & 0x3F) + 1
            
            if count > width_remaining:
                count = width_remaining
            
            if bit7 == 1:
                if bit6 == 1:
                    # Skip (transparent)
                    pass
                else:
                    # Copy from source
                    if src_ptr + count <= seg_data_len:
                        for i in range(count):
                            if dst_ptr + i < len(pixels):
                                pixels[dst_ptr + i] = data[src_ptr + i]
                        src_ptr += count
            else:
                # Fill with single value
                fill_val = data[src_ptr] if src_ptr < seg_data_len else 0
                src_ptr += 1
                for i in range(count):
                    if dst_ptr + i < len(pixels):
                        pixels[dst_ptr + i] = fill_val
            
            dst_ptr += count
            width_remaining -= count
    
    return pixels

def count_nonzero(pixels):
    """Count non-zero (non-transparent) pixels"""
    return sum(1 for p in pixels if p != 0)

def analyze_directions(icon_data, icon_id=0):
    """Analyze all 4 directions of an icon"""
    # Each icon has 12 segments
    # Front: 0-2, Left: 3-5, Back: 6-8, Right: 9-11
    
    directions = ['Front', 'Left', 'Back', 'Right']
    
    for dir_idx in range(4):
        print(f"\n{'='*50}")
        print(f"Direction: {directions[dir_idx]}")
        print(f"{'='*50}")
        
        for frame in range(3):
            seg_idx = dir_idx * 3 + frame
            offset = icon_data[seg_idx]
            next_offset = icon_data[seg_idx + 1] if seg_idx + 1 < len(icon_data) else None
            
            if next_offset is None:
                print(f"  Frame {frame}: no next offset, skipping")
                continue
            
            seg_size = next_offset - offset
            print(f"  Frame {frame}: offset=0x{offset:X}, size={seg_size} bytes")
            
            # Assume data starts right after offset
            # In real implementation, data is loaded into buffer
            # For testing, we just show the stats
            
def main():
    fdicon_path = sys.argv[1] if len(sys.argv) > 1 else 'FDICON.B24'
    
    try:
        with open(fdicon_path, 'rb') as f:
            f.seek(6)  # Skip header
            offset_table = f.read(6720)  # 1680 DWORDs
            
        offsets = struct.unpack('<' + 'I' * 1680, offset_table)
        
        print(f"FDICON.B24 offset table loaded")
        print(f"Total entries: 1680 (140 icons x 12 segments)")
        
        # Check first few icons
        for icon_id in range(3):
            base = icon_id * 12
            print(f"\n{'#'*60}")
            print(f"Icon {icon_id}")
            print(f"{'#'*60}")
            
            offsets_for_icon = offsets[base:base+12]
            print(f"  Offsets: {[hex(o) for o in offsets_for_icon]}")
            
            # Check data size for each segment
            for seg in range(12):
                seg_offset = offsets_for_icon[seg]
                if seg + 1 < 12:
                    next_seg_offset = offsets_for_icon[seg + 1]
                else:
                    next_seg_offset = offsets[base + 12] if base + 12 < len(offsets) else None
                
                if next_seg_offset is None:
                    print(f"  Segment {seg:2d}: offset=0x{seg_offset:X}, size=unknown")
                else:
                    size = next_seg_offset - seg_offset
                    print(f"  Segment {seg:2d}: offset=0x{seg_offset:X}, size={size:4d} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
