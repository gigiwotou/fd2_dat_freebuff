#!/usr/bin/env python3
"""
Debug XMIDI parsing byte by byte
"""

import struct
from pathlib import Path

def parse_vlq_v2(data, pos, end, max_bytes=4):
    """Parse VLQ exactly like IDA sub_424B0"""
    value = 0
    count = 0
    
    while pos < end and count < max_bytes:
        byte = data[pos]
        pos += 1
        count += 1
        # IDA code: v2 = v3 & 0x7F | (v2 << 7)
        value = (byte & 0x7F) | (value << 7)
        
        # IDA code: if (v3 >= 0) break - in signed char, >= 0 means bit7 is 0
        if not (byte & 0x80):
            break
    
    return value, pos

def analyze_track_11():
    fdmus_path = Path('game/FDMUS.DAT')
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    # Track 11
    start = offsets[11]
    end = offsets[12] if 12 < count else len(data)
    track = data[start:end]
    
    # Find EVNT
    evnt_pos = track.find(b'EVNT')
    evnt_size = struct.unpack('>I', track[evnt_pos+4:evnt_pos+8])[0]
    data_start = evnt_pos + 8
    data_end = data_start + evnt_size
    
    print(f"Track 11: {len(track)} bytes")
    print(f"EVNT: pos={evnt_pos:#x}, size={evnt_size}")
    print(f"EVNT data: {data_start:#x} to {data_end:#x}")
    print()
    
    # Print first 50 bytes of EVNT data
    print("First 50 bytes of EVNT data:")
    for i in range(0, 50, 16):
        chunk = track[data_start+i:data_start+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  +{i:03X}: {hex_str}")
    print()
    
    # Try parsing as: delta(VLQ) then event
    pos = data_start
    print("Parsing as delta+event:")
    for evt in range(10):
        delta_start = pos
        delta, pos = parse_vlq_v2(track, pos, data_end)
        
        if pos >= data_end:
            break
        
        print(f"  Event {evt}: delta_start={delta_start-start:#x}")
        print(f"    Delta bytes from {delta_start-start:#x}: ", end="")
        for i in range(delta_start, pos):
            print(f"{track[i]:02X} ", end="")
        print(f"= {delta}")
        
        status = track[pos]
        print(f"    Status at {pos-start:#x}: 0x{status:02X}")
        pos += 1
        
        if status == 0xFF:
            if pos < data_end:
                meta_type = track[pos]
                pos += 1
                print(f"    Meta type: 0x{meta_type:02X}")
                
                # Length is VLQ
                length, pos = parse_vlq_v2(track, pos, data_end)
                print(f"    Length: {length}")
                
                if pos + length <= data_end:
                    meta_data = track[pos:pos+length]
                    pos += length
                    print(f"    Data: {' '.join(f'{b:02X}' for b in meta_data)}")
                    
                    if meta_type == 0x51 and length == 3:
                        tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                        bpm = 60000000 / tempo if tempo > 0 else 0
                        print(f"    Tempo: {tempo} = {bpm:.1f} BPM (raw/16={tempo//16}, {(60000000//(tempo//16)):.1f} BPM)")
            else:
                break
        elif status >= 0x80:
            command = status & 0xF0
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 2 <= data_end:
                    b1, b2 = track[pos], track[pos+1]
                    pos += 2
                    print(f"    Command: 0x{command:02X}, ch={status&0xF}, data={b1}, {b2}")
                    
                    # Check for duration after Note On
                    if command == 0x90 and b2 > 0:
                        duration, pos = parse_vlq_v2(track, pos, data_end)
                        print(f"    Duration: {duration}")
            elif command in (0xC0, 0xD0):
                if pos <= data_end:
                    b1 = track[pos]
                    pos += 1
                    print(f"    Command: 0x{command:02X}, ch={status&0xF}, data={b1}")
        else:
            print(f"    Running status? (byte=0x{status:02X})")
        
        print()

def analyze_track_10():
    fdmus_path = Path('game/FDMUS.DAT')
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    # Track 10
    start = offsets[10]
    end = offsets[11] if 11 < count else len(data)
    track = data[start:end]
    
    evnt_pos = track.find(b'EVNT')
    evnt_size = struct.unpack('>I', track[evnt_pos+4:evnt_pos+8])[0]
    data_start = evnt_pos + 8
    
    print(f"\nTrack 10: {len(track)} bytes")
    print(f"EVNT: pos={evnt_pos:#x}, size={evnt_size}")
    print()
    
    print("First 50 bytes of EVNT data:")
    for i in range(0, 50, 16):
        chunk = track[data_start+i:data_start+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  +{i:03X}: {hex_str}")

if __name__ == '__main__':
    analyze_track_11()
    analyze_track_10()
