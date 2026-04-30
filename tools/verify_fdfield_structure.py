#!/usr/bin/env python3
"""
Verify FDFIELD.DAT structure by comparing IDA analysis vs documentation

IDA sub_111BA shows:
  fseek(v3, 4 * a3 + 6, 0)  # offset = 4 * map_index + 6
  read 8 bytes (2 DWORDs)
  size = dword[1] - dword[0]
  seek to dword[0]
  read data of 'size'

Documentation says:
  12 bytes per map (3 DWORDs):
  - DWORD[0]: tile data offset
  - DWORD[1]: control/treasure data offset  
  - DWORD[2]: character position data offset
"""

import struct
import sys

def verify_structure(filepath, map_index=32):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    print(f"Testing map index: {map_index}")
    print()
    
    # Verify header
    magic = data[0:6]
    print(f"Header: {magic} (expected 'LLLLLL')")
    assert magic == b'LLLLLL', "Invalid header!"
    print()
    
    # Test IDA structure: 4 bytes per map index, read 8 bytes
    print("=" * 60)
    print("TEST 1: IDA Structure (4 bytes per map)")
    print("=" * 60)
    
    ida_offset = 4 * map_index + 6
    print(f"Index offset: 4 * {map_index} + 6 = {ida_offset} (0x{ida_offset:04X})")
    
    if ida_offset + 8 <= len(data):
        offset1, offset2 = struct.unpack_from('<II', data, ida_offset)
        print(f"Read 8 bytes: [0x{offset1:06X}, 0x{offset2:06X}]")
        print(f"  Start offset: {offset1} (0x{offset1:06X})")
        print(f"  End offset:   {offset2} (0x{offset2:06X})")
        print(f"  Data size:    {offset2 - offset1} bytes")
        
        if 0 < offset1 < len(data):
            print(f"\n  Data at offset {offset1}:")
            print(f"    First 16 bytes: {data[offset1:offset1+16].hex()}")
            if offset1 + 2 <= len(data):
                word0 = struct.unpack_from('<H', data, offset1)[0]
                print(f"    First WORD: {word0} (0x{word0:04X})")
    else:
        print(f"  ERROR: Offset {ida_offset} out of range")
    
    print()
    print("=" * 60)
    print("TEST 2: Documentation Structure (12 bytes per map)")
    print("=" * 60)
    
    doc_offset = 6 + map_index * 12
    print(f"Index offset: 6 + {map_index} * 12 = {doc_offset} (0x{doc_offset:04X})")
    
    if doc_offset + 12 <= len(data):
        tile_off, ctrl_off, char_off = struct.unpack_from('<III', data, doc_offset)
        print(f"Read 12 bytes: [0x{tile_off:06X}, 0x{ctrl_off:06X}, 0x{char_off:06X}]")
        print(f"  Tile data offset:     {tile_off} (0x{tile_off:06X})")
        print(f"  Control data offset:  {ctrl_off} (0x{ctrl_off:06X})")
        print(f"  Character pos offset: {char_off} (0x{char_off:06X})")
        
        # Test character position data
        if 0 < char_off < len(data):
            print(f"\n  Character position data at {char_off}:")
            if char_off + 2 <= len(data):
                total_chars = struct.unpack_from('<H', data, char_off)[0]
                print(f"    Total characters: {total_chars}")
                
                if total_chars > 0 and total_chars < 100:
                    print(f"    First few characters:")
                    for i in range(min(5, total_chars)):
                        pos = char_off + 2 + i * 6
                        if pos + 6 <= len(data):
                            x, y, portrait = struct.unpack_from('<HHH', data, pos)
                            print(f"      Char {i}: X={x}, Y={y}, Portrait={portrait}")
    else:
        print(f"  ERROR: Offset {doc_offset} out of range")
    
    print()
    print("=" * 60)
    print("TEST 3: Compare multiple maps with both structures")
    print("=" * 60)
    
    print(f"\n{'Map':<6} {'IDA: Start':<15} {'IDA: End':<15} {'IDA: Size':<12} {'Doc: Tile':<15} {'Doc: Char':<15}")
    print("-" * 78)
    
    for mid in [30, 31, 32, 33, 34]:
        # IDA structure
        ida_off = 4 * mid + 6
        if ida_off + 8 <= len(data):
            ida_start, ida_end = struct.unpack_from('<II', data, ida_off)
            ida_size = ida_end - ida_start
            ida_str = f"0x{ida_start:06X}"
            ida_end_str = f"0x{ida_end:06X}"
            ida_size_str = f"{ida_size}"
        else:
            ida_str = ida_end_str = ida_size_str = "N/A"
        
        # Documentation structure
        doc_off = 6 + mid * 12
        if doc_off + 12 <= len(data):
            tile_off, ctrl_off, char_off = struct.unpack_from('<III', data, doc_off)
            doc_tile_str = f"0x{tile_off:06X}"
            doc_char_str = f"0x{char_off:06X}"
        else:
            doc_tile_str = doc_char_str = "N/A"
        
        print(f"{mid:<6} {ida_str:<15} {ida_end_str:<15} {ida_size_str:<12} {doc_tile_str:<15} {doc_char_str:<15}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <FDFIELD.DAT> [map_index]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    verify_structure(filepath, map_index)
