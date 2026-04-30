#!/usr/bin/env python3
"""
Convert XMIDI to standard MIDI - Final version
Fixes:
1. Add Tempo meta event at start
2. Remove XMIDI-specific meta events (0x21, 0x59)
3. Proper running status handling
4. Add End of Track
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

def extract_xmidi_events(data):
    """Extract MIDI events from XMIDI EVNT chunk"""
    events = []
    pos = 0
    
    if data[:4] != b'EVNT':
        return events
    
    chunk_size = struct.unpack('>I', data[4:8])[0]
    pos = 8
    end = pos + chunk_size
    
    running_status = 0
    
    while pos < end:
        delta, pos = parse_variable_length(data, pos, end)
        
        if pos >= end:
            break
        
        status = data[pos]
        pos += 1
        
        if status == 0xFF:  # Meta event
            if pos >= end:
                break
            meta_type = data[pos]
            pos += 1
            
            length, pos = parse_variable_length(data, pos, end)
            
            if meta_type == 0x2F:  # End of track
                events.append((delta, 0xFF, 0x2F, b''))
                break
            
            data_bytes = data[pos:pos+length]
            pos += length
            
            # Skip XMIDI-specific events but keep Tempo
            if meta_type == 0x21:  # Port prefix - skip
                continue
            if meta_type == 0x59:  # Key signature - skip
                continue
            
            events.append((delta, 0xFF, meta_type, data_bytes))
            running_status = 0
            
        elif status == 0xF0 or status == 0xF7:  # SysEx
            length, pos = parse_variable_length(data, pos, end)
            sys_ex_data = data[pos:pos+length]
            pos += length
            events.append((delta, status, 0, sys_ex_data))
            running_status = 0
            
        elif status >= 0x80:  # Channel event
            running_status = status
            command = status & 0xF0
            
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
            else:
                pos -= 1
                continue
        else:  # Running status
            pos -= 1
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                events.append((delta, running_status, byte1, byte2))
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = data[pos]
                pos += 1
                events.append((delta, running_status, byte1, 0))
    
    return events

def convert_xmidi_to_midi(xmidi_data):
    """Convert full XMIDI file to standard MIDI"""
    
    # Find FORM chunk
    if xmidi_data[:4] == b'FORM' and b'XMID' in xmidi_data[12:20]:
        pass
    elif b'FORM' in xmidi_data:
        form_pos = xmidi_data.find(b'FORM')
        xmidi_data = xmidi_data[form_pos:]
    else:
        return None
    
    # Find EVNT chunk
    evnt_pos = xmidi_data.find(b'EVNT')
    if evnt_pos < 0:
        return None
    
    # Extract events
    events = extract_xmidi_events(xmidi_data[evnt_pos:])
    
    if not events:
        return None
    
    # Build MIDI file
    midi_data = struct.pack('>4sIHHH',
                           b'MThd',
                           6,
                           0,    # Format 0
                           1,    # 1 track
                           120   # 120 ticks/quarter
                           )
    
    track_events = b''
    
    # Add Tempo at start (120 BPM)
    track_events += bytes([0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20])
    
    # Convert events
    for delta, status, byte1, byte2 in events:
        # Delta (variable length)
        if delta == 0:
            track_events += bytes([0])
        else:
            vl_bytes = []
            val = delta
            vl_bytes.append(val & 0x7F)
            val >>= 7
            while val > 0:
                vl_bytes.append(0x80 | (val & 0x7F))
                val >>= 7
            track_events += bytes(reversed(vl_bytes))
        
        # Event
        if status == 0xFF:  # Meta
            track_events += bytes([0xFF])
            if isinstance(byte2, bytes):
                track_events += bytes([byte1, len(byte2)]) + byte2
            else:
                track_events += bytes([byte1, 0])
        elif status in (0xF0, 0xF7):  # SysEx
            track_events += bytes([status])
            if isinstance(byte2, bytes):
                track_events += bytes([len(byte2)]) + byte2
        else:
            command = status & 0xF0
            if command in (0xC0, 0xD0):
                track_events += bytes([status, byte1])
            else:
                track_events += bytes([status, byte1, byte2])
    
    # Add End of Track
    if not any(e[1] == 0xFF and e[2] == 0x2F for e in events):
        track_events += bytes([0x00, 0xFF, 0x2F, 0x00])
    
    # Track chunk
    midi_data += struct.pack('>4sI', b'MTrk', len(track_events))
    midi_data += track_events
    
    return midi_data

def convert_all_tracks(input_dir, output_dir):
    """Convert all XMIDI tracks"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    
    for track_file in sorted(input_dir.glob("track_*.bin")):
        if track_file.stat().st_size < 100:
            continue
        
        with open(track_file, 'rb') as f:
            data = f.read()
        
        midi_data = convert_xmidi_to_midi(data)
        
        if midi_data:
            track_id = track_file.stem.split('_')[1]
            midi_file = output_dir / f"track_{track_id}.mid"
            midi_file.write_bytes(midi_data)
            print(f"  [{track_id}] {len(data)} -> {len(midi_data)} bytes")
            converted += 1
        else:
            print(f"  [SKIP] {track_file.name}")
    
    print(f"\nConverted {converted} tracks to {output_dir}")

def main():
    input_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi_final")
    
    if not input_dir.exists():
        print("Error: Input directory not found")
        return
    
    print("Converting XMIDI to standard MIDI (final)...")
    convert_all_tracks(input_dir, output_dir)
    
    print(f"\nMIDI files saved to: {output_dir}")

if __name__ == "__main__":
    main()
