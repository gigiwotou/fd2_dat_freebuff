"""Deep analysis of FDICON.B24 segment data format.

Segments are ~400-500 bytes, not matching simple dimensions.
This suggests RLE compression or variable-length encoding.
"""

import struct
import sys

def analyze_icon_segments(fdicon_path, icon_id):
    data = open(fdicon_path, 'rb').read()
    offset_table = struct.unpack('<1680I', data[6:6+6720])
    
    base_idx = icon_id * 12
    data_start = offset_table[base_idx]
    data_end = offset_table[(icon_id + 1) * 12] if icon_id < 139 else len(data)
    icon_data = data[data_start:data_end]
    
    print(f"\n{'='*60}")
    print(f"Icon {icon_id}: data_start={data_start}, data_end={data_end}, size={len(icon_data)}")
    print(f"{'='*60}")
    
    for seg in range(12):
        seg_start = offset_table[base_idx + seg] - data_start
        seg_end = (offset_table[base_idx + seg + 1] - data_start) if seg < 11 else len(icon_data)
        seg_size = seg_end - seg_start
        
        if seg_start >= len(icon_data) or seg_size <= 0:
            print(f"  Segment {seg}: SKIP (start={seg_start}, size={seg_size})")
            continue
        
        seg_data = icon_data[seg_start:seg_start + seg_size]
        
        # Analyze data patterns
        # Check if it looks like RLE
        rle_like = False
        for i in range(0, min(len(seg_data)-1, 100), 2):
            if seg_data[i] == seg_data[i+1]:
                rle_like = True
                break
        
        # Check entropy (unique byte count)
        unique_bytes = len(set(seg_data))
        
        # Look for 0x00 or 0xFF patterns
        zero_count = seg_data.count(0)
        ff_count = seg_data.count(0xFF)
        
        # First 20 bytes hex dump
        hex_sample = ' '.join(f'{b:02x}' for b in seg_data[:20])
        
        # Try to detect if it's run-length encoded
        # RLE usually has pairs: (count, value) or (value, count)
        
        print(f"  Segment {seg}: size={seg_size:4d}, unique={unique_bytes:3d}, zeros={zero_count:4d}, 0xFF={ff_count:4d}, rle_like={rle_like}")
        print(f"    First 20 bytes: {hex_sample}")
        
        # Try to decompress as simple RLE (count, value)
        if rle_like:
            try_rle_count = 0
            rle_pixels = []
            i = 0
            while i < len(seg_data) - 1:
                if i + 1 < len(seg_data):
                    count = seg_data[i]
                    value = seg_data[i+1]
                    if count <= 50:  # Reasonable RLE count
                        rle_pixels.extend([value] * count)
                        try_rle_count += 1
                    i += 2
                else:
                    break
            
            # Check if RLE decoded to reasonable image size
            if len(rle_pixels) > 0:
                sqrt_size = int(len(rle_pixels) ** 0.5)
                if sqrt_size * sqrt_size == len(rle_pixels):
                    print(f"    RLE decode: {len(rle_pixels)} pixels -> {sqrt_size}x{sqrt_size}")
                elif len(rle_pixels) in [256, 576, 1024, 1536, 2304, 3072, 4096]:
                    print(f"    RLE decode: {len(rle_pixels)} pixels (common size)")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    # Analyze first 10 icons in detail
    for i in range(10):
        analyze_icon_segments(fdicon_path, i)
    
    # Also check a larger icon
    analyze_icon_segments(fdicon_path, 39)  # This had 24-byte segments
