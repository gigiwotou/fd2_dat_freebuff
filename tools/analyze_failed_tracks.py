#!/usr/bin/env python3
"""
Analyze why some tracks failed to convert
"""

from pathlib import Path
import struct

failed_tracks = [1, 4, 6, 8]
track_dir = Path("output/fdmus_tracks")

for idx in failed_tracks:
    track_file = track_dir / f"track_{idx:03d}.bin"
    with open(track_file, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*60}")
    print(f"track_{idx:03d}.bin - {len(data)} bytes")
    
    evnt_pos = data.find(b'EVNT')
    if evnt_pos >= 0:
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        print(f"EVNT at: {evnt_pos}, chunk size: {chunk_size}")
        
        # Check for 0xFF events
        evnt_data = data[evnt_pos+8:evnt_pos+8+chunk_size]
        ff_count = evnt_data.count(b'\xFF')
        print(f"0xFF bytes in EVNT: {ff_count}")
        
        # Show first 50 bytes of EVNT
        print(f"First 50 bytes of EVNT:")
        for i in range(0, 50, 16):
            chunk = evnt_data[i:i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"  {evnt_pos+8+i:04X}: {hex_str:<48} {ascii_str}")
    else:
        print("No EVNT found!")
