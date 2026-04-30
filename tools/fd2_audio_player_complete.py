#!/usr/bin/env python3
"""
FD2 Complete Audio Player
Based on IDA MCP reverse engineering of FD2.EXE

Key findings from AIL analysis:
- sub_3AEEE: AIL_start_sequence() wrapper
- sub_3AF5B: AIL_stop_sequence() wrapper  
- sub_44790: Sequence initialization (calls sub_3AF5B + sub_43160)
- sub_43160: MIDI parser state initializer (sets channel maps, buffers)
- sub_422C0: MIDI event buffer writer (handles 0x80-0xE0 commands)
- sub_447D0: Sequence cleanup (writes CC 0x40=0, CC 0x70=0 per channel)

XMIDI Format:
- FORM/XMID container with TIMB and EVNT chunks
- Delta times are variable-length encoded
- NO running status - every event has explicit status byte
- Standard MIDI events (0x80-0xFF) with proper data bytes
"""

import struct
import mido
import io
from io import BytesIO
from pathlib import Path
import pygame
import pygame.mixer
import time
import sys

class XMidiParser:
    """Parse XMIDI data based on FD2.EXE reverse engineering"""
    
    def __init__(self):
        self.events = []
        
    def parse(self, data):
        """Parse XMIDI data and return MIDI events"""
        self.events = []
        
        # Find EVNT chunk
        evnt_pos = data.find(b'EVNT')
        if evnt_pos < 0:
            return self.events
        
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        pos = evnt_pos + 8
        end = pos + chunk_size
        
        event_count = 0
        while pos < end and event_count < 10000:
            # Parse delta time (stops at byte >= 0x80)
            delta = 0
            while pos < end:
                byte = data[pos]
                if byte >= 0x80:
                    break
                pos += 1
                delta = (delta << 7) | byte
            
            if pos >= end:
                break
            
            # Parse status byte (always present, NO running status)
            status_byte = data[pos]
            pos += 1
            
            if status_byte == 0xFF:
                pos = self._parse_meta(data, pos, end, delta)
            elif status_byte >= 0x80:
                pos = self._parse_channel(data, pos, end, delta, status_byte)
            else:
                break
            
            event_count += 1
        
        return self.events
    
    def _parse_meta(self, data, pos, end, delta):
        """Parse meta event (0xFF)"""
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
        
        if meta_type == 0x2F:  # End of track
            self.events.append((delta, 0xFF, 0x2F, 0))
        elif meta_type == 0x51 and length == 3:  # Tempo
            tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
            self.events.append((delta, 0xFF, 0x51, tempo))
        elif meta_type == 0x58 and length == 4:  # Time signature
            self.events.append((delta, 0xFF, 0x58, 0))
        elif meta_type == 0x59 and length == 2:  # Key signature
            self.events.append((delta, 0xFF, 0x59, 0))
        else:
            self.events.append((delta, 0xFF, meta_type, length))
        
        return pos
    
    def _parse_channel(self, data, pos, end, delta, status):
        """Parse channel event based on sub_422C0 logic"""
        command = status & 0xF0
        
        # 2-byte data events
        if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            if pos + 1 < end:
                byte1 = data[pos]
                byte2 = data[pos+1]
                pos += 2
                # Clamp to valid MIDI range
                byte1 = max(0, min(127, byte1))
                byte2 = max(0, min(127, byte2))
                self.events.append((delta, status, byte1, byte2))
        # 1-byte data events  
        elif command in (0xC0, 0xD0):
            if pos < end:
                byte1 = data[pos]
                pos += 1
                byte1 = max(0, min(127, byte1))
                self.events.append((delta, status, byte1, 0))
        
        return pos

