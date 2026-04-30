#!/usr/bin/env python3
"""
FD2 XMIDI to MIDI Converter v3
Key finding from IDA + raw analysis: XMIDI does NOT use running status
Every MIDI event has an explicit status byte (0x80-0xFF).
Delta encoding is variable-length but stops at any byte >= 0x80.
"""

import struct
import mido
import io
from io import BytesIO
from pathlib import Path

class XMidiParser:
    def __init__(self):
        self.events = []
        
    def parse(self, data):
        self.events = []
        
        evnt_pos = data.find(b'EVNT')
        if evnt_pos < 0:
            return self.events
        
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        pos = evnt_pos + 8
        end = pos + chunk_size
        
        while pos < end:
            # Parse delta time (variable-length, stops at byte >= 0x80)
            delta = 0
            while pos < end:
                byte = data[pos]
                if byte >= 0x80:
                    break
                pos += 1
                delta = (delta << 7) | byte
            
            if pos >= end:
                break
            
            # Parse status byte (always present in XMIDI, no running status)
            status_byte = data[pos]
            pos += 1
            
            if status_byte == 0xFF:
                pos = self._parse_meta(data, pos, end, delta)
            elif status_byte >= 0x80:
                pos = self._parse_channel(data, pos, end, delta, status_byte)
            else:
                # Invalid: byte < 0x80 where status expected
                break
        
        return self.events
    
    def _parse_meta(self, data, pos, end, delta):
        if pos >= end:
            return pos
        
        meta_type = data[pos]
        pos += 1
        
        # Parse variable-length length
        length = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            length = (length << 7) | byte
            if not (byte & 0x80):
                break
        
        data_bytes = data[pos:pos+length]
        pos += length
        
        if meta_type == 0x2F:
            self.events.append((delta, 0xFF, 0x2F, 0))
        elif meta_type == 0x51 and length == 3:
            tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
            self.events.append((delta, 0xFF, 0x51, tempo))
        else:
            self.events.append((delta, 0xFF, meta_type, length))
        
        return pos
    
    def _parse_channel(self, data, pos, end, delta, status):
        command = status & 0xF0
        
        if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            if pos + 1 < end:
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                # Clamp to valid MIDI range
                byte1 = max(0, min(127, byte1))
                byte2 = max(0, min(127, byte2))
                self.events.append((delta, status, byte1, byte2))
        elif command in (0xC0, 0xD0):
            if pos < end:
                byte1 = data[pos]
                pos += 1
                byte1 = max(0, min(127, byte1))
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
    
    buf = BytesIO()
    mid.save(file=buf)
    return buf.getvalue()

def main():
    track_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi_v3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print(f"Converting {len(tracks)} XMIDI tracks to MIDI (v3 - no running status)...")
    
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
    
    print(f"\nConverted {success_count}/10 tracks successfully")

if __name__ == "__main__":
    main()
