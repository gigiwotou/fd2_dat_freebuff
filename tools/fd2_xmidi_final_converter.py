#!/usr/bin/env python3
"""
FD2 XMIDI to Standard MIDI Converter - Final Version
Based on IDA MCP deep analysis of sub_43270, sub_424B0, sub_422C0, sub_42980

Key findings:
1. XMIDI format: FORM XDIR INFO CAT XMID TIMB EVNT chunks
2. EVNT contains MIDI events with VLQ delta times
3. Delta parsing uses sub_424B0 - max 4 bytes VLQ
4. Meta event length also uses VLQ (sub_424B0)
5. Note On events have duration field after note data
6. Running status is supported
7. Tempo (0x51) is stored as standard MIDI tempo
"""

import struct
import io
from pathlib import Path

class XMIDIParser:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.end = len(data)
        self.running_status = None
    
    def parse_vlq(self, max_bytes=4):
        """Parse VLQ exactly like IDA sub_424B0"""
        value = 0
        count = 0
        
        while self.pos < self.end and count < max_bytes:
            byte = self.data[self.pos]
            self.pos += 1
            count += 1
            value = (byte & 0x7F) | (value << 7)
            
            if not (byte & 0x80):
                break
        
        return value
    
    def parse_events(self):
        """Parse all XMIDI events"""
        events = []
        self.running_status = None
        
        while self.pos < self.end:
            # Parse delta time
            delta = self.parse_vlq()
            
            if self.pos >= self.end:
                break
            
            status = self.data[self.pos]
            self.pos += 1
            
            if status == 0xFF:
                # Meta event
                if self.pos >= self.end:
                    break
                    
                meta_type = self.data[self.pos]
                self.pos += 1
                
                # Length is VLQ
                length = self.parse_vlq()
                
                if meta_type == 0x2F:
                    # End of Track
                    events.append((delta, 'meta', 0x2F, b''))
                    break
                elif meta_type == 0x51:
                    # Tempo
                    if self.pos + 3 <= self.end:
                        tempo_data = self.data[self.pos:self.pos+3]
                        self.pos += 3
                        events.append((delta, 'meta', 0x51, bytes(tempo_data)))
                else:
                    # Other meta events
                    if self.pos + length <= self.end:
                        meta_data = self.data[self.pos:self.pos+length]
                        self.pos += length
                        events.append((delta, 'meta', meta_type, bytes(meta_data)))
                        
            elif status == 0xF0 or status == 0xF7:
                # SysEx - skip
                length = self.parse_vlq()
                if self.pos + length <= self.end:
                    self.pos += length
                    
            elif status >= 0x80:
                # New status byte
                self.running_status = status
                command = status & 0xF0
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    if self.pos + 2 <= self.end:
                        b1 = self.data[self.pos]
                        b2 = self.data[self.pos + 1]
                        self.pos += 2
                        
                        if command == 0x90:
                            if b2 > 0:
                                # Note On - XMIDI has duration after
                                duration = self.parse_vlq()
                                events.append((delta, 'note_on', status & 0xF, b1, b2, duration))
                            else:
                                events.append((delta, 'note_off', status & 0xF, b1))
                        elif command == 0x80:
                            events.append((delta, 'note_off', status & 0xF, b1))
                        else:
                            events.append((delta, 'midi', status, b1, b2))
                            
                elif command in (0xC0, 0xD0):
                    if self.pos <= self.end:
                        b1 = self.data[self.pos]
                        self.pos += 1
                        events.append((delta, 'midi', status, b1))
                        
            else:
                # Running status
                if self.running_status is None:
                    continue
                    
                command = self.running_status & 0xF0
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    b1 = status
                    if self.pos < self.end:
                        b2 = self.data[self.pos]
                        self.pos += 1
                        
                        if command == 0x90:
                            if b2 > 0:
                                duration = self.parse_vlq()
                                events.append((delta, 'note_on', self.running_status & 0xF, b1, b2, duration))
                            else:
                                events.append((delta, 'note_off', self.running_status & 0xF, b1))
                        elif command == 0x80:
                            events.append((delta, 'note_off', self.running_status & 0xF, b1))
                        else:
                            events.append((delta, 'midi', self.running_status, b1, b2))
                            
                elif command in (0xC0, 0xD0):
                    events.append((delta, 'midi', self.running_status, status))
        
        return events

