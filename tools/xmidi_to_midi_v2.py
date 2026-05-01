#!/usr/bin/env python3
"""
XMIDI to Standard MIDI converter v2
Based on detailed analysis of FD2.EXE IDA decompilation

XMIDI EVNT format:
- Starts with header meta events (no delta time): FF 58 (time sig), FF 21 (port), FF 59 (key sig)
- Then FF 51 (tempo) event
- Then regular MIDI events with variable-length delta times
- Note On (0x90) has extra duration field after note+velocity
"""

import struct
from pathlib import Path
from mido import MidiFile, MidiTrack, Message, MetaMessage

def read_variable_length(data, pos):
    """
    IDA sub_424B0: Variable-length integer decoder
    Each byte: 7 data bits + 1 continuation bit (MSB)
    MSB=1 means more bytes follow, MSB=0 means last byte
    """
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

def parse_xmidi_to_mido_events(evnt_data):
    """
    Parse XMIDI EVNT data and return list of mido events
    Returns (meta_events, midi_events) where meta_events are header events
    """
    pos = 0
    end = len(evnt_data)
    running_status = None
    
    meta_events = []
    midi_events = []  # (delta, mido_message, duration_for_note_on)
    
    # Parse header meta events (no delta time at start)
    while pos < end:
        byte = evnt_data[pos]
        
        if byte != 0xFF:
            break  # First non-meta event, switch to normal parsing
        
        # Meta event
        pos += 1  # Skip 0xFF
        if pos >= end:
            break
        
        meta_type = evnt_data[pos]
        pos += 1
        
        # Read length (variable-length)
        length, pos = read_variable_length(evnt_data, pos)
        
        if pos + length > end:
            break
        
        meta_data = evnt_data[pos:pos+length]
        pos += length
        
        if meta_type == 0x58:
            # Time signature: numerator, denominator, clocks, notes
            if length >= 4:
                num = meta_data[0]
                denom = meta_data[1]
                meta_events.append(('time_signature', num, denom))
        elif meta_type == 0x59:
            # Key signature
            if length >= 2:
                meta_events.append(('key_signature', meta_data[0], meta_data[1]))
        elif meta_type == 0x51:
            # Tempo
            if length == 3:
                tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                meta_events.append(('tempo', tempo))
        elif meta_type == 0x21:
            # XMIDI port prefix - skip
            pass
    
    # Now parse regular events with delta times
    while pos < end:
        # Read delta time
        delta, pos = read_variable_length(evnt_data, pos)
        
        if pos >= end:
            break
        
        # Read status
        byte = evnt_data[pos]
        
        if byte >= 0x80:
            # Status byte
            status = byte
            pos += 1
            running_status = status
        else:
            # Running status
            if running_status is None:
                pos += 1  # Skip unknown byte
                continue
            status = running_status
        
        status_type = status & 0xF0
        channel = status & 0x0F
        
        if status == 0xFF:
            # Meta event in the middle of stream
            if pos >= end:
                break
            meta_type = evnt_data[pos]
            pos += 1
            length, pos = read_variable_length(evnt_data, pos)
            if pos + length > end:
                break
            meta_data = evnt_data[pos:pos+length]
            pos += length
            
            if meta_type == 0x51 and length == 3:
                tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                msg = MetaMessage('set_tempo', tempo=tempo, time=delta)
                midi_events.append((delta, msg))
            elif meta_type == 0x2F:
                # End of track
                msg = MetaMessage('end_of_track', time=delta)
                midi_events.append((delta, msg))
                break
            else:
                # Other meta events - skip
                pass
        
        elif status >= 0xF0:
            # System events - skip
            running_status = None
            if status == 0xF0 or status == 0xF7:
                length, pos = read_variable_length(evnt_data, pos)
                pos += length
            else:
                pos += 1
        
        else:
            # Regular MIDI events
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                # 2 data bytes
                if pos + 1 >= end:
                    break
                data1 = evnt_data[pos]
                pos += 1
                data2 = evnt_data[pos]
                pos += 1
                
                if status_type == 0x90:
                    # Note On - XMIDI has duration after data
                    duration, pos = read_variable_length(evnt_data, pos)
                    
                    # Clamp note and velocity to valid MIDI range
                    note = max(0, min(127, data1))
                    vel = max(0, min(127, data2))
                    
                    # Create Note On message
                    msg = Message('note_on', channel=channel, note=note, velocity=vel, time=delta)
                    midi_events.append((delta, msg, duration))
                    
                elif status_type == 0x80:
                    note = max(0, min(127, data1))
                    vel = max(0, min(127, data2))
                    msg = Message('note_off', channel=channel, note=note, velocity=vel, time=delta)
                    midi_events.append((delta, msg))
                    
                elif status_type == 0xB0:
                    ctrl = max(0, min(127, data1))
                    val = max(0, min(127, data2))
                    msg = Message('control_change', channel=channel, control=ctrl, value=val, time=delta)
                    midi_events.append((delta, msg))
                    
                elif status_type == 0xE0:
                    lsb = max(0, min(127, data1))
                    msb = max(0, min(127, data2))
                    value = (msb << 7) | lsb
                    # Clamp pitchwheel to -8192..8191
                    pitch = max(-8192, min(8191, value - 8192))
                    msg = Message('pitchwheel', channel=channel, pitch=pitch, time=delta)
                    midi_events.append((delta, msg))
                    
            elif status_type == 0xC0:
                # 1 data byte
                if pos >= end:
                    break
                prog = max(0, min(127, evnt_data[pos]))
                pos += 1
                msg = Message('program_change', channel=channel, program=prog, time=delta)
                midi_events.append((delta, msg))
                
            elif status_type == 0xD0:
                # 1 data byte
                if pos >= end:
                    break
                val = max(0, min(127, evnt_data[pos]))
                pos += 1
                msg = Message('aftertouch', channel=channel, value=val, time=delta)
                midi_events.append((delta, msg))
    
    return meta_events, midi_events

