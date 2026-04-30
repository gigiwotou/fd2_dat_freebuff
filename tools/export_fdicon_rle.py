"""Export FDICON.B24 icons using RLE decoding from IDA sub_4E98D."""

import struct
import os
from PIL import Image

def decode_rle_sub_4E98D(seg_data, width=24, height=24, palette_offset=-1):
    """
    Decode RLE compressed sprite data using algorithm from IDA sub_4E98D.
    
    Algorithm from IDA analysis:
    - Read command byte
    - Check carry flag after left shift (bit 7)
    - Based on bits 7 and 6, determine operation type:
      - 0xC0+ (bits 11): SKIP pixels (transparent)
      - 0x80-0xBF (bits 10): COPY raw bytes from source
      - 0x40-0x7F (bits 01): INTERLEAVED FILL (every 2nd pixel)
      - 0x00-0x3F (bits 00): FILL with single value
    - Count = (value & 0x3F) + 1
    """
    pixels = bytearray(width * height)
    src_ptr = 0
    dst_ptr = 0
    width_remaining = width
    
    for y in range(height):
        width_remaining = width
        dst_ptr = y * width
        
        while width_remaining > 0 and src_ptr < len(seg_data):
            value = seg_data[src_ptr]
            src_ptr += 1
            
            # Check bit 7 (carry flag after << 1)
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            count = (value & 0x3F) + 1
            
            if bit7 and bit6:
                # 0xC0+: SKIP pixels (transparent)
                if count > width_remaining:
                    count = width_remaining
                dst_ptr += count
                width_remaining -= count
            elif bit7 and not bit6:
                # 0x80-0xBF: COPY raw bytes from source
                if count > width_remaining:
                    count = width_remaining
                if src_ptr + count > len(seg_data):
                    break
                for i in range(count):
                    pixels[dst_ptr] = seg_data[src_ptr]
                    dst_ptr += 1
                    src_ptr += 1
                width_remaining -= count
            elif not bit7 and bit6:
                # 0x40-0x7F: INTERLEAVED FILL (every 2nd pixel)
                if src_ptr >= len(seg_data):
                    break
                fill_value = seg_data[src_ptr]
                src_ptr += 1
                
                if count > width_remaining:
                    count = width_remaining
                
                for i in range(count):
                    if dst_ptr < len(pixels):
                        pixels[dst_ptr] = fill_value
                    dst_ptr += 2
                    width_remaining -= 2
                    if width_remaining <= 0:
                        break
            else:
                # 0x00-0x3F: FILL with single value
                if src_ptr >= len(seg_data):
                    break
                fill_value = seg_data[src_ptr]
                src_ptr += 1
                
                if count > width_remaining:
                    count = width_remaining
                
                for i in range(count):
                    if dst_ptr < len(pixels):
                        pixels[dst_ptr] = fill_value
                    dst_ptr += 1
                width_remaining -= count
    
    return bytes(pixels)

def export_icons_rle(fdicon_path, output_dir, max_icons=5):
    """Export icons using RLE decoding from IDA sub_4E98D."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 size: {len(data)} bytes")
    
    # Read offsets
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    total_icons = len(offsets) // 12
    print(f"Total icons: {total_icons}")
    
    # Grayscale palette
    palette = [(i, i, i) for i in range(256)]
    
    directions = ['Front', 'Left', 'Back', 'Right']
    frames = ['Frame0', 'Frame1', 'Frame2']
    
    # Try different dimensions
    test_dims = [(24, 24), (32, 32), (16, 16), (24, 32), (32, 24), (20, 20)]
    
    for icon_id in range(min(max_icons, total_icons)):
        icon_dir = os.path.join(output_dir, f"icon_{icon_id:03d}")
        os.makedirs(icon_dir, exist_ok=True)
        
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        icon_data = data[data_start:data_end]
        
        print(f"\nIcon {icon_id}:")
        
        # Only test first segment for now
        seg_idx = 0
        seg_start = icon_offsets[seg_idx] - data_start
        seg_end = icon_offsets[seg_idx + 1] - data_start
        seg_data = icon_data[seg_start:seg_end]
        
        dir_name = directions[seg_idx // 3]
        frame_name = frames[seg_idx % 3]
        
        print(f"  {dir_name} {frame_name}: {len(seg_data)} bytes")
        
        # Try decoding with different dimensions
        for width, height in test_dims:
            pixels = decode_rle_sub_4E98D(seg_data, width, height)
            
            # Count non-transparent pixels
            non_trans = sum(1 for b in pixels if b != 0)
            total = width * height
            
            # Check if decoding looks reasonable (at least 10% non-transparent)
            if non_trans > total * 0.1:
                filename = f"{dir_name}_{frame_name}_{width}x{height}_rle.bmp"
                filepath = os.path.join(icon_dir, filename)
                
                img = Image.new('P', (width, height))
                img.putdata(pixels)
                pal = []
                for i in range(256):
                    pal.extend(palette[i] if i < len(palette) else (0,0,0))
                img.putpalette(pal)
                img.save(filepath)
                
                print(f"    {width}x{height}: {non_trans}/{total} non-zero -> saved")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\fdicon_icons'
    
    export_icons_rle(fdicon_path, output_dir, max_icons=3)
    print(f"\nDone! Check: {output_dir}")
