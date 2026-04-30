"""Export icons from FDICON.B24 as PNG images.

Based on IDA analysis, each icon has 12 segments.
This exports all 140 icons, with all 12 segments each.
"""

import struct
import sys
import os

try:
    from PIL import Image
except ImportError:
    print("PIL/Pillow not installed. Installing...")
    os.system('pip install Pillow')
    from PIL import Image

def export_icons(fdicon_path, output_dir):
    data = open(fdicon_path, 'rb').read()
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table from byte 6
    offset_table = struct.unpack('<1680I', data[6:6+6720])
    num_icons = 140
    segments_per_icon = 12
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Export each icon
    for icon_id in range(num_icons):
        base_idx = icon_id * segments_per_icon
        
        # Get data range for this icon
        data_start = offset_table[base_idx]
        data_end = offset_table[(icon_id + 1) * segments_per_icon] if icon_id < num_icons - 1 else len(data)
        data_size = data_end - data_start
        
        if data_size <= 0:
            print(f"Icon {icon_id}: invalid size {data_size}")
            continue
        
        icon_data = data[data_start:data_end]
        
        # Create subdirectory for this icon
        icon_dir = os.path.join(output_dir, f"icon_{icon_id:03d}")
        os.makedirs(icon_dir, exist_ok=True)
        
        # Try to decode each segment as 8-bit palette image
        for seg in range(segments_per_icon):
            seg_offset = offset_table[base_idx + seg] - data_start
            if seg < 11:
                next_seg_offset = offset_table[base_idx + seg + 1] - data_start
            else:
                next_seg_offset = data_size
            
            seg_size = next_seg_offset - seg_offset
            if seg_size <= 0 or seg_offset >= data_size:
                continue
            
            seg_data = icon_data[seg_offset:seg_offset + seg_size]
            
            # Try different image dimensions
            # Based on analysis: 24x24 = 576 bytes, 32x32 = 1024 bytes
            for w, h in [(16,16), (24,24), (32,32), (16,32), (32,16), (48,48), (64,64), (80,60), (100,75)]:
                if w * h == seg_size:
                    img = Image.frombytes('P', (w, h), seg_data)
                    # Apply a default palette (will need game's actual palette)
                    img.save(os.path.join(icon_dir, f"segment_{seg}_{w}x{h}.png"))
                    if seg == 0:
                        print(f"Icon {icon_id}: segment {seg} -> {w}x{h} ({seg_size} bytes)")
                    break
            else:
                # Save raw data if size doesn't match known dimensions
                if seg == 0:
                    print(f"Icon {icon_id}: segment 0 size={seg_size} bytes (no match, saving raw)")
                    with open(os.path.join(icon_dir, f"segment_{seg}_raw.bin"), 'wb') as f:
                        f.write(seg_data)

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\fdicon_icons'
    
    if len(sys.argv) > 1:
        fdicon_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    export_icons(fdicon_path, output_dir)
    print(f"\nExported icons to {output_dir}")
