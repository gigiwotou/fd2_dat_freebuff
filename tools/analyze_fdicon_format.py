"""Analyze FDICON.B24 segment data to understand the exact encoding format."""

import struct
from PIL import Image

def analyze_segment_structure(seg_data):
    """Analyze segment data structure in detail."""
    print(f"\nSegment size: {len(seg_data)} bytes")
    print(f"First 100 bytes: {' '.join(f'{b:02x}' for b in seg_data[:100])}")
    
    # Analyze byte frequency
    freq = {}
    for b in seg_data:
        freq[b] = freq.get(b, 0) + 1
    
    # Top 10 most frequent bytes
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\nTop 10 most frequent bytes:")
    for byte, count in sorted_freq:
        print(f"  0x{byte:02x}: {count} times")
    
    # Check if it follows the pattern observed:
    # c4 05 fe - possibly (command, count, value)
    # c1 05 fe - possibly (command, count, value)
    
    print(f"\nAnalyzing command patterns:")
    for i in range(0, min(30, len(seg_data))):
        b = seg_data[i]
        if b >= 0xc0:
            print(f"  [{i}] 0x{b:02x}: High command (>=0xc0)")
        elif b >= 0x80:
            print(f"  [{i}] 0x{b:02x}: Mid command (0x80-0xbf)")
        elif b == 0xfe:
            print(f"  [{i}] 0x{b:02x}: Skip marker")
        else:
            print(f"  [{i}] 0x{b:02x}: Value ({b})")

def decode_fdicon_v2(seg_data, width=24, height=24):
    """
    Decode FDICON.B24 segment with improved algorithm.
    
    Based on the pattern observed:
    - 0xc4 05 fe: command 0xc4, count 5, value 0xfe (skip)
    - 0xc1 05 fe: command 0xc1, count 5, value 0xfe (skip)
    - Looks like RLE encoding
    """
    pixels = bytearray(width * height)
    src_ptr = 0
    dst_ptr = 0
    total_pixels = width * height
    
    while src_ptr < len(seg_data) and dst_ptr < total_pixels:
        cmd = seg_data[src_ptr]
        src_ptr += 1
        
        if cmd == 0xd5:
            # End marker
            break
        elif cmd == 0xfe:
            # Skip pixel (transparent)
            dst_ptr += 1
        elif cmd == 0xd7:
            # Special marker, skip
            pass
        elif cmd >= 0xc0:
            # RLE run command
            # 0xc4 -> count = 4, 0xc1 -> count = 1, etc.
            count = cmd - 0xc0
            if count == 0:
                count = 256  # Special case
            
            # Get next byte (value or skip indicator)
            if src_ptr < len(seg_data):
                value = seg_data[src_ptr]
                src_ptr += 1
                
                if value == 0xfe:
                    # Skip pixels (transparent)
                    dst_ptr += count
                else:
                    # Fill with value
                    for i in range(count):
                        if dst_ptr < total_pixels:
                            pixels[dst_ptr] = value
                        dst_ptr += 1
        elif cmd >= 0x80:
            # Raw pixel copy
            count = cmd - 0x80
            if count == 0:
                count = 256
            
            for i in range(count):
                if src_ptr < len(seg_data) and dst_ptr < total_pixels:
                    pixels[dst_ptr] = seg_data[src_ptr]
                    src_ptr += 1
                dst_ptr += 1
        else:
            # Single pixel value
            if dst_ptr < total_pixels:
                pixels[dst_ptr] = cmd
            dst_ptr += 1
    
    return bytes(pixels)

def test_all_icons():
    """Test decoding multiple icons."""
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    # Read offsets
    offsets = []
    for i in range(140 * 12 + 4):
        offset = struct.unpack('<I', data[6 + i*4:6 + (i+1)*4])[0]
        offsets.append(offset)
    
    print(f"Testing first 5 icons...\n")
    
    for icon_id in range(5):
        print(f"{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        # Get all 12 segments
        seg0_start = offsets[icon_id * 12]
        seg0_end = offsets[icon_id * 12 + 1]
        seg0_data = data[seg0_start:seg0_end]
        
        # Analyze first segment
        analyze_segment_structure(seg0_data)
        
        # Decode with new algorithm
        pixels = decode_fdicon_v2(seg0_data, 24, 24)
        non_trans = sum(1 for b in pixels if b != 0)
        print(f"\nDecoded: {non_trans} non-transparent pixels")
        
        if non_trans > 0:
            img = Image.new('P', (24, 24))
            img.putdata(pixels)
            pal = []
            for i in range(256):
                pal.extend([i, i, i])
            img.putpalette(pal)
            img.save(f"fd2_icon_{icon_id}_decoded.bmp")
            print(f"Saved fd2_icon_{icon_id}_decoded.bmp")

if __name__ == '__main__':
    test_all_icons()
