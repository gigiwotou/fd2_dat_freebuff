#!/usr/bin/env python3
"""Debug why V2 parser skips events - more detailed"""
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
print(f"\nFull hex dump:")
for i in range(0, len(evnt_data), 16):
    hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in evnt_data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

# Manual parse - byte by byte
print(f"\n\nByte-by-byte analysis:")
pos = 0
event_count = 0

# Skip header meta events
print("Header:")
while pos < len(evnt_data):
    byte = evnt_data[pos]
    if byte != 0xFF:
        print(f"  First non-FF at pos {pos}: 0x{byte:02X}")
        break
    
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
    
    meta_data = evnt_data[pos:pos+length]
    pos += length
    
    if meta_type == 0x51:
        tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
        print(f"  [{pos}] FF 51 Tempo={tempo} (len={length})")
    elif meta_type == 0x58:
        print(f"  [{pos}] FF 58 Time Sig (len={length}) data={meta_data.hex()}")
    elif meta_type == 0x59:
        print(f"  [{pos}] FF 59 Key Sig (len={length}) data={meta_data.hex()}")
    elif meta_type == 0x21:
        print(f"  [{pos}] FF 21 Port (len={length}) data={meta_data.hex()}")
    else:
        print(f"  [{pos}] FF {meta_type:02X} len={length}")

print(f"\nStarting events at pos={pos}:")

running_status = None
max_events = 50

while pos < len(evnt_data) and event_count < max_events:
    start_pos = pos
    
    # Read delta - single byte most likely
    byte = evnt_data[pos]
    
    if byte == 0x00:
        delta = 0
        pos += 1
    elif byte < 0x80:
        delta = byte
        pos += 1
    else:
        # Multi-byte delta
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
        status_info = f"new status 0x{status:02X}"
    else:
        if running_status is None:
            print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | ERROR: No running status")
            event_count += 1
            continue
        status = running_status
        status_info = f"running 0x{status:02X}"
    
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
        meta_data = evnt_data[pos:pos+length]
        pos += length
        
        if meta_type == 0x51 and length == 3:
            tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
            print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | FF 51 Tempo={tempo}")
        elif meta_type == 0x2F:
            print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | FF 2F End")
            break
        else:
            print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | FF {meta_type:02X} len={length}")
    
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
            print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | {status:02X} SysEx")
        else:
            if pos < len(evnt_data):
                pos += 1
            print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | {status:02X}")
    else:
        if status_type == 0x90:
            # Note On with duration
            if pos + 1 < len(evnt_data):
                note = evnt_data[pos]
                vel = evnt_data[pos+1]
                pos += 2
                
                duration = 0
                while pos < len(evnt_data):
                    b = evnt_data[pos]
                    pos += 1
                    duration = (duration << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                
                print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | {status_info} NoteOn Ch{channel} Note={note} Vel={vel} Dur={duration}")
        elif status_type == 0xB0:
            if pos + 1 < len(evnt_data):
                ctrl = evnt_data[pos]
                val = evnt_data[pos+1]
                pos += 2
                print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | {status_info} CC Ch{channel} Ctrl={ctrl} Val={val}")
        elif status_type == 0xC0:
            if pos < len(evnt_data):
                prog = evnt_data[pos]
                pos += 1
                print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | {status_info} Program Ch{channel} Prog={prog}")
        else:
            if pos + 1 < len(evnt_data):
                d1 = evnt_data[pos]
                d2 = evnt_data[pos+1]
                pos += 2
                print(f"  [{event_count:3d}] pos={start_pos:4d} delta={delta:4d} | {status_info} {status:02X} Ch{channel} {d1:02X} {d2:02X}")
    
    event_count += 1