def build_midi_file(meta_events, midi_events, ppqn=480):
    """Build a standard MIDI file from parsed events"""
    mid = MidiFile(type=0, ticks_per_beat=ppqn)
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Add header meta events first
    for event in meta_events:
        if event[0] == 'tempo':
            track.append(MetaMessage('set_tempo', tempo=event[1], time=0))
        elif event[0] == 'time_signature':
            track.append(MetaMessage('time_signature', numerator=event[1], denominator=event[2], time=0))
        elif event[0] == 'key_signature':
            try:
                track.append(MetaMessage('key_signature', key=event[1], mode=event[2], time=0))
            except:
                pass
    
    # Build list of all events including Note Off from duration
    all_events = []  # (absolute_tick, message)
    
    abs_tick = 0
    for event in midi_events:
        delta = event[0]
        msg = event[1]
        abs_tick += delta
        
        if len(event) == 3 and hasattr(msg, 'type') and msg.type == 'note_on':
            # Note On with duration - add Note Off at abs_tick + duration
            duration = event[2]
            all_events.append((abs_tick, msg))
            
            # Create Note Off at the correct time
            note_off = Message('note_off', channel=msg.channel, note=msg.note, velocity=0, time=0)
            all_events.append((abs_tick + duration, note_off))
        else:
            all_events.append((abs_tick, msg))
    
    # Sort by absolute tick
    all_events.sort(key=lambda x: x[0])
    
    # Convert to relative delta times
    prev_tick = 0
    for abs_tick, msg in all_events:
        delta = abs_tick - prev_tick
        msg.time = delta
        track.append(msg)
        prev_tick = abs_tick
    
    # Add End of Track if not present
    if not any(isinstance(m, MetaMessage) and m.type == 'end_of_track' for m in track):
        track.append(MetaMessage('end_of_track', time=0))
    
    return mid

def convert_xmidi_file(fdmus_path, output_dir, track_indices=None):
    """Convert XMIDI tracks from FDMUS.DAT to standard MIDI"""
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    # Read track count and offsets
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
        
        # Find EVNT chunk
        evnt_pos = track_data.find(b'EVNT')
        if evnt_pos < 0:
            continue
        
        # Get EVNT data
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        # Parse XMIDI
        meta_events, midi_events = parse_xmidi_to_mido_events(evnt_data)
        
        if not midi_events:
            continue
        
        # Build MIDI file
        mid = build_midi_file(meta_events, midi_events)
        
        # Save
        midi_file = output_dir / f"track_{track_idx:03d}.mid"
        mid.save(midi_file)
        print(f"Track {track_idx:3d}: {len(evnt_data)} bytes EVNT -> {len(midi_events)} events -> {midi_file.name}")
        converted += 1
    
    print(f"\nConverted {converted} tracks to {output_dir}")

def main():
    fdmus_path = Path("game/FDMUS.DAT")
    output_dir = Path("output/fdmus_midi_v2")
    
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    print("XMIDI to MIDI Converter v2 (Based on IDA Analysis)")
    print("=" * 60)
    print("Converting tracks from FDMUS.DAT...")
    print()
    
    convert_xmidi_file(fdmus_path, output_dir)
    
    print("\nTest playback with:")
    print(f"  {output_dir}/track_000.mid")
    print(f"  {output_dir}/track_010.mid")
    print(f"  {output_dir}/track_011.mid")

if __name__ == "__main__":
    main()
