#!/usr/bin/env python3
"""Check V3 MIDI files"""
from pathlib import Path
from mido import MidiFile

output_dir = Path("output/fdmus_midi_v3")

for track_file in sorted(output_dir.glob("track_*.mid"))[:5]:
    try:
        mid = MidiFile(str(track_file))
        track = mid.tracks[0]
        
        note_on = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_on')
        note_off = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_off')
        cc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'control_change')
        pc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'program_change')
        tempo = sum(1 for m in track if hasattr(m, 'type') and m.type == 'set_tempo')
        
        print(f"OK: {track_file.name}")
        print(f"    {len(track)} events: NoteOn={note_on}, NoteOff={note_off}, CC={cc}, PC={pc}, Tempo={tempo}")
        
        # Show first 5 events
        for i, msg in enumerate(track[:5]):
            print(f"    [{i}] {msg}")
    except Exception as e:
        print(f"ERROR: {track_file.name}: {e}")
