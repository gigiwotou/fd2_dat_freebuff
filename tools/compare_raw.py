#!/usr/bin/env python3
"""Compare correct MIDI files with v2 output using raw bytes"""
import struct
from pathlib import Path

correct_dir = Path("tools/fd2 midi")
v2_dir = Path("output/fdmus_midi_v2")

pairs = [
    ("fd200000.mid", "track_000.mid"),
    ("fd200003.mid", "track_003.mid"),
    ("fd200005.mid", "track_005.mid"),
    ("fd200010.mid", "track_010.mid"),
    ("fd200011.mid", "track_011.mid"),
]

for correct_file, v2_file in pairs:
    correct_path = correct_dir / correct_file
    v2_path = v2_dir / v2_file
    
    if not correct_path.exists():
        continue
    
    if not v2_path.exists():
        continue
    
    print(f"\n{'='*60}")
    print(f"Comparing: {correct_file} vs {v2_file}")
    print(f"{'='*60}")
    
    with open(correct_path, 'rb') as f:
        correct_data = f.read()
    with open(v2_path, 'rb') as f:
        v2_data = f.read()
    
    print(f"\nCorrect file: {len(correct_data)} bytes")
    print(f"V2 file:      {len(v2_data)} bytes")
    
    # Show first 64 bytes of each
    print(f"\nCorrect file first 64 bytes:")
    for i in range(0, min(64, len(correct_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in correct_data[i:i+16])
        print(f"  {i:04X}: {hex_str}")
    
    print(f"\nV2 file first 64 bytes:")
    for i in range(0, min(64, len(v2_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in v2_data[i:i+16])
        print(f"  {i:04X}: {hex_str}")
    
    # Parse headers
    print(f"\nHeader comparison:")
    
    # Correct
    if correct_data[:4] == b'MThd':
        header_len = struct.unpack('>I', correct_data[4:8])[0]
        fmt, tracks, ppqn = struct.unpack('>HHH', correct_data[8:14])
        print(f"  Correct: Format={fmt}, Tracks={tracks}, PPQN={ppqn}")
        
        # Find tempo
        pos = 14
        if correct_data[pos:pos+4] == b'MTrk':
            track_len = struct.unpack('>I', correct_data[pos+4:pos+8])[0]
            track_start = pos + 8
            
            # Parse track to find tempo
            tpos = track_start
            while tpos < track_start + track_len:
                # Read delta
                delta = 0
                while tpos < track_start + track_len:
                    b = correct_data[tpos]
                    tpos += 1
                    delta = (delta << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                
                if tpos >= track_start + track_len:
                    break
                
                status = correct_data[tpos]
                tpos += 1
                
                if status == 0xFF:
                    if tpos >= track_start + track_len:
                        break
                    meta_type = correct_data[tpos]
                    tpos += 1
                    
                    length = 0
                    while tpos < track_start + track_len:
                        b = correct_data[tpos]
                        tpos += 1
                        length = (length << 7) | (b & 0x7F)
                        if not (b & 0x80):
                            break
                    
                    if meta_type == 0x51 and length == 3:
                        tempo = struct.unpack('>I', b'\x00' + correct_data[tpos:tpos+3])[0]
                        print(f"  Correct Tempo: {tempo} ({60000000/tempo:.1f} BPM)")
                        break
                    elif meta_type == 0x2F:
                        break
                    else:
                        tpos += length
    
    if v2_data[:4] == b'MThd':
        header_len = struct.unpack('>I', v2_data[4:8])[0]
        fmt, tracks, ppqn = struct.unpack('>HHH', v2_data[8:14])
        print(f"  V2:      Format={fmt}, Tracks={tracks}, PPQN={ppqn}")
