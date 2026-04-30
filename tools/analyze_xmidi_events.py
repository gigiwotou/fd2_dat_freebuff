#!/usr/bin/env python3
"""
Detailed XMIDI analysis to find conversion issues
"""

import struct
from pathlib import Path

def parse_variable_length(data, pos, end):
    """Parse variable-length quantity"""
    value = 0
    count = 0
    while pos < end:
        byte = data[pos]
        pos += 1
        count += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
        if count > 4:
            print(f"  WARNING: Variable length too long at pos {pos}")
            break
    return value, pos

def analyze_xmidi(filepath):
    """Deep analysis of XMIDI structure"""
    print(f"\n{'='*70}")
    print(f"Analyzing XMIDI: {filepath.name}")
    print(f"{'='*70}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find EVNT chunk
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        print("No EVNT chunk found")
        return
    
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    print(f"EVNT chunk at 0x{evnt_pos:X}, size: {chunk_size}")
    
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    print(f"\nFirst 100 XMIDI events:")
    print(f"{'#':<5} {'Delta':<10} {'Status':<8} {'B1':<6} {'B2':<6} {'Description':<30}")
    print("-" * 70)
    
    event_num = 0
    running_status = 0
    issues = []
    
    while pos < end and event_num < 100:
        delta, pos = parse_variable_length(data, pos, end)
        
        if pos >= end:
            break
        
        status = data[pos]
        pos += 1
        
        if status == 0xFF:  # Meta
            if pos >= end:
                break
            meta_type = data[pos]
            pos += 1
            
            length, pos = parse_variable_length(data, pos, end)
            
            if meta_type == 0x2F:
                print(f"{event_num:<5} {delta:<10} 0xFF     0x2F   0x00   End of Track")
                event_num += 1
                break
            
            data_bytes = data[pos:pos+length]
            pos += length
            
            if meta_type == 0x51:  # Tempo
                if len(data_bytes) == 3:
                    tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                    bpm = 60000000 / tempo if tempo > 0 else 0
                    print(f"{event_num:<5} {delta:<10} 0xFF     0x51   {length:<4} Tempo: {bpm:.0f} BPM")
            elif meta_type == 0x21:
                print(f"{event_num:<5} {delta:<10} 0xFF     0x21   {length:<4} XMIDI port prefix")
            elif meta_type == 0x59:
                print(f"{event_num:<5} {delta:<10} 0xFF     0x59   {length:<4} XMIDI key signature")
            else:
                print(f"{event_num:<5} {delta:<10} 0xFF     0x{meta_type:02X} {length:<4} Meta event")
            
            event_num += 1
            
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                desc = ""
                if command == 0x80:
                    desc = f"Note Off ch={status&0xF} n={byte1} v={byte2}"
                elif command == 0x90:
                    if byte2 == 0:
                        desc = f"Note Off ch={status&0xF} n={byte1}"
                    else:
                        desc = f"Note On ch={status&0xF} n={byte1} v={byte2}"
                elif command == 0xB0:
                    desc = f"CC ch={status&0xF} c={byte1} v={byte2}"
                
                print(f"{event_num:<5} {delta:<10} 0x{status:02X}   0x{byte1:02X}   0x{byte2:02X} {desc}")
                event_num += 1
                
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = data[pos]
                pos += 1
                
                if command == 0xC0:
                    desc = f"Prog Ch ch={status&0xF} p={byte1}"
                else:
                    desc = f"Aftertouch ch={status&0xF} p={byte1}"
                
                print(f"{event_num:<5} {delta:<10} 0x{status:02X}   0x{byte1:02X}   0x00   {desc}")
                event_num += 1
        else:
            # Running status
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                desc = ""
                if command == 0x80:
                    desc = f"Note Off ch={running_status&0xF} n={byte1} v={byte2}"
                elif command == 0x90:
                    if byte2 == 0:
                        desc = f"Note Off ch={running_status&0xF} n={byte1}"
                    else:
                        desc = f"Note On ch={running_status&0xF} n={byte1} v={byte2}"
                elif command == 0xB0:
                    desc = f"CC ch={running_status&0xF} c={byte1} v={byte2}"
                
                print(f"{event_num:<5} {delta:<10} run      0x{byte1:02X}   0x{byte2:02X} {desc}")
                event_num += 1
            
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = data[pos]
                pos += 1
                
                if command == 0xC0:
                    desc = f"Prog Ch ch={running_status&0xF} p={byte1}"
                else:
                    desc = f"Aftertouch ch={running_status&0xF} p={byte1}"
                
                print(f"{event_num:<5} {delta:<10} run      0x{byte1:02X}   0x00   {desc}")
                event_num += 1
    
    # Count note events
    print(f"\nChecking for Note On/Off events...")
    pos = evnt_pos + 8
    running_status = 0
    note_on_count = 0
    note_off_count = 0
    
    while pos < end:
        delta, pos = parse_variable_length(data, pos, end)
        if pos >= end:
            break
        
        status = data[pos]
        pos += 1
        
        if status >= 0x80:
            running_status = status
            command = status & 0xF0
            
            if command == 0x90:
                if pos < end:
                    byte2 = data[pos+1]
                    if byte2 > 0:
                        note_on_count += 1
                    else:
                        note_off_count += 1
                    pos += 2
            elif command in (0x80, 0xA0, 0xB0, 0xE0):
                pos += 2
            elif command in (0xC0, 0xD0):
                pos += 1
        elif running_status & 0xF0 == 0x90:
            if pos < end:
                byte2 = data[pos+1]
                if byte2 > 0:
                    note_on_count += 1
                else:
                    note_off_count += 1
                pos += 2
        elif running_status & 0xF0 in (0x80, 0xA0, 0xB0, 0xE0):
            pos += 2
        elif running_status & 0xF0 in (0xC0, 0xD0):
            pos += 1
    
    print(f"  Note On events: {note_on_count}")
    print(f"  Note Off events: {note_off_count}")
    
    if note_on_count == 0 and note_off_count == 0:
        print(f"\n  *** WARNING: No note events found! ***")
        print(f"  *** This MIDI file will produce no sound ***")

def main():
    track_dir = Path("output/fdmus_tracks")
    
    # Analyze original XMIDI files
    test_tracks = ["track_000.bin", "track_001.bin", "track_005.bin"]
    
    for track in test_tracks:
        track_file = track_dir / track
        if track_file.exists():
            analyze_xmidi(track_file)

if __name__ == "__main__":
    main()
