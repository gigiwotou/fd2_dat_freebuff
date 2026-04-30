#!/usr/bin/env python3
"""
Fix MIDI files by adding missing End of Track meta events
"""

import struct
from pathlib import Path

def fix_midi_file(filepath):
    """Fix a MIDI file by ensuring it has End of Track event"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Check if already has End of Track
    if b'\xFF\x2F\x00' in data[-20:]:
        return False, "Already has End of Track"
    
    # Add End of Track event at the end of track
    # End of Track: FF 2F 00
    end_of_track = bytes([0x00, 0xFF, 0x2F, 0x00])  # delta=0, meta=FF, type=2F, length=00
    
    # Find the track chunk end
    if data[:4] != b'MThd':
        return False, "Invalid header"
    
    # Find MTrk chunk
    mtrk_pos = data.find(b'MTrk', 14)
    if mtrk_pos < 0:
        return False, "No track found"
    
    # Get track size
    track_size_pos = mtrk_pos + 4
    track_size = struct.unpack('>I', data[track_size_pos:track_size_pos+4])[0]
    
    # Add End of Track to track data
    new_track_data = data[mtrk_pos+8:] + end_of_track
    new_track_size = len(new_track_data)
    
    # Rebuild file
    new_data = data[:mtrk_pos+8] + new_track_data
    
    # Update track size
    new_data = new_data[:track_size_pos] + struct.pack('>I', new_track_size) + new_data[track_size_pos+4:]
    
    # Write back
    with open(filepath, 'wb') as f:
        f.write(new_data)
    
    return True, f"Added End of Track, new size: {len(new_data)}"

def main():
    midi_dir = Path("output/fdmus_midi_v2")
    
    if not midi_dir.exists():
        print("Error: MIDI directory not found")
        return
    
    midi_files = sorted(midi_dir.glob("track_*.mid"))
    
    print("Fixing MIDI files...\n")
    
    fixed_count = 0
    skipped_count = 0
    
    for midi_file in midi_files:
        success, msg = fix_midi_file(midi_file)
        
        if success:
            print(f"  FIXED: {midi_file.name} - {msg}")
            fixed_count += 1
        else:
            print(f"  SKIP:  {midi_file.name} - {msg}")
            skipped_count += 1
    
    print(f"\nFixed {fixed_count} files, skipped {skipped_count}")
    print(f"\nAll MIDI files should now be playable")

if __name__ == "__main__":
    main()
