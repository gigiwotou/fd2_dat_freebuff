#!/usr/bin/env python3
"""
FD2 Audio Test Tool - Summary Report
No playback required - just shows extracted data
"""

from pathlib import Path

def main():
    print("="*70)
    print("FD2 FDMUS.DAT Audio Resource Analysis Report")
    print("="*70)
    
    # Check original DAT file
    fdmus_path = Path("game/FDMUS.DAT")
    if fdmus_path.exists():
        size = fdmus_path.stat().st_size
        print(f"\nOriginal file: {fdmus_path}")
        print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
    else:
        print(f"\nERROR: {fdmus_path} not found!")
        return
    
    # Check extracted tracks
    track_dir = Path("output/fdmus_tracks")
    midi_dir_v2 = Path("output/fdmus_midi_v2")
    
    if track_dir.exists():
        tracks = list(track_dir.glob("track_*.bin"))
        print(f"\nExtracted tracks: {len(tracks)}")
        
        # Show size distribution
        sizes = [t.stat().st_size for t in tracks]
        print(f"  Size range: {min(sizes)} - {max(sizes)} bytes")
        print(f"  Total size: {sum(sizes):,} bytes")
    
    if midi_dir_v2.exists():
        midi_files = list(midi_dir_v2.glob("track_*.mid"))
        print(f"\nConverted MIDI files: {len(midi_files)}")
        
        # Show track info
        print(f"\n{'Track ID':<10} {'Raw Size':<10} {'MIDI Size':<10}")
        print("-" * 50)
        
        for midi_file in sorted(midi_dir_v2.glob("track_*.mid")):
            track_id = midi_file.stem.split('_')[1]
            raw_file = track_dir / f"track_{track_id}.bin"
            
            if raw_file.exists():
                raw_size = raw_file.stat().st_size
                midi_size = midi_file.stat().st_size
                print(f"[{track_id}]      {raw_size:<10,} {midi_size:<10,}")
        
        print(f"\nMIDI files saved to: {midi_dir_v2}")
    
    print(f"\n{'='*70}")
    print("How to play these MIDI files:")
    print(f"{'='*70}")
    print(f"""
1. Using VLC Media Player:
   vlc output/fdmus_midi_v2/track_000.mid

2. Using Windows Media Player:
   Double-click the .mid files

3. Using Python with pygame (local, not sandbox):
   pip install pygame
   python -c "import pygame; pygame.mixer.init(); pygame.mixer.music.load('output/fdmus_midi_v2/track_000.mid'); pygame.mixer.music.play()"

4. Using command line (Linux/Mac with timidity):
   timidity output/fdmus_midi_v2/track_000.mid
""")

if __name__ == "__main__":
    main()
