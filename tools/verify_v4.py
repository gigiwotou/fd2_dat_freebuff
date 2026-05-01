#!/usr/bin/env python3
"""Verify V4 MIDI file structure"""
import struct
from pathlib import Path

# Check V4 file
v4_file = Path("output/fdmus_midi_v4/track_011.mid")
with open(v4_file, 'rb') as f:
    data = f.read()

print(f"V4 File size: {len(data)} bytes")
print(f"\nFirst 64 bytes:")
for i in range(0, min(64, len(data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

# Parse first few events
print(f"\nFirst 20 events:")
pos = 14 + 8
event_count = 0

while pos < len(data) and event_count < 20:
    start_pos = pos
    
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
        
        if meta == 0x51:
            tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
            print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | FF 51 Tempo={tempo}")
        elif meta == 0x58:
            print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | FF 58 Time Sig")
        elif meta == 0x2F:
            print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | FF 2F End")
            break
        else:
            print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | FF {meta:02X}")
    else:
        status_type = status & 0xF0
        if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            d1 = data[pos]
            d2 = data[pos+1]
            pos += 2
            if status_type == 0x90:
                print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} NoteOn Ch{status&0xF} Note={d1} Vel={d2}")
            elif status_type == 0x80:
                print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} NoteOff Ch{status&0xF} Note={d1}")
            elif status_type == 0xB0:
                print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} CC Ch{status&0xF} Ctrl={d1} Val={d2}")
            else:
                print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} Data={d1:02X} {d2:02X}")
        elif status_type in (0xC0, 0xD0):
            d1 = data[pos]
            pos += 1
            print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} Ch{status&0xF} Data={d1}")
        else:
            print(f"  [{event_count:2d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} Unknown")
    
    event_count += 1

# Also compare with correct file
correct_file = Path("tools/fd2 midi/fd200011.mid")
if correct_file.exists():
    with open(correct_file, 'rb') as f:
        correct_data = f.read()
    
    print(f"\n\nCorrect file first 64 bytes:")
    for i in range(0, min(64, len(correct_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in correct_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in correct_data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
