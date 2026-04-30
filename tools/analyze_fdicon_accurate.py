"""Analyze and test FDICON.B24 icon segment decoding with accurate algorithm."""

import struct
from PIL import Image
import sys

def decode_icon_segment_v2(seg_data, width=24, height=24):
    """
    Decode a single icon segment using the RLE algorithm.
    
    Based on detailed analysis of the compressed data patterns:
    - Each command byte uses bits to determine operation type
    - Similar to the RLE format used in other FD2 resources
    """
    pixels = bytearray(width * height)
    src = bytearray(seg_data)
    src_ptr = 0
    x, y = 0, 0
    
    while y < height and src_ptr < len(src):
        cmd = src[src_ptr]
        src_ptr += 1
        
        # Extract command bits
        bit7 = (cmd >> 7) & 1
        bit6 = (cmd >> 6) & 1
        value = cmd & 0x3F
        
        if bit7 and bit6:
            # 11xxxxxx: Run of transparent/skip pixels
            for i in range(value):
                x += 1
                if x >= width:
                    x = 0
                    y += 1
                    if y >= height:
                        break
        elif bit7 and not bit6:
            # 10xxxxxx: Run of solid color pixels
            if src_ptr < len(src):
                color = src[src_ptr]
                src_ptr += 1
                for i in range(value):
                    if y < height and x < width:
                        pixels[y * width + x] = color
                    x += 1
                    if x >= width:
                        x = 0
                        y += 1
                        if y >= height:
                            break
        elif not bit7 and bit6:
            # 01xxxxxx: Copy raw pixels
            count = value
            for i in range(count):
                if src_ptr < len(src) and y < height and x < width:
                    pixels[y * width + x] = src[src_ptr]
                    src_ptr += 1
                x += 1
                if x >= width:
                    x = 0
                    y += 1
                    if y >= height:
                        break
        else:
            # 00xxxxxx: Another variant (possibly fill or special)
            if src_ptr < len(src):
                color = src[src_ptr]
                src_ptr += 1
                for i in range(value):
                    if y < height and x < width:
                        pixels[y * width + x] = color
                    x += 1
                    if x >= width:
                        x = 0
                        y += 1
                        if y >= height:
                            break
    
    return bytes(pixels)

def analyze_icon_decoding_accurate(fdicon_path):
    """Analyze icon decoding with accurate algorithm."""
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table
    offsets = []
    for i in range(140 * 12 + 4):
        offset = struct.unpack('<I', data[6 + i*4:6 + (i+1)*4])[0]
        offsets.append(offset)
    
    print(f"Total icons in table: 140")
    
    # Test first 5 icons with all 12 segments
    for icon_id in range(min(5, 140)):
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        icon_data = data[data_start:data_end]
        
        # Decode each segment
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_data = icon_data[seg_start:seg_end]
            
            if len(seg_data) == 0:
                continue
            
            # Try decoding with different dimensions
            for width, height in [(24, 24), (16, 16), (32, 32)]:
                try:
                    pixels = decode_icon_segment_v2(seg_data, width, height)
                    non_trans = sum(1 for b in pixels if b != 0)
                    
                    if 50 < non_trans < width * height * 0.9:  # Reasonable icon
                        print(f"  Segment {seg_idx:2d}: {width}x{height}, {non_trans} pixels")
                        
                        # Save first segment of first few icons as image
                        if icon_id < 3 and seg_idx == 0 and width == 24:
                            img = Image.new('P', (width, height))
                            img.putdata(pixels)
                            # Create grayscale palette
                            pal = []
                            for i in range(256):
                                pal.extend([i, i, i])
                            img.putpalette(pal)
                            img.save(f"icon_{icon_id}_seg{seg_idx}_{width}x{height}.bmp")
                        break
                except Exception as e:
                    continue

def analyze_compression_pattern(fdicon_path):
    """Detailed analysis of compression pattern."""
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    # Read first icon, first segment
    offset = struct.unpack('<I', data[6:10])[0]
    next_offset = struct.unpack('<I', data[10:14])[0]
    seg_data = data[offset:next_offset]
    
    print(f"\n{'='*60}")
    print(f"Compression Pattern Analysis")
    print(f"{'='*60}")
    print(f"First segment: {len(seg_data)} bytes")
    
    # Analyze byte patterns
    print(f"\nFirst 50 bytes (hex):")
    for i in range(0, min(50, len(seg_data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in seg_data[i:i+16])
        print(f"  {i:04x}: {hex_str}")
    
    # Analyze bit7/bit6 distribution
    bit7_6_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for b in seg_data:
        bits = (b >> 6) & 3
        bit7_6_counts[bits] += 1
    
    print(f"\nBit7:Bit6 distribution:")
    print(f"  00 (fill): {bit7_6_counts[0]}")
    print(f"  01 (copy): {bit7_6_counts[1]}")
    print(f"  10 (run):  {bit7_6_counts[2]}")
    print(f"  11 (skip): {bit7_6_counts[3]}")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    analyze_compression_pattern(fdicon_path)
    print(f"\n{'='*60}")
    print("Testing icon decoding...")
    print(f"{'='*60}")
    analyze_icon_decoding_accurate(fdicon_path)
