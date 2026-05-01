#!/usr/bin/env python3
"""Debug v2 MIDI files"""
from pathlib import Path
from mido import MidiFile

output_dir = Path("output/fdmus_midi_v2")

for track_file in sorted(output_dir.glob("track_*.mid"))[:5]:
    print(f"\n{'='*60}")
    print(f"File: {track_file.name}")
    print(f"{'='*60}")
    
    mid = MidiFile(str(track_file))
    print(f"  Type: {mid.type}, Ticks/beat: {mid.ticks_per_beat}")
    print(f"  Tracks: {len(mid.tracks)}")
    
    for i, track in enumerate(mid.tracks):
        print(f"\n  Track {i}: {len(track)} events")
        event_count = 0
        for msg in track:
            if event_count < 15:
                print(f"    {msg}")
            event_count += 1
        
        # Count event types
        note_on = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_on')
        note_off = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_off')
        cc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'control_change')
        pc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'program_change')
        tempo = sum(1 for m in track if hasattr(m, 'type') and m.type == 'set_tempo')
        
        print(f"\n  Event counts: NoteOn={note_on}, NoteOff={note_off}, CC={cc}, PC={pc}, Tempo={tempo}")
        if event_count > 15:
            print(f"  ... ({event_count} total events)")
