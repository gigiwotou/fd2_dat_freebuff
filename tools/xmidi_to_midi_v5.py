#!/usr/bin/env python3
"""
XMIDI to Standard MIDI converter V5
Based on xmi/main.c reference implementation

Key finding: delta time needs conversion!
factor = timebase * DEFAULT_QN / (qnlen * DEFAULT_TIMEBASE)
where:
  timebase = 960 (output MIDI PPQN)
  DEFAULT_QN = 500000 (default tempo)
  DEFAULT_TIMEBASE = 60
  qnlen = actual tempo from XMIDI
"""

import struct
from pathlib import Path

# Constants from main.c
TIMEBASE = 960  # Output MIDI PPQN
DEFAULT_TEMPO = 120
XMI_FREQ = 120
DEFAULT_TIMEBASE = XMI_FREQ * 60 // DEFAULT_TEMPO  # = 60
DEFAULT_QN = 60 * 1000000 // DEFAULT_TEMPO  # = 500000

def read_variable_length(data, pos):
    """Read variable-length integer (same as main.c)"""
    value = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
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

def parse_xmidi_v5(evnt_data):
    """Parse XMIDI EVNT data, return list of (raw_delta, raw_event_bytes)"""
    pos = 0
    end = len(evnt_data)
    running_status = None
    
    events = []  # (raw_delta, raw_event_bytes, is_note_on_with_duration)
    current_tempo = DEFAULT_QN  # Default tempo
    
    # Step 1: Parse header meta events (no delta time)
    while pos < end and evnt_data[pos] == 0xFF:
        pos += 1
        meta_type = evnt_data[pos]
        pos += 1
        
        length, pos = read_variable_length(evnt_data, pos)
        meta_data = evnt_data[pos:pos+length]
        pos += length
        
        if meta_type == 0x51 and length == 3:
            current_tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
        
        event_bytes = bytes([0xFF, meta_type]) + write_variable_length(length) + meta_data
        events.append((0, event_bytes, False))
    
    # Step 2: Parse events with delta times
    delta = 0  # First event after headers has delta=0
    
    while pos < end:
        abs_delta = delta  # Accumulate for conversion
        
        byte = evnt_data[pos]
        
        if byte >= 0x80:
            delta = 0
            status = byte
            pos += 1
            running_status = status
        else:
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
            meta_type = evnt_data[pos]
            pos += 1
            length, pos = read_variable_length(evnt_data, pos)
            meta_data = evnt_data[pos:pos+length]
            pos += length
            
            event_bytes = bytes([0xFF, meta_type]) + write_variable_length(length) + meta_data
            events.append((abs_delta, event_bytes, False))
            
            if meta_type == 0x51 and length == 3:
                current_tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
            
            if meta_type == 0x2F:
                break
        
        elif status >= 0xF0:
            running_status = None
            if status in (0xF0, 0xF7):
                length, pos = read_variable_length(evnt_data, pos)
                sysex_data = evnt_data[pos:pos+length]
                pos += length
                event_bytes = bytes([status]) + write_variable_length(length) + sysex_data
                events.append((abs_delta, event_bytes, False))
            else:
                if pos < end:
                    event_bytes = bytes([status, evnt_data[pos]])
                    pos += 1
                    events.append((abs_delta, event_bytes, False))
        
        else:
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                data1 = evnt_data[pos]
                pos += 1
                data2 = evnt_data[pos]
                pos += 1
                
                data1 = max(0, min(127, data1))
                data2 = max(0, min(127, data2))
                
                if status_type == 0x90:
                    # Note On with duration - CRITICAL!
                    duration, pos = read_variable_length(evnt_data, pos)
                    
                    # Note On event
                    event_bytes = bytes([status, data1, data2])
                    events.append((abs_delta, event_bytes, True, duration))
                
                else:
                    event_bytes = bytes([status, data1, data2])
                    events.append((abs_delta, event_bytes, False))
            
            elif status_type in (0xC0, 0xD0):
                if pos >= end:
                    break
                data1 = max(0, min(127, evnt_data[pos]))
                pos += 1
                event_bytes = bytes([status, data1])
                events.append((abs_delta, event_bytes, False))
    
    return events, current_tempo

