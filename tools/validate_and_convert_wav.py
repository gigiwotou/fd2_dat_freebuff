#!/usr/bin/env python3
"""
Convert XMIDI to WAV format for guaranteed playback
"""

import struct
import io
from pathlib import Path
import numpy as np

def parse_xmidi_v3(data, pos, end):
    """Parse XMIDI with correct delta handling"""
    events = []
    running_status = None
    tempo_data = None
    
    while pos < end:
        delta = 0
        first_byte = data[pos]
        
        if first_byte < 0x80:
            delta = first_byte
            pos += 1
            if pos >= end:
                break
            status = data[pos]
            pos += 1
        else:
            status = first_byte
            pos += 1
        
        if status == 0xFF:
            if pos >= end:
                break
            
            meta_type = data[pos]
            pos += 1
            
            length = 0
            count = 0
            while pos < end and count < 4:
                byte = data[pos]
                pos += 1
                count += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if meta_type == 0x2F:
                events.append((delta, 'meta', 0x2F, b''))
                break
            elif meta_type == 0x51 and length == 3:
                if pos + 3 <= end:
                    tempo_data = bytes(data[pos:pos+3])
                    pos += 3
                    events.append((delta, 'meta', 0x51, tempo_data))
            else:
                if pos + length <= end:
                    meta_data = bytes(data[pos:pos+length])
                    pos += length
                    events.append((delta, 'meta', meta_type, meta_data))
                    
        elif status == 0xF0 or status == 0xF7:
            length = 0
            count = 0
            while pos < end and count < 4:
                byte = data[pos]
                pos += 1
                count += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            if pos + length <= end:
                pos += length
                
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 2 <= end:
                    b1 = data[pos]
                    b2 = data[pos + 1]
                    pos += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            duration = 0
                            count = 0
                            while pos < end and count < 4:
                                byte = data[pos]
                                pos += 1
                                count += 1
                                duration = (duration << 7) | (byte & 0x7F)
                                if not (byte & 0x80):
                                    break
                            
                            events.append((delta, 'note_on', status & 0xF, b1, b2, duration))
                        else:
                            events.append((delta, 'note_off', status & 0xF, b1))
                    elif command == 0x80:
                        events.append((delta, 'note_off', status & 0xF, b1))
                    else:
                        events.append((delta, 'midi', status, b1, b2))
                        
            elif command in (0xC0, 0xD0):
                if pos <= end:
                    b1 = data[pos]
                    pos += 1
                    events.append((delta, 'midi', status, b1))
                    
        else:
            if running_status is None:
                continue
                
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                b1 = status
                if pos < end:
                    b2 = data[pos]
                    pos += 1
                    
                    if command == 0x90:
                        if b2 > 0:
                            duration = 0
                            count = 0
                            while pos < end and count < 4:
                                byte = data[pos]
                                pos += 1
                                count += 1
                                duration = (duration << 7) | (byte & 0x7F)
                                if not (byte & 0x80):
                                    break
                            
                            events.append((delta, 'note_on', running_status & 0xF, b1, b2, duration))
                        else:
                            events.append((delta, 'note_off', running_status & 0xF, b1))
                    elif command == 0x80:
                        events.append((delta, 'note_off', running_status & 0xF, b1))
                    else:
                        events.append((delta, 'midi', running_status, b1, b2))
                        
            elif command in (0xC0, 0xD0):
                events.append((delta, 'midi', running_status, status))
    
    return events, tempo_data

def midi_to_wav(events, tempo_data, output_file, sample_rate=44100):
    """Convert MIDI events to WAV audio"""
    if not events:
        return
    
    # Calculate tempo
    tempo = 500000  # Default 120 BPM
    if tempo_data:
        tempo = (tempo_data[0] << 16) | (tempo_data[1] << 8) | tempo_data[2]
    
    seconds_per_beat = tempo / 1000000
    ticks_per_beat = 480  # PPQN
    seconds_per_tick = seconds_per_beat / ticks_per_beat
    
    # Build note list
    notes = []  # (start_time, duration, note, velocity)
    current_time = 0
    active_notes = {}  # note -> start_time
    
    for event in events:
        delta = event[0]
        current_time += delta * seconds_per_tick
        
        evt_type = event[1]
        
        if evt_type == 'note_on':
            channel = event[2]
            note = event[3]
            velocity = event[4]
            duration = event[5] if len(event) > 5 else 0
            
            duration_time = duration * seconds_per_tick
            
            # Store active note
            key = (channel, note)
            active_notes[key] = (current_time, duration_time, velocity)
            
        elif evt_type == 'note_off':
            channel = event[2]
            note = event[3]
            
            key = (channel, note)
            if key in active_notes:
                start_time, duration_time, velocity = active_notes[key]
                notes.append((start_time, duration_time, note, velocity))
                del active_notes[key]
    
    if not notes:
        print(f"  No notes found")
        return
    
    # Calculate total duration
    max_time = max(note[0] + note[1] for note in notes)
    num_samples = int(max_time * sample_rate)
    
    if num_samples == 0 or num_samples > sample_rate * 300:  # Max 5 minutes
        print(f"  Invalid duration: {num_samples} samples")
        return
    
    # Generate audio
    audio = np.zeros(num_samples, dtype=np.float32)
    
    for start_time, duration_time, note, velocity in notes:
        # MIDI note to frequency
        frequency = 440 * (2 ** ((note - 69) / 12))
        
        start_sample = int(start_time * sample_rate)
        end_sample = int((start_time + duration_time) * sample_rate)
        
        if start_sample >= num_samples:
            continue
        
        end_sample = min(end_sample, num_samples)
        
        # Generate sine wave
        t = np.arange(end_sample - start_sample) / sample_rate
        # Apply velocity to amplitude (0-127 -> 0-0.3)
        amplitude = (velocity / 127) * 0.3
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Apply envelope
        attack_time = 0.01
        release_time = 0.05
        
        attack_samples = int(attack_time * sample_rate)
        release_samples = int(release_time * sample_rate)
        
        if len(wave) > attack_samples + release_samples:
            # Attack
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
            # Release
            wave[-release_samples:] *= np.linspace(1, 0, release_samples)
        
        audio[start_sample:end_sample] += wave
    
    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.9
    
    # Convert to 16-bit
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Write WAV
    import wave
    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    duration_sec = num_samples / sample_rate
    print(f"  Generated {duration_sec:.2f}s WAV")

def main():
    fdmus_path = Path('game/FDMUS.DAT')
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    output_dir = Path('output/fdmus_wav')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert tracks 10, 11, 12 first
    for i in [10, 11, 12]:
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        track_data = data[start:end]
        
        evnt_pos = track_data.find(b'EVNT')
        if evnt_pos < 0:
            continue
        
        if evnt_pos + 8 > len(track_data):
            continue
        
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        
        if evnt_pos + 8 + chunk_size > len(track_data):
            continue
        
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        events, tempo_data = parse_xmidi_v3(evnt_data, 0, len(evnt_data))
        
        if not events:
            continue
        
        output_file = output_dir / f'track_{i:03d}.wav'
        midi_to_wav(events, tempo_data, output_file)
        print(f"Track {i}: {len(events)} events -> {output_file}")

if __name__ == '__main__':
    main()
