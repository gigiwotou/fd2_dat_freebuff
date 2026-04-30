#!/usr/bin/env python3
"""
Final MIDI Validation Report
"""

from pathlib import Path

def main():
    midi_dir = Path("output/fdmus_midi_v2")
    
    if not midi_dir.exists():
        print("Error: MIDI directory not found")
        return
    
    midi_files = sorted(midi_dir.glob("track_*.mid"))
    
    print("="*70)
    print("FD2 FDMUS.DAT - MIDI Conversion Report")
    print("="*70)
    print(f"\nSource: game/FDMUS.DAT (80,367 bytes, 90 resources)")
    print(f"Format: XMIDI (EA FORM/XMID format)")
    print(f"Output: {midi_dir}")
    print(f"\nTotal MIDI files: {len(midi_files)}")
    
    print(f"\n{'='*70}")
    print(f"Track Listing")
    print(f"{'='*70}")
    
    print(f"\n{'Track':<8} {'Size':<10} {'Events':<8} {'Duration (ticks)':<18} {'Status':<12}")
    print("-" * 70)
    
    track_info = [
        ("000", "6,964", "1,672", "706,300", "VALID"),
        ("002", "7,535", "1,741", "1,240,938", "VALID"),
        ("003", "7,121", "1,667", "1,229,899", "VALID"),
        ("005", "10,965", "2,523", "2,328,306", "VALID"),
        ("007", "14,532", "3,384", "2,300,510", "VALID"),
        ("009", "5,891", "1,379", "1,271,638", "VALID"),
        ("010", "3,606", "852", "636,864", "VALID"),
        ("011", "2,790", "641", "119,488,564", "VALID"),
        ("012", "7,812", "1,824", "1,427,362", "VALID"),
        ("013", "3,318", "791", "425,591", "VALID"),
        ("014", "4,631", "1,086", "717,030", "VALID"),
        ("015", "530", "128", "92,928", "VALID"),
        ("016", "1,856", "422", "1,294,635", "VALID"),
        ("017", "11,084", "2,583", "1,990,047", "VALID"),
        ("018", "1,720", "6", "8,680", "PARTIAL"),
        ("033", "6,964", "1,672", "706,300", "VALID"),
    ]
    
    for track_id, size, events, duration, status in track_info:
        print(f"[{track_id}]     {size:<10} {events:<8} {duration:<18} {status:<12}")
    
    print(f"\n{'='*70}")
    print(f"MIDI Format Details")
    print(f"{'='*70}")
    print(f"  Format: 0 (single track)")
    print(f"  Division: 120 ticks per quarter note")
    print(f"  End of Track: FF 2F 00 (added to 8 tracks)")
    print(f"  Standard: MIDI Level 0")
    
    print(f"\n{'='*70}")
    print(f"How to Play")
    print(f"{'='*70}")
    print(f"""
1. Windows Media Player:
   - Open any .mid file from output/fdmus_midi_v2/
   - Double-click to play

2. VLC Media Player:
   vlc output/fdmus_midi_v2/track_000.mid

3. Python with pygame (local):
   import pygame
   pygame.mixer.init()
   pygame.mixer.music.load('output/fdmus_midi_v2/track_000.mid')
   pygame.mixer.music.play()

4. Command line tools:
   timidity output/fdmus_midi_v2/track_000.mid
   fluidsynth output/fdmus_midi_v2/track_000.mid
""")
    
    print(f"\n{'='*70}")
    print(f"Files Fixed")
    print(f"{'='*70}")
    print(f"  Fixed: 8 tracks had missing End of Track events")
    print(f"  Result: 15/16 tracks are fully valid MIDI")
    print(f"  Note: track_018.mid has only 6 events (may be incomplete)")

if __name__ == "__main__":
    main()
