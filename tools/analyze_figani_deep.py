"""Deep analysis of FIGANI.DAT sprite structure."""

import struct
import sys

def analyze_figani_deep(figani_path):
    data = open(figani_path, 'rb').read()
    print(f"FIGANI.DAT file size: {len(data)} bytes")
    
    # Format 2 parsing
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data):
            break
        offsets.append(offset)
        pos += 4
    
    print(f"Resource count: {len(offsets)}")
    
    # Analyze first 10 resources in detail
    for i in range(min(10, len(offsets) - 1)):
        start = offsets[i]
        end = offsets[i + 1] if i < len(offsets) - 1 else len(data)
        res_data = data[start:end]
        size = len(res_data)
        
        print(f"\n{'='*60}")
        print(f"Resource {i}: offset={start}, size={size}")
        print(f"{'='*60}")
        
        # Parse header as multiple DWORDs
        num_dwords = min(20, size // 4)
        dwords = struct.unpack(f'<{num_dwords}I', res_data[:num_dwords*4])
        print(f"First {num_dwords} DWORDs: {dwords}")
        
        # Try to find width/height patterns
        # Check if some DWORDs could be dimensions
        for j in range(min(4, num_dwords)):
            val = dwords[j]
            if 4 <= val <= 200:  # Reasonable dimension
                print(f"  DWORD[{j}] = {val} (possible dimension)")
        
        # Look for frame offsets (monotonically increasing)
        frame_offsets = []
        for j in range(0, min(50, num_dwords)):
            if j + 1 < num_dwords:
                if dwords[j+1] > dwords[j] > 0:
                    frame_offsets.append(dwords[j])
        
        if frame_offsets:
            print(f"  Possible frame offsets: {frame_offsets[:5]}")
            print(f"  Frame count: {len(frame_offsets)}")
        
        # Check if data after header is RLE compressed
        header_size = num_dwords * 4
        rle_data = res_data[header_size:]
        if len(rle_data) > 100:
            high_bit_count = sum(1 for b in rle_data[:100] if b & 0x80)
            print(f"  RLE high-bit ratio: {high_bit_count}/100 = {high_bit_count}%")

if __name__ == '__main__':
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    if len(sys.argv) > 1:
        figani_path = sys.argv[1]
    
    analyze_figani_deep(figani_path)