def convert_deltas(events, qnlen):
    """Convert XMIDI deltas to MIDI deltas using the formula from main.c"""
    factor = TIMEBASE * DEFAULT_QN / (qnlen * DEFAULT_TIMEBASE)
    
    converted_events = []
    for event in events:
        raw_delta = event[0]
        
        # Apply conversion factor
        converted_delta = int(raw_delta * factor + 0.5)
        
        converted_events.append((converted_delta,) + event[1:])
    
    return converted_events

def build_midi_v5(events, qnlen, ppqn=TIMEBASE):
    """Build MIDI file with converted deltas"""
    # Build track data
    track_data = bytearray()
    
    for event in events:
        delta = event[0]
        event_bytes = event[1]
        is_note_on = event[2] if len(event) > 2 else False
        
        # Write delta time
        track_data.extend(write_variable_length(delta))
        
        # Write event
        track_data.extend(event_bytes)
        
        # If Note On with duration, schedule Note Off
        if is_note_on and len(event) == 4:
            duration_raw = event[3]
            duration_converted = int(duration_raw * (TIMEBASE * DEFAULT_QN / (qnlen * DEFAULT_TIMEBASE)) + 0.5)
            
            channel = event_bytes[0] & 0x0F
            note = event_bytes[1]
            note_off_bytes = bytes([0x80 | channel, note, 0])
            
            # We'll insert this later - for now, just mark it
            # Actually, we need to handle this differently...
            # The note off should be inserted at (current_tick + duration)
    
    # This approach won't work - we need to rebuild with note offs
    # Let me use a different approach
    return build_midi_with_note_offs(events, qnlen, ppqn)

def build_midi_with_note_offs(events, qnlen, ppqn=TIMEBASE):
    """Build MIDI file with proper Note Off events"""
    # Convert all deltas first
    converted = convert_deltas(events, qnlen)
    
    # Build list of all events including Note Offs
    all_events = []  # (abs_tick, event_bytes)
    abs_tick = 0
    
    for event in converted:
        delta = event[0]
        event_bytes = event[1]
        is_note_on = event[2] if len(event) > 2 else False
        
        abs_tick += delta
        
        all_events.append((abs_tick, event_bytes))
        
        # If Note On with duration, add Note Off
        if is_note_on and len(event) == 4:
            duration_raw = event[3]
            duration_converted = int(duration_raw * (TIMEBASE * DEFAULT_QN / (qnlen * DEFAULT_TIMEBASE)) + 0.5)
            
            channel = event_bytes[0] & 0x0F
            note = event_bytes[1]
            note_off_bytes = bytes([0x80 | channel, note, 0])
            
            all_events.append((abs_tick + duration_converted, note_off_bytes))
    
    # Sort by absolute tick
    all_events.sort(key=lambda x: x[0])
    
    # Build track with relative deltas
    track_data = bytearray()
    prev_tick = 0
    
    for abs_tick, event_bytes in all_events:
        delta = abs_tick - prev_tick
        track_data.extend(write_variable_length(delta))
        track_data.extend(event_bytes)
        prev_tick = abs_tick
    
    # Add End of Track
    track_data.extend([0x00, 0xFF, 0x2F, 0x00])
    
    # Build complete MIDI file
    midi_data = bytearray()
    midi_data.extend(b'MThd')
    midi_data.extend(struct.pack('>I', 6))
    midi_data.extend(struct.pack('>HHH', 0, 1, ppqn))
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
        events, final_tempo = parse_xmidi_v5(evnt_data)
        
        if not events:
            continue
        
        # Build MIDI with delta conversion
        midi_bytes = build_midi_with_note_offs(events, final_tempo)
        
        # Save
        midi_file = output_dir / f"track_{track_idx:03d}.mid"
        midi_file.write_bytes(midi_bytes)
        
        # Calculate factor for debugging
        factor = TIMEBASE * DEFAULT_QN / (final_tempo * DEFAULT_TIMEBASE)
        print(f"Track {track_idx:3d}: tempo={final_tempo} factor={factor:.4f} -> {midi_file.name}")
        converted += 1
    
    print(f"\nConverted {converted} tracks to {output_dir}")

if __name__ == "__main__":
    fdmus_path = Path("game/FDMUS.DAT")
    output_dir = Path("output/fdmus_midi_v5")
    
    print("XMIDI to MIDI Converter V5 (Based on main.c)")
    print(f"TIMEBASE={TIMEBASE}, DEFAULT_QN={DEFAULT_QN}, DEFAULT_TIMEBASE={DEFAULT_TIMEBASE}")
    print("=" * 60)
    convert_all_tracks(fdmus_path, output_dir)
