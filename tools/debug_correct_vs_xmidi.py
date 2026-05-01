#!/usr/bin/env python3
"""Debug: trace through correct MIDI parsing and compare with XMIDI"""
import struct
from pathlib import Path

# Read the CORRECT MIDI file
correct_path = Path("tools/fd2 midi/fd200011.mid")
with open(correct_path, 'rb') as f:
    midi_data = f.read()

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

print("=" * 70)
print("CORRECT MIDI FILE FORMAT (fd200011.mid)")
print("=" * 70)

# Parse MIDI header
fmt, tracks, ppqn = struct.unpack('>HHH', midi_data[8:14])
print(f"Format: {fmt}, Tracks: {tracks}, PPQN: {ppqn}")

# Parse track
pos = 14 + 8  # Skip MThd + MTrk header
track_end = len(midi_data)

print("\nMIDI events:")
running_status = None
event_count = 0

while pos < track_end:
    # Read delta
    delta = 0
    delta_start = pos
    while pos < track_end:
        b = midi_data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    if pos >= track_end:
        break
    
    byte = midi_data[pos]
    
    if byte >= 0x80:
        status = byte
        pos += 1
        running_status = status
    else:
        status = running_status
    
    status_type = status & 0xF0
    channel = status & 0x0F
    
    event_count += 1
    
    if status == 0xFF:
        meta_type = midi_data[pos]
        pos += 1
        length = 0
        while pos < track_end:
            b = midi_data[pos]
            pos += 1
            length = (length << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        meta_data = midi_data[pos:pos+length]
        pos += length
        
        if meta_type == 0x51 and length == 3:
            tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | FF 51 Tempo={tempo} ({60000000/tempo:.1f} BPM)")
        elif meta_type == 0x2F:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | FF 2F End of Track")
            break
        else:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | FF {meta_type:02X} len={length}")
    
    elif status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
        data1 = midi_data[pos]
        pos += 1
        data2 = midi_data[pos]
        pos += 1
        
        if status_type == 0x90:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | {status:02X} NoteOn Ch{channel} Note={data1} Vel={data2}")
        elif status_type == 0x80:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | {status:02X} NoteOff Ch{channel} Note={data1} Vel={data2}")
        elif status_type == 0xB0:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | {status:02X} CC Ch{channel} Ctrl={data1} Val={data2}")
        else:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | {status:02X} Ch{channel} {data1:02X} {data2:02X}")
    
    elif status_type in (0xC0, 0xD0):
        data1 = midi_data[pos]
        pos += 1
        if status_type == 0xC0:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | {status:02X} Program Ch{channel} Prog={data1}")
        else:
            print(f"  [{event_count:4d}] pos={delta_start:4d} delta={delta:5d} | {status:02X} Pressure Ch{channel} Val={data1}")
    
    if event_count > 15:
        print("  ...")
        break

# Now compare with XMIDI
print("\n" + "=" * 70)
print("XMIDI EVNT DATA (track 11)")
print("=" * 70)
print(f"Size: {chunk_size} bytes")

print("\nFirst 64 bytes hex:")
for i in range(0, min(64, len(evnt_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in evnt_data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

# Skip headers
pos = 0
while pos < len(evnt_data) and evnt_data[pos] == 0xFF:
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
    pos += length

print(f"\nAfter header: pos={pos}")
print(f"Bytes at pos {pos}: {' '.join(f'{b:02X}' for b in evnt_data[pos:pos+20])}")

# Parse like correct MIDI
print("\nXMIDI events (parsed like correct MIDI):")
running_status = None
event_count = 0

while pos < len(evnt_data) and event_count < 15:
    start_pos = pos
    
    # Read delta
    delta = 0
    while pos < len(evnt_data):
        b = evnt_data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    if pos >= len(evnt_data):
        break
    
    byte = evnt_data[pos]
    
    if byte >= 0x80:
        status = byte
        pos += 1
        running_status = status
    else:
        status = running_status
    
    status_type = status & 0xF0
    channel = status & 0x0F
    
    event_count += 1
    
    if status == 0xFF:
        meta_type = evnt_data[pos]
        pos += 1
        length = 0
        while pos < len(evnt_data):
            b = evnt_data[pos]
            pos += 1
            length = (length << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        pos += length
        print(f"  [{event_count:4d}] pos={start_pos:4d} delta={delta:5d} | FF {meta_type:02X}")
    
    elif status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
        data1 = evnt_data[pos]
        pos += 1
        data2 = evnt_data[pos]
        pos += 1
        
        if status_type == 0x90:
            # Duration
            duration = 0
            while pos < len(evnt_data):
                b = evnt_data[pos]
                pos += 1
                duration = (duration << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            print(f"  [{event_count:4d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} NoteOn Ch{channel} Note={data1} Vel={data2} Dur={duration}")
        elif status_type == 0xB0:
            print(f"  [{event_count:4d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} CC Ch{channel} Ctrl={data1} Val={data2}")
        else:
            print(f"  [{event_count:4d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} Ch{channel} {data1:02X} {data2:02X}")
    
    elif status_type in (0xC0, 0xD0):
        data1 = evnt_data[pos]
        pos += 1
        if status_type == 0xC0:
            print(f"  [{event_count:4d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} Program Ch{channel} Prog={data1}")
        else:
            print(f"  [{event_count:4d}] pos={start_pos:4d} delta={delta:5d} | {status:02X} Pressure Ch{channel} Val={data1}")
