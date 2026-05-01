#!/usr/bin/env python3
"""Parse the correct MIDI file to understand its structure"""
import struct
from pathlib import Path

# Read the correct MIDI for track 11 (smallest)
correct_path = Path("tools/fd2 midi/fd200011.mid")
with open(correct_path, 'rb') as f:
    data = f.read()

print(f"Total size: {len(data)} bytes")

# Parse header
print(f"\nHeader:")
print(f"  MThd: {data[:4]}")
header_len = struct.unpack('>I', data[4:8])[0]
fmt, tracks, ppqn = struct.unpack('>HHH', data[8:14])
print(f"  Header len: {header_len}")
print(f"  Format: {fmt}")
print(f"  Tracks: {tracks}")
print(f"  PPQN: {ppqn}")

# Parse track
pos = 14
track_header = data[pos:pos+4]
pos += 4
track_len = struct.unpack('>I', data[pos:pos+4])[0]
pos += 4

print(f"\nTrack 0:")
print(f"  MTrk: {track_header}")
print(f"  Track len: {track_len}")

track_start = pos
track_end = pos + track_len

print(f"\nEvents:")

running_status = None
event_count = 0

while pos < track_end:
    # Read delta time
    delta = 0
    delta_start = pos
    while pos < track_end:
        b = data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    if pos >= track_end:
        break
    
    # Read status
    byte = data[pos]
    pos += 1
    
    if byte >= 0x80:
        status = byte
        running_status = status
    else:
        status = running_status
        pos -= 1  # Put back data byte
    
    status_type = status & 0xF0
    channel = status & 0x0F
    
    event_count += 1
    
    if status == 0xFF:
        # Meta event
        meta_type = data[pos]
        pos += 1
        
        # Read length
        length = 0
        while pos < track_end:
            b = data[pos]
            pos += 1
            length = (length << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        
        meta_data = data[pos:pos+length]
        pos += length
        
        if meta_type == 0x51 and length == 3:
            tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
            print(f"  [{event_count:4d}] delta={delta:6d} | FF 51 Tempo={tempo} ({60000000/tempo:.1f} BPM)")
        elif meta_type == 0x2F:
            print(f"  [{event_count:4d}] delta={delta:6d} | FF 2F End of Track")
            break
        elif meta_type == 0x58:
            print(f"  [{event_count:4d}] delta={delta:6d} | FF 58 Time Signature")
        elif meta_type == 0x01:
            text = meta_data.decode('ascii', errors='ignore')[:40]
            print(f"  [{event_count:4d}] delta={delta:6d} | FF 01 Text: '{text}'")
        else:
            print(f"  [{event_count:4d}] delta={delta:6d} | FF {meta_type:02X} len={length}")
    
    elif status >= 0xF0:
        if status == 0xF0 or status == 0xF7:
            length = 0
            while pos < track_end:
                b = data[pos]
                pos += 1
                length = (length << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            sysex_data = data[pos:pos+length]
            pos += length
            print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} SysEx ({length} bytes)")
        else:
            data1 = data[pos]
            pos += 1
            print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} {data1:02X}")
            running_status = None
    else:
        if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            data1 = data[pos]
            pos += 1
            data2 = data[pos]
            pos += 1
            
            if status_type == 0x90:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} NoteOn  Ch{channel} Note={data1:3d} Vel={data2:3d}")
            elif status_type == 0x80:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} NoteOff Ch{channel} Note={data1:3d} Vel={data2:3d}")
            elif status_type == 0xB0:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} CC      Ch{channel} Ctrl={data1:3d} Val={data2:3d}")
            elif status_type == 0xE0:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} PitchBend Ch{channel} LSB={data1} MSB={data2}")
            else:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} Data={data1:02X} {data2:02X}")
                
        elif status_type in (0xC0, 0xD0):
            data1 = data[pos]
            pos += 1
            if status_type == 0xC0:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} Program Ch{channel} Prog={data1:3d}")
            else:
                print(f"  [{event_count:4d}] delta={delta:6d} | {status:02X} Pressure Ch{channel} Val={data1:3d}")
    
    if event_count > 20:
        print("  ...")
        break
