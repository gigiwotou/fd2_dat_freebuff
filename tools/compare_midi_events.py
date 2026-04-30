#!/usr/bin/env python3
"""
Deep comparison: known_good.mid vs track_000.mid
Find why track_000.mid doesn't play
"""

import struct
from pathlib import Path

def analyze_midi_events(filepath, max_events=20):
    """Detailed analysis of MIDI events"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*70}")
    print(f"File: {filepath.name}")
    print(f"{'='*70}")
    
    # Find track
    mtrk_pos = data.find(b'MTrk')
    track_data = data[mtrk_pos+8:]
    
    print(f"\nFirst {max_events} events:")
    print(f"{'#':<5} {'Delta':<10} {'Status':<8} {'B1':<6} {'B2':<6} {'Type':<20}")
    print("-" * 70)
    
    pos = 0
    running_status = 0
    
    for i in range(max_events):
        if pos >= len(track_data):
            break
        
        # Parse delta
        delta = 0
        while pos < len(track_data):
            byte = track_data[pos]
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        if pos >= len(track_data):
            break
        
        status = track_data[pos]
        pos += 1
        
        if status == 0xFF:  # Meta
            if pos >= len(track_data):
                break
            meta_type = track_data[pos]
            pos += 1
            
            # Parse length
            length = 0
            while pos < len(track_data):
                byte = track_data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if meta_type == 0x2F:
                print(f"{i:<5} {delta:<10} 0xFF     0x2F   0x00   End of Track")
                break
            elif meta_type == 0x51:
                if length == 3 and pos + 3 <= len(track_data):
                    tempo = (track_data[pos] << 16) | (track_data[pos+1] << 8) | track_data[pos+2]
                    bpm = 60000000 / tempo
                    print(f"{i:<5} {delta:<10} 0xFF     0x51   0x03   Tempo: {bpm:.0f} BPM")
                pos += length
            elif meta_type == 0x03:
                name = track_data[pos:pos+length].decode('ascii', errors='replace')
                print(f"{i:<5} {delta:<10} 0xFF     0x03   0x{length:02X}   Name: {name}")
                pos += length
            else:
                print(f"{i:<5} {delta:<10} 0xFF     0x{meta_type:02X} 0x{length:02X}   Meta")
                pos += length
            
            running_status = 0
            
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= len(track_data):
                    break
                b1 = track_data[pos]
                b2 = track_data[pos+1]
                pos += 2
                
                type_str = ""
                if command == 0x80:
                    type_str = f"Note Off ch={status&0xF}"
                elif command == 0x90:
                    if b2 == 0:
                        type_str = f"Note Off ch={status&0xF}"
                    else:
                        type_str = f"Note On ch={status&0xF} note={b1} vel={b2}"
                elif command == 0xB0:
                    type_str = f"CC ch={status&0xF} ctrl={b1}"
                
                print(f"{i:<5} {delta:<10} 0x{status:02X}   0x{b1:02X}   0x{b2:02X} {type_str}")
                
            elif command in (0xC0, 0xD0):
                if pos >= len(track_data):
                    break
                b1 = track_data[pos]
                pos += 1
                
                if command == 0xC0:
                    type_str = f"ProgCh ch={status&0xF} prog={b1}"
                else:
                    type_str = f"Aftertouch ch={status&0xF}"
                
                print(f"{i:<5} {delta:<10} 0x{status:02X}   0x{b1:02X}   0x00   {type_str}")
        
        else:  # Running status
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= len(track_data):
                    break
                b1 = track_data[pos]
                b2 = track_data[pos+1]
                pos += 2
                
                type_str = ""
                if command == 0x90:
                    if b2 == 0:
                        type_str = f"Note Off ch={running_status&0xF}"
                    else:
                        type_str = f"Note On ch={running_status&0xF} note={b1} vel={b2}"
                elif command == 0x80:
                    type_str = f"Note Off ch={running_status&0xF}"
                elif command == 0xB0:
                    type_str = f"CC ch={running_status&0xF}"
                
                print(f"{i:<5} {delta:<10} run      0x{b1:02X}   0x{b2:02X} {type_str}")
            
            elif command in (0xC0, 0xD0):
                if pos >= len(track_data):
                    break
                b1 = track_data[pos]
                pos += 1
                
                if command == 0xC0:
                    type_str = f"ProgCh ch={running_status&0xF} prog={b1}"
                else:
                    type_str = f"Aftertouch"
                
                print(f"{i:<5} {delta:<10} run      0x{b1:02X}   0x00   {type_str}")

def count_note_events(filepath):
    """Count note on/off events in entire file"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    mtrk_pos = data.find(b'MTrk')
    track_data = data[mtrk_pos+8:]
    
    pos = 0
    running_status = 0
    note_on = 0
    note_off = 0
    
    while pos < len(track_data):
        delta = 0
        while pos < len(track_data):
            byte = track_data[pos]
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        if pos >= len(track_data):
            break
        
        status = track_data[pos]
        pos += 1
        
        if status == 0xFF:
            meta_type = track_data[pos]
            pos += 1
            length = 0
            while pos < len(track_data):
                byte = track_data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            pos += length
            running_status = 0
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                pos += 2
                if command == 0x90:
                    if status == 0x90 and pos >= 2:
                        b2 = track_data[pos-1]
                        if b2 > 0:
                            note_on += 1
                        else:
                            note_off += 1
            elif command in (0xC0, 0xD0):
                pos += 1
        else:
            command = running_status & 0xF0
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                pos += 2
                if command == 0x90 and pos >= 2:
                    b2 = track_data[pos-1]
                    if b2 > 0:
                        note_on += 1
                    else:
                        note_off += 1
            elif command in (0xC0, 0xD0):
                pos += 1
    
    print(f"\n{filepath.name}:")
    print(f"  Note On: {note_on}")
    print(f"  Note Off: {note_off}")
    print(f"  Total: {note_on + note_off}")

def main():
    # Analyze both files
    analyze_midi_events(Path("output/known_good.mid"), 10)
    analyze_midi_events(Path("output/fdmus_midi_v3/track_000.mid"), 50)
    
    # Count notes
    print(f"\n{'='*70}")
    print("Note Event Statistics:")
    print(f"{'='*70}")
    count_note_events(Path("output/known_good.mid"))
    count_note_events(Path("output/fdmus_midi_v3/track_000.mid"))

if __name__ == "__main__":
    main()
