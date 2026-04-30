#!/usr/bin/env python3
"""
Use mido library to create proper MIDI from XMIDI events
mido is a proper MIDI library that handles all the details correctly
"""

try:
    import mido
    HAS_MIDO = True
except ImportError:
    HAS_MIDO = False
    print("Installing mido library...")
    import subprocess
    subprocess.run(['pip', 'install', 'mido'])
    import mido
    HAS_MIDO = True

import struct
from pathlib import Path

def parse_variable_length(data, pos, end):
    """Parse variable-length quantity"""
    value = 0
    while pos < end:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos

def extract_midi_messages(xmidi_data):
    """Extract MIDI messages from XMIDI EVNT chunk"""
    messages = []
    
    evnt_pos = xmidi_data.find(b'EVNT')
    if evnt_pos < 0:
        return messages
    
    chunk_size = struct.unpack('>I', xmidi_data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    running_status = 0
    abs_time = 0
    
    while pos < end:
        delta, pos = parse_variable_length(xmidi_data, pos, end)
        abs_time += delta
        
        if pos >= end:
            break
        
        byte = xmidi_data[pos]
        
        if byte >= 0x80:
            status = byte
            pos += 1
            running_status = status
        else:
            status = running_status
        
        if status == 0xFF:  # Meta
            if pos >= end:
                break
            meta_type = xmidi_data[pos]
            pos += 1
            
            length = 0
            while pos < end:
                b = xmidi_data[pos]
                pos += 1
                length = (length << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            
            if meta_type == 0x2F:
                messages.append(('end_of_track', abs_time))
                break
            
            data_bytes = xmidi_data[pos:pos+length]
            pos += length
            
            if meta_type == 0x51:  # Tempo
                if len(data_bytes) == 3:
                    tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                    messages.append(('set_tempo', abs_time, tempo))
            # Skip other meta events
            
            running_status = 0
            
        elif status in (0xF0, 0xF7):  # SysEx
            length, pos = parse_variable_length(xmidi_data, pos, end)
            pos += length
            running_status = 0
            
        elif status >= 0x80:
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 >= end:
                    break
                byte1 = xmidi_data[pos]
                byte2 = xmidi_data[pos+1]
                pos += 2
                
                # Clamp values to valid MIDI range
                byte1 = max(0, min(127, byte1))
                byte2 = max(0, min(127, byte2))
                
                if command == 0x90:
                    if byte2 > 0:
                        messages.append(('note_on', abs_time, channel, byte1, byte2))
                    else:
                        messages.append(('note_off', abs_time, channel, byte1))
                elif command == 0x80:
                    messages.append(('note_off', abs_time, channel, byte1))
                elif command == 0xB0:
                    messages.append(('control_change', abs_time, channel, byte1, byte2))
                elif command == 0xE0:
                    pitch = (byte2 << 7) | byte1
                    messages.append(('pitchwheel', abs_time, channel, pitch))
                    
            elif command in (0xC0, 0xD0):
                if pos >= end:
                    break
                byte1 = xmidi_data[pos]
                pos += 1
                byte1 = max(0, min(127, byte1))
                
                if command == 0xC0:
                    messages.append(('program_change', abs_time, channel, byte1))
    
    return messages

def convert_xmidi_to_midi_with_mido(xmidi_data):
    """Convert XMIDI to MIDI using mido library"""
    
    # Find FORM chunk
    if xmidi_data[:4] == b'FORM' and b'XMID' in xmidi_data[12:20]:
        pass
    elif b'FORM' in xmidi_data:
        form_pos = xmidi_data.find(b'FORM')
        xmidi_data = xmidi_data[form_pos:]
    else:
        return None
    
    # Extract MIDI messages
    messages = extract_midi_messages(xmidi_data)
    
    if not messages:
        return None
    
    # Create MIDI file using mido
    mid = mido.MidiFile(type=0, ticks_per_beat=120)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Add messages in order
    prev_time = 0
    for msg in messages:
        if msg[0] == 'end_of_track':
            track.append(mido.MetaMessage('end_of_track', time=msg[1] - prev_time))
            break
        elif msg[0] == 'set_tempo':
            track.append(mido.MetaMessage('set_tempo', tempo=msg[2], time=msg[1] - prev_time))
        elif msg[0] == 'note_on':
            track.append(mido.Message('note_on', channel=msg[2], note=msg[3], velocity=msg[4], 
                                     time=msg[1] - prev_time))
        elif msg[0] == 'note_off':
            track.append(mido.Message('note_off', channel=msg[2], note=msg[3], 
                                     time=msg[1] - prev_time))
        elif msg[0] == 'program_change':
            track.append(mido.Message('program_change', channel=msg[2], program=msg[3],
                                     time=msg[1] - prev_time))
        elif msg[0] == 'control_change':
            track.append(mido.Message('control_change', channel=msg[2], control=msg[3], 
                                     value=msg[4], time=msg[1] - prev_time))
        elif msg[0] == 'pitchwheel':
            track.append(mido.Message('pitchwheel', channel=msg[2], pitch=msg[3],
                                     time=msg[1] - prev_time))
        
        prev_time = msg[1]
    
    # Convert to bytes
    import io
    buf = io.BytesIO()
    mid.save(file=buf)
    
    return buf.getvalue()

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
        
        midi_data = convert_xmidi_to_midi_with_mido(data)
        
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
    output_dir = Path("output/fdmus_midi_mido")
    
    if not input_dir.exists():
        print("Error: Input directory not found")
        return
    
    print("Converting XMIDI to MIDI using mido library...")
    convert_all_tracks(input_dir, output_dir)
    
    print(f"\nMIDI files saved to: {output_dir}")
    print(f"\nTest: {output_dir}/track_000.mid")

if __name__ == "__main__":
    main()
