#!/usr/bin/env python3
"""
FD2 XMIDI to Standard MIDI Converter - CORRECTED
Based on IDA MCP analysis: delta time is SINGLE BYTE (0-127), NOT VLQ!
"""

import struct
import io
from pathlib import Path

def parse_xmidi_events(data, pos, end):
    """Parse XMIDI events with single-byte delta times"""
    events = []
    running_status = None
    tempo_data = None
    
    while pos < end:
        # Delta time is SINGLE BYTE (from IDA analysis)
        delta = data[pos]
        pos += 1
        
        if delta >= 0x80:
            # This shouldn't happen if parsing is correct
            # Delta should be < 0x80
            break
        
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
            
            # Length is VLQ (from IDA sub_424B0)
            length = 0
            max_bytes = 4
            count = 0
            while pos < end and count < max_bytes:
                byte = data[pos]
                pos += 1
                count += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if meta_type == 0x2F:
                events.append((delta, 'meta', 0x2F, b''))
                break
            elif meta_type == 0x51 and length == 3:
                if pos + 3 <= end:
                    tempo_data = bytes(data[pos:pos+3])
                    pos += 3
                    events.append((delta, 'meta', 0x51, tempo_data))
            else:
                if pos + length <= end:
                    meta_data = bytes(data[pos:pos+length])
                    pos += length
                    events.append((delta, 'meta', meta_type, meta_data))
                    
        elif status == 0xF0 or status == 0xF7:
            # SysEx - length is VLQ
            length = 0
            max_bytes = 4
            count = 0
            while pos < end and count < max_bytes:
                byte = data[pos]
                pos += 1
                count += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if pos + length <= end:
                pos += length
                
        elif status >= 0x80:
            # New status byte
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                # 2 data bytes
                if pos + 2 <= end:
                    b1 = data[pos]
                    b2 = data[pos + 1]
                    pos += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Note On - has duration after (VLQ from IDA)
                            duration = 0
                            max_bytes = 4
                            count = 0
                            dur_pos = pos
                            while pos < end and count < max_bytes:
                                byte = data[pos]
                                pos += 1
                                count += 1
                                duration = (duration << 7) | (byte & 0x7F)
                                if not (byte & 0x80):
                                    break
                            
                            events.append((delta, 'note_on', status & 0xF, b1, b2, duration))
                        else:
                            events.append((delta, 'note_off', status & 0xF, b1))
                    elif command == 0x80:
                        events.append((delta, 'note_off', status & 0xF, b1))
                    else:
                        events.append((delta, 'midi', status, b1, b2))
                        
            elif command in (0xC0, 0xD0):
                # 1 data byte
                if pos <= end:
                    b1 = data[pos]
                    pos += 1
                    events.append((delta, 'midi', status, b1))
                    
        else:
            # Running status
            if running_status is None:
                # Invalid - skip
                continue
                
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                b1 = status
                if pos < end:
                    b2 = data[pos]
                    pos += 1
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Duration is VLQ
                            duration = 0
                            max_bytes = 4
                            count = 0
                            while pos < end and count < max_bytes:
                                byte = data[pos]
                                pos += 1
                                count += 1
                                duration = (duration << 7) | (byte & 0x7F)
                                if not (byte & 0x80):
                                    break
                            
                            events.append((delta, 'note_on', running_status & 0xF, b1, b2, duration))
                        else:
                            events.append((delta, 'note_off', running_status & 0xF, b1))
                    elif command == 0x80:
                        events.append((delta, 'note_off', running_status & 0xF, b1))
                    else:
                        events.append((delta, 'midi', running_status, b1, b2))
                        
            elif command in (0xC0, 0xD0):
                events.append((delta, 'midi', running_status, status))
    
    return events, tempo_data

def write_vlq(value):
    """Write value as VLQ"""
    if value == 0:
        return b'\x00'
    
    bits = value.bit_length()
    num_bytes = (bits + 6) // 7
    
    result = []
    for i in range(num_bytes - 1, -1, -1):
        byte = (value >> (i * 7)) & 0x7F
        if i > 0:
            byte |= 0x80
        result.append(byte)
    
    return bytes(result)

def convert_to_midi(events, tempo_data=None):
    """Convert events to standard MIDI"""
    midi = io.BytesIO()
    
    # Header
    midi.write(b'MThd')
    midi.write(struct.pack('>I', 6))
    midi.write(struct.pack('>H', 0))  # Format 0
    midi.write(struct.pack('>H', 1))  # 1 track
    midi.write(struct.pack('>H', 480))  # 480 PPQN
    
    # Track
    track = io.BytesIO()
    
    if tempo_data:
        track.write(b'\x00\xFF\x51\x03')
        track.write(tempo_data)
    
    for event in events:
        delta = event[0]
        evt_type = event[1]
        
        # Write delta as VLQ
        track.write(write_vlq(delta))
        
        if evt_type == 'meta':
            meta_type = event[2]
            meta_data = event[3] if len(event) > 3 else b''
            if meta_type == 0x2F:
                track.write(b'\xFF\x2F\x00')
            else:
                track.write(bytes([0xFF, meta_type, len(meta_data)]))
                track.write(meta_data)
                
        elif evt_type == 'note_on':
            channel = event[2]
            note = max(0, min(127, event[3]))
            velocity = max(0, min(127, event[4]))
            duration = event[5] if len(event) > 5 else 0
            
            track.write(bytes([0x90 | channel, note, velocity]))
            
            if duration > 0:
                track.write(write_vlq(duration))
                track.write(bytes([0x80 | channel, note, 0]))
                
        elif evt_type == 'note_off':
            channel = event[2]
            note = max(0, min(127, event[3]))
            track.write(bytes([0x80 | channel, note, 0]))
            
        elif evt_type == 'midi':
            if len(event) == 4:
                status = event[2]
                b1 = event[3]
                track.write(bytes([status, b1]))
            else:
                status = event[2]
                b1 = event[3]
                b2 = event[4]
                track.write(bytes([status, b1, b2]))
    
    track.write(b'\xFF\x2F\x00')
    
    track_data = track.getvalue()
    midi.write(b'MTrk')
    midi.write(struct.pack('>I', len(track_data)))
    midi.write(track_data)
    
    return midi.getvalue()

def main():
    fdmus_path = Path('game/FDMUS.DAT')
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    output_dir = Path('output/fdmus_midi_corrected')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        track_data = data[start:end]
        
        evnt_pos = track_data.find(b'EVNT')
        if evnt_pos < 0:
            continue
        
        if evnt_pos + 8 > len(track_data):
            continue
        
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        
        if evnt_pos + 8 + chunk_size > len(track_data):
            continue
        
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        events, tempo_data = parse_xmidi_events(evnt_data, 0, len(evnt_data))
        
        if not events:
            continue
        
        midi_data = convert_to_midi(events, tempo_data)
        
        output_file = output_dir / f'track_{i:03d}.mid'
        output_file.write_bytes(midi_data)
        print(f"Track {i}: {len(events)} events -> {output_file}")

if __name__ == '__main__':
    main()
