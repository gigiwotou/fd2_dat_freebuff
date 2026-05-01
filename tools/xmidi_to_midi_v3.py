#!/usr/bin/env python3
"""
XMIDI to Standard MIDI converter V3
Based on IDA analysis + comparison with working MIDI files

Key findings:
1. XMIDI EVNT starts with header meta events (no delta time):
   - FF 58 (Time Signature)
   - FF 21 (Port Prefix) - multiple may exist
   - FF 59 (Key Signature)
   - (Optionally FF 51 Tempo)
   
2. After headers, events start with delta times (variable-length)

3. For Note On (0x90), XMIDI adds a duration field after note+velocity
   - This duration is in ticks
   - Need to generate corresponding Note Off events

4. Standard MIDI requires:
   - Delta time for EVERY event (including headers)
   - Separate Note Off events (0x80)
"""

import struct
from pathlib import Path
from mido import MidiFile, MidiTrack, Message, MetaMessage

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

def parse_xmidi_v3(evnt_data):
    """Parse XMIDI EVNT data, return list of (abs_tick, event)"""
    pos = 0
    end = len(evnt_data)
    running_status = None
    abs_tick = 0
    
    events = []  # (abs_tick, type, data)
    
    # Step 1: Parse header meta events (no delta time)
    # These will be placed at tick 0
    while pos < end and evnt_data[pos] == 0xFF:
        pos += 1  # Skip 0xFF
        meta_type = evnt_data[pos]
        pos += 1
        
        length, pos = read_variable_length(evnt_data, pos)
        meta_data = evnt_data[pos:pos+length]
        pos += length
        
        if meta_type == 0x58:
            # Time signature
            if length >= 4:
                events.append((0, 'time_signature', {
                    'numerator': meta_data[0],
                    'denominator': meta_data[1],
                    'clocks_per_click': meta_data[2],
                    'notated_32nd_notes_per_beat': meta_data[3]
                }))
        elif meta_type == 0x59:
            # Key signature
            if length >= 2:
                events.append((0, 'key_signature', {
                    'key': meta_data[0],
                    'mode': meta_data[1]
                }))
        elif meta_type == 0x51:
            # Tempo
            if length == 3:
                tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                events.append((0, 'tempo', {'tempo': tempo}))
        # Skip FF 21 (port prefix) and other meta events
    
    # Step 2: Parse regular events with delta times
    # After headers, first event may have no delta (delta=0) if it starts with status byte
    if pos < end and evnt_data[pos] >= 0x80:
        # First event after headers has delta=0
        delta = 0
    else:
        delta, pos = read_variable_length(evnt_data, pos)
    
    while pos < end:
        # If we didn't read delta above, read it now
        if delta is None:
            delta, pos = read_variable_length(evnt_data, pos)
            if pos >= end:
                break
        
        abs_tick += delta
        delta = None  # Reset for next iteration
        
        # Read status byte
        byte = evnt_data[pos]
        
        if byte >= 0x80:
            status = byte
            pos += 1
            running_status = status
        else:
            if running_status is None:
                # No running status, skip
                continue
            status = running_status
        
        status_type = status & 0xF0
        channel = status & 0x0F
        
        if status == 0xFF:
            # Meta event in stream
            meta_type = evnt_data[pos]
            pos += 1
            length, pos = read_variable_length(evnt_data, pos)
            meta_data = evnt_data[pos:pos+length]
            pos += length
            
            if meta_type == 0x51 and length == 3:
                tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                events.append((abs_tick, 'tempo', {'tempo': tempo}))
            elif meta_type == 0x2F:
                events.append((abs_tick, 'end_of_track', {}))
                break
        
        elif status >= 0xF0:
            # System events - skip
            running_status = None
            if status in (0xF0, 0xF7):
                length, pos = read_variable_length(evnt_data, pos)
                pos += length
            else:
                pos += 1
        
        else:
            # Regular MIDI events
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                data1 = evnt_data[pos]
                pos += 1
                data2 = evnt_data[pos]
                pos += 1
                
                if status_type == 0x90:
                    # Note On with duration
                    duration, pos = read_variable_length(evnt_data, pos)
                    
                    # Clamp to valid range
                    note = max(0, min(127, data1))
                    vel = max(0, min(127, data2))
                    
                    events.append((abs_tick, 'note_on', {
                        'channel': channel,
                        'note': note,
                        'velocity': vel
                    }))
                    
                    # Schedule Note Off
                    if duration > 0:
                        events.append((abs_tick + duration, 'note_off', {
                            'channel': channel,
                            'note': note,
                            'velocity': 0
                        }))
                
                elif status_type == 0x80:
                    note = max(0, min(127, data1))
                    vel = max(0, min(127, data2))
                    events.append((abs_tick, 'note_off', {
                        'channel': channel,
                        'note': note,
                        'velocity': vel
                    }))
                
                elif status_type == 0xB0:
                    ctrl = max(0, min(127, data1))
                    val = max(0, min(127, data2))
                    events.append((abs_tick, 'control_change', {
                        'channel': channel,
                        'control': ctrl,
                        'value': val
                    }))
                
                elif status_type == 0xE0:
                    lsb = max(0, min(127, data1))
                    msb = max(0, min(127, data2))
                    pitch = (msb << 7) | lsb
                    # Convert to -8192..8191 range
                    pitch = max(-8192, min(8191, pitch - 8192))
                    events.append((abs_tick, 'pitchwheel', {
                        'channel': channel,
                        'pitch': pitch
                    }))
                
                else:
                    events.append((abs_tick, 'unknown', {
                        'status': status,
                        'data1': data1,
                        'data2': data2
                    }))
            
            elif status_type == 0xC0:
                if pos >= end:
                    break
                prog = max(0, min(127, evnt_data[pos]))
                pos += 1
                events.append((abs_tick, 'program_change', {
                    'channel': channel,
                    'program': prog
                }))
            
            elif status_type == 0xD0:
                if pos >= end:
                    break
                val = max(0, min(127, evnt_data[pos]))
                pos += 1
                events.append((abs_tick, 'aftertouch', {
                    'channel': channel,
                    'value': val
                }))
    
    return events