class MidiConverter:
    """Convert parsed XMIDI events to standard MIDI file"""
    
    def __init__(self):
        self.ticks_per_beat = 480
        
    def convert(self, events):
        """Convert events to MIDI file bytes"""
        mid = mido.MidiFile(type=0, ticks_per_beat=self.ticks_per_beat)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Add initial tempo if present
        has_tempo = False
        for delta, status, byte1, byte2 in events:
            if status == 0xFF and byte1 == 0x51:
                track.append(mido.MetaMessage('set_tempo', tempo=byte2, time=max(0, delta)))
                has_tempo = True
                break
        
        if not has_tempo:
            # Default tempo: 120 BPM
            track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        
        # Add all events
        for delta, status, byte1, byte2 in events:
            if status == 0xFF:
                if byte1 == 0x2F:
                    track.append(mido.MetaMessage('end_of_track', time=max(0, delta)))
                    break
                elif byte1 in (0x51, 0x58, 0x59):
                    continue  # Already handled
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
        
        # Ensure end of track exists
        if not any(isinstance(m, mido.MetaMessage) and m.type == 'end_of_track' for m in track):
            track.append(mido.MetaMessage('end_of_track', time=0))
        
        buf = BytesIO()
        mid.save(file=buf)
        return buf.getvalue()

class FD2AudioPlayer:
    """Complete audio player for FD2 XMIDI files"""
    
    def __init__(self):
        self.initialized = False
        self.parser = XMidiParser()
        self.converter = MidiConverter()
        
    def initialize(self):
        """Initialize pygame audio system"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.init()
            self.initialized = True
            print("Audio system initialized")
            return True
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            return False
    
    def load_and_convert(self, filepath):
        """Load XMIDI file and convert to MIDI"""
        with open(filepath, 'rb') as f:
            data = f.read()
        
        events = self.parser.parse(data)
        if not events:
            return None
        
        # Check for note events (0x8X = note off, 0x9X = note on)
        note_events = [e for e in events if (e[1] & 0xF0) in (0x80, 0x90)]
        if not note_events:
            return None
        
        midi_data = self.converter.convert(events)
        return midi_data
    
    def play_midi_data(self, midi_data, duration=10):
        """Play MIDI data using pygame"""
        try:
            # Save to temp file for pygame
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
                f.write(midi_data)
                temp_path = f.name
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            print(f"Playing for {duration} seconds...")
            for i in range(duration):
                print(f"  {duration-i}s remaining...", end='\r')
                time.sleep(1)
            
            pygame.mixer.music.stop()
            print("\nPlayback complete")
            
            import os
            os.unlink(temp_path)
            return True
            
        except Exception as e:
            print(f"Playback error: {e}")
            return False

def main():
    """Main player loop"""
    player = FD2AudioPlayer()
    if not player.initialize():
        return
    
    track_dir = Path("output/fdmus_tracks")
    midi_dir = Path("output/fdmus_midi_complete")
    midi_dir.mkdir(parents=True, exist_ok=True)
    
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print(f"\n{'='*70}")
    print(f"FD2 Audio Player - Complete Version")
    print(f"Based on IDA MCP reverse engineering")
    print(f"{'='*70}")
    
    # Convert and show tracks
    valid_tracks = []
    for i, track in enumerate(tracks):
        print(f"\n[{i}] {track.name}...", end=' ')
        midi_data = player.load_and_convert(track)
        if midi_data:
            midi_path = midi_dir / f"track_{i:03d}.mid"
            with open(midi_path, 'wb') as f:
                f.write(midi_data)
            valid_tracks.append((i, track, midi_path))
            print(f"OK ({len(midi_data)} bytes)")
        else:
            print("EMPTY")
    
    print(f"\n{'='*70}")
    print(f"Found {len(valid_tracks)} valid tracks")
    print(f"\nCommands:")
    print(f"  <number> - Play track")
    print(f"  a        - Play all tracks (5s each)")
    print(f"  q        - Quit")
    
    while True:
        try:
            cmd = input("\nSelect: ").strip()
            
            if cmd.lower() == 'q':
                break
            elif cmd.lower() == 'a':
                for idx, track, midi_path in valid_tracks:
                    print(f"\n{'='*60}")
                    print(f"Now playing: {track.name}")
                    player.play_midi_data(open(midi_path, 'rb').read(), duration=5)
            elif cmd.isdigit():
                idx = int(cmd)
                if 0 <= idx < len(valid_tracks):
                    actual_idx, track, midi_path = valid_tracks[idx]
                    print(f"\n{'='*60}")
                    print(f"Playing: {track.name}")
                    player.play_midi_data(open(midi_path, 'rb').read(), duration=15)
                else:
                    print(f"Invalid track number")
            else:
                print(f"Unknown command")
        except KeyboardInterrupt:
            print("\nStopped")
            continue
        except EOFError:
            break
    
    pygame.quit()

if __name__ == "__main__":
    main()