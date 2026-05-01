#!/usr/bin/env python3
"""Compare correct MIDI files with v2 output"""
from pathlib import Path
from mido import MidiFile

correct_dir = Path("tools/fd2 midi")
v2_dir = Path("output/fdmus_midi_v2")

# Compare track 0, 3, 5, 7, 10, 11 (some that exist in both)
pairs = [
    ("fd200000.mid", "track_000.mid"),
    ("fd200003.mid", "track_003.mid"),
    ("fd200005.mid", "track_005.mid"),
    ("fd200007.mid", "track_007.mid"),
    ("fd200010.mid", "track_010.mid"),
    ("fd200011.mid", "track_011.mid"),
]

for correct_file, v2_file in pairs:
    correct_path = correct_dir / correct_file
    v2_path = v2_dir / v2_file
    
    if not correct_path.exists():
        print(f"\n{'='*60}")
        print(f"Correct file not found: {correct_file}")
        continue
    
    if not v2_path.exists():
        print(f"\n{'='*60}")
        print(f"V2 file not found: {v2_file}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Comparing: {correct_file} vs {v2_file}")
    print(f"{'='*60}")
    
    # Correct file
    mid_correct = MidiFile(str(correct_path))
    print(f"\nCorrect file:")
    print(f"  Type: {mid_correct.type}, Ticks/beat: {mid_correct.ticks_per_beat}")
    print(f"  Tracks: {len(mid_correct.tracks)}")
    
    for i, track in enumerate(mid_correct.tracks):
        print(f"\n  Track {i}: {len(track)} events")
        event_count = 0
        for msg in track[:10]:
            print(f"    {msg}")
            event_count += 1
        
        # Count event types
        note_on = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_on')
        note_off = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_off')
        cc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'control_change')
        pc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'program_change')
        tempo = sum(1 for m in track if hasattr(m, 'type') and m.type == 'set_tempo')
        end_track = sum(1 for m in track if hasattr(m, 'type') and m.type == 'end_of_track')
        time_sig = sum(1 for m in track if hasattr(m, 'type') and m.type == 'time_signature')
        key_sig = sum(1 for m in track if hasattr(m, 'type') and m.type == 'key_signature')
        
        print(f"\n  Events: NoteOn={note_on}, NoteOff={note_off}, CC={cc}, PC={pc}, Tempo={tempo}, TimeSig={time_sig}, KeySig={key_sig}, End={end_track}")
    
    # V2 file
    mid_v2 = MidiFile(str(v2_path))
    print(f"\nV2 file:")
    print(f"  Type: {mid_v2.type}, Ticks/beat: {mid_v2.ticks_per_beat}")
    print(f"  Tracks: {len(mid_v2.tracks)}")
    
    for i, track in enumerate(mid_v2.tracks):
        print(f"\n  Track {i}: {len(track)} events")
        event_count = 0
        for msg in track[:10]:
            print(f"    {msg}")
            event_count += 1
        
        # Count event types
        note_on = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_on')
        note_off = sum(1 for m in track if hasattr(m, 'type') and m.type == 'note_off')
        cc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'control_change')
        pc = sum(1 for m in track if hasattr(m, 'type') and m.type == 'program_change')
        tempo = sum(1 for m in track if hasattr(m, 'type') and m.type == 'set_tempo')
        end_track = sum(1 for m in track if hasattr(m, 'type') and m.type == 'end_of_track')
        time_sig = sum(1 for m in track if hasattr(m, 'type') and m.type == 'time_signature')
        key_sig = sum(1 for m in track if hasattr(m, 'type') and m.type == 'key_signature')
        
        print(f"\n  Events: NoteOn={note_on}, NoteOff={note_off}, CC={cc}, PC={pc}, Tempo={tempo}, TimeSig={time_sig}, KeySig={key_sig}, End={end_track}")
    
    # Show first tempo difference
    if mid_correct.type == 0 and mid_v2.type == 0:
        correct_tempo = None
        v2_tempo = None
        for msg in mid_correct.tracks[0]:
            if hasattr(msg, 'type') and msg.type == 'set_tempo':
                correct_tempo = msg.tempo
                break
        for msg in mid_v2.tracks[0]:
            if hasattr(msg, 'type') and msg.type == 'set_tempo':
                v2_tempo = msg.tempo
                break
        
        if correct_tempo and v2_tempo:
            print(f"\nTempo comparison:")
            print(f"  Correct: {correct_tempo} ({60000000/correct_tempo:.1f} BPM)")
            print(f"  V2:      {v2_tempo} ({60000000/v2_tempo:.1f} BPM)")
            print(f"  Ratio:   {v2_tempo/correct_tempo:.2f}x")