def extract_evnt_data(track_data):
    """Extract EVNT chunk data from track"""
    # Find FORM XDIR INFO CAT XMID TIMB EVNT structure
    evnt_pos = track_data.find(b'EVNT')
    if evnt_pos < 0:
        return None
    
    # EVNT chunk: 'EVNT' + size(4) + data
    if evnt_pos + 8 > len(track_data):
        return None
    
    chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
    
    if evnt_pos + 8 + chunk_size > len(track_data):
        return None
    
    return track_data[evnt_pos+8:evnt_pos+8+chunk_size]

def convert_to_midi(events, tempo_data=None):
    """Convert parsed events to MIDI format"""
    midi = io.BytesIO()
    
    # MIDI header
    midi.write(b'MThd')
    midi.write(struct.pack('>I', 6))
    midi.write(struct.pack('>H', 0))  # Format 0
    midi.write(struct.pack('>H', 1))  # 1 track
    midi.write(struct.pack('>H', 480))  # 480 PPQN
    
    # Track data
    track = io.BytesIO()
    
    # Add tempo at start if present
    if tempo_data:
        track.write(b'\x00')  # Delta 0
        track.write(b'\xFF\x51\x03')
        track.write(tempo_data)
    
    # Write events
    for event in events:
        delta = event[0]
        evt_type = event[1]
        
        # Write delta as VLQ
        if delta == 0:
            track.write(b'\x00')
        else:
            # Calculate VLQ bytes
            value = delta
            vlq_bytes = []
            if value == 0:
                vlq_bytes = [0]
            else:
                bits = value.bit_length()
                num_bytes = (bits + 6) // 7
                for i in range(num_bytes - 1, -1, -1):
                    byte = (value >> (i * 7)) & 0x7F
                    if i > 0:
                        byte |= 0x80
                    vlq_bytes.append(byte)
            track.write(bytes(vlq_bytes))
        
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
            note = event[3]
            velocity = event[4]
            duration = event[5] if len(event) > 5 else 0
            # Clamp values to MIDI range
            note = max(0, min(127, note))
            velocity = max(0, min(127, velocity))
            
            track.write(bytes([0x90 | channel, note, velocity]))
            
            # Write note off after duration
            if duration > 0:
                # Duration VLQ
                if duration == 0:
                    track.write(b'\x00')
                else:
                    bits = duration.bit_length()
                    num_bytes = (bits + 6) // 7
                    for i in range(num_bytes - 1, -1, -1):
                        byte = (duration >> (i * 7)) & 0x7F
                        if i > 0:
                            byte |= 0x80
                        track.write(bytes([byte]))
                track.write(bytes([0x80 | channel, note, 0]))
                
        elif evt_type == 'note_off':
            channel = event[2]
            note = event[3]
            note = max(0, min(127, note))
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
    
    # End of track
    track.write(b'\xFF\x2F\x00')
    
    # Write track header and data
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
    
    output_dir = Path('output/fdmus_midi_final')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    for i in range(count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        track_data = data[start:end]
        
        # Extract EVNT data
        evnt_data = extract_evnt_data(track_data)
        if not evnt_data:
            print(f"Track {i}: No EVNT found")
            continue
        
        # Parse events
        parser = XMIDIParser(evnt_data)
        events = parser.parse_events()
        
        if not events:
            print(f"Track {i}: No events parsed")
            continue
        
        # Convert to MIDI
        midi_data = convert_to_midi(events)
        
        output_file = output_dir / f'track_{i:03d}.mid'
        output_file.write_bytes(midi_data)
        print(f"Track {i}: {len(events)} events, {len(midi_data)} bytes -> {output_file}")
        converted += 1
    
    print(f"\nConverted {converted}/{count} tracks to {output_dir}")

if __name__ == '__main__':
    main()
