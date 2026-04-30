#!/usr/bin/env python3
"""
FD2 XMIDI to Standard MIDI Converter
Based on IDA MCP analysis of sub_43270, sub_424B0, and related functions

Key findings from IDA:
1. Delta time uses VLQ format (max 4 bytes) - sub_424B0
2. Meta event length also uses VLQ format - sub_424B0
3. Tempo (0x51) is stored as standard MIDI tempo (game multiplies by 16 at runtime)
4. Note On events have an extra duration field after the note data
5. Running status is supported
"""

import struct
import io
from pathlib import Path

def parse_vlq(data, pos, end, max_bytes=4):
    """Parse Variable Length Quantity (from IDA sub_424B0)"""
    value = 0
    count = 0
    
    while pos < end and count < max_bytes:
        byte = data[pos]
        pos += 1
        count += 1
        value = (value << 7) | (byte & 0x7F)
        
        # If high bit is 0, we're done
        if not (byte & 0x80):
            break
    
    return value, pos

def write_vlq(value):
    """Write a value as VLQ"""
    if value < 0:
        value = 0
    
    # Special case for 0
    if value == 0:
        return bytes([0])
    
    # Calculate how many 7-bit groups we need
    bits = value.bit_length()
    num_bytes = (bits + 6) // 7
    
    result = []
    for i in range(num_bytes - 1, -1, -1):
        byte = (value >> (i * 7)) & 0x7F
        if i > 0:
            byte |= 0x80  # Set continuation bit
        result.append(byte)
    
    return bytes(result)

def parse_xmidi_events(data, pos, end):
    """Parse XMIDI events based on IDA analysis"""
    events = []
    running_status = None
    tempo_raw = None
    
    while pos < end:
        # Parse delta time (VLQ, max 4 bytes)
        delta, pos = parse_vlq(data, pos, end, max_bytes=4)
        
        if pos >= end:
            break
        
        status = data[pos]
        pos += 1
        
        if status == 0xFF:
            # Meta event
            if pos >= end:
                break
                
            meta_type = data[pos]
            pos += 1
            
            # Parse length using VLQ (IDA sub_424B0)
            length, pos = parse_vlq(data, pos, end, max_bytes=4)
            
            if meta_type == 0x2F:
                # End of Track
                events.append((delta, 'meta', 0x2F, b''))
                break
            elif meta_type == 0x51 and length == 3:
                # Tempo - keep original value (game multiplies by 16 at runtime)
                if pos + 3 <= end:
                    tempo_data = data[pos:pos+3]
                    pos += 3
                    events.append((delta, 'meta', 0x51, tempo_data))
                    tempo_raw = (tempo_data[0] << 16) | (tempo_data[1] << 8) | tempo_data[2]
            else:
                # Other meta events
                if pos + length <= end:
                    meta_data = data[pos:pos+length]
                    pos += length
                    events.append((delta, 'meta', meta_type, meta_data))
                    
        elif status == 0xF0 or status == 0xF7:
            # SysEx - skip (IDA handles with sub_424B0 for length)
            length, pos = parse_vlq(data, pos, end, max_bytes=4)
            if pos + length <= end:
                pos += length
                
        elif status >= 0x80:
            # New status byte
            running_status = status
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                # 2 data bytes
                if pos + 2 <= end:
                    b1 = data[pos]
                    b2 = data[pos + 1]
                    pos += 2
                    
                    # Clamp values to MIDI range (0-127)
                    b1 = max(0, min(127, b1))
                    b2 = max(0, min(127, b2))
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Note On - XMIDI has extra duration field!
                            # From IDA: sub_424B0 is called after note on
                            duration, pos = parse_vlq(data, pos, end, max_bytes=4)
                            events.append((delta, 'note_on', channel, b1, b2, duration))
                        else:
                            # Note Off (velocity 0 = note off)
                            events.append((delta, 'note_off', channel, b1, 0))
                    elif command == 0x80:
                        events.append((delta, 'note_off', channel, b1, 0))
                    else:
                        events.append((delta, 'midi', status, b1, b2))
                        
            elif command in (0xC0, 0xD0):
                # 1 data byte
                if pos <= end:
                    b1 = data[pos]
                    pos += 1
                    b1 = max(0, min(127, b1))
                    events.append((delta, 'midi', status, b1))
                    
        else:
            # Running status
            if running_status is None:
                # Invalid - skip this byte
                continue
                
            command = running_status & 0xF0
            channel = running_status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                # Need 2 data bytes - status is first data byte
                b1 = status
                if pos < end:
                    b2 = data[pos]
                    pos += 1
                    
                    b1 = max(0, min(127, b1))
                    b2 = max(0, min(127, b2))
                    
                    if command == 0x90:
                        if b2 > 0:
                            duration, pos = parse_vlq(data, pos, end, max_bytes=4)
                            events.append((delta, 'note_on', channel, b1, b2, duration))
                        else:
                            events.append((delta, 'note_off', channel, b1, 0))
                    elif command == 0x80:
                        events.append((delta, 'note_off', channel, b1, 0))
                    else:
                        events.append((delta, 'midi', running_status, b1, b2))
                        
            elif command in (0xC0, 0xD0):
                # Need 1 data byte - status is the data byte
                b1 = status
                b1 = max(0, min(127, b1))
                events.append((delta, 'midi', running_status, b1))
    
    return events, tempo_raw

