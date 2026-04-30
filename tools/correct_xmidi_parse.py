#!/usr/bin/env python3
"""
Correct XMIDI parser - properly handle running status
The key insight: running status is only used when status byte < 0x80
"""

import struct
from pathlib import Path

def parse_variable_length(data, pos, end):
    """Parse variable-length quantity"""
    value = 0
    while pos < end:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos

def correct_parse_xmidi(data):
    """Parse XMIDI with correct running status handling"""
    events = []
    
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        return events
    
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    running_status = 0
    
    while pos < end:
        delta, pos = parse_variable_length(data, pos, end)
        
        if pos >= end:
            break
        
        # Determine if this is a status byte or running status
        byte = data[pos]
        
        if byte >= 0x80:
            # This is a new status byte
            status = byte
            pos += 1
            running_status = status
        else:
            # This is data - use running status
            status = running_status
        
        # Now parse based on status
        if status == 0xFF:  # Meta
            if pos >= end:
                break
            meta_type = data[pos]
            pos += 1
            
            length = 0
            while pos < end:
                byte = data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if meta_type == 0x2F:
                events.append((delta, 0xFF, 0x2F, b''))
                break
            
            data_bytes = data[pos:pos+length]
            pos += length
            
            if meta_type not in (0x21, 0x59):
                events.append((delta, 0xFF, meta_type, data_bytes))
            
            running_status = 0
            
        elif status in (0xF0, 0xF7):  # SysEx
            length, pos = parse_variable_length(data, pos, end)
            sys_ex_data = data[pos:pos+length]
            pos += length
            events.append((delta, status, 0, sys_ex_data))
            running_status = 0
            
        elif status >= 0x80:  # MIDI channel event
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                events.append((delta, status, byte1, byte2))
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = data[pos]
                pos += 1
                events.append((delta, status, byte1, 0))
    
    return events

def analyze_events(events, max_show=30):
    """Analyze parsed events"""
    print(f"\n{'='*70}")
    print(f"Parsed {len(events)} events")
    print(f"{'='*70}")
    
    print(f"\n{'#':<5} {'Delta':<10} {'Status':<8} {'B1':<6} {'B2':<6} {'Description':<40}")
    print("-" * 70)
    
    note_events = []
    
    for i, (delta, status, b1, b2) in enumerate(events[:max_show]):
        if status == 0xFF:
            if b1 == 0x2F:
                desc = "End of Track"
            elif b1 == 0x51 and isinstance(b2, bytes) and len(b2) == 3:
                tempo = (b2[0] << 16) | (b2[1] << 8) | b2[2]
                bpm = 60000000 / tempo
                desc = f"Tempo: {bpm:.0f} BPM"
            else:
                desc = f"Meta 0x{b1:02X}"
            print(f"{i:<5} {delta:<10} 0xFF     0x{b1:02X}   {b2:<4} {desc}")
        else:
            command = status & 0xF0
            channel = status & 0xF
            
            if command == 0x90:
                if b2 > 0:
                    desc = f"Note On  ch={channel} note={b1} vel={b2}"
                    note_events.append(('On', channel, b1, b2))
                else:
                    desc = f"Note Off ch={channel} note={b1}"
                    note_events.append(('Off', channel, b1, 0))
            elif command == 0x80:
                desc = f"Note Off ch={channel} note={b1} vel={b2}"
                note_events.append(('Off', channel, b1, b2))
            elif command == 0xB0:
                desc = f"CC       ch={channel} ctrl={b1} val={b2}"
            elif command == 0xC0:
                desc = f"ProgCh   ch={channel} prog={b1}"
            else:
                desc = f"Command  0x{command:02X} ch={channel}"
            
            print(f"{i:<5} {delta:<10} 0x{status:02X}   0x{b1:02X}   0x{b2:02X} {desc}")
    
    # Analyze notes
    print(f"\n{'='*70}")
    print(f"Note Analysis:")
    print(f"{'='*70}")
    
    on_notes = [e for e in note_events if e[0] == 'On']
    off_notes = [e for e in note_events if e[0] == 'Off']
    
    print(f"  Note On events: {len(on_notes)}")
    print(f"  Note Off events: {len(off_notes)}")
    
    if on_notes:
        notes = [e[2] for e in on_notes]
        vels = [e[3] for e in on_notes]
        print(f"  Note range: {min(notes)} - {max(notes)}")
        print(f"  Velocity range: {min(vels)} - {max(vels)}")
        
        # Check if notes are in valid MIDI range
        valid = [n for n in notes if 0 <= n <= 127]
        invalid = [n for n in notes if n < 0 or n > 127]
        
        print(f"  Valid notes (0-127): {len(valid)}")
        print(f"  Invalid notes: {len(invalid)}")
        
        if invalid:
            print(f"\n  *** PROBLEM: Notes outside MIDI range ***")

def main():
    track_dir = Path("output/fdmus_tracks")
    track_file = track_dir / "track_000.bin"
    
    if track_file.exists():
        events = correct_parse_xmidi(track_file.read_bytes())
        analyze_events(events, 40)

if __name__ == "__main__":
    main()
