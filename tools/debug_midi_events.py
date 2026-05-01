#!/usr/bin/env python3
"""
Debug script to validate converted MIDI files
Parse MIDI and show events for verification
"""

import struct
from pathlib import Path

def read_variable_length(data, pos):
    """Read variable-length value from MIDI"""
    value = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos

def parse_midi_file(midi_path):
    """Parse a MIDI file and show events"""
    with open(midi_path, 'rb') as f:
        data = f.read()
    
    pos = 0
    
    # Read header
    header = data[pos:pos+4]
    pos += 4
    if header != b'MThd':
        print(f"  Invalid header: {header}")
        return
    
    header_len = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    
    midi_format, num_tracks, ppqn = struct.unpack('>HHH', data[pos:pos+6])
    pos += header_len
    
    print(f"  Format: {midi_format}, Tracks: {num_tracks}, PPQN: {ppqn}")
    
    # Parse tracks
    for track_idx in range(num_tracks):
        track_header = data[pos:pos+4]
        pos += 4
        if track_header != b'MTrk':
            print(f"  Invalid track header: {track_header}")
            return
        
        track_len = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        
        track_end = pos + track_len
        abs_tick = 0
        running_status = None
        event_count = 0
        
        print(f"\n  Track {track_idx} ({track_len} bytes):")
        
        while pos < track_end:
            # Read delta
            delta, pos = read_variable_length(data, pos)
            abs_tick += delta
            
            # Read status
            byte = data[pos]
            pos += 1
            
            if byte >= 0x80:
                status = byte
                running_status = status
            else:
                if running_status is None:
                    print(f"    ERROR: No running status at tick {abs_tick}")
                    return
                status = running_status
                pos -= 1  # Go back to read data byte
            
            status_type = status & 0xF0
            channel = status & 0x0F
            
            event_count += 1
            
            if status == 0xFF:
                # Meta event
                meta_type = data[pos]
                pos += 1
                length, pos = read_variable_length(data, pos)
                meta_data = data[pos:pos+length]
                pos += length
                
                if meta_type == 0x51:  # Tempo
                    tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
                    bpm = 60000000 / tempo if tempo > 0 else 0
                    print(f"    [{abs_tick:6d}] Tempo: {tempo} ({bpm:.1f} BPM)")
                elif meta_type == 0x2F:  # End of Track
                    print(f"    [{abs_tick:6d}] End of Track")
                    break
                elif meta_type == 0x03:  # Track name
                    print(f"    [{abs_tick:6d}] Track Name: {meta_data.decode('ascii', errors='ignore')}")
                elif meta_type == 0x58:  # Time signature
                    print(f"    [{abs_tick:6d}] Time Signature: {meta_data.hex()}")
                else:
                    print(f"    [{abs_tick:6d}] Meta 0x{meta_type:02X}: {meta_data[:10].hex()}")
            
            elif status_type == 0x90:  # Note On
                if pos + 1 >= track_end:
                    break
                note = data[pos]
                velocity = data[pos+1]
                pos += 2
                duration_info = ""
                print(f"    [{abs_tick:6d}] Note On  Ch:{channel} Note:{note} Vel:{velocity}")
                
            elif status_type == 0x80:  # Note Off
                if pos + 1 >= track_end:
                    break
                note = data[pos]
                velocity = data[pos+1]
                pos += 2
                print(f"    [{abs_tick:6d}] Note Off Ch:{channel} Note:{note} Vel:{velocity}")
                
            elif status_type == 0xB0:  # Control Change
                if pos + 1 >= track_end:
                    break
                controller = data[pos]
                value = data[pos+1]
                pos += 2
                print(f"    [{abs_tick:6d}] CC       Ch:{channel} Ctrl:{controller} Val:{value}")
                
            elif status_type == 0xC0:  # Program Change
                if pos >= track_end:
                    break
                program = data[pos]
                pos += 1
                print(f"    [{abs_tick:6d}] Program  Ch:{channel} Prog:{program}")
            
            elif status_type == 0xE0:  # Pitch Bend
                if pos + 1 >= track_end:
                    break
                lsb = data[pos]
                msb = data[pos+1]
                pos += 2
                bend = (msb << 7) | lsb
                print(f"    [{abs_tick:6d}] PitchBend Ch:{channel} Val:{bend}")
            
            elif status == 0xF0:  # SysEx
                length, pos = read_variable_length(data, pos)
                pos += length
                print(f"    [{abs_tick:6d}] SysEx ({length} bytes)")
            
            else:
                print(f"    [{abs_tick:6d}] Status 0x{status:02X} (unknown)")
            
            # Limit output to first 30 events
            if event_count >= 30:
                print(f"    ... ({event_count} events shown, more follow)")
                break
        
        print(f"  Total events: {event_count}")

def main():
    midi_dir = Path("output/fdmus_midi_fixed")
    
    if not midi_dir.exists():
        print(f"Error: {midi_dir} not found")
        return
    
    # Test a few tracks
    for track_file in sorted(midi_dir.glob("track_*.mid"))[:3]:
        print(f"\n{'='*60}")
        print(f"Parsing: {track_file.name}")
        print(f"{'='*60}")
        parse_midi_file(track_file)

if __name__ == "__main__":
    main()
