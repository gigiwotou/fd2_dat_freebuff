#!/usr/bin/env python3
"""
分析FDOTHER.DAT的资源结构
"""

import struct
import sys
import os

def analyze_fdother(dat_path):
    with open(dat_path, 'rb') as f:
        # Read DAT header
        magic = f.read(6)
        print(f"Magic: {magic}")
        if magic != b'LLLLLL':
            print("Invalid DAT file")
            return
        
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"Resource count: {resource_count}")
        
        # Read offset table
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        print(f"\nFirst 20 resources:")
        for i in range(min(20, resource_count)):
            start = offsets[i]
            end = offsets[i+1] if i+1 < resource_count else os.path.getsize(dat_path)
            size = end - start
            
            f.seek(start)
            first_bytes = f.read(min(20, size))
            first_word0 = struct.unpack('<H', first_bytes[0:2])[0] if len(first_bytes) >= 2 else 0
            first_word1 = struct.unpack('<H', first_bytes[2:4])[0] if len(first_bytes) >= 4 else 0
            
            print(f"  Index {i:2d}: offset={start:7d} (0x{start:06X}), size={size:6d}, w/h={first_word0}/{first_word1}")

if __name__ == '__main__':
    dat_path = 'bin/FDOTHER.DAT'
    if len(sys.argv) > 1:
        dat_path = sys.argv[1]
    
    if not os.path.exists(dat_path):
        print(f"File not found: {dat_path}")
        sys.exit(1)
    
    analyze_fdother(dat_path)
