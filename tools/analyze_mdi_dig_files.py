#!/usr/bin/env python3
"""
Analyze .MDI and .DIG files in game directory
.MDI = MIDI driver files (Miles Sound System)
.DIG = Digital audio driver files (Miles Sound System)
"""

import os
from pathlib import Path

def analyze_file(filepath):
    """Analyze a single file to determine if it's audio"""
    print(f"\n{'='*60}")
    print(f"File: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    
    file_size = os.path.getsize(filepath)
    print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    with open(filepath, 'rb') as f:
        data = f.read(min(256, file_size))
    
    print(f"  First 64 bytes (hex):")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"    {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Check for known signatures
    if data[:4] == b'MThd':
        print(f"\n  ** Standard MIDI file detected **")
        return True, "MIDI"
    
    if data[:4] == b'AIL3':
        print(f"\n  ** AIL3 driver file detected (Miles Sound System) **")
        return False, "AIL3 Driver"
    
    if data[:4] in (b'XMI ', b'FORM'):
        print(f"\n  ** XMIDI/RIFF format detected **")
        return True, "XMIDI"
    
    if b'MDI' in data[:100] or b'midi' in data[:100].lower():
        print(f"\n  ** Likely MIDI driver file **")
        return False, "MIDI Driver"
    
    if b'DIG' in data[:100] or b'digital' in data[:100].lower():
        print(f"\n  ** Likely DIGITAL audio driver file **")
        return False, "Digital Driver"
    
    # Check if mostly code (driver) or data (audio)
    printable = sum(1 for b in data if 32 <= b < 127 or b in (0x0A, 0x0D, 0x09))
    printable_ratio = printable / len(data)
    print(f"\n  Printable ASCII ratio: {printable_ratio*100:.1f}%")
    
    if printable_ratio > 0.5:
        print(f"  ** Likely contains text/configuration (driver file) **")
        return False, "Driver"
    else:
        print(f"  ** Likely binary data (possible audio) **")
        return True, "Binary"

def main():
    game_dir = Path("game")
    
    mdi_files = sorted(game_dir.glob("*.MDI"))
    dig_files = sorted(game_dir.glob("*.DIG"))
    
    print(f"Found {len(mdi_files)} .MDI files")
    print(f"Found {len(dig_files)} .DIG files")
    
    audio_files = []
    driver_files = []
    
    print(f"\n{'='*60}")
    print(f"Analyzing .MDI files (MIDI drivers)")
    print(f"{'='*60}")
    
    for f in mdi_files:
        is_audio, file_type = analyze_file(f)
        if is_audio:
            audio_files.append((f, file_type))
        else:
            driver_files.append((f, file_type))
    
    print(f"\n{'='*60}")
    print(f"Analyzing .DIG files (Digital audio drivers)")
    print(f"{'='*60}")
    
    for f in dig_files:
        is_audio, file_type = analyze_file(f)
        if is_audio:
            audio_files.append((f, file_type))
        else:
            driver_files.append((f, file_type))
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"\nAudio files found: {len(audio_files)}")
    for f, t in audio_files:
        print(f"  {f.name}: {t}")
    
    print(f"\nDriver files found: {len(driver_files)}")
    for f, t in driver_files:
        print(f"  {f.name}: {t}")
    
    print(f"\n{'='*60}")
    print(f"CONCLUSION")
    print(f"{'='*60}")
    if not audio_files:
        print(f"\n  ** No actual audio files found in .MDI/.DIG files **")
        print(f"  ** These are all DRIVER files for Miles Sound System **")
        print(f"  ** The actual audio data is in FDMUS.DAT and potentially embedded in the game **")
    else:
        print(f"\n  Found {len(audio_files)} audio file(s)")

if __name__ == "__main__":
    main()
