#!/usr/bin/env python3
"""Debug why V2 parser skips events"""
import struct
from pathlib import Path

# Read XMIDI EVNT for track 11
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

print(f"Track {track_idx}: {chunk_size} bytes EVNT")
print(f"\nFirst 100 bytes:")
for i in range(0, min(100, len(evnt_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in evnt_data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

# Manual parse to see what V2 does
print(f"\n\nManual parse:")
pos = 0

# Skip header meta events
print("Header meta events (no delta):")
while pos < len(evnt_data):
    byte = evnt_data[pos]
    if byte != 0xFF:
        print(f"  Non-meta at pos {pos}: 0x{byte:02X}")
        break
    
    pos += 1
    meta_type = evnt_data[pos]
    pos += 1
    
    # Variable length
    length = 0
    length_bytes = []
    while pos < len(evnt_data):
        b = evnt_data[pos]
        length_bytes.append(b)
        pos += 1
        length = (length << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    meta_data = evnt_data[pos:pos+length]
    pos += length
    
    if meta_type == 0x51 and length == 3:
        tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
        print(f"  FF 51 Tempo={tempo}")
    elif meta_type == 0x58:
        print(f"  FF 58 Time Sig")
    elif meta_type == 0x59:
        print(f"  FF 59 Key Sig")
    elif meta_type == 0x21:
        print(f"  FF 21 Port")
    else:
        print(f"  FF {meta_type:02X} len={length}")

print(f"\nNow at pos {pos}, byte=0x{evnt_data[pos]:02X}")

# Parse events
running_status = None
event_count = 0
max_events = 30

while pos < len(evnt_data) and event_count < max_events:
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
        if running_status is None:
            print(f"  [{event_count}] delta={delta} | ERROR: No running status, byte=0x{byte:02X}")
            event_count += 1
            continue
        status = running_status
    
    status_type = status & 0xF0
    channel = status & 0x0F
    
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
        print(f"  [{event_count}] delta={delta} | FF {meta_type:02X}")
    
    elif status >= 0xF0:
        running_status = None
        if status == 0xF0 or status == 0xF7:
            length = 0
            while pos < len(evnt_data):
                b = evnt_data[pos]
                pos += 1
                length = (length << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            pos += length
            print(f"  [{event_count}] delta={delta} | {status:02X} SysEx")
        else:
            pos += 1
            print(f"  [{event_count}] delta={delta} | {status:02X}")
    else:
        if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
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
                print(f"  [{event_count}] delta={delta} | {status:02X} NoteOn Ch{channel} Note={data1} Vel={data2} Dur={duration}")
            else:
                print(f"  [{event_count}] delta={delta} | {status:02X} Ch{channel} Data={data1:02X} {data2:02X}")
        elif status_type in (0xC0, 0xD0):
            data1 = evnt_data[pos]
            pos += 1
            print(f"  [{event_count}] delta={delta} | {status:02X} Ch{channel} Data={data1:02X}")
    
    event_count += 1
