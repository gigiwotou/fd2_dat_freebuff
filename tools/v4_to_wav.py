#!/usr/bin/env python3
"""Convert V4 MIDI to WAV for direct playback"""
import struct
import numpy as np
from pathlib import Path
import wave

def read_variable_length(data, pos):
    """Read variable-length integer"""
    value = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos

def midi_to_wav(midi_path, wav_path=None, sample_rate=22050):
    """Convert MIDI to WAV using simple synthesis"""
    with open(midi_path, 'rb') as f:
        data = f.read()
    
    # Parse header
    if data[:4] != b'MThd':
        return False
    
    fmt, tracks, ppqn = struct.unpack('>HHH', data[8:14])
    
    # Find track
    pos = 14
    if data[pos:pos+4] != b'MTrk':
        return False
    
    track_len = struct.unpack('>I', data[pos+4:pos+8])[0]
    track_data = data[pos+8:pos+8+track_len]
    
    # Parse all events
    events = []  # (abs_tick, type, data)
    abs_tick = 0
    tempo = 500000  # default 120 BPM
    running_status = None
    pos = 0
    
    while pos < len(track_data):
        # Read delta
        delta, pos = read_variable_length(track_data, pos)
        abs_tick += delta
        
        if pos >= len(track_data):
            break
        
        byte = track_data[pos]
        
        if byte >= 0x80:
            status = byte
            pos += 1
            running_status = status
        else:
            status = running_status
        
        if status is None:
            continue
        
        status_type = status & 0xF0
        channel = status & 0x0F
        
        if status == 0xFF:
            meta = track_data[pos]
            pos += 1
            length, pos = read_variable_length(track_data, pos)
            meta_data = track_data[pos:pos+length]
            pos += length
            
            if meta == 0x51 and length == 3:
                tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
            elif meta == 0x2F:
                break
        
        elif status >= 0xF0:
            if status in (0xF0, 0xF7):
                length, pos = read_variable_length(track_data, pos)
                pos += length
            else:
                pos += 1
            running_status = None
        
        else:
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                data1 = track_data[pos]
                data2 = track_data[pos+1]
                pos += 2
                
                if status_type == 0x90:
                    events.append((abs_tick, 'note_on', channel, data1, data2))
                elif status_type == 0x80:
                    events.append((abs_tick, 'note_off', channel, data1, data2))
            
            elif status_type in (0xC0, 0xD0):
                data1 = track_data[pos]
                pos += 1
                events.append((abs_tick, 'program', channel, data1, 0))
    
    if not events:
        return False
    
    # Calculate timing
    seconds_per_tick = tempo / 1000000.0 / ppqn
    max_tick = events[-1][0]
    duration_sec = max_tick * seconds_per_tick
    
    print(f"  PPQN: {ppqn}, Tempo: {tempo} ({60000000/tempo:.1f} BPM)")
    print(f"  Duration: {duration_sec:.2f}s, Events: {len(events)}")
    
    # Generate audio
    audio = np.zeros(int(duration_sec * sample_rate + 1), dtype=np.float32)
    
    # Simple sine wave synthesis
    active_notes = {}
    
    for abs_tick, event_type, channel, data1, data2 in events:
        time_sec = abs_tick * seconds_per_tick
        start_sample = int(time_sec * sample_rate)
        
        if event_type == 'note_on' and data2 > 0:
            freq = 440 * (2 ** ((data1 - 69) / 12.0))
            active_notes[data1] = (start_sample, freq, data2 / 127.0)
        elif event_type == 'note_off' or (event_type == 'note_on' and data2 == 0):
            if data1 in active_notes:
                start_sample, freq, vol = active_notes.pop(data1)
                
                # Find note duration
                end_sample = start_sample
                for next_tick, next_type, _, _, _ in events:
                    if next_tick > abs_tick:
                        end_sample = int(next_tick * seconds_per_tick * sample_rate)
                        break
                
                note_duration = (end_sample - start_sample) / sample_rate
                
                if 0.001 < note_duration < 5.0:
                    t = np.arange(int(note_duration * sample_rate)) / sample_rate
                    note = vol * 0.3 * np.sin(2 * np.pi * freq * t)
                    
                    # Envelope
                    attack = min(0.01, note_duration / 4)
                    release = min(0.05, note_duration / 4)
                    env = np.ones(len(note))
                    
                    if len(env) > int(attack * sample_rate):
                        env[:int(attack * sample_rate)] = np.linspace(0, 1, int(attack * sample_rate))
                    if len(env) > int(release * sample_rate):
                        env[-int(release * sample_rate):] = np.linspace(1, 0, int(release * sample_rate))
                    
                    note *= env
                    
                    # Mix
                    end_idx = min(start_sample + len(note), len(audio))
                    audio[start_sample:end_idx] += note[:end_idx-start_sample]
    
    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8
    
    # Save WAV
    if wav_path:
        with wave.open(str(wav_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        print(f"  Saved: {wav_path} ({len(audio)/sample_rate:.2f}s)")
        return True
    
    return False

# Convert all V5 MIDI files
output_dir = Path("output/fdmus_midi_v5")
wav_dir = output_dir / "wav"
wav_dir.mkdir(exist_ok=True)

for midi_file in sorted(output_dir.glob("track_*.mid")):
    wav_path = wav_dir / f"{midi_file.stem}.wav"
    print(f"\nConverting {midi_file.name}...")
    try:
        midi_to_wav(midi_file, wav_path)
    except Exception as e:
        print(f"  Error: {e}")
