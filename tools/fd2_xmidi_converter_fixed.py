#!/usr/bin/env python3
"""
FD2 XMIDI to MIDI Converter - Fixed version
Based on IDA MCP reverse engineering

Key insight: XMIDI uses standard MIDI delta encoding but must stop delta parsing
at 0xFF (meta event marker) since 0xFF should never be consumed as delta data.
"""

import struct
import mido
import io
from pathlib import Path

class XMidiParser:
    def __init__(self):
        self.events = []
        self.running_status = 0
        
    def parse(self, data):
        self.events = []
        self.running_status = 0
        
        evnt_pos = data.find(b'EVNT')
        if evnt_pos < 0:
            print("No EVNT chunk found")
            return self.events
        
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        pos = evnt_pos + 8
        end = pos + chunk_size
        
        print(f"EVNT chunk at {evnt_pos:#x}, size {chunk_size}")
        
        event_count = 0
        while pos < end and event_count < 5000:
            # Parse delta time - STOP at 0xFF or any status byte (>= 0x80)
            delta = 0
            while pos < end:
                byte = data[pos]
                if byte >= 0x80:
                    break
                pos += 1
                delta = (delta << 7) | byte
            
            if pos >= end:
                break
            
            status_byte = data[pos]
            pos += 1
            
            if status_byte == 0xFF:
                pos = self._parse_meta(data, pos, end, delta)
                event_count += 1
            elif status_byte >= 0x80:
                self.running_status = status_byte
                pos = self._parse_channel(data, pos, end, delta, status_byte)
                event_count += 1
            else:
                if self.running_status:
                    pos = self._parse_channel(data, pos, end, delta, self.running_status)
                    event_count += 1
                else:
                    break
        
        print(f"Parsed {len(self.events)} events")
        return self.events
    
    def _parse_meta(self, data, pos, end, delta):
        if pos >= end:
            return pos
        
        meta_type = data[pos]
        pos += 1
        
        length = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            length = (length << 7) | byte
            if not (byte & 0x80):
                break
        
        if meta_type == 0x2F:
            self.events.append((delta, 0xFF, 0x2F, 0))
            return pos
        
        data_bytes = data[pos:pos+length]
        pos += length
        
        if meta_type == 0x51 and length == 3:
            tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
            self.events.append((delta, 0xFF, 0x51, tempo))
        elif meta_type == 0x58 and length == 4:
            self.events.append((delta, 0xFF, 0x58, 0))
        elif meta_type == 0x59 and length == 2:
            self.events.append((delta, 0xFF, 0x59, 0))
        else:
            self.events.append((delta, 0xFF, meta_type, length))
        
        return pos
    
    def _parse_channel(self, data, pos, end, delta, status):
        command = status & 0xF0
        channel = status & 0xF
        
        if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            if pos + 1 < end:
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                self.events.append((delta, status, byte1, byte2))
        elif command in (0xC0, 0xD0):
            if pos < end:
                byte1 = data[pos]
                pos += 1
                self.events.append((delta, status, byte1, 0))
        
        return pos

def convert_xmidi_to_midi(xmidi_data):
    parser = XMidiParser()
    events = parser.parse(xmidi_data)
    
    if not events:
        return None
    
    mid = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    for delta, status, byte1, byte2 in events:
        if status == 0xFF:
            if byte1 == 0x2F:
                track.append(mido.MetaMessage('end_of_track', time=max(0, delta)))
                break
            elif byte1 == 0x51:
                track.append(mido.MetaMessage('set_tempo', tempo=byte2, time=max(0, delta)))
            elif byte1 == 0x58:
                track.append(mido.MetaMessage('time_signature', time=max(0, delta)))
            elif byte1 == 0x59:
                track.append(mido.MetaMessage('key_signature', time=max(0, delta)))
        else:
            command = status & 0xF0
            channel = status & 0xF
            
            if command == 0x90:
                if byte2 > 0:
                    track.append(mido.Message('note_on', note=byte1, velocity=byte2, 
                                            channel=channel, time=max(0, delta)))
                else:
                    track.append(mido.Message('note_off', note=byte1, velocity=0, 
                                            channel=channel, time=max(0, delta)))
            elif command == 0x80:
                track.append(mido.Message('note_off', note=byte1, velocity=byte2, 
                                        channel=channel, time=max(0, delta)))
            elif command == 0xB0:
                track.append(mido.Message('control_change', control=byte1, value=byte2, 
                                        channel=channel, time=max(0, delta)))
            elif command == 0xC0:
                track.append(mido.Message('program_change', program=byte1, 
                                        channel=channel, time=max(0, delta)))
            elif command == 0xE0:
                pitch = (byte2 << 7) | byte1
                track.append(mido.Message('pitchwheel', pitch=pitch - 8192, 
                                        channel=channel, time=max(0, delta)))
    
    buf = io.BytesIO()
    mid.save(buf)
    return buf.getvalue()

def main():
    track_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi_fixed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print(f"Converting {len(tracks)} XMIDI tracks to MIDI (fixed parser)...")
    
    success_count = 0
    for i, track in enumerate(tracks[:10]):
        print(f"\n[{i}] {track.name}")
        with open(track, 'rb') as f:
            data = f.read()
        
        midi_data = convert_xmidi_to_midi(data)
        if midi_data:
            midi_path = output_dir / f"track_{i:03d}.mid"
            with open(midi_path, 'wb') as f:
                f.write(midi_data)
            print(f"  -> {midi_path.name} ({len(midi_data)} bytes)")
            success_count += 1
        else:
            print(f"  -> FAILED")
    
    print(f"\nConverted {success_count}/10 tracks")

if __name__ == "__main__":
    main()
