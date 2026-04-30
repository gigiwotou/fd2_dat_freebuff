"""Test RLE decoder for FIGANI.DAT sprites."""

import struct
import sys
from PIL import Image

def rle_decode(src_data, img_width, img_height):
    """
    RLE decoder based on IDA sub_4E98D analysis.
    
    Command encoding:
    - value & 0x80: Command A
      - (value << 1) & 0x80: Skip (transparent)
      - else: Copy from source
    - value & 0x80 == 0: Command B
      - (value << 1) & 0x80: Fill with value
      - else: Fill alternating
    """
    dest = [0] * (img_width * img_height)
    src_pos = 0
    dst_pos = 0
    
    for y in range(img_height):
        row_start = y * img_width
        remaining = img_width
        
        while remaining > 0 and src_pos < len(src_data):
            value = src_data[src_pos]
            src_pos += 1
            count = value + 1
            
            if value & 0x80:
                # Command A
                if (value << 1) & 0x80:
                    # Skip (transparent)
                    skip = min(count, remaining)
                    dst_pos += skip
                    remaining -= skip
                else:
                    # Copy from source
                    copy_len = min(count, remaining)
                    for i in range(copy_len):
                        dest[row_start + dst_pos] = src_data[src_pos]
                        src_pos += 1
                        dst_pos += 1
                    remaining -= copy_len
            else:
                # Command B
                if (value << 1) & 0x80:
                    # Fill with value
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    fill_len = min(count, remaining)
                    for i in range(fill_len):
                        dest[row_start + dst_pos] = fill_value
                        dst_pos += 1
                    remaining -= fill_len
                else:
                    # Fill alternating
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    written = 0
                    for i in range(count):
                        if dst_pos < remaining:
                            dest[row_start + dst_pos] = fill_value
                            dst_pos += 2
                            written += 2
                        else:
                            break
                    remaining -= written
    
    return bytes(dest)

def decode_sprite(figani_path, resource_index, output_path):
    """Decode a single sprite resource and save as PNG."""
    data = open(figani_path, 'rb').read()
    
    # Parse format 2 offset table
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data):
            break
        offsets.append(offset)
        pos += 4
    
    if resource_index >= len(offsets) - 1:
        print(f"Resource {resource_index} out of range (max {len(offsets)-2})")
        return
    
    # Extract resource data
    start = offsets[resource_index]
    end = offsets[resource_index + 1] if resource_index < len(offsets) - 1 else len(data)
    res_data = data[start:end]
    
    if len(res_data) < 12:
        print(f"Resource {resource_index}: too small ({len(res_data)} bytes)")
        return
    
    # Parse header
    header = struct.unpack('<I', res_data[0:4])[0]
    width = struct.unpack('<H', res_data[4:6])[0]
    height = struct.unpack('<H', res_data[6:8])[0]
    
    print(f"Resource {resource_index}:")
    print(f"  Header: 0x{header:08X}")
    print(f"  Dimensions: {width}x{height}")
    print(f"  Size: {len(res_data)} bytes")
    
    # Count frame offsets
    frame_offsets = []
    offset = 12
    while offset + 4 <= len(res_data):
        frame_off = struct.unpack('<I', res_data[offset:offset+4])[0]
        if frame_off >= len(res_data) or frame_off < 12:
            break
        frame_offsets.append(frame_off)
        offset += 4
    
    print(f"  Frame count: {len(frame_offsets)}")
    print(f"  Frame offsets: {frame_offsets[:5]}...")
    
    # Decode first frame
    if len(frame_offsets) > 0:
        frame_start = frame_offsets[0]
        if len(frame_offsets) > 1:
            frame_end = frame_offsets[1]
        else:
            frame_end = len(res_data)
        
        frame_data = res_data[frame_start:frame_end]
        print(f"  Frame 0: offset={frame_start}, size={len(frame_data)}")
        
        # Try RLE decode
        try:
            pixels = rle_decode(frame_data, width, height)
            img = Image.frombytes('P', (width, height), pixels)
            
            # Create a simple palette for visualization
            palette = []
            for i in range(256):
                palette.extend([i, i, i])
            img.putpalette(palette)
            
            img.save(output_path)
            print(f"  Saved to {output_path}")
        except Exception as e:
            print(f"  Decode failed: {e}")

if __name__ == '__main__':
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\sprites'
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Test first few sprites
    for i in [0, 1, 3, 4, 6]:
        output_path = os.path.join(output_dir, f"sprite_{i}.png")
        decode_sprite(figani_path, i, output_path)
        print()
