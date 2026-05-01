#!/usr/bin/env python3
"""
XMIDI to Standard MIDI converter
Based on IDA analysis of FD2.EXE audio playback functions

Key findings from reverse engineering:
1. sub_424B0: Variable-length integer decoder (delta time, note duration)
   - Each byte: 7 data bits + 1 continuation bit (MSB)
   - MSB=1 means more bytes follow, MSB=0 means last byte
   - Max 4 bytes

2. sub_43270: Main XMIDI playback loop
   - Reads delta time (variable-length)
   - Reads status byte (or uses running status)
   - For 0xFF meta events:
     - 0x2F: End of Track
     - 0x51: Set Tempo (3 bytes) - stores as tempo*16
     - 0x58: Time Signature
   - For 0x90 Note On: reads note, velocity, then duration (variable-length)
   - For other MIDI events: reads 1-2 data bytes based on status type

3. Event sizes:
   - 0x80, 0x90, 0xA0, 0xE0: 2 data bytes (3 bytes total)
   - 0xC0, 0xD0: 1 data byte (2 bytes total)
   - 0xB0: 2 data bytes (3 bytes total)

4. XMIDI EVNT format: [delta_time] [status_byte] [data_bytes...]
   - Delta time uses variable-length encoding
   - Running status is supported
"""

import struct
from pathlib import Path

def read_variable_length(data, pos):
    """
    IDA: sub_424B0 - Variable-length integer decoder
    Returns (value, new_pos)
    """
    value = 0
    count = 0
    while count < 4 and pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        count += 1
        if not (byte & 0x80):  # MSB=0 means last byte
            break
    
    if count >= 4 and (byte & 0x80):
        # Force stop after 4 bytes
        pass
    
    return value, pos

def is_midi_status(byte):
    """Check if byte is a MIDI status byte (MSB set)"""
    return byte >= 0x80

def parse_xmidi_events(evnt_data):
    """
    Parse XMIDI EVNT data into MIDI events
    Based on sub_43270 analysis
    
    Returns list of (delta_time, event_bytes)
    """
    events = []
    pos = 0
    end = len(evnt_data)
    running_status = None
    
    while pos < end:
        # Read delta time
        delta, pos = read_variable_length(evnt_data, pos)
        
        if pos >= end:
            break
        
        # Read status byte
        byte = evnt_data[pos]
        
        if is_midi_status(byte):
            # This is a status byte
            status = byte
            pos += 1
            
            # Check for system real-time or meta events
            if status == 0xFF:
                # Meta event
                if pos >= end:
                    break
                    
                meta_type = evnt_data[pos]
                pos += 1
                
                # Read length (variable-length in XMIDI)
                length, pos = read_variable_length(evnt_data, pos)
                
                if pos + length > end:
                    break
                    
                meta_data = evnt_data[pos:pos+length]
                pos += length
                
                # Build MIDI meta event: delta + FF + type + length + data
                event_bytes = bytes([0xFF, meta_type]) + encode_length_standard(length) + meta_data
                events.append((delta, event_bytes))
                
            elif status >= 0xF0:
                # System exclusive or other system events
                if status == 0xF0 or status == 0xF7:
                    # SysEx: read length + data
                    length, pos = read_variable_length(evnt_data, pos)
                    if pos + length > end:
                        break
                    sysex_data = evnt_data[pos:pos+length]
                    pos += length
                    
                    event_bytes = bytes([status]) + encode_length_standard(length) + sysex_data
                    events.append((delta, event_bytes))
                else:
                    # Other system events (F1-F6)
                    pos += 1  # Skip one byte
                    events.append((delta, bytes([status, evnt_data[pos-1]])))
                
                running_status = None  # System events cancel running status
            else:
                # Regular MIDI event
                running_status = status
                status_type = status & 0xF0
                
                # Determine data bytes count
                if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    # 2 data bytes
                    if pos + 1 > end:
                        break
                    data1 = evnt_data[pos]
                    pos += 1
                    
                    # For Note On (0x90), XMIDI has an extra duration field
                    if status_type == 0x90:
                        # Read duration (variable-length in XMIDI)
                        duration, pos = read_variable_length(evnt_data, pos)
                        
                        # In standard MIDI, Note On with velocity 0 = Note Off
                        # We'll use the duration to generate Note Off later
                        # For now, store duration for later processing
                        data2 = evnt_data[pos] if pos < end else 0
                        pos += 1
                        
                        event_bytes = bytes([status, data1, data2])
                        events.append((delta, event_bytes, duration))
                    else:
                        if pos >= end:
                            break
                        data2 = evnt_data[pos]
                        pos += 1
                        event_bytes = bytes([status, data1, data2])
                        events.append((delta, event_bytes))
                        
                elif status_type in (0xC0, 0xD0):
                    # 1 data byte
                    if pos >= end:
                        break
                    data1 = evnt_data[pos]
                    pos += 1
                    event_bytes = bytes([status, data1])
                    events.append((delta, event_bytes))
                else:
                    # Unknown status, skip
                    pass
        else:
            # Running status - use previous status
            if running_status is None:
                # No running status, skip this byte
                continue
            
            status = running_status
            status_type = status & 0xF0
            
            # byte is data1
            data1 = byte
            
            # Determine data bytes count
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                # 2 data bytes
                if pos >= end:
                    break
                data2 = evnt_data[pos]
                pos += 1
                
                # For Note On (0x90), XMIDI has an extra duration field
                if status_type == 0x90:
                    # Read duration (variable-length in XMIDI)
                    duration, pos = read_variable_length(evnt_data, pos)
                    
                    event_bytes = bytes([status, data1, data2])
                    events.append((delta, event_bytes, duration))
                else:
                    event_bytes = bytes([status, data1, data2])
                    events.append((delta, event_bytes))
                    
            elif status_type in (0xC0, 0xD0):
                # 1 data byte - already read
                event_bytes = bytes([status, data1])
                events.append((delta, event_bytes))
            else:
                # Unknown, skip
                pass
    
    return events

