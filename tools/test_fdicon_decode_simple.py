"""Test FDICON.B24 icon decoding and rendering."""

import struct
from PIL import Image

def decode_icon_segment(seg_data, width=24, height=24):
    """Decode a single icon segment using RLE-like algorithm."""
    pixels = bytearray(width * height)
    src = seg_data
    src_ptr = 0
    x, y = 0, 0
    
    while y < height and src_ptr < len(src):
        cmd = src[src_ptr]
        src_ptr += 1
        
        # Analyze command byte
        if cmd == 0xfe:
            # High frequency byte - likely "skip" or transparent
            x += 1
        elif cmd == 0xd7:
            # Special marker
            continue
        elif cmd >= 0xd0:
            # High value commands
            if cmd == 0xd5:
                # Possibly end of segment
                break
            elif cmd >= 0xd0:
                # Run command
                count = cmd & 0x0f
                if src_ptr < len(src):
                    value = src[src_ptr]
                    src_ptr += 1
                    for i in range(count):
                        if y < height and x < width:
                            pixels[y * width + x] = value
                        x += 1
                        if x >= width:
                            x = 0
                            y += 1
        elif cmd >= 0xc0:
            # Copy command
            count = cmd & 0x3f
            for i in range(count):
                if src_ptr < len(src) and y < height and x < width:
                    pixels[y * width + x] = src[src_ptr]
                    src_ptr += 1
                x += 1
                if x >= width:
                    x = 0
                    y += 1
        else:
            # Low value - likely single pixel
            if y < height and x < width:
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
    
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table
    offsets = []
    for i in range(140 * 12 + 4):
        offset = struct.unpack('<I', data[6 + i*4:6 + (i+1)*4])[0]
        offsets.append(offset)
    
    print(f"Total offsets: {len(offsets)}")
    
    # Test first 3 icons
    for icon_id in range(3):
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        # Get segment 0 (Front, frame 0)
        seg_start = offsets[icon_id * 12]
        seg_end = offsets[icon_id * 12 + 1]
        seg_size = seg_end - seg_start
        
        print(f"Segment 0: {seg_size} bytes")
        
        # Extract segment data
        seg_data = data[seg_start:seg_end]
        
        # Print first 50 bytes
        print(f"First 50 bytes: {' '.join(f'{b:02x}' for b in seg_data[:50])}")
        
        # Try decoding
        pixels = decode_icon_segment(seg_data, 24, 24)
        
        # Count non-zero pixels
        non_zero = sum(1 for b in pixels if b != 0)
        print(f"Decoded {24}x{24}: {non_zero} non-zero pixels")
        
        # Save as image for inspection
        if non_zero > 0:
            img = Image.new('P', (24, 24))
            img.putdata(pixels)
            # Create grayscale palette for visualization
            palette = []
            for i in range(256):
                palette.extend([i, i, i])
            img.putpalette(palette)
            img.save(f"icon_{icon_id}_seg0.bmp")
            print(f"Saved icon_{icon_id}_seg0.bmp")

if __name__ == '__main__':
    test_icon_decoding()
