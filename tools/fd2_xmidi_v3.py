#!/usr/bin/env python3
"""
FD2 XMIDI to Standard MIDI Converter v3
Key insight from IDA: delta < 0x80 is explicit byte, >= 0x80 means delta=0 and byte is status
"""

import struct
import io
from pathlib import Path

def parse_xmidi_v3(data, pos, end):
    """Parse XMIDI with correct delta handling"""
    events = []
    running_status = None
    tempo_data = None
    
    while pos < end:
        delta = 0
        first_byte = data[pos]
        
        # If byte < 0x80, it's delta time. Otherwise delta=0 and byte is status
        if first_byte < 0x80:
            delta = first_byte
            pos += 1
            if pos >= end:
                break
            status = data[pos]
            pos += 1
        else:
            # No delta byte, this is status
            status = first_byte
            pos += 1
        
        if status == 0xFF:
            # Meta event
            if pos >= end:
                break
            
            meta_type = data[pos]
            pos += 1
            
            # Length is VLQ
            length = 0
            count = 0
            while pos < end and count < 4:
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
            # SysEx
            length = 0
            count = 0
            while pos < end and count < 4:
                byte = data[pos]
                pos += 1
                count += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if pos + length <= end:
                pos += length
                
        elif status >= 0x80:
            # New status
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 2 <= end:
                    b1 = data[pos]
                    b2 = data[pos + 1]
                    pos += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Note On - duration is VLQ
                            duration = 0
                            count = 0
                            while pos < end and count < 4:
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
                if pos <= end:
                    b1 = data[pos]
                    pos += 1
                    events.append((delta, 'midi', status, b1))
                    
        else:
            # Running status
            if running_status is None:
                continue
                
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                b1 = status
                if pos < end:
                    b2 = data[pos]
                    pos += 1
                    
                    if command == 0x90:
                        if b2 > 0:
                            duration = 0
                            count = 0
                            while pos < end and count < 4:
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

def convert_to_midi_v3(events, tempo_data=None):
    """Convert to standard MIDI"""
    midi = io.BytesIO()
    
    midi.write(b'MThd')
    midi.write(struct.pack('>I', 6))
    midi.write(struct.pack('>H', 0))  # Format 0
    midi.write(struct.pack('>H', 1))  # 1 track
    midi.write(struct.pack('>H', 480))  # 480 PPQN
    
    track = io.BytesIO()
    
    # Add tempo at start
    if tempo_data:
        track.write(b'\x00\xFF\x51\x03')
        track.write(tempo_data)
    
    for event in events:
        delta = event[0]
        evt_type = event[1]
        
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
                track.write(bytes([event[2], event[3]]))
            else:
                track.write(bytes([event[2], event[3], event[4]]))
    
    track.write(b'\xFF\x2F\x00')
    
    track_data = track.getvalue()
    midi.write(b'MTrk')
    midi.write(struct.pack('>I', len(track_data)))
    midi.write(track_data)
    
    return midi.getvalue()

def main():
    fdmus_path = Path('game/FDMUS.DAT')
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    output_dir = Path('output/fdmus_midi_v3')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
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
        
        events, tempo_data = parse_xmidi_v3(evnt_data, 0, len(evnt_data))
        
        if not events:
            continue
        
        midi_data = convert_to_midi_v3(events, tempo_data)
        
        output_file = output_dir / f'track_{i:03d}.mid'
        output_file.write_bytes(midi_data)
        print(f"Track {i}: {len(events)} events, {len(midi_data)} bytes")
        converted += 1
    
    print(f"\nConverted {converted}/{count} tracks to {output_dir}")

if __name__ == '__main__':
    main()
