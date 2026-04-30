#!/usr/bin/env python3
"""
Validate MIDI file format
Check if converted MIDI files are standard and correct format errors
"""

import struct
from pathlib import Path

def validate_midi_file(filepath):
    """Validate a MIDI file's structure"""
    print(f"\n{'='*60}")
    print(f"Validating: {filepath.name}")
    print(f"{'='*60}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    pos = 0
    errors = []
    warnings = []
    
    # Check file size
    if len(data) < 14:
        errors.append(f"File too small: {len(data)} bytes (minimum 14)")
        return errors, warnings
    
    # Parse header chunk
    if data[0:4] != b'MThd':
        errors.append(f"Missing MThd header. Found: {data[0:4]}")
        return errors, warnings
    
    pos = 4
    header_size = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    
    if header_size != 6:
        warnings.append(f"Header size is {header_size} (expected 6)")
    
    if pos + 6 > len(data):
        errors.append("Header chunk truncated")
        return errors, warnings
    
    format_type = struct.unpack('>H', data[pos:pos+2])[0]
    ntracks = struct.unpack('>H', data[pos+2:pos+4])[0]
    division = struct.unpack('>H', data[pos+4:pos+6])[0]
    pos += 6
    
    print(f"  Format: {format_type}")
    print(f"  Tracks: {ntracks}")
    print(f"  Division: {division}")
    
    if format_type > 2:
        errors.append(f"Invalid format type: {format_type}")
    
    if ntracks == 0:
        errors.append("No tracks defined")
        return errors, warnings
    
    # Parse each track
    for track_idx in range(ntracks):
        if pos + 8 > len(data):
            errors.append(f"Track {track_idx}: Header truncated")
            break
        
        if data[pos:pos+4] != b'MTrk':
            errors.append(f"Track {track_idx}: Missing MTrk header. Found: {data[pos:pos+4]}")
            break
        
        pos += 4
        track_size = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        
        print(f"\n  Track {track_idx}: {track_size} bytes")
        
        if pos + track_size > len(data):
            errors.append(f"Track {track_idx}: Data truncated (need {track_size}, have {len(data)-pos})")
            break
        
        track_end = pos + track_size
        
        # Parse track events
        event_count = 0
        has_end_of_track = False
        last_status = 0
        abs_time = 0
        
        while pos < track_end:
            # Parse delta time
            delta = 0
            byte_count = 0
            while pos < track_end:
                byte = data[pos]
                pos += 1
                byte_count += 1
                delta = (delta << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
                
                if byte_count > 4:
                    errors.append(f"Track {track_idx}: Variable-length quantity too long at event {event_count}")
                    break
            
            abs_time += delta
            
            if pos >= track_end:
                errors.append(f"Track {track_idx}: Unexpected end of track after delta time")
                break
            
            # Parse event
            status = data[pos]
            
            if status == 0xFF:  # Meta event
                pos += 1
                if pos >= track_end:
                    errors.append(f"Track {track_idx}: Truncated meta event")
                    break
                
                meta_type = data[pos]
                pos += 1
                
                # Parse length
                length = 0
                byte_count = 0
                while pos < track_end:
                    byte = data[pos]
                    pos += 1
                    byte_count += 1
                    length = (length << 7) | (byte & 0x7F)
                    if not (byte & 0x80):
                        break
                
                if meta_type == 0x2F:  # End of track
                    has_end_of_track = True
                    if length != 0:
                        warnings.append(f"Track {track_idx}: End of track event has length {length} (expected 0)")
                
                pos += length
                event_count += 1
                
            elif status == 0xF0 or status == 0xF7:  # SysEx
                pos += 1
                length = 0
                byte_count = 0
                while pos < track_end:
                    byte = data[pos]
                    pos += 1
                    byte_count += 1
                    length = (length << 7) | (byte & 0x7F)
                    if not (byte & 0x80):
                        break
                
                pos += length
                event_count += 1
                
            elif status >= 0x80:  # MIDI channel event
                last_status = status
                command = status & 0xF0
                pos += 1
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):  # 2 data bytes
                    if pos + 1 >= track_end:
                        errors.append(f"Track {track_idx}: Truncated channel event at event {event_count}")
                        break
                    pos += 2
                elif command in (0xC0, 0xD0):  # 1 data byte
                    if pos >= track_end:
                        errors.append(f"Track {track_idx}: Truncated channel event at event {event_count}")
                        break
                    pos += 1
                else:
                    errors.append(f"Track {track_idx}: Unknown channel command 0x{command:02X} at event {event_count}")
                    break
                
                event_count += 1
                
            else:  # Running status
                command = last_status & 0xF0
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    if pos + 1 >= track_end:
                        errors.append(f"Track {track_idx}: Truncated running status at event {event_count}")
                        break
                    pos += 2
                elif command in (0xC0, 0xD0):
                    if pos >= track_end:
                        errors.append(f"Track {track_idx}: Truncated running status at event {event_count}")
                        break
                    pos += 1
                else:
                    errors.append(f"Track {track_idx}: Invalid running status 0x{status:02X} at event {event_count}")
                    break
                
                event_count += 1
        
        print(f"    Events: {event_count}")
        print(f"    Has End of Track: {has_end_of_track}")
        print(f"    Duration (ticks): {abs_time}")
        
        if not has_end_of_track:
            errors.append(f"Track {track_idx}: Missing End of Track meta event")
    
    return errors, warnings

def main():
    midi_dir = Path("output/fdmus_midi_v2")
    
    if not midi_dir.exists():
        print(f"Error: {midi_dir} not found")
        return
    
    midi_files = sorted(midi_dir.glob("track_*.mid"))
    
    print(f"Checking {len(midi_files)} MIDI files...")
    
    total_errors = 0
    total_warnings = 0
    
    for midi_file in midi_files:
        errors, warnings = validate_midi_file(midi_file)
        
        if errors:
            print(f"\n  ERRORS:")
            for err in errors:
                print(f"    - {err}")
        
        if warnings:
            print(f"\n  WARNINGS:")
            for warn in warnings:
                print(f"    - {warn}")
        
        if not errors and not warnings:
            print(f"  VALID MIDI file")
        
        total_errors += len(errors)
        total_warnings += len(warnings)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total errors: {total_errors}")
    print(f"  Total warnings: {total_warnings}")
    print(f"  Valid files: {len(midi_files) - total_errors}/{len(midi_files)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
