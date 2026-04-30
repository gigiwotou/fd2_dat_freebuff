#!/usr/bin/env python3
"""
Check if XMIDI notes are valid MIDI notes (0-127)
and velocities are reasonable
"""

import struct
from pathlib import Path

def analyze_notes(filepath):
    """Analyze note events in XMIDI"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {filepath.name}")
    print(f"{'='*60}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find EVNT
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        print("No EVNT found")
        return
    
    pos = evnt_pos + 8
    end = pos + struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    
    running_status = 0
    note_events = []
    
    while pos < end and len(note_events) < 50:
        # Parse delta
        delta = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        if pos >= end:
            break
        
        status = data[pos]
        pos += 1
        
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
            pos += length
            running_status = 0
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                if command == 0x90 and byte2 > 0:
                    note_events.append({
                        'type': 'Note On',
                        'channel': channel,
                        'note': byte1,
                        'velocity': byte2,
                        'delta': delta
                    })
                elif command == 0x90 and byte2 == 0:
                    note_events.append({
                        'type': 'Note Off',
                        'channel': channel,
                        'note': byte1,
                        'velocity': 0,
                        'delta': delta
                    })
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = data[pos]
                pos += 1
        else:
            command = running_status & 0xF0
            channel = running_status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                
                if command == 0x90 and byte2 > 0:
                    note_events.append({
                        'type': 'Note On',
                        'channel': channel,
                        'note': byte1,
                        'velocity': byte2,
                        'delta': delta
                    })
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = data[pos]
                pos += 1
    
    print(f"\nTotal note events: {len(note_events)}")
    
    # Show first 20 notes
    print(f"\n{'#':<5} {'Type':<10} {'Ch':<4} {'Note':<6} {'MIDI#':<6} {'Velocity':<10} {'Delta':<8}")
    print("-" * 60)
    
    for i, note in enumerate(note_events[:20]):
        midi_note = note['note']
        # Calculate frequency: f = 440 * 2^((n-69)/12)
        if 0 <= midi_note <= 127:
            freq = 440 * (2 ** ((midi_note - 69) / 12))
            note_name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][midi_note % 12]
            octave = (midi_note // 12) - 1
            display = f"{note_name}{octave} ({freq:.0f}Hz)"
        else:
            display = f"INVALID (out of range)"
        
        print(f"{i:<5} {note['type']:<10} {note['channel']:<4} {display:<24} {note['velocity']:<10} {note['delta']:<8}")
    
    # Check for issues
    invalid_notes = [n for n in note_events if n['note'] > 127 or n['note'] < 0]
    zero_velocity = [n for n in note_events if n['velocity'] == 0 and n['type'] == 'Note On']
    
    print(f"\nAnalysis:")
    print(f"  Total notes: {len(note_events)}")
    print(f"  Invalid notes (>127 or <0): {len(invalid_notes)}")
    print(f"  Note On with velocity=0: {len(zero_velocity)}")
    
    if invalid_notes:
        print(f"\n  *** PROBLEM: Invalid notes found! ***")
        print(f"  *** These will produce no sound ***")
    
    # Check channel distribution
    channels = {}
    for n in note_events:
        ch = n['channel']
        if ch not in channels:
            channels[ch] = 0
        channels[ch] += 1
    
    print(f"\n  Channel distribution:")
    for ch, count in sorted(channels.items()):
        ch_type = "Drums" if ch == 9 else "Melody"
        print(f"    Channel {ch}: {count} notes ({ch_type})")

def main():
    track_dir = Path("output/fdmus_tracks")
    
    # Analyze original XMIDI
    test_tracks = ["track_000.bin", "track_005.bin"]
    
    for track in test_tracks:
        track_file = track_dir / track
        if track_file.exists():
            analyze_notes(track_file)

if __name__ == "__main__":
    main()
