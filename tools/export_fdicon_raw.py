"""Export FDICON.B24 character icons to BMP images for testing.
Output to output/ directory.
Try both RAW and RLE decoded versions.
"""

import struct
import os
import sys

def write_bmp(filename, pixels, width, height, palette=None):
    """Write pixel data as BMP file (8-bit indexed)."""
    row_size = (width + 3) & ~3
    pixel_data_size = row_size * height
    file_size = 54 + (256 * 4) + pixel_data_size
    
    # BMP header
    bmp_header = struct.pack('<2sIHHI',
                            b'BM',
                            file_size,
                            0, 0,
                            54 + (256 * 4))
    
    # DIB header
    dib_header = struct.pack('<IIIHHIIIIII',
                            40, width, height,
                            1, 8, 0,
                            pixel_data_size,
                            2835, 2835,
                            256, 0)
    
    # Palette (256 colors)
    palette_data = bytearray()
    if palette:
        for i in range(256):
            if i < len(palette):
                r, g, b = palette[i]
                palette_data.extend([b, g, r, 0])
            else:
                palette_data.extend([0, 0, 0, 0])
    else:
        # Grayscale
        for i in range(256):
            palette_data.extend([i, i, i, 0])
    
    # Pixel data (bottom-up, padded rows)
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

def export_fdicon_icons_raw(fdicon_path, output_dir, max_icons=None):
    """Export icons from FDICON.B24 to BMP images (RAW pixel data)."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table (Format 2)
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
    
    # Grayscale palette for testing
    palette = [(i, i, i) for i in range(256)]
    
    # Direction and frame labels
    directions = ['Front', 'Left', 'Back', 'Right']
    frames = ['Frame0', 'Frame1', 'Frame2']
    
    # Export icons
    if max_icons is None:
        max_icons = total_icons
    else:
        max_icons = min(max_icons, total_icons)
    
    print(f"\nExporting {max_icons} icons to {output_dir}...")
    
    for icon_id in range(max_icons):
        icon_dir = os.path.join(output_dir, f"icon_{icon_id:03d}")
        os.makedirs(icon_dir, exist_ok=True)
        
        # Get 13 offsets for this icon (12 segments + 1 end marker)
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        icon_data = data[data_start:data_end]
        
        print(f"\nIcon {icon_id}:")
        
        # Export each segment as RAW data
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_data = icon_data[seg_start:seg_end]
            
            if len(seg_data) == 0:
                continue
            
            dir_idx = seg_idx // 3
            frame_idx = seg_idx % 3
            
            dir_name = directions[dir_idx]
            frame_name = frames[frame_idx]
            
            # Try different dimensions
            possible_sizes = [
                (24, 24), (16, 16), (32, 32), (24, 32), (32, 24),
                (20, 20), (24, 20), (20, 24)
            ]
            
            for width, height in possible_sizes:
                if len(seg_data) == width * height:
                    # Exact match - save as BMP
                    filename = f"{dir_name}_{frame_name}_{width}x{height}_raw.bmp"
                    filepath = os.path.join(icon_dir, filename)
                    non_zero = sum(1 for b in seg_data if b != 0)
                    write_bmp(filepath, seg_data, width, height, palette)
                    print(f"  {dir_name:5s} {frame_name:6s}: {len(seg_data):3d} bytes -> {width}x{height} ({non_zero} non-zero)")
                    break
            else:
                # No exact match - save first 576 bytes as 24x24 if possible
                if len(seg_data) >= 576:
                    filename = f"{dir_name}_{frame_name}_24x24_partial.bmp"
                    filepath = os.path.join(icon_dir, filename)
                    pixels = seg_data[:576]
                    non_zero = sum(1 for b in pixels if b != 0)
                    write_bmp(filepath, pixels, 24, 24, palette)
                    print(f"  {dir_name:5s} {frame_name:6s}: {len(seg_data):3d} bytes -> 24x24 partial ({non_zero} non-zero)")
                else:
                    # Save raw data for inspection
                    filename = f"{dir_name}_{frame_name}_{len(seg_data)}bytes.raw"
                    filepath = os.path.join(icon_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(seg_data)
                    print(f"  {dir_name:5s} {frame_name:6s}: {len(seg_data):3d} bytes -> saved as raw")

def main():
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\fdicon_icons'
    
    if not os.path.exists(fdicon_path):
        print(f"Error: FDICON.B24 not found at {fdicon_path}")
        return 1
    
    print("="*60)
    print("FDICON.B24 Icon Exporter (RAW mode)")
    print("="*60)
    
    export_fdicon_icons_raw(fdicon_path, output_dir, max_icons=5)
    
    print(f"\n{'='*60}")
    print(f"Export complete! Check: {output_dir}")
    print(f"{'='*60}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
