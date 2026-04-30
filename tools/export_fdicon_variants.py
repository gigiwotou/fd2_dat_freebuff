"""Export FDICON.B24 icons - try different header sizes and dimensions."""

import struct
import os

def write_bmp(filename, pixels, width, height, palette=None):
    """Write pixel data as BMP file (8-bit indexed)."""
    row_size = (width + 3) & ~3
    pixel_data_size = row_size * height
    file_size = 54 + (256 * 4) + pixel_data_size
    
    bmp_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54 + (256 * 4))
    dib_header = struct.pack('<IIIHHIIIIII', 40, width, height, 1, 8, 0, pixel_data_size, 2835, 2835, 256, 0)
    
    palette_data = bytearray()
    if palette:
        for i in range(256):
            r, g, b = palette[i] if i < len(palette) else (0, 0, 0)
            palette_data.extend([b, g, r, 0])
    else:
        for i in range(256):
            palette_data.extend([i, i, i, 0])
    
    pixel_data = bytearray()
    for y in range(height - 1, -1, -1):
        row_start = y * width
        pixel_data.extend(pixels[row_start:row_start + width])
        padding = row_size - width
        if padding > 0:
            pixel_data.extend(b'\x00' * padding)
    
    with open(filename, 'wb') as f:
        f.write(bmp_header)
        f.write(dib_header)
        f.write(palette_data)
        f.write(pixel_data)

def export_all_variants(fdicon_path, output_dir, max_icons=3):
    """Export icons trying different header sizes and dimensions."""
    
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
    
    palette = [(i, i, i) for i in range(256)]
    
    directions = ['Front', 'Left', 'Back', 'Right']
    frames = ['Frame0', 'Frame1', 'Frame2']
    
    # Try different header sizes and dimensions
    header_sizes = [0, 2, 4, 6, 8]
    dimensions = [
        (24, 24), (16, 16), (32, 32),
        (16, 24), (24, 16),
        (16, 32), (32, 16),
        (20, 20), (24, 20), (20, 24),
        (28, 28), (32, 24), (24, 32),
    ]
    
    for icon_id in range(min(max_icons, total_icons)):
        icon_dir = os.path.join(output_dir, f"icon_{icon_id:03d}")
        os.makedirs(icon_dir, exist_ok=True)
        
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        icon_data = data[data_start:data_end]
        
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_data = icon_data[seg_start:seg_end]
            
            if len(seg_data) == 0:
                continue
            
            dir_name = directions[seg_idx // 3]
            frame_name = frames[seg_idx % 3]
            
            seg_dir = os.path.join(icon_dir, f"{dir_name}_{frame_name}")
            os.makedirs(seg_dir, exist_ok=True)
            
            # Save raw data
            raw_file = os.path.join(seg_dir, f"raw_{len(seg_data)}bytes.dat")
            with open(raw_file, 'wb') as f:
                f.write(seg_data)
            
            # Try each header size and dimension combination
            found_matches = []
            for header_size in header_sizes:
                if header_size >= len(seg_data):
                    continue
                
                pixel_data = seg_data[header_size:]
                
                for width, height in dimensions:
                    if width * height == len(pixel_data):
                        # Exact match
                        filename = f"{width}x{height}_hdr{header_size}.bmp"
                        filepath = os.path.join(seg_dir, filename)
                        write_bmp(filepath, pixel_data, width, height, palette)
                        non_zero = sum(1 for b in pixel_data if b != 0)
                        found_matches.append((width, height, header_size, non_zero))
            
            if found_matches:
                print(f"\n{dir_name} {frame_name} ({len(seg_data)} bytes):")
                for w, h, hdr, nz in found_matches:
                    print(f"  {w}x{h} (header={hdr}): {nz} non-zero pixels")
            else:
                print(f"\n{dir_name} {frame_name} ({len(seg_data)} bytes): no exact match")
            
            # Stop after first segment if we found matches
            if seg_idx == 0 and found_matches:
                break

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\fdicon_icons'
    
    export_all_variants(fdicon_path, output_dir, max_icons=2)
    print(f"\nDone! Check: {output_dir}")
