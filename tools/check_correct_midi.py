#!/usr/bin/env python3
"""Check if correct MIDI files can be parsed by mido"""
from pathlib import Path
from mido import MidiFile

correct_dir = Path("tools/fd2 midi")

for midi_file in sorted(correct_dir.glob("fd2*.mid"))[:5]:
    try:
        mid = MidiFile(str(midi_file))
        print(f"✓ {midi_file.name}: Type={mid.type}, PPQN={mid.ticks_per_beat}, Tracks={len(mid.tracks)}")
        for i, track in enumerate(mid.tracks):
            events = len(track)
            print(f"    Track {i}: {events} events")
    except Exception as e:
        print(f"✗ {midi_file.name}: {e}")
