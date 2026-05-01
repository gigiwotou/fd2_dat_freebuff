#!/usr/bin/env python3
"""
XMIDI to Standard MIDI converter V4
Uses raw MIDI byte writing instead of mido to avoid delta=0 bug
"""

import struct
from pathlib import Path

def read_variable_length(data, pos):
    """IDA sub_424B0: Variable-length integer decoder"""
    value = 0
    count = 0
    while count < 4 and pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        count += 1
        if not (byte & 0x80):
            break
    return value, pos

def write_variable_length(value):
    """Write variable-length integer"""
    if value < 0:
        value = 0
    elif value > 0x0FFFFFFF:
        value = 0x0FFFFFFF
    
    bytes_list = []
    bytes_list.append(value & 0x7F)
    value >>= 7
    
    while value > 0:
        bytes_list.append((value & 0x7F) | 0x80)
        value >>= 7
    
    return bytes(bytes_list[::-1])

def parse_xmidi_v4(evnt_data):
    """Parse XMIDI EVNT data, return list of (abs_tick, raw_midi_bytes)"""
    pos = 0
    end = len(evnt_data)
    running_status = None
    abs_tick = 0
    
    events = []  # (abs_tick, raw_bytes_for_event)
    
    # Step 1: Parse header meta events (no delta time)
    while pos < end and evnt_data[pos] == 0xFF:
        pos += 1
        meta_type = evnt_data[pos]
        pos += 1
        
        length, pos = read_variable_length(evnt_data, pos)
        meta_data = evnt_data[pos:pos+length]
        pos += length
        
        # Build raw MIDI meta event: FF + type + length + data
        # length in standard MIDI is variable-length encoded
        event_bytes = bytes([0xFF, meta_type]) + write_variable_length(length) + meta_data
        events.append((0, event_bytes))
    
    # Step 2: Parse regular events with delta times
    # After headers, first event has delta=0 (no delta bytes in XMIDI)
    # Subsequent events: if byte >= 0x80, it's a status byte with delta=0
    
    delta = 0  # First event after headers always has delta=0
    
    while pos < end:
        abs_tick += delta
        
        # Check if next byte is a status byte (delta=0, no delta bytes)
        byte = evnt_data[pos]
        
        # If byte >= 0x80, it's a status byte with delta=0
        # If byte < 0x80, it's a delta time
        if byte >= 0x80:
            delta = 0
            # Status byte will be read below
        else:
            # Read delta time
            delta, pos = read_variable_length(evnt_data, pos)
            if pos >= end:
                break
            byte = evnt_data[pos]
        
        if byte >= 0x80:
            status = byte
            pos += 1
            running_status = status
        else:
            if running_status is None:
                continue
            status = running_status
        
        status_type = status & 0xF0
        channel = status & 0x0F
        
        if status == 0xFF:
            # Meta event
            meta_type = evnt_data[pos]
            pos += 1
            length, pos = read_variable_length(evnt_data, pos)
            meta_data = evnt_data[pos:pos+length]
            pos += length
            
            event_bytes = bytes([0xFF, meta_type]) + write_variable_length(length) + meta_data
            events.append((abs_tick, event_bytes))
            
            if meta_type == 0x2F:
                break
        
        elif status >= 0xF0:
            running_status = None
            if status in (0xF0, 0xF7):
                length, pos = read_variable_length(evnt_data, pos)
                sysex_data = evnt_data[pos:pos+length]
                pos += length
                event_bytes = bytes([status]) + write_variable_length(length) + sysex_data
                events.append((abs_tick, event_bytes))
            else:
                if pos < end:
                    event_bytes = bytes([status, evnt_data[pos]])
                    pos += 1
                    events.append((abs_tick, event_bytes))
        
        else:
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                data1 = evnt_data[pos]
                pos += 1
                data2 = evnt_data[pos]
                pos += 1
                
                # Clamp to valid range
                data1 = max(0, min(127, data1))
                data2 = max(0, min(127, data2))
                
                if status_type == 0x90:
                    # Note On with duration
                    duration, pos = read_variable_length(evnt_data, pos)
                    
                    # Note On
                    event_bytes = bytes([status, data1, data2])
                    events.append((abs_tick, event_bytes))
                    
                    # Schedule Note Off
                    if duration > 0:
                        note_off_bytes = bytes([0x80 | channel, data1, 0])
                        events.append((abs_tick + duration, note_off_bytes))
                
                else:
                    event_bytes = bytes([status, data1, data2])
                    events.append((abs_tick, event_bytes))
            
            elif status_type in (0xC0, 0xD0):
                if pos >= end:
                    break
                data1 = max(0, min(127, evnt_data[pos]))
                pos += 1
                event_bytes = bytes([status, data1])
                events.append((abs_tick, event_bytes))
    
    return events

def build_midi_raw(events, ppqn=480):
    """Build raw MIDI file bytes"""
    # Build track data
    track_data = bytearray()
    events.sort(key=lambda x: x[0])
    
    prev_tick = 0
    for abs_tick, event_bytes in events:
        delta = abs_tick - prev_tick
        
        # Write delta time (ALWAYS write it, even if 0)
        track_data.extend(write_variable_length(delta))
        
        # Write event bytes
        track_data.extend(event_bytes)
        
        prev_tick = abs_tick
    
    # Add End of Track if not present
    if not (len(track_data) >= 3 and track_data[-3] == 0xFF and track_data[-2] == 0x2F):
        track_data.extend([0x00, 0xFF, 0x2F, 0x00])
    
    # Build complete MIDI file
    midi_data = bytearray()
    
    # Header
    midi_data.extend(b'MThd')
    midi_data.extend(struct.pack('>I', 6))  # Header length
    midi_data.extend(struct.pack('>HHH', 0, 1, ppqn))  # Format 0, 1 track, PPQN
    
    # Track
    midi_data.extend(b'MTrk')
    midi_data.extend(struct.pack('>I', len(track_data)))
    midi_data.extend(track_data)
    
    return bytes(midi_data)

def convert_all_tracks(fdmus_path, output_dir, track_indices=None):
    """Convert all XMIDI tracks"""
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    if track_indices is None:
        track_indices = range(count)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    
    for track_idx in track_indices:
        if track_idx >= count:
            continue
        
        start = offsets[track_idx]
        end = offsets[track_idx+1] if track_idx+1 < count else len(data)
        track_data = data[start:end]
        
        evnt_pos = track_data.find(b'EVNT')
        if evnt_pos < 0:
            continue
        
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        # Parse XMIDI
        events = parse_xmidi_v4(evnt_data)
        
        if not events:
            continue
        
        # Build MIDI
        midi_bytes = build_midi_raw(events)
        
        # Save
        midi_file = output_dir / f"track_{track_idx:03d}.mid"
        midi_file.write_bytes(midi_bytes)
        print(f"Track {track_idx:3d}: {len(evnt_data)} bytes -> {len(events)} events -> {midi_file.name} ({len(midi_bytes)} bytes)")
        converted += 1
    
    print(f"\nConverted {converted} tracks to {output_dir}")

if __name__ == "__main__":
    fdmus_path = Path("game/FDMUS.DAT")
    output_dir = Path("output/fdmus_midi_v4")
    
    print("XMIDI to MIDI Converter V4 (Raw byte writing)")
    print("=" * 60)
    convert_all_tracks(fdmus_path, output_dir)
