"""Export FDICON.B24 icons - try RAW pixel data without compression."""

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

def export_icons(fdicon_path, output_dir, max_icons=5):
    """Export icons trying RAW data."""
    
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
    
    # Palette
    palette = [(i, i, i) for i in range(256)]
    
    directions = ['Front', 'Left', 'Back', 'Right']
    frames = ['Frame0', 'Frame1', 'Frame2']
    
    for icon_id in range(min(max_icons, total_icons)):
        icon_dir = os.path.join(output_dir, f"icon_{icon_id:03d}")
        os.makedirs(icon_dir, exist_ok=True)
        
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        icon_data = data[data_start:data_end]
        
        print(f"\nIcon {icon_id}:")
        
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_data = icon_data[seg_start:seg_end]
            
            if len(seg_data) == 0:
                continue
            
            dir_name = directions[seg_idx // 3]
            frame_name = frames[seg_idx % 3]
            
            # Analyze first 20 bytes to find pattern
            first_bytes = seg_data[:20].hex(' ')
            
            # Check for header pattern
            # Maybe first 2-4 bytes are header (width, height, etc.)
            # Rest is pixel data
            
            # Try different header sizes
            for header_size in [0, 2, 4, 6]:
                pixel_data = seg_data[header_size:]
                
                # Try to fit to common sizes
                for width, height in [(24, 24), (16, 16), (32, 32), (24, 16), (16, 24)]:
                    if len(pixel_data) >= width * height:
                        # Take first width*height bytes
                        pixels = pixel_data[:width * height]
                        non_zero = sum(1 for b in pixels if b != 0)
                        
                        if non_zero > width * height * 0.1:  # At least 10% non-zero
                            filename = f"{dir_name}_{frame_name}_{width}x{height}_hdr{header_size}.bmp"
                            filepath = os.path.join(icon_dir, filename)
                            write_bmp(filepath, pixels, width, height, palette)
                            
                            if header_size == 0 and seg_idx == 0:
                                print(f"  {dir_name} {frame_name}: saved as {width}x{height} (no header, {non_zero} non-zero)")
                            break
            
            # Save raw data for manual inspection
            if seg_idx == 0:
                raw_file = os.path.join(icon_dir, f"{dir_name}_{frame_name}_{len(seg_data)}bytes.raw")
                with open(raw_file, 'wb') as f:
                    f.write(seg_data)

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\fdicon_icons'
    
    export_icons(fdicon_path, output_dir, max_icons=3)
    print(f"\nDone! Check: {output_dir}")