def build_midi_v3(events, ppqn=480):
    """Build standard MIDI file from parsed events"""
    mid = MidiFile(type=0, ticks_per_beat=ppqn)
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Sort events by absolute tick
    events.sort(key=lambda x: x[0])
    
    # Convert to messages
    prev_tick = 0
    for abs_tick, event_type, data in events:
        delta = abs_tick - prev_tick
        
        if event_type == 'tempo':
            track.append(MetaMessage('set_tempo', tempo=data['tempo'], time=delta))
        elif event_type == 'time_signature':
            track.append(MetaMessage('time_signature',
                                   numerator=data['numerator'],
                                   denominator=data['denominator'],
                                   clocks_per_click=data.get('clocks_per_click', 24),
                                   notated_32nd_notes_per_beat=data.get('notated_32nd_notes_per_beat', 8),
                                   time=delta))
        elif event_type == 'key_signature':
            try:
                track.append(MetaMessage('key_signature',
                                       key=data['key'],
                                       mode=data['mode'],
                                       time=delta))
            except:
                pass
        elif event_type == 'note_on':
            track.append(Message('note_on',
                               channel=data['channel'],
                               note=data['note'],
                               velocity=data['velocity'],
                               time=delta))
        elif event_type == 'note_off':
            track.append(Message('note_off',
                               channel=data['channel'],
                               note=data['note'],
                               velocity=data['velocity'],
                               time=delta))
        elif event_type == 'control_change':
            track.append(Message('control_change',
                               channel=data['channel'],
                               control=data['control'],
                               value=data['value'],
                               time=delta))
        elif event_type == 'program_change':
            track.append(Message('program_change',
                               channel=data['channel'],
                               program=data['program'],
                               time=delta))
        elif event_type == 'pitchwheel':
            track.append(Message('pitchwheel',
                               channel=data['channel'],
                               pitch=data['pitch'],
                               time=delta))
        
        prev_tick = abs_tick
    
    # Add End of Track if not present
    if not any(isinstance(m, MetaMessage) and m.type == 'end_of_track' for m in track):
        track.append(MetaMessage('end_of_track', time=0))
    
    return mid

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
        events = parse_xmidi_v3(evnt_data)
        
        if not events:
            continue
        
        # Build MIDI
        mid = build_midi_v3(events)
        
        # Save
        midi_file = output_dir / f"track_{track_idx:03d}.mid"
        mid.save(midi_file)
        print(f"Track {track_idx:3d}: {len(evnt_data)} bytes -> {len(events)} events -> {midi_file.name}")
        converted += 1
    
    print(f"\nConverted {converted} tracks to {output_dir}")

if __name__ == "__main__":
    fdmus_path = Path("game/FDMUS.DAT")
    output_dir = Path("output/fdmus_midi_v3")
    
    print("XMIDI to MIDI Converter V3")
    print("=" * 60)
    convert_all_tracks(fdmus_path, output_dir)
