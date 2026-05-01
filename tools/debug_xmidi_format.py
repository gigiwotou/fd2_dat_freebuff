#!/usr/bin/env python3
"""
Dump specific byte ranges to understand XMIDI format
"""

import struct
from pathlib import Path

fdmus_path = Path("game/FDMUS.DAT")
with open(fdmus_path, 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]

for track_idx in [0, 11]:
    start = offsets[track_idx]
    end = offsets[track_idx+1] if track_idx+1 < count else len(data)
    track_data = data[start:end]
    
    evnt_pos = track_data.find(b'EVNT')
    if evnt_pos < 0:
        continue
    
    chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
    evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
    
    print(f"\nTrack {track_idx}: {chunk_size} bytes")
    print("="*60)
    
    # Show with explicit position numbers
    for i in range(min(80, len(evnt_data))):
        if i % 16 == 0:
            print(f"\n  {i:03d}:", end="")
        print(f" {evnt_data[i]:02X}", end="")
    
    print("\n\nInterpreted:")
    print("-"*60)
    
    # Try interpretation: XMIDI header is first 8 bytes (2x FF events)
    # Then events start at position 8
    
    pos = 0
    event_num = 0
    
    # Skip potential header
    if evnt_data[0] == 0xFF and evnt_data[1] == 0x58:
        print(f"  Header: FF 58 (Time Signature marker)")
        print(f"    Data: {evnt_data[2]:02X} {evnt_data[3]:02X} {evnt_data[4]:02X} {evnt_data[5]:02X} {evnt_data[6]:02X}")
        pos = 7
        print(f"  Next byte at position {pos}: {evnt_data[pos]:02X}")
    
    # Parse from position 7
    while pos < min(80, len(evnt_data)):
        byte = evnt_data[pos]
        
        if byte == 0xFF:
            # Meta event
            meta_type = evnt_data[pos+1]
            pos += 2
            
            # Variable length
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
                bpm = 60000000 / tempo if tempo > 0 else 0
                print(f"  [{event_num}] META Tempo: {tempo} ({bpm:.1f} BPM)")
            elif meta_type == 0x59:
                print(f"  [{event_num}] META Key Signature")
            elif meta_type == 0x2F:
                print(f"  [{event_num}] META End of Track")
                break
            else:
                print(f"  [{event_num}] META Type 0x{meta_type:02X} len={length} data={meta_data[:4].hex()}")
        
        elif byte >= 0x80:
            # Status byte
            status = byte
            pos += 1
            status_type = status & 0xF0
            channel = status & 0x0F
            
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                # 2 data bytes
                data1 = evnt_data[pos]
                pos += 1
                data2 = evnt_data[pos]
                pos += 1
                
                if status_type == 0x80:
                    print(f"  [{event_num}] NoteOff Ch{channel} Note={data1} Vel={data2}")
                elif status_type == 0x90:
                    # Check for duration
                    duration = 0
                    dur_pos = pos
                    while dur_pos < len(evnt_data):
                        b = evnt_data[dur_pos]
                        dur_pos += 1
                        duration = (duration << 7) | (b & 0x7F)
                        if not (b & 0x80):
                            break
                    
                    if dur_pos > pos:
                        print(f"  [{event_num}] NoteOn Ch{channel} Note={data1} Vel={data2} Dur={duration}")
                        pos = dur_pos
                    else:
                        print(f"  [{event_num}] NoteOn Ch{channel} Note={data1} Vel={data2}")
                elif status_type == 0xB0:
                    print(f"  [{event_num}] CC Ch{channel} Ctrl={data1} Val={data2}")
                else:
                    print(f"  [{event_num}] Status 0x{status:02X} Ch{channel} Data={data1:02X} {data2:02X}")
                    
            elif status_type in (0xC0, 0xD0):
                # 1 data byte
                data1 = evnt_data[pos]
                pos += 1
                if status_type == 0xC0:
                    print(f"  [{event_num}] Program Ch{channel} Prog={data1}")
                else:
                    print(f"  [{event_num}] Pressure Ch{channel} Val={data1}")
            else:
                print(f"  [{event_num}] Unknown status: 0x{status:02X}")
        
        else:
            # Data byte < 0x80 - either delta or running status data
            print(f"  [{event_num}] Byte 0x{byte:02X} (delta or data)")
            pos += 1
        
        event_num += 1
        
        if event_num > 30:
            print("  ...")
            break
