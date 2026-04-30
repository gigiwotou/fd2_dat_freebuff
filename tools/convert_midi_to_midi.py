#!/usr/bin/env python3
"""
Convert FDMUS.DAT tracks to standard MIDI format
MDI is Miles Sound System's variant of MIDI
"""

import struct
from pathlib import Path

def convert_mdi_to_midi(mdi_data):
    """
    Convert MDI format to standard MIDI
    MDI format may have a custom header before the MIDI data
    """
    # Check if it's already standard MIDI
    if mdi_data[:4] == b'MThd':
        return mdi_data
    
    # Check for FORM header (XMIDI)
    if mdi_data[:4] == b'FORM':
        # Try to extract MIDI from XMIDI container
        # XMIDI has a different structure, may need timidity to convert
        return mdi_data
    
    # MDI format usually has 12-byte header before MThd
    # Search for MThd signature
    midi_start = mdi_data.find(b'MThd')
    if midi_start >= 0:
        return mdi_data[midi_start:]
    
    # If no MThd found, the entire data might be raw MIDI events
    # Add minimal MIDI header
    header = struct.pack('>4sIHHH',
                        b'MThd',  # Magic
                        6,        # Header chunk size
                        0,        # Format 0 (single track)
                        1,        # One track
                        120       # 120 ticks per quarter note
                        )
    
    track_data = struct.pack('>4sI', b'MTrk', len(mdi_data)) + mdi_data
    return header + track_data

def convert_all_tracks(input_dir, output_dir):
    """Convert all extracted tracks to MIDI"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    
    for track_file in sorted(input_dir.glob('track_*.bin')):
        track_id = track_file.stem.split('_')[1]
        
        with open(track_file, 'rb') as f:
            data = f.read()
        
        midi_data = convert_mdi_to_midi(data)
        
        midi_file = output_dir / f"track_{track_id}.mid"
        midi_file.write_bytes(midi_data)
        
        if data[:4] == b'MThd':
            fmt = "Already MIDI"
        elif b'MThd' in data[:100]:
            fmt = "Extracted MIDI"
        elif data[:4] == b'FORM':
            fmt = "XMIDI (may need timidity)"
        else:
            fmt = "Wrapped in MIDI container"
        
        print(f"  [{track_id}] {track_file.name} -> {midi_file.name} ({fmt})")
        converted += 1
    
    print(f"\nConverted {converted} tracks to {output_dir}")
    return output_dir

def main():
    input_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi")
    
    if not input_dir.exists():
        print(f"Error: {input_dir} not found")
        print("Run test_fd2_audio_player.py first to extract tracks")
        return
    
    print("Converting FDMUS.DAT tracks to standard MIDI format...")
    convert_all_tracks(input_dir, output_dir)
    
    print(f"\nMIDI files saved to: {output_dir}")
    print("\nTo play:")
    print(f"  vlc {output_dir}/track_000.mid")
    print(f"  timidity {output_dir}/track_000.mid")
    print(f"  python -m pygame.examples.music {output_dir}/track_000.mid")

if __name__ == "__main__":
    main()
