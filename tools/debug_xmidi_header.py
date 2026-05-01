#!/usr/bin/env python3
"""Detailed analysis of XMIDI header structure"""
import struct
from pathlib import Path

# Read XMIDI source
fdmus_path = Path("game/FDMUS.DAT")
with open(fdmus_path, 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]

track_idx = 11
start = offsets[track_idx]
end = offsets[track_idx+1] if track_idx+1 < count else len(data)
track_data = data[start:end]

evnt_pos = track_data.find(b'EVNT')
chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]

print("XMIDI EVNT detailed parse:")
print(f"Total: {chunk_size} bytes")
print(f"\nFirst 100 bytes:")
for i in range(0, min(100, len(evnt_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in evnt_data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

# Correct MIDI also starts with FF 58, then FF 59
# But the correct MIDI has delta times!
# Let me check if XMIDI actually has delta times for headers too

print("\n\nHypothesis: XMIDI headers have delta=0 (implicit)")
print("Looking at correct MIDI structure:")

correct_path = Path("tools/fd2 midi/fd200011.mid")
with open(correct_path, 'rb') as f:
    midi_data = f.read()

# Skip header
pos = 14 + 8
print("\nCorrect MIDI events:")
for i in range(20):
    # Read delta
    delta = 0
    delta_pos = pos
    while pos < len(midi_data):
        b = midi_data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    status = midi_data[pos]
    pos += 1
    
    if status == 0xFF:
        meta = midi_data[pos]
        pos += 1
        length = 0
        while pos < len(midi_data):
            b = midi_data[pos]
            pos += 1
            length = (length << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        meta_data = midi_data[pos:pos+length]
        pos += length
        
        print(f"  [{i}] pos={delta_pos:3d} delta={delta:3d} | FF {meta:02X} len={length} data={meta_data[:10].hex()}")
    else:
        status_type = status & 0xF0
        if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            d1 = midi_data[pos]
            d2 = midi_data[pos+1]
            pos += 2
            print(f"  [{i}] pos={delta_pos:3d} delta={delta:3d} | {status:02X} {d1:02X} {d2:02X}")
        else:
            d1 = midi_data[pos]
            pos += 1
            print(f"  [{i}] pos={delta_pos:3d} delta={delta:3d} | {status:02X} {d1:02X}")

# Now let me look at XMIDI header parsing
print("\n\nXMIDI Header Analysis:")
print("The first bytes after EVNT chunk are headers, NO delta time")
print("BUT: Correct MIDI has delta=0 for each event")
print("So XMIDI just omits the 0x00 delta bytes for headers")

# Parse XMIDI headers manually
pos = 0
print("\nXMIDI headers (no delta):")
header_count = 0

while pos < len(evnt_data) and evnt_data[pos] == 0xFF and header_count < 30:
    pos += 1
    meta_type = evnt_data[pos]
    pos += 1
    
    length = 0
    while pos < len(evnt_data):
        b = evnt_data[pos]
        pos += 1
        length = (length << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    data = evnt_data[pos:pos+length]
    pos += length
    
    if meta_type == 0x58:
        print(f"  FF 58 Time Sig: len={length} data={data.hex()}")
    elif meta_type == 0x59:
        print(f"  FF 59 Key Sig: len={length} data={data.hex()}")
    elif meta_type == 0x21:
        print(f"  FF 21 Port: len={length} data={data.hex()}")
    elif meta_type == 0x51:
        if length == 3:
            tempo = struct.unpack('>I', b'\x00' + data)[0]
            print(f"  FF 51 Tempo: len={length} data={data.hex()} tempo={tempo} ({60000000/tempo:.1f} BPM)")
        else:
            print(f"  FF 51 Tempo?: len={length} data={data.hex()}")
    else:
        print(f"  FF {meta_type:02X}: len={length} data={data[:10].hex()}")
    
    header_count += 1

print(f"\nAfter {header_count} headers, pos={pos}")
print(f"Next bytes: {' '.join(f'{b:02X}' for b in evnt_data[pos:pos+20])}")

# AHA! Now I see it
# XMIDI: FF 58 (header) then many FF 21, then FF 59, then actual events START!
# The "C3 39 C4 5C C5 5A" are the FIRST events AFTER headers
