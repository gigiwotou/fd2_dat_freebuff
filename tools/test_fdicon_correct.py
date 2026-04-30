"""Test FDICON.B24 icon decoding with correct RLE algorithm."""

import struct
import sys
from PIL import Image

def decode_fdicon_segment(seg_data, width=24, height=24):
    """
    Decode a FDICON.B24 segment using RLE algorithm.
    
    Based on analysis of actual FDICON.B24 data:
    - 0xfe: Skip/transparent pixel
    - 0xd0-0xd7: Row markers
    - 0xc0-0xff: Run encoding (count = byte - 0xc0, next byte = color)
    - 0x80-0xbf: Raw pixel copy (count = byte - 0x80)
    - 0x00-0x7f: Single pixel value
    """
    pixels = bytearray(width * height)
    x, y = 0, 0
    src_ptr = 0
    
    while y < height and src_ptr < len(seg_data):
        cmd = seg_data[src_ptr]
        src_ptr += 1
        
        if cmd == 0xfe:
            # Transparent pixel
            x += 1
            if x >= width:
                x = 0
                y += 1
        elif cmd >= 0xd0 and cmd <= 0xd7:
            # Row marker
            y += 1
            x = 0
        elif cmd >= 0xc0:
            # Run encoding
            count = cmd - 0xc0 + 1
            if src_ptr < len(seg_data):
                color = seg_data[src_ptr]
                src_ptr += 1
                for i in range(count):
                    if y < height and x < width:
                        pixels[y * width + x] = color
                    x += 1
                    if x >= width:
                        x = 0
                        y += 1
        elif cmd >= 0x80:
            # Raw pixel copy
            count = cmd - 0x80 + 1
            for i in range(count):
                if src_ptr < len(seg_data) and y < height and x < width:
                    pixels[y * width + x] = seg_data[src_ptr]
                    src_ptr += 1
                x += 1
                if x >= width:
                    x = 0
                    y += 1
        else:
            # Single pixel
            if x < width and y < height:
                pixels[y * width + x] = cmd
            x += 1
            if x >= width:
                x = 0
                y += 1
    
    return bytes(pixels)

def test_icon_decoding():
    """Test icon decoding from FDICON.B24."""
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 size: {len(data)} bytes")
    
    # Read offset table
    offsets = []
    for i in range(140 * 12 + 4):
        offset = struct.unpack('<I', data[6 + i*4:6 + (i+1)*4])[0]
        offsets.append(offset)
    
    print(f"Total icons: 140")
    
    # Test first 10 icons
    for icon_id in range(min(10, 140)):
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        # Get all 12 segments
        data_start = offsets[icon_id * 12]
        data_end = offsets[icon_id * 12 + 12]
        icon_data = data[data_start:data_end]
        
        # Decode segment 0 (front, frame 0)
        seg0_start = offsets[icon_id * 12] - data_start
        seg0_end = offsets[icon_id * 12 + 1] - data_start
        seg0_data = icon_data[seg0_start:seg0_end]
        
        if len(seg0_data) == 0:
            print(f"  Segment 0: empty")
            continue
        
        print(f"  Segment 0: {len(seg0_data)} bytes")
        
        # Try decoding with 24x24
        pixels = decode_fdicon_segment(seg0_data, 24, 24)
        non_zero = sum(1 for b in pixels if b != 0)
        
        print(f"  Decoded 24x24: {non_zero} non-transparent pixels")
        
        if non_zero > 50:  # Reasonable icon
            # Save as image
            img = Image.new('P', (24, 24))
            img.putdata(pixels)
            # Create palette
            pal = []
            for i in range(256):
                pal.extend([i, i, i])
            img.putpalette(pal)
            img.save(f"fd2_icon_{icon_id}_seg0_24x24.bmp")
            print(f"  Saved: fd2_icon_{icon_id}_seg0_24x24.bmp")

if __name__ == '__main__':
    test_icon_decoding()
