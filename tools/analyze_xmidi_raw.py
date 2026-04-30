#!/usr/bin/env python3
"""
Detailed XMIDI byte analysis to find the correct note/velocity encoding
"""

import struct
from pathlib import Path

def analyze_raw_xmidi(filepath, max_events=30):
    """Show raw bytes and parse events to understand encoding"""
    print(f"\n{'='*70}")
    print(f"File: {filepath.name}")
    print(f"{'='*70}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find EVNT
    evnt_pos = data.find(b'EVNT')
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    print(f"\nRaw bytes from EVNT (first 200 bytes):")
    for i in range(0, min(200, chunk_size), 16):
        offset = evnt_pos + 8 + i
        raw_data = data[offset:offset+16]
        hex_str = ' '.join(f'{b:02X}' for b in raw_data)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw_data)
        print(f"  {evnt_pos+8+i:04X}: {hex_str:<48} {ascii_str}")
    
    print(f"\n{'='*70}")
    print(f"Parsed events:")
    print(f"{'='*70}")
    
    running_status = 0
    event_num = 0
    
    while pos < end and event_num < max_events:
        # Record position
        event_start = pos
        
        # Parse delta
        delta = 0
        delta_bytes = []
        while pos < end:
            byte = data[pos]
            delta_bytes.append(byte)
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        status = data[pos]
        pos += 1
        
        # Show raw bytes for this event
        event_bytes = data[event_start:pos]
        raw_hex = ' '.join(f'{b:02X}' for b in event_bytes)
        
        if status == 0xFF:  # Meta
            meta_type = data[pos]
            pos += 1
            length = 0
            while pos < end:
                byte = data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            data_bytes = data[pos:pos+length]
            pos += length
            
            if meta_type == 0x2F:
                print(f"  {event_num:<5} [Delta={delta:<8}] Meta End of Track")
                break
            elif meta_type == 0x51:
                if len(data_bytes) == 3:
                    tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                    bpm = 60000000 / tempo
                    print(f"  {event_num:<5} [Delta={delta:<8}] Meta Tempo: {bpm:.0f} BPM")
            else:
                print(f"  {event_num:<5} [Delta={delta:<8}] Meta 0x{meta_type:02X} len={length}")
            
            running_status = 0
            event_num += 1
            
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                raw_hex_full = f"{raw_hex} {byte1:02X} {byte2:02X}"
                
                if command == 0x90:
                    if byte2 > 0:
                        # Note On - analyze the values
                        print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X} 0x{byte2:02X}  "
                              f"Note On  ch={channel} raw_note={byte1} raw_vel={byte2}")
                    else:
                        print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X} 0x00  "
                              f"Note Off ch={channel} raw_note={byte1}")
                elif command == 0xB0:
                    print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X} 0x{byte2:02X}  "
                          f"CC       ch={channel} ctrl={byte1} val={byte2}")
                elif command == 0xA0:
                    print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X} 0x{byte2:02X}  "
                          f"PolyTouch ch={channel}")
                else:
                    print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X} 0x{byte2:02X}  "
                          f"Command 0x{command:02X} ch={channel}")
                
            elif command in (0xC0, 0xD0):
                byte1 = data[pos]
                pos += 1
                
                if command == 0xC0:
                    print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X}      "
                          f"ProgCh   ch={channel} prog={byte1}")
                else:
                    print(f"  {event_num:<5} [Delta={delta:<8}] 0x{status:02X} 0x{byte1:02X}      "
                          f"AfterTouch ch={channel}")
            
            event_num += 1
            
        else:  # Running status
            command = running_status & 0xF0
            channel = running_status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                if command == 0x90:
                    if byte2 > 0:
                        print(f"  {event_num:<5} [Delta={delta:<8}] run      0x{byte1:02X} 0x{byte2:02X}  "
                              f"Note On  ch={channel} raw_note={byte1} raw_vel={byte2}")
                    else:
                        print(f"  {event_num:<5} [Delta={delta:<8}] run      0x{byte1:02X} 0x00  "
                              f"Note Off ch={channel} raw_note={byte1}")
                elif command == 0xB0:
                    print(f"  {event_num:<5} [Delta={delta:<8}] run      0x{byte1:02X} 0x{byte2:02X}  "
                          f"CC       ch={channel}")
            elif command in (0xC0, 0xD0):
                byte1 = data[pos]
                pos += 1
                print(f"  {event_num:<5} [Delta={delta:<8}] run      0x{byte1:02X}      "
                      f"ProgCh   ch={channel}")
            
            event_num += 1

def main():
    track_dir = Path("output/fdmus_tracks")
    track_file = track_dir / "track_000.bin"
    
    if track_file.exists():
        analyze_raw_xmidi(track_file)

if __name__ == "__main__":
    main()
