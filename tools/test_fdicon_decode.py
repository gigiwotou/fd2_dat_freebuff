"""Test FDICON.B24 icon decoding and rendering."""

import struct
import sys

def decode_icon_segment(seg_data, width=24, height=24):
    """
    Decode a single icon segment from FDICON.B24.
    
    Based on analysis of actual data patterns:
    - 0xfe appears to be a "skip" command (transparent)
    - Other bytes may be RLE encoded commands
    
    Pattern observed in data:
    c5 04 6f - could be (count, value, color) or similar
    """
    pixels = bytearray(width * height)
    src_ptr = 0
    dst = 0
    dst_end = width * height
    
    while src_ptr < len(seg_data) and dst < dst_end:
        cmd = seg_data[src_ptr]
        src_ptr += 1
        
        if cmd == 0xfe:
            # Skip command - skip next pixel (transparent)
            dst += 1
        elif cmd & 0x80:
            # High bit set - likely a command
            if cmd == 0xd7:
                # Special marker, skip
                continue
            elif cmd & 0x40:
                # 0xC0-0xDF range: command with count
                count = cmd & 0x3F
                if src_ptr < len(seg_data):
                    value = seg_data[src_ptr]
                    src_ptr += 1
                    for i in range(count):
                        if dst < dst_end:
                            pixels[dst] = value
                        dst += 1
            else:
                # 0x80-0xBF: possibly copy raw bytes
                count = cmd & 0x7F
                for i in range(count):
                    if src_ptr < len(seg_data) and dst < dst_end:
                        pixels[dst] = seg_data[src_ptr]
                        src_ptr += 1
                        dst += 1
        else:
            # Low byte (0x00-0x7F): likely a palette index
            if dst < dst_end:
                pixels[dst] = cmd
            dst += 1
    
    # Count non-zero (non-transparent) pixels
    non_transparent = sum(1 for b in pixels if b != 0)
    return bytes(pixels), non_transparent

def analyze_icon_decoding(fdicon_path):
    """Analyze icon decoding with different algorithms."""
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table
    offsets = []
    for i in range(140 * 12 + 4):
        offset = struct.unpack('<I', data[6 + i*4:6 + (i+1)*4])[0]
        offsets.append(offset)
    
    # Test first 3 icons, first segment
    for icon_id in range(min(3, 140)):
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        # Get segment 0 (Front, Frame 0)
        seg_start = offsets[icon_id * 12]
        seg_end = offsets[icon_id * 12 + 1]
        seg_data = data[seg_start:seg_end]
        
        print(f"  Segment 0 size: {len(seg_data)} bytes")
        
        # Try different width/height combinations
        for width, height in [(24, 24), (16, 16), (32, 32)]:
            pixels, non_trans = decode_icon_segment(seg_data, width, height)
            if non_trans > 0:
                print(f"  Decoded {width}x{height}: {non_trans} non-zero pixels")
                
                # Save as raw for inspection
                with open(f"icon_{icon_id}_{width}x{height}.raw", 'wb') as f:
                    f.write(pixels)

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    analyze_icon_decoding(fdicon_path)