def encode_length_standard(length):
    """Encode length in standard MIDI format (1-4 bytes, MSB=continue)"""
    if length < 0x80:
        return bytes([length])
    elif length < 0x4000:
        return bytes([(length >> 7) | 0x80, length & 0x7F])
    elif length < 0x200000:
        return bytes([((length >> 14) | 0x80), ((length >> 7) & 0x7F) | 0x80, length & 0x7F])
    else:
        return bytes([((length >> 21) | 0x80), ((length >> 14) & 0x7F) | 0x80, 
                     ((length >> 7) & 0x7F) | 0x80, length & 0x7F])

def convert_xmidi_to_midi(evnt_data, track_idx=0):
    """
    Convert XMIDI EVNT data to standard MIDI track data
    """
    # Parse XMIDI events
    events = parse_xmidi_events(evnt_data)
    
    if not events:
        return None
    
    # Build MIDI track data
    track_data = bytearray()
    active_notes = []  # (note_off_delta, note_on_event)
    abs_tick = 0
    
    for event in events:
        delta = event[0]
        event_bytes = event[1]
        duration = event[2] if len(event) > 2 else None
        
        abs_tick += delta
        
        # Add delta time to track data
        track_data.extend(encode_length_standard(delta))
        track_data.extend(event_bytes)
        
        # If this is a Note On with duration, schedule Note Off
        if duration is not None and duration > 0:
            note = event_bytes[1]
            velocity = event_bytes[2]
            channel = event_bytes[0] & 0x0F
            
            # Calculate note off absolute tick
            note_off_tick = abs_tick + duration
            note_off_status = 0x80 | channel  # Note Off
            active_notes.append((note_off_tick, note_off_status, note, velocity))
    
    # Sort and insert Note Off events
    if active_notes:
        # We need to rebuild the track with Note Off events inserted
        track_data = bytearray()
        active_notes.sort(key=lambda x: x[0])
        
        # Merge Note On and Note Off events by absolute tick
        all_events = []
        abs_tick = 0
        
        for event in events:
            delta = event[0]
            event_bytes = event[1]
            duration = event[2] if len(event) > 2 else None
            
            abs_tick += delta
            all_events.append((abs_tick, event_bytes, 'note_on'))
            
            if duration is not None and duration > 0:
                note = event_bytes[1]
                velocity = event_bytes[2]
                channel = event_bytes[0] & 0x0F
                note_off_tick = abs_tick + duration
                note_off_status = 0x80 | channel
                all_events.append((note_off_tick, bytes([note_off_status, note, velocity]), 'note_off'))
        
        # Sort by absolute tick
        all_events.sort(key=lambda x: x[0])
        
        # Build track with relative delta times
        prev_tick = 0
        running_status = None
        
        for abs_tick, event_bytes, event_type in all_events:
            delta = abs_tick - prev_tick
            prev_tick = abs_tick
            
            # Add delta time
            track_data.extend(encode_length_standard(delta))
            
            # Optimize with running status
            status = event_bytes[0]
            if status == running_status and status >= 0x80:
                # Use running status - omit status byte
                track_data.extend(event_bytes[1:])
            else:
                track_data.extend(event_bytes)
                running_status = status
    
    # Add End of Track
    track_data.extend([0x00, 0xFF, 0x2F, 0x00])
    
    return bytes(track_data)

def extract_and_convert_from_dat(fdmus_path, output_dir, track_indices=None):
    """Extract XMIDI tracks from FDMUS.DAT and convert to MIDI"""
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
            print(f"  Track {track_idx}: No EVNT chunk found")
            continue
        
        # Get EVNT data
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        # Convert to MIDI
        midi_track = convert_xmidi_to_midi(evnt_data, track_idx)
        
        if midi_track:
            # Build complete MIDI file
            midi_data = struct.pack('>4sIHHH',
                                   b'MThd',
                                   6,
                                   0,    # Format 0
                                   1,    # 1 track
                                   480   # 480 ticks/quarter note (standard)
                                   )
            
            # Add track header and data
            midi_data += struct.pack('>4sI', b'MTrk', len(midi_track))
            midi_data += midi_track
            
            # Save
            midi_file = output_dir / f"track_{track_idx:03d}.mid"
            midi_file.write_bytes(midi_data)
            print(f"  Track {track_idx:3d}: {len(evnt_data)} bytes EVNT -> {len(midi_track)} bytes MIDI")
            converted += 1
        else:
            print(f"  Track {track_idx:3d}: Conversion failed")
    
    print(f"\nConverted {converted} tracks to {output_dir}")

def main():
    fdmus_path = Path("game/FDMUS.DAT")
    output_dir = Path("output/fdmus_midi_fixed")
    
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    print("XMIDI to MIDI Converter (Based on IDA Analysis)")
    print("=" * 60)
    print("Converting tracks from FDMUS.DAT...")
    print()
    
    # Convert all tracks
    extract_and_convert_from_dat(fdmus_path, output_dir)
    
    print("\nTest playback with:")
    print(f"  {output_dir}/track_000.mid")
    print(f"  {output_dir}/track_010.mid")
    print(f"  {output_dir}/track_011.mid")

if __name__ == "__main__":
    main()
