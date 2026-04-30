"""Test RLE decoder for FIGANI.DAT sprites - v2."""

import struct
import sys
from PIL import Image

def decode_sprite_v2(figani_path, resource_index, output_path):
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
    
    if len(res_data) < 16:
        print(f"Resource {resource_index}: too small ({len(res_data)} bytes)")
        return
    
    # Parse header as 4 DWORDs
    d0 = struct.unpack('<I', res_data[0:4])[0]
    d1 = struct.unpack('<I', res_data[4:8])[0]
    d2 = struct.unpack('<I', res_data[8:12])[0]
    d3 = struct.unpack('<I', res_data[12:16])[0]
    
    # Try to find width and height in the header
    # From analysis:
    # Resource 0: d0=262148 (0x40004), d1=0, d2=24, d3=5265
    # Resource 1: d0=720907 (0xB000B), d1=5, d2=52, d3=5293
    # Resource 4: d0=458759 (0x70007), d1=2, d2=36, d3=4320
    
    # Pattern: d0 = (frame_count << 16) | frame_count?
    #          d1 = small number (0, 5, 2)
    #          d2 = dimension-like (24, 52, 36)
    #          d3+ = frame offsets
    
    print(f"Resource {resource_index}:")
    print(f"  d0=0x{d0:08X} ({d0}), d1=0x{d1:08X} ({d1}), d2=0x{d2:08X} ({d2})")
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
    print(f"  Frame offsets: {frame_offsets[:5]}")
    
    # Try decoding first frame with different dimensions
    if len(frame_offsets) > 0:
        frame_start = frame_offsets[0]
        if len(frame_offsets) > 1:
            frame_end = frame_offsets[1]
        else:
            frame_end = len(res_data)
        
        frame_data = res_data[frame_start:frame_end]
        frame_size = len(frame_data)
        print(f"  Frame 0: offset={frame_start}, size={frame_size}")
        
        # Try common sprite dimensions
        for width in [16, 24, 32, 36, 48, 64]:
            for height in [16, 24, 32, 36, 48, 64]:
                if width * height == frame_size:
                    print(f"    Trying {width}x{height} (exact fit)")
                    pixels = bytes(frame_data)
                    img = Image.frombytes('P', (width, height), pixels)
                    palette = [i for i in range(768)]
                    img.putpalette(palette)
                    img.save(output_path.replace('.png', f'_{width}x{height}.png'))
                    break
        
        # Also try RLE decode with d2 as dimension
        if d2 > 0 and d2 < 100:
            for dim in [d2]:
                if frame_size > dim * dim:
                    print(f"    Trying RLE decode with {dim}x{dim}")
                    try:
                        pixels = rle_decode_simple(frame_data, dim, dim)
                        img = Image.frombytes('P', (dim, dim), pixels)
                        palette = [i for i in range(768)]
                        img.putpalette(palette)
                        img.save(output_path.replace('.png', f'_rle{dim}x{dim}.png'))
                        print(f"    Saved RLE {dim}x{dim}")
                    except Exception as e:
                        print(f"    RLE decode failed: {e}")

def rle_decode_simple(src_data, img_width, img_height):
    """Simplified RLE decoder."""
    dest = bytearray(img_width * img_height)
    src_pos = 0
    dst_pos = 0
    
    for y in range(img_height):
        row_start = y * img_width
        remaining = img_width
        
        while remaining > 0 and src_pos < len(src_data) - 1:
            value = src_data[src_pos]
            src_pos += 1
            count = value + 1
            
            if value & 0x80:
                if (value << 1) & 0x80:
                    # Skip
                    skip = min(count, remaining)
                    dst_pos += skip
                    remaining -= skip
                else:
                    # Copy
                    copy_len = min(count, remaining)
                    if src_pos + copy_len > len(src_data):
                        break
                    for i in range(copy_len):
                        dest[row_start + dst_pos] = src_data[src_pos]
                        src_pos += 1
                        dst_pos += 1
                    remaining -= copy_len
            else:
                if (value << 1) & 0x80:
                    # Fill
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    fill_len = min(count, remaining)
                    for i in range(fill_len):
                        dest[row_start + dst_pos] = fill_value
                        dst_pos += 1
                    remaining -= fill_len
                else:
                    # Alternating
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

if __name__ == '__main__':
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\sprites'
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Test first few sprites
    for i in [0, 1, 3, 4]:
        output_path = os.path.join(output_dir, f"sprite_{i}.png")
        decode_sprite_v2(figani_path, i, output_path)
        print()