def convert_xmidi_to_midi(xmidi_data):
    """Convert XMIDI track to standard MIDI format"""
    # Find EVNT chunk
    evnt_pos = xmidi_data.find(b'EVNT')
    if evnt_pos < 0:
        return None
    
    chunk_size = struct.unpack('>I', xmidi_data[evnt_pos+4:evnt_pos+8])[0]
    data_start = evnt_pos + 8
    data_end = data_start + chunk_size
    
    # Parse events
    events, tempo_raw = parse_xmidi_events(xmidi_data, data_start, data_end)
    
    if not events:
        return None
    
    # Build MIDI file
    midi = io.BytesIO()
    
    # MIDI header: MThd + size + format + ntrks + division
    midi.write(b'MThd')
    midi.write(struct.pack('>I', 6))  # Header size
    midi.write(struct.pack('>H', 0))  # Format 0 (single track)
    midi.write(struct.pack('>H', 1))  # 1 track
    midi.write(struct.pack('>H', 480))  # 480 ticks per quarter note
    
    # Track header: MTrk + size (calculated later)
    track_data = io.BytesIO()
    
    # Add tempo event at the beginning if found
    if tempo_raw is not None:
        track_data.write(write_vlq(0))  # Delta 0
        track_data.write(bytes([0xFF, 0x51, 0x03]))  # Meta tempo, 3 bytes
        track_data.write(bytes([
            (tempo_raw >> 16) & 0xFF,
            (tempo_raw >> 8) & 0xFF,
            tempo_raw & 0xFF
        ]))
    
    # Write all events
    for event in events:
        delta = event[0]
        track_data.write(write_vlq(delta))
        
        if event[1] == 'meta':
            _, meta_type, meta_data = event
            if meta_type == 0x2F:
                track_data.write(bytes([0xFF, 0x2F, 0x00]))
            else:
                track_data.write(bytes([0xFF, meta_type, len(meta_data)]))
                track_data.write(meta_data)
                
        elif event[1] == 'note_on':
            _, channel, note, velocity, duration = event
            track_data.write(bytes([0x90 | channel, note, velocity]))
            
            # Add note off event after duration ticks
            track_data.write(write_vlq(duration))
            track_data.write(bytes([0x80 | channel, note, 0]))
            
        elif event[1] == 'note_off':
            _, channel, note, _ = event
            track_data.write(bytes([0x80 | channel, note, 0]))
            
        elif event[1] == 'midi':
            if len(event) == 4:
                _, status, b1 = event
                track_data.write(bytes([status, b1]))
            else:
                _, status, b1, b2 = event
                track_data.write(bytes([status, b1, b2]))
    
    # End of track
    track_data.write(bytes([0xFF, 0x2F, 0x00]))
    
    # Write track
    track_bytes = track_data.getvalue()
    midi.write(b'MTrk')
    midi.write(struct.pack('>I', len(track_bytes)))
    midi.write(track_bytes)
    
    return midi.getvalue()

def main():
    # Extract from FDMUS.DAT
    fdmus_path = Path('game/FDMUS.DAT')
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    # Parse header
    if data[:6] != b'LLLLLL':
        print("Invalid FDMUS.DAT format")
        return
    
    count = struct.unpack('<I', data[6:10])[0]
    print(f"Music count: {count}")
    
    # Parse offset table
    offsets = []
    for i in range(count):
        offset = struct.unpack('<I', data[10 + i*4:14 + i*4])[0]
        offsets.append(offset)
    
    # Create output directory
    output_dir = Path('output/fdmus_midi_fixed')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert each track
    for i in range(count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        track_data = data[start:end]
        
        midi_data = convert_xmidi_to_midi(track_data)
        if midi_data:
            output_file = output_dir / f'track_{i:03d}.mid'
            output_file.write_bytes(midi_data)
            print(f"Converted track {i}: {len(midi_data)} bytes")
        else:
            print(f"Failed to convert track {i}")
    
    print(f"\nConverted {count} tracks to {output_dir}")

if __name__ == '__main__':
    main()
