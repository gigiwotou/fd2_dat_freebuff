"""Analyze FIGANI.DAT sprite structure."""

import struct
import sys

def analyze_figani(figani_path):
    data = open(figani_path, 'rb').read()
    print(f"FIGANI.DAT file size: {len(data)} bytes")
    
    # Check header format
    print(f"First 20 bytes: {data[:20].hex(' ')}")
    print(f"Header (6 bytes): {data[:6].hex(' ')}")
    
    # Try Format 2 parsing (offset table from byte 6)
    if data[:6] == b'LLLLLL':
        print("Format 2 detected (LLLLLL header)")
        
        # Read offset table
        offsets = []
        pos = 6
        while pos + 4 <= len(data):
            offset = struct.unpack('<I', data[pos:pos+4])[0]
            if offset > len(data):
                break
            offsets.append(offset)
            pos += 4
        
        print(f"\nOffset table: {len(offsets)} resources")
        print(f"First 10 offsets: {offsets[:10]}")
        
        # Analyze first few sprites
        for i in range(min(5, len(offsets) - 1)):
            start = offsets[i]
            end = offsets[i + 1] if i < len(offsets) - 1 else len(data)
            sprite_data = data[start:end]
            size = len(sprite_data)
            
            # Check if it has width/height header
            if size >= 4:
                width = struct.unpack('<H', sprite_data[0:2])[0]
                height = struct.unpack('<H', sprite_data[2:4])[0]
                
                print(f"\nSprite {i}: offset={start}, size={size}")
                print(f"  Possible dimensions: {width}x{height}")
                print(f"  Data size for pixels: {size - 4}")
                print(f"  First 20 bytes: {sprite_data[4:24].hex(' ')}")
                
                # Check RLE patterns
                rle_bytes = sprite_data[4:]
                high_bit_count = sum(1 for b in rle_bytes[:100] if b & 0x80)
                print(f"  High bit ratio: {high_bit_count}/100 = {high_bit_count}%")
    else:
        print("Unknown format, analyzing as raw data")

if __name__ == '__main__':
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    if len(sys.argv) > 1:
        figani_path = sys.argv[1]
    
    analyze_figani(figani_path)
