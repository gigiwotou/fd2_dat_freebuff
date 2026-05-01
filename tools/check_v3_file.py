#!/usr/bin/env python3
"""Check V3 MIDI file structure"""
import struct
from pathlib import Path

v3_file = Path("output/fdmus_midi_v3/track_011.mid")
with open(v3_file, 'rb') as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print(f"\nFirst 64 bytes:")
for i in range(0, min(64, len(data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

# Parse header
if data[:4] == b'MThd':
    header_len = struct.unpack('>I', data[4:8])[0]
    fmt, tracks, ppqn = struct.unpack('>HHH', data[8:14])
    print(f"\nHeader: Format={fmt}, Tracks={tracks}, PPQN={ppqn}")

# Find first tempo event
pos = 14
while pos < len(data):
    # Read delta
    delta = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    if pos >= len(data):
        break
    
    status = data[pos]
    pos += 1
    
    if status == 0xFF:
        meta = data[pos]
        pos += 1
        length = 0
        while pos < len(data):
            b = data[pos]
            pos += 1
            length = (length << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        meta_data = data[pos:pos+length]
        pos += length
        
        if meta == 0x51 and length == 3:
            tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
            print(f"Tempo event found at pos {pos-3-length}: tempo={tempo} ({60000000/tempo:.1f} BPM)")
            break
        elif meta == 0x2F:
            print("End of track found early!")
            break

# Count events
note_on = 0
note_off = 0
pos = 14 + 8  # Skip headers
while pos < len(data):
    delta = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    if pos >= len(data):
        break
    
    status = data[pos]
    pos += 1
    
    status_type = status & 0xF0
    
    if status_type == 0x90:
        note_on += 1
        pos += 2
    elif status_type == 0x80:
        note_off += 1
        pos += 2
    elif status == 0xFF:
        meta = data[pos]
        pos += 1
        length = 0
        while pos < len(data):
            b = data[pos]
            pos += 1
            length = (length << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        pos += length
        if meta == 0x2F:
            break

print(f"\nEvents in file: NoteOn={note_on}, NoteOff={note_off}")
