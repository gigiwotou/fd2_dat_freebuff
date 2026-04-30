"""Analyze FDICON.B24 segment sizes to find exact pixel dimensions."""

import struct

def analyze_segment_sizes(fdicon_path):
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
    
    # Collect all segment sizes
    sizes = {}
    
    for icon_id in range(total_icons):
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_size = seg_end - seg_start
            
            if seg_size > 0:
                if seg_size not in sizes:
                    sizes[seg_size] = 0
                sizes[seg_size] += 1
    
    print(f"\nSegment size distribution:")
    for size in sorted(sizes.keys()):
        count = sizes[size]
        # Check if size matches common dimensions
        matches = []
        for w in range(8, 64):
            for h in range(8, 64):
                if w * h == size:
                    matches.append(f"{w}x{h}")
        
        match_str = f" ({', '.join(matches)})" if matches else ""
        print(f"  {size:4d} bytes: {count:4d} segments{match_str}")
    
    # Show first few icons with sizes
    print(f"\nFirst 5 icons segment sizes:")
    for icon_id in range(min(5, total_icons)):
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        
        print(f"\nIcon {icon_id}:")
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_size = seg_end - seg_start
            
            dir_name = ['Front', 'Left', 'Back', 'Right'][seg_idx // 3]
            frame_name = f"Frame{seg_idx % 3}"
            
            matches = []
            for w in range(8, 64):
                for h in range(8, 64):
                    if w * h == seg_size:
                        matches.append(f"{w}x{h}")
            
            match_str = f" ({', '.join(matches[:3])})" if matches else ""
            print(f"  {dir_name:5s} {frame_name:6s}: {seg_size:4d} bytes{match_str}")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    analyze_segment_sizes(fdicon_path)
