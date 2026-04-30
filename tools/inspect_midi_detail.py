#!/usr/bin/env python3
"""
Deep inspection of MIDI file content
Check if the converted data is actually valid MIDI events
"""

import struct
from pathlib import Path

def inspect_midi_file(filepath):
    """Detailed inspection of MIDI file"""
    print(f"\n{'='*70}")
    print(f"Inspecting: {filepath.name}")
    print(f"{'='*70}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    print(f"\nFirst 64 bytes (hex):")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Parse header
    pos = 0
    if data[pos:pos+4] != b'MThd':
        print(f"\nERROR: Missing MThd header")
        return
    
    header_size = struct.unpack('>I', data[4:8])[0]
    format_type = struct.unpack('>H', data[8:10])[0]
    ntracks = struct.unpack('>H', data[10:12])[0]
    division = struct.unpack('>H', data[12:14])[0]
    
    print(f"\nHeader:")
    print(f"  Size: {header_size}")
    print(f"  Format: {format_type}")
    print(f"  Tracks: {ntracks}")
    print(f"  Division: {division}")
    
    # Parse track
    pos = 14
    if data[pos:pos+4] != b'MTrk':
        print(f"\nERROR: Missing MTrk at pos {pos}")
        return
    
    track_size = struct.unpack('>I', data[pos+4:pos+8])[0]
    pos += 8
    
    print(f"\nTrack: {track_size} bytes")
    
    # Parse first 50 events
    print(f"\nFirst 50 MIDI events:")
    print(f"{'#':<5} {'Delta':<10} {'Status':<8} {'Byte1':<6} {'Byte2':<6} {'Description':<30}")
    print("-" * 70)
    
    event_num = 0
    running_status = 0
    abs_time = 0
    
    while event_num < 50 and pos < len(data) - 8:
        # Parse delta
        delta = 0
        while True:
            if pos >= len(data):
                break
            byte = data[pos]
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        abs_time += delta
        
        if pos >= len(data):
            break
        
        status = data[pos]
        
        if status == 0xFF:  # Meta
            pos += 1
            meta_type = data[pos]
            pos += 1
            
            length = 0
            while True:
                byte = data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if meta_type == 0x2F:
                print(f"{event_num:<5} {delta:<10} {'0xFF':<8} {'0x2F':<6} {'0':<6} {'End of Track':<30}")
                event_num += 1
                break
            
            data_bytes = data[pos:pos+length]
            pos += length
            
            if meta_type == 0x51:  # Tempo
                if len(data_bytes) == 3:
                    tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                    bpm = 60000000 / tempo if tempo > 0 else 0
                    print(f"{event_num:<5} {delta:<10} {'0xFF':<8} {'0x51':<6} {'':<6} {'Tempo: ' + str(int(bpm)) + ' BPM':<30}")
            elif meta_type == 0x03:  # Track name
                print(f"{event_num:<5} {delta:<10} {'0xFF':<8} {'0x03':<6} {'':<6} {'Name: ' + data_bytes.decode('ascii', errors='replace'):<30}")
            else:
                print(f"{event_num:<5} {delta:<10} {'0xFF':<8} {f'0x{meta_type:02X}':<6} {'':<6} {'Meta event':<30}")
            
            event_num += 1
            
        elif status >= 0x80:  # MIDI event
            running_status = status
            command = status & 0xF0
            channel = status & 0x0F
            pos += 1
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                desc = ""
                if command == 0x80:
                    desc = f"Note Off ch={channel} note={byte1} vel={byte2}"
                elif command == 0x90:
                    if byte2 > 0:
                        desc = f"Note On ch={channel} note={byte1} vel={byte2}"
                    else:
                        desc = f"Note Off ch={channel} note={byte1}"
                elif command == 0xB0:
                    desc = f"CC ch={channel} ctrl={byte1} val={byte2}"
                elif command == 0xE0:
                    pitch = (byte2 << 7) | byte1
                    desc = f"Pitch Bend ch={channel} val={pitch}"
                
                print(f"{event_num:<5} {delta:<10} {f'0x{status:02X}':<8} {f'0x{byte1:02X}':<6} {f'0x{byte2:02X}':<6} {desc:<30}")
                event_num += 1
                
            elif command in (0xC0, 0xD0):
                byte1 = data[pos]
                pos += 1
                
                if command == 0xC0:
                    desc = f"Program Change ch={channel} program={byte1}"
                else:
                    desc = f"Aftertouch ch={channel} pressure={byte1}"
                
                print(f"{event_num:<5} {delta:<10} {f'0x{status:02X}':<8} {f'0x{byte1:02X}':<6} {'0x00':<6} {desc:<30}")
                event_num += 1
                
        else:  # Running status
            command = running_status & 0xF0
            channel = running_status & 0x0F
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                desc = ""
                if command == 0x80:
                    desc = f"Note Off ch={channel} note={byte1} vel={byte2}"
                elif command == 0x90:
                    if byte2 > 0:
                        desc = f"Note On ch={channel} note={byte1} vel={byte2}"
                    else:
                        desc = f"Note Off ch={channel} note={byte1}"
                elif command == 0xB0:
                    desc = f"CC ch={channel} ctrl={byte1} val={byte2}"
                
                print(f"{event_num:<5} {delta:<10} {f'run':<8} {f'0x{byte1:02X}':<6} {f'0x{byte2:02X}':<6} {desc:<30}")
                event_num += 1
                
            elif command in (0xC0, 0xD0):
                byte1 = data[pos]
                pos += 1
                
                if command == 0xC0:
                    desc = f"Program Change ch={channel} program={byte1}"
                else:
                    desc = f"Aftertouch ch={channel} pressure={byte1}"
                
                print(f"{event_num:<5} {delta:<10} {f'run':<8} {f'0x{byte1:02X}':<6} {'0x00':<6} {desc:<30}")
                event_num += 1

def main():
    midi_dir = Path("output/fdmus_midi_v2")
    
    # Inspect track 000 (valid) and track 018 (problematic)
    test_tracks = ["track_000.mid", "track_018.mid", "track_001.mid"]
    
    for track in test_tracks:
        track_file = midi_dir / track
        if track_file.exists():
            inspect_midi_file(track_file)

if __name__ == "__main__":
    main()
