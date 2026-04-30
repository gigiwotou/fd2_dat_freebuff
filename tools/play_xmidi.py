#!/usr/bin/env python3
"""
FD2 XMIDI Player using pygame.midi
Plays XMIDI tracks through Windows MIDI synthesizer
"""

import pygame
import pygame.midi
import struct
import time
from pathlib import Path

def parse_midi_events(midi_data):
    """Parse MIDI events from raw data"""
    events = []
    pos = 0
    
    if midi_data[:4] != b'MThd':
        print("Warning: No MThd header found")
        return events
    
    # Skip header
    header_size = struct.unpack('>I', midi_data[4:8])[0]
    pos = 8 + header_size
    
    # Find track
    if midi_data[pos:pos+4] != b'MTrk':
        print("Warning: No MTrk found")
        return events
    
    pos += 4
    track_size = struct.unpack('>I', midi_data[pos:pos+4])[0]
    pos += 4
    
    track_end = pos + track_size
    
    while pos < track_end:
        # Parse delta time (variable length)
        delta = 0
        while True:
            byte = midi_data[pos]
            pos += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        # Parse MIDI event
        status = midi_data[pos]
        
        if status == 0xFF:  # Meta event
            pos += 1
            meta_type = midi_data[pos]
            pos += 1
            length = 0
            while True:
                byte = midi_data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if meta_type == 0x2F:  # End of track
                break
            
            pos += length
            
        elif status == 0xF0 or status == 0xF7:  # SysEx
            pos += 1
            length = 0
            while True:
                byte = midi_data[pos]
                pos += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            pos += length
            
        elif status >= 0x80:  # Channel event
            pos += 1
            
            if status < 0xC0:  # 2 byte events
                byte1 = midi_data[pos]
                byte2 = midi_data[pos+1]
                pos += 2
                events.append((delta, status, byte1, byte2))
            else:  # 1 byte events
                byte1 = midi_data[pos]
                pos += 1
                events.append((delta, status, byte1, 0))
        else:
            # Running status - use previous status
            pos -= 1
            continue
    
    return events

def play_midi_with_pygame_midi(midi_file):
    """Play MIDI file using pygame.midi"""
    try:
        pygame.midi.init()
        
        # Find output device
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            interf, name, is_input, is_output, is_opened = info
            if is_output:
                print(f"  MIDI output device {i}: {name.decode('utf-8', errors='replace')}")
                try:
                    output = pygame.midi.Output(i)
                    print(f"  Using device: {name.decode('utf-8', errors='replace')}")
                    break
                except:
                    continue
        else:
            print("Error: No MIDI output device found")
            pygame.midi.quit()
            return False
        
        # Read MIDI file
        with open(midi_file, 'rb') as f:
            data = f.read()
        
        # Parse events
        events = parse_midi_events(data)
        
        if not events:
            print("No MIDI events found")
            output.close()
            pygame.midi.quit()
            return False
        
        print(f"\nPlaying {midi_file.name} ({len(events)} events)")
        print("Press Ctrl+C to stop")
        
        # Play events with timing
        tempo = 500000  # Default: 120 BPM (microseconds per quarter note)
        current_time = 0
        absolute_time = 0
        
        try:
            for delta, status, byte1, byte2 in events:
                absolute_time += delta
                
                # Handle tempo change
                if status == 0xFF and byte1 == 0x51:
                    # Tempo meta event
                    pass
                
                # Convert to MIDI message
                channel = status & 0x0F
                command = status & 0xF0
                
                if command == 0x80:  # Note Off
                    output.note_off(byte1, byte2, channel)
                elif command == 0x90:  # Note On
                    if byte2 > 0:
                        output.note_on(byte1, byte2, channel)
                    else:
                        output.note_off(byte1, channel)
                elif command == 0xA0:  # Polyphonic Aftertouch
                    pass
                elif command == 0xB0:  # Control Change
                    pass
                elif command == 0xC0:  # Program Change
                    output.set_instrument(byte1, channel)
                elif command == 0xE0:  # Pitch Bend
                    pass
            
            print("Playback complete")
            
        except KeyboardInterrupt:
            print("\nPlayback stopped")
        
        output.close()
        pygame.midi.quit()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        pygame.midi.quit()
        return False

def show_menu(tracks):
    """Show track menu"""
    print("\n" + "="*60)
    print("FD2 XMIDI Player (pygame.midi)")
    print("="*60)
    print(f"\nAvailable tracks ({len(tracks)}):")
    print(f"  {'ID':<5} {'Size':<10} {'File':<30}")
    print(f"  {'-'*45}")
    
    for i, track in enumerate(tracks):
        size = track.stat().st_size
        print(f"  [{i:<3}] {size:<10,} {track.name}")
    
    print(f"\nCommands:")
    print(f"  <number>  - Play track")
    print(f"  q         - Quit")
    
    return input("\nSelect: ")

def main():
    midi_dir = Path("output/fdmus_tracks")
    
    if not midi_dir.exists():
        print("Error: Track directory not found")
        return
    
    tracks = sorted([t for t in midi_dir.glob("track_*.bin") if t.stat().st_size > 100])
    
    if not tracks:
        print("No tracks found")
        return
    
    print(f"Found {len(tracks)} tracks")
    
    pygame.init()
    
    while True:
        try:
            cmd = show_menu(tracks)
            
            if cmd.lower() == 'q':
                break
            elif cmd.isdigit():
                track_idx = int(cmd)
                if 0 <= track_idx < len(tracks):
                    play_midi_with_pygame_midi(tracks[track_idx])
                else:
                    print(f"Invalid track ID")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
    
    pygame.quit()

if __name__ == "__main__":
    main()
