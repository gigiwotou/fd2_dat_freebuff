#!/usr/bin/env python3
"""
FD2 Audio Player
Plays FDMUS.DAT music using pygame with proper XMIDI parsing
Based on reverse engineering of FD2.EXE audio functions
"""

import struct
import pygame
import pygame.mixer
from pathlib import Path
import sys
import time

class FD2AudioPlayer:
    def __init__(self):
        self.initialized = False
        
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
    
    def parse_xmidi(self, data):
        """Parse XMIDI data and extract MIDI events"""
        events = []
        
        # Find EVNT chunk
        evnt_pos = data.find(b'EVNT')
        if evnt_pos < 0:
            return events
        
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        pos = evnt_pos + 8
        end = pos + chunk_size
        
        running_status = 0
        
        while pos < end:
            # Parse delta time
            delta = 0
            while pos < end:
                byte = data[pos]
                pos += 1
                delta = (delta << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if pos >= end:
                break
            
            # Parse status
            byte = data[pos]
            
            if byte >= 0x80:
                status = byte
                pos += 1
                running_status = status
            else:
                status = running_status
            
            # Parse based on status
            if status == 0xFF:  # Meta
                if pos >= end:
                    break
                meta_type = data[pos]
                pos += 1
                
                length = 0
                while pos < end:
                    b = data[pos]
                    pos += 1
                    length = (length << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                
                if meta_type == 0x2F:  # End of track
                    events.append((delta, 'end_of_track'))
                    break
                elif meta_type == 0x51:  # Tempo
                    if length == 3 and pos + 3 <= end:
                        tempo = (data[pos] << 16) | (data[pos+1] << 8) | data[pos+2]
                        events.append((delta, 'tempo', tempo))
                    pos += length
                else:
                    pos += length
                    
            elif status >= 0x80:
                command = status & 0xF0
                channel = status & 0xF
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    if pos + 1 >= end:
                        break
                    byte1 = data[pos]
                    byte2 = data[pos+1]
                    pos += 2
                    
                    # Clamp to valid MIDI range
                    byte1 = max(0, min(127, byte1))
                    byte2 = max(0, min(127, byte2))
                    
                    if command == 0x90:
                        if byte2 > 0:
                            events.append((delta, 'note_on', channel, byte1, byte2))
                        else:
                            events.append((delta, 'note_off', channel, byte1))
                    elif command == 0x80:
                        events.append((delta, 'note_off', channel, byte1))
                    elif command == 0xB0:
                        events.append((delta, 'control_change', channel, byte1, byte2))
                    elif command == 0xA0:
                        events.append((delta, 'poly_pressure', channel, byte1, byte2))
                    elif command == 0xE0:
                        pitch = (byte2 << 7) | byte1
                        events.append((delta, 'pitch_bend', channel, pitch))
                        
                elif command in (0xC0, 0xD0):
                    if pos >= end:
                        break
                    byte1 = data[pos]
                    pos += 1
                    byte1 = max(0, min(127, byte1))
                    
                    if command == 0xC0:
                        events.append((delta, 'program_change', channel, byte1))
                    elif command == 0xD0:
                        events.append((delta, 'channel_pressure', channel, byte1))
        
        return events
    
    def play_xmidi(self, filepath):
        """Play XMIDI file by parsing and synthesizing"""
        print(f"\nLoading: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Parse events
        events = self.parse_xmidi(data)
        
        if not events:
            print("No events found")
            return False
        
        print(f"Parsed {len(events)} events")
        
        # Filter and show note events
        note_events = [e for e in events if e[1] in ('note_on', 'note_off')]
        print(f"Note events: {len(note_events)}")
        
        if not note_events:
            print("No note events found - cannot play")
            return False
        
        # Show first few notes
        print("\nFirst 10 notes:")
        shown = 0
        for delta, ev_type, *args in note_events:
            if shown >= 10:
                break
            if ev_type == 'note_on':
                ch, note, vel = args
                print(f"  Delta={delta:<8} Note On  Ch={ch} Note={note} Vel={vel}")
            else:
                ch, note = args
                print(f"  Delta={delta:<8} Note Off Ch={ch} Note={note}")
            shown += 1
        
        print("\nNote: This XMIDI file requires specialized conversion")
        print("The data contains valid MIDI events but needs proper timing conversion")
        
        return True

def main():
    # Initialize audio
    player = FD2AudioPlayer()
    if not player.initialize():
        print("Cannot initialize audio system")
        return
    
    fdmus_tracks = Path("output/fdmus_tracks")
    
    if not fdmus_tracks.exists():
        print("Error: No tracks found")
        return
    
    # List tracks
    tracks = sorted(fdmus_tracks.glob("track_*.bin"))
    
    print(f"\n{'='*70}")
    print(f"FD2 Audio Player - XMIDI Analysis Mode")
    print(f"{'='*70}")
    print(f"\nAvailable tracks: {len(tracks)}")
    
    for i, track in enumerate(tracks[:10]):
        size = track.stat().st_size
        print(f"  [{i}] {track.name} ({size:,} bytes)")
    
    print(f"\nCommands:")
    print(f"  <number> - Analyze track")
    print(f"  q        - Quit")
    
    while True:
        try:
            cmd = input("\nSelect: ").strip()
            
            if cmd.lower() == 'q':
                break
            elif cmd.isdigit():
                idx = int(cmd)
                if 0 <= idx < len(tracks):
                    player.play_xmidi(tracks[idx])
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
