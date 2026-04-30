#!/usr/bin/env python3
"""
FD2 Audio Resource Analyzer v2
Analyzes FDMUS.DAT (music) and TAI.DAT (unknown - suspected portraits)
Fixed: resource_count is 4 bytes (DWORD), not 2 bytes (WORD)
"""

import struct
import os
from pathlib import Path

def parse_dat_file(filepath):
    """Parse DAT file and return all resource data"""
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    file_size = len(file_data)
    
    magic = file_data[:6]
    if magic != b'LLLLLL':
        print(f"  Error: Unknown magic {magic}")
        return None, None
    
    resource_count = struct.unpack('<I', file_data[6:10])[0]
    print(f"  Magic: {magic.decode('ascii')}")
    print(f"  Resource count: {resource_count}")
    print(f"  File size: {file_size} bytes")
    
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', file_data[10 + i*4:14 + i*4])[0]
        offsets.append(offset)
    
    print(f"  Offset table: {len(offsets)} entries")
    print(f"  First offset: 0x{offsets[0]:08X} ({offsets[0]})")
    
    if offsets[0] > file_size:
        print(f"\n  ** WARNING: Offsets are larger than file size! **")
        print(f"  This suggests offsets are relative to a memory base, not file start")
        print(f"  Trying to normalize offsets...")
        
        base_offset = offsets[0]
        normalized_offsets = [off - base_offset for off in offsets]
        print(f"  Base offset: 0x{base_offset:08X}")
        print(f"  Normalized first offset: 0x{normalized_offsets[0]:08X}")
        
        if normalized_offsets[0] == 0 and normalized_offsets[-1] < file_size:
            print(f"  ** SUCCESS: Normalized offsets work! **")
            offsets = normalized_offsets
        else:
            print(f"  Normalization didn't work, trying alternative approaches...")
            
            for try_base in [0x400000, 0x500000, 0x600000, 0x10000000]:
                test_offsets = [off - try_base for off in offsets]
                if test_offsets[0] >= 0 and test_offsets[0] < 100 and test_offsets[-1] < file_size:
                    print(f"  ** Found working base: 0x{try_base:X} **")
                    offsets = test_offsets
                    break
    
    resources = []
    for i in range(resource_count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < resource_count else file_size
        size = end - start
        
        if start < 0 or start >= file_size:
            print(f"  Resource {i}: invalid start offset 0x{start:X}")
            resources.append(None)
            continue
        
        if size <= 0:
            print(f"  Resource {i}: invalid size {size}")
            resources.append(None)
            continue
        
        if start + size > file_size:
            size = file_size - start
        
        resources.append(file_data[start:start+size])
    
    return offsets, resources

def analyze_resource_data(data, index, show_detail=True):
    """Analyze resource data to identify format"""
    if data is None:
        return
    
    size = len(data)
    print(f"\n  Resource {index}: {size} bytes")
    
    if size < 4:
        print(f"    Too small: {data.hex()}")
        return
    
    first_bytes = data[:min(32, size)]
    print(f"    First 32 bytes: {first_bytes.hex(' ')}")
    
    if size >= 4:
        val32_le = struct.unpack('<I', data[:4])[0]
        val16_le = struct.unpack('<H', data[:2])[0]
        print(f"    DWORD@0: 0x{val32_le:08X} ({val32_le})")
        print(f"    WORD@0:  0x{val16_le:04X} ({val16_le})")
    
    if size >= 6:
        if data[:6] in (b'XMI ', b'FORM'):
            print(f"    ** XMIDI/RIFF format **")
    
    if size >= 4 and data[:4] == b'MThd':
        print(f"    ** Standard MIDI format **")
    
    if size > 100:
        entropy = len(set(data)) / 256.0
        print(f"    Byte diversity: {entropy*100:.1f}% ({len(set(data))} unique values)")
        
        zero_count = data.count(0)
        print(f"    Zero bytes: {zero_count} ({zero_count/size*100:.1f}%)")
        
        if zero_count / size > 0.5:
            print(f"    ** High zero ratio - likely sparse data or instrument patterns **")

def analyze_fdmus(filepath):
    """Analyze FDMUS.DAT music file"""
    print(f"\n{'='*80}")
    print(f"Analyzing FDMUS.DAT (Music - MDI format)")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return
    
    offsets, resources = parse_dat_file(filepath)
    if resources is None:
        return
    
    valid_resources = [r for r in resources if r is not None]
    print(f"\n  Valid resources: {len(valid_resources)}/{len(resources)}")
    
    if not valid_resources:
        print(f"  ** No valid resources extracted - need to investigate format **")
        return
    
    for i, res in enumerate(resources[:20]):
        analyze_resource_data(res, i)
    
    sizes = [len(r) for r in valid_resources]
    print(f"\n  Summary:")
    print(f"    Size range: {min(sizes)} - {max(sizes)} bytes")
    print(f"    Average size: {sum(sizes)/len(sizes):.0f} bytes")
    print(f"    Total size: {sum(sizes)} bytes")

def analyze_tai(filepath):
    """Analyze TAI.DAT file"""
    print(f"\n{'='*80}")
    print(f"Analyzing TAI.DAT (Unknown format)")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return
    
    offsets, resources = parse_dat_file(filepath)
    if resources is None:
        return
    
    valid_resources = [r for r in resources if r is not None]
    print(f"\n  Valid resources: {len(valid_resources)}/{len(resources)}")
    
    if not valid_resources:
        print(f"  ** No valid resources extracted **")
        return
    
    for i, res in enumerate(resources[:20]):
        analyze_resource_data(res, i)
    
    sizes = [len(r) for r in valid_resources]
    print(f"\n  Summary:")
    print(f"    Size range: {min(sizes)} - {max(sizes)} bytes")
    print(f"    Average size: {sum(sizes)/len(sizes):.0f} bytes")
    print(f"    Total size: {sum(sizes)} bytes")
    
    size_groups = {}
    for s in sizes:
        rounded = (s // 100) * 100
        size_groups[rounded] = size_groups.get(rounded, 0) + 1
    
    print(f"\n  Size distribution (by 100B groups):")
    for size in sorted(size_groups.keys())[:20]:
        count = size_groups[size]
        print(f"    {size}-{size+99} bytes: {count} resources")

def extract_resources(filepath, output_dir, max_extract=10):
    """Extract resources for detailed analysis"""
    print(f"\n{'='*80}")
    print(f"Extracting from {os.path.basename(filepath)}")
    print(f"{'='*80}")
    
    offsets, resources = parse_dat_file(filepath)
    if resources is None:
        return
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extract_count = 0
    for i, res in enumerate(resources):
        if res is None or extract_count >= max_extract:
            continue
        
        output_file = output_dir / f"resource_{i:03d}.bin"
        output_file.write_bytes(res)
        print(f"  Extracted resource {i}: {len(res)} bytes -> {output_file}")
        extract_count += 1

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
