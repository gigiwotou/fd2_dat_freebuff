#!/usr/bin/env python3
"""
FD2 Audio Resource Analyzer
Analyzes FDMUS.DAT (music) and TAI.DAT (unknown - suspected sound effects or portraits)
Based on IDA reverse engineering of FD2.EXE
"""

import struct
import os
from pathlib import Path

def parse_dat_header(filepath):
    """Parse DAT file header (LLLLLL format)"""
    with open(filepath, 'rb') as f:
        magic = f.read(6)
        if magic != b'LLLLLL':
            print(f"  Warning: Unknown magic {magic}")
            return None
        
        resource_count = struct.unpack('<H', f.read(2))[0]
        print(f"  Magic: {magic.decode('ascii')}")
        print(f"  Resource count: {resource_count}")
        
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        return offsets

def analyze_resource_data(data, index):
    """Analyze resource data to identify format"""
    print(f"\n  Resource {index}: {len(data)} bytes")
    
    if len(data) < 4:
        print(f"    Too small to analyze: {data.hex()}")
        return
    
    first_bytes = data[:16]
    print(f"    First 16 bytes: {first_bytes.hex(' ')}")
    
    is_text = all(32 <= b < 127 or b in (0x0A, 0x0D, 0x09) for b in first_bytes)
    if is_text:
        print(f"    Appears to be ASCII text: {first_bytes.decode('ascii', errors='replace')}")
    
    if data[:4] == b'RIFF':
        print(f"    ** RIFF format detected (WAV/AVI) **")
        if len(data) >= 12:
            riff_size = struct.unpack('<I', data[4:8])[0]
            riff_type = data[8:12]
            print(f"    RIFF size: {riff_size}, Type: {riff_type.decode('ascii', errors='replace')}")
    
    if data[:2] == b'MThd':
        print(f"    ** MIDI format detected **")
    
    if data[:4] in (b'XMI ', b'FORM'):
        print(f"    ** XMIDI format detected **")
    
    if data[:4] == b'AIL3':
        print(f"    ** AIL3 format detected **")
    
    if data[0] == 0x1A and data[1:5] == b'AFM ':
        print(f"    ** AFM animation format **")
    
    for offset in [0, 0x50, 0xA0]:
        if offset < len(data) - 4:
            val32 = struct.unpack('<I', data[offset:offset+4])[0]
            print(f"    DWORD@0x{offset:02X}: 0x{val32:08X} ({val32})")

def analyze_fdmus(filepath):
    """Analyze FDMUS.DAT music file"""
    print(f"\n{'='*80}")
    print(f"Analyzing FDMUS.DAT (Music)")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return
    
    file_size = os.path.getsize(filepath)
    print(f"  File size: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    offsets = parse_dat_header(filepath)
    if not offsets:
        return
    
    print(f"\n  Analyzing resources...")
    
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    resource_sizes = []
    for i, offset in enumerate(offsets):
        if offset >= len(file_data):
            print(f"  Resource {i}: offset 0x{offset:X} out of bounds")
            continue
        
        end_offset = offsets[i+1] if i+1 < len(offsets) else len(file_data)
        size = end_offset - offset
        resource_sizes.append(size)
        
        if size <= 0:
            print(f"  Resource {i}: invalid size {size}")
            continue
        
        data = file_data[offset:offset+min(size, 256)]
        analyze_resource_data(data, i)
    
    if resource_sizes:
        print(f"\n  Summary:")
        print(f"    Total resources: {len(resource_sizes)}")
        print(f"    Size range: {min(resource_sizes)} - {max(resource_sizes)} bytes")
        print(f"    Average size: {sum(resource_sizes)/len(resource_sizes):.0f} bytes")
        
        small = sum(1 for s in resource_sizes if s < 100)
        medium = sum(1 for s in resource_sizes if 100 <= s < 1000)
        large = sum(1 for s in resource_sizes if s >= 1000)
        print(f"    Small (<100B): {small}, Medium (100-1000B): {medium}, Large (>1KB): {large}")

def analyze_tai(filepath):
    """Analyze TAI.DAT file - purpose unknown"""
    print(f"\n{'='*80}")
    print(f"Analyzing TAI.DAT (Unknown - suspected portraits or effects)")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return
    
    file_size = os.path.getsize(filepath)
    print(f"  File size: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    offsets = parse_dat_header(filepath)
    if not offsets:
        return
    
    print(f"\n  Analyzing resources...")
    
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    resource_sizes = []
    has_rle = 0
    has_palette = 0
    
    for i, offset in enumerate(offsets):
        if offset >= len(file_data):
            print(f"  Resource {i}: offset 0x{offset:X} out of bounds")
            continue
        
        end_offset = offsets[i+1] if i+1 < len(offsets) else len(file_data)
        size = end_offset - offset
        resource_sizes.append(size)
        
        if size <= 0:
            print(f"  Resource {i}: invalid size {size}")
            continue
        
        data = file_data[offset:offset+min(size, 256)]
        
        if i < 20:
            analyze_resource_data(data, i)
        
        if size >= 6 and data[0] == 0 and data[1] == 0:
            width = struct.unpack('<H', data[2:4])[0]
            height = struct.unpack('<H', data[4:6])[0]
            if 0 < width <= 320 and 0 < height <= 200:
                has_rle += 1
        
        if size == 768 or size == 772:
            has_palette += 1
    
    if resource_sizes:
        print(f"\n  Summary:")
        print(f"    Total resources: {len(resource_sizes)}")
        print(f"    Size range: {min(resource_sizes)} - {max(resource_sizes)} bytes")
        print(f"    Average size: {sum(resource_sizes)/len(resource_sizes):.0f} bytes")
        print(f"    Possible RLE images: {has_rle}")
        print(f"    Possible palettes (768B): {has_palette}")
        
        size_groups = {}
        for s in resource_sizes:
            rounded = (s // 100) * 100
            size_groups[rounded] = size_groups.get(rounded, 0) + 1
        
        print(f"\n    Size distribution (grouped by 100B):")
        for size in sorted(size_groups.keys()):
            count = size_groups[size]
            print(f"      {size}-{size+99} bytes: {count} resources")

def extract_resources(filepath, output_dir, max_extract=10):
    """Extract first few resources for detailed analysis"""
    print(f"\n{'='*80}")
    print(f"Extracting resources from {os.path.basename(filepath)}")
    print(f"{'='*80}")
    
    offsets = parse_dat_header(filepath)
    if not offsets:
        return
    
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extract_count = min(max_extract, len(offsets))
    
    for i in range(extract_count):
        offset = offsets[i]
        end_offset = offsets[i+1] if i+1 < len(offsets) else len(file_data)
        size = end_offset - offset
        
        if size <= 0 or offset >= len(file_data):
            continue
        
        data = file_data[offset:offset+size]
        output_file = output_dir / f"resource_{i:03d}.bin"
        output_file.write_bytes(data)
        print(f"  Extracted resource {i}: {size} bytes -> {output_file}")

def main():
    base_dir = Path("game")
    output_dir = Path("output/audio_analysis")
    
    fdmus_path = base_dir / "FDMUS.DAT"
    tai_path = base_dir / "TAI.DAT"
    
    analyze_fdmus(fdmus_path)
    analyze_tai(tai_path)
    
    extract_resources(fdmus_path, output_dir / "fdmus", max_extract=5)
    extract_resources(tai_path, output_dir / "tai", max_extract=20)
    
    print(f"\n{'='*80}")
    print(f"Analysis complete! Check {output_dir} for extracted resources")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
