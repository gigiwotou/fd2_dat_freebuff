#!/usr/bin/env python3
"""
FD2 XMIDI to MIDI Converter
Based on IDA MCP reverse engineering of FD2.EXE audio functions

Key findings from IDA analysis:
- sub_422C0: MIDI event buffer writer (handles 0x80-0xE0 commands)
- sub_43160: MIDI parser state initializer
- sub_44790: Sequence initialization (sets up XMID parser)
- XMIDI format: FORM/XMID with EVNT chunk containing delta-encoded events
"""

import struct
import mido
import io
from pathlib import Path
import sys

class XMidiParser:
    """Parse XMIDI format based on FD2.EXE reverse engineering"""
    
    def __init__(self):
        self.events = []
        self.running_status = 0
        
    def parse(self, data):
        """Parse XMIDI data and return MIDI events"""
        self.events = []
        self.running_status = 0
        
        evnt_pos = data.find(b'EVNT')
        if evnt_pos < 0:
            return self.events
        
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        pos = evnt_pos + 8
        end = pos + chunk_size
        
        while pos < end:
            delta = self._parse_delta(data, pos, end)
            if delta is None:
                break
            pos = delta[1]
            delta_time = delta[0]
            
            if pos >= end:
                break
            
            status_byte = data[pos]
            pos += 1
            
            if status_byte >= 0x80:
                self.running_status = status_byte
            else:
                pos -= 1
                status_byte = self.running_status
            
            command = status_byte & 0xF0
            channel = status_byte & 0xF
            
            if status_byte == 0xFF:
                pos = self._parse_meta(data, pos, end, delta_time)
            elif command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 < end:
                    byte1 = data[pos]
                    byte2 = data[pos+1]
                    pos += 2
                    self.events.append((delta_time, status_byte, byte1, byte2))
            elif command in (0xC0, 0xD0):
                if pos < end:
                    byte1 = data[pos]
                    pos += 1
                    self.events.append((delta_time, status_byte, byte1, 0))
        
        return self.events
    
    def _parse_delta(self, data, pos, end):
        """Parse variable-length delta time"""
        delta = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                return delta, pos
        return None
    
    def _parse_meta(self, data, pos, end, delta_time):
        """Parse meta event"""
        if pos >= end:
            return pos
        
        meta_type = data[pos]
        pos += 1
        
        length = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            length = (length << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        if meta_type == 0x2F:
            self.events.append((delta_time, 0xFF, 0x2F, 0))
            return pos
        
        if meta_type == 0x51 and length == 3 and pos + 3 <= end:
            tempo = (data[pos] << 16) | (data[pos+1] << 8) | data[pos+2]
            self.events.append((delta_time, 0xFF, 0x51, tempo))
        
        return pos + length

class MidiConverter:
    """Convert parsed XMIDI events to standard MIDI"""
    
    def __init__(self):
        self.ticks_per_beat = 120
        
    def convert(self, events):
        """Convert XMIDI events to MIDI file bytes"""
        mid = mido.MidiFile(type=0, ticks_per_beat=self.ticks_per_beat)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        for delta, status, byte1, byte2 in events:
            if status == 0xFF:
                if byte1 == 0x2F:
                    track.append(mido.MetaMessage('end_of_track', time=delta))
                    break
                elif byte1 == 0x51:
                    track.append(mido.MetaMessage('set_tempo', tempo=byte2, time=delta))
            else:
                command = status & 0xF0
                channel = status & 0xF
                
                if command == 0x90:
                    if byte2 > 0:
                        track.append(mido.Message('note_on', note=byte1, velocity=byte2, 
                                                channel=channel, time=delta))
                    else:
                        track.append(mido.Message('note_off', note=byte1, velocity=0, 
                                                channel=channel, time=delta))
                elif command == 0x80:
                    track.append(mido.Message('note_off', note=byte1, velocity=0, 
                                            channel=channel, time=delta))
                elif command == 0xB0:
                    track.append(mido.Message('control_change', control=byte1, value=byte2, 
                                            channel=channel, time=delta))
                elif command == 0xC0:
                    track.append(mido.Message('program_change', program=byte1, 
                                            channel=channel, time=delta))
                elif command == 0xE0:
                    pitch = (byte2 << 7) | byte1
                    track.append(mido.Message('pitchwheel', pitch=pitch - 8192, 
                                            channel=channel, time=delta))
        
        buf = io.BytesIO()
        mid.save(buf)
        return buf.getvalue()

def convert_xmidi_file(xmidi_path, midi_path):
    """Convert single XMIDI file to MIDI"""
    with open(xmidi_path, 'rb') as f:
        data = f.read()
    
    parser = XMidiParser()
    events = parser.parse(data)
    
    if not events:
        return False
    
    converter = MidiConverter()
    midi_data = converter.convert(events)
    
    with open(midi_path, 'wb') as f:
        f.write(midi_data)
    
    return True

def main():
    track_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print(f"Converting {len(tracks)} XMIDI tracks to MIDI...")
    
    success_count = 0
    for i, track in enumerate(tracks[:10]):
        midi_path = output_dir / f"track_{i:03d}.mid"
        if convert_xmidi_file(track, midi_path):
            print(f"  [{i}] {track.name} -> {midi_path.name}")
            success_count += 1
        else:
            print(f"  [{i}] {track.name} -> FAILED")
    
    print(f"\nConverted {success_count}/{min(len(tracks), 10)} tracks")

if __name__ == "__main__":
    main()