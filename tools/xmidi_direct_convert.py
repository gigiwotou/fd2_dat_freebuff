#!/usr/bin/env python3
"""
XMIDI to MIDI converter - Direct passthrough approach
Instead of parsing and reconstructing, just extract EVNT data
and wrap it in standard MIDI format
"""

import struct
from pathlib import Path

def convert_xmidi_direct(xmidi_data):
    """
    Direct conversion: extract EVNT chunk data as-is
    and wrap in MIDI container
    """
    
    # Find FORM chunk
    if xmidi_data[:4] == b'FORM' and b'XMID' in xmidi_data[12:20]:
        pass
    elif b'FORM' in xmidi_data:
        form_pos = xmidi_data.find(b'FORM')
        xmidi_data = xmidi_data[form_pos:]
    else:
        return None
    
    # Find EVNT chunk
    evnt_pos = xmidi_data.find(b'EVNT')
    if evnt_pos < 0:
        return None
    
    # Get EVNT chunk size
    chunk_size = struct.unpack('>I', xmidi_data[evnt_pos+4:evnt_pos+8])[0]
    evnt_data = xmidi_data[evnt_pos+8:evnt_pos+8+chunk_size]
    
    print(f"  EVNT chunk: {chunk_size} bytes")
    
    # Use EVNT data directly as track data
    # XMIDI EVNT format is already close to MIDI track format
    
    # Build MIDI file
    midi_data = struct.pack('>4sIHHH',
                           b'MThd',
                           6,
                           0,    # Format 0
                           1,    # 1 track
                           120   # 120 ticks/quarter
                           )
    
    # Add Tempo at start
    tempo_event = bytes([0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20])
    
    # Combine tempo + EVNT data + End of Track
    track_data = tempo_event + evnt_data
    
    # Add End of Track if not present
    if b'\xFF\x2F\x00' not in track_data[-20:]:
        track_data += bytes([0x00, 0xFF, 0x2F, 0x00])
    
    # Track header
    midi_data += struct.pack('>4sI', b'MTrk', len(track_data))
    midi_data += track_data
    
    return midi_data

def convert_all_tracks(input_dir, output_dir):
    """Convert all XMIDI tracks"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    
    for track_file in sorted(input_dir.glob("track_*.bin")):
        if track_file.stat().st_size < 100:
            continue
        
        with open(track_file, 'rb') as f:
            data = f.read()
        
        midi_data = convert_xmidi_direct(data)
        
        if midi_data:
            track_id = track_file.stem.split('_')[1]
            midi_file = output_dir / f"track_{track_id}.mid"
            midi_file.write_bytes(midi_data)
            print(f"  [{track_id}] {len(data)} -> {len(midi_data)} bytes")
            converted += 1
        else:
            print(f"  [SKIP] {track_file.name}")
    
    print(f"\nConverted {converted} tracks to {output_dir}")

def main():
    input_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi_direct")
    
    if not input_dir.exists():
        print("Error: Input directory not found")
        return
    
    print("Converting XMIDI to MIDI (direct passthrough)...")
    convert_all_tracks(input_dir, output_dir)
    
    print(f"\nMIDI files saved to: {output_dir}")
    print(f"\nTest: {output_dir}/track_000.mid")

if __name__ == "__main__":
    main()
