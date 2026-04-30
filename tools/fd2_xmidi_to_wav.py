#!/usr/bin/env python3
"""
FD2 XMIDI to WAV Converter - Direct synthesis for guaranteed playback
"""

import struct
import math
import wave
import numpy as np
from pathlib import Path

def parse_xmidi(data):
    """Parse XMIDI events"""
    events = []
    running_status = None
    tempo_data = None
    pos = 0
    end = len(data)
    
    while pos < end:
        delta = 0
        first_byte = data[pos]
        
        # Delta time: single byte < 0x80
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
            # Meta event
            if pos >= end:
                break
            
            meta_type = data[pos]
            pos += 1
            
            # Length is VLQ
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
                    pos += length
                    
        elif status == 0xF0 or status == 0xF7:
            # SysEx - skip
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
            # New status
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 2 <= end:
                    b1 = data[pos]
                    b2 = data[pos + 1]
                    pos += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Note On - duration is VLQ
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
                    else:
                        pass  # Other MIDI events
                        
            elif command in (0xC0, 0xD0):
                if pos <= end:
                    pos += 1
                    
        else:
            # Running status
            if running_status is None:
                continue
                
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                pos += 1 if command in (0xC0, 0xD0) else 2
                    
            elif command in (0xC0, 0xD0):
                pass  # Single data byte is 'status' itself
    
    return events, tempo_data

def midi_note_to_freq(note):
    """Convert MIDI note number to frequency"""
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))

def generate_wav(events, tempo_data, output_path, sample_rate=44100):
    """Generate WAV from MIDI events"""
    if not events:
        return False
    
    # Parse tempo
    tempo = 500000  # Default 120 BPM (500000 microseconds per beat)
    if tempo_data and len(tempo_data) == 3:
        tempo = (tempo_data[0] << 16) | (tempo_data[1] << 8) | tempo_data[2]
    
    ppqn = 480  # Ticks per beat
    seconds_per_tick = tempo / 1000000.0 / ppqn
    
    # Collect all notes with timing
    notes = []  # (start_tick, duration_ticks, note, velocity, channel)
    active_notes = {}  # (channel, note) -> (start_tick, velocity)
    current_tick = 0
    
    for event in events:
        delta = event[0]
        current_tick += delta
        
        evt_type = event[1]
        
        if evt_type == 'note_on':
            channel = event[2]
            note = event[3]
            velocity = event[4]
            duration = event[5] if len(event) > 5 else 0
            
            key = (channel, note)
            active_notes[key] = (current_tick, velocity, duration)
            
            # If duration > 0, create note immediately
            if duration > 0:
                notes.append((current_tick, duration, note, velocity, channel))
                
        elif evt_type == 'note_off':
            channel = event[2]
            note = event[3]
            
            key = (channel, note)
            if key in active_notes:
                start_tick, velocity, _ = active_notes[key]
                duration = current_tick - start_tick
                notes.append((start_tick, max(duration, 10), note, velocity, channel))
                del active_notes[key]
    
    # Handle remaining active notes
    for key, (start_tick, velocity, duration) in active_notes.items():
        channel, note = key
        if duration > 0:
            notes.append((start_tick, duration, note, velocity, channel))
        else:
            notes.append((start_tick, 480, note, velocity, channel))  # Default 1 beat
    
    if not notes:
        return False
    
    # Calculate total duration
    max_tick = max(start + dur for start, dur, _, _, _ in notes)
    total_seconds = max_tick * seconds_per_tick
    
    if total_seconds <= 0 or total_seconds > 300:  # Max 5 minutes
        return False
    
    num_samples = int(total_seconds * sample_rate)
    audio = np.zeros(num_samples, dtype=np.float64)
    
    # Generate audio for each note
    for start_tick, duration_ticks, note, velocity, channel in notes:
        freq = midi_note_to_freq(note)
        
        start_sample = int(start_tick * seconds_per_tick * sample_rate)
        duration_seconds = duration_ticks * seconds_per_tick
        end_sample = int((start_tick + duration_ticks) * seconds_per_tick * sample_rate)
        
        start_sample = max(0, min(start_sample, num_samples - 1))
        end_sample = max(start_sample + 1, min(end_sample, num_samples))
        
        num_note_samples = end_sample - start_sample
        if num_note_samples <= 0:
            continue
        
        t = np.arange(num_note_samples) / sample_rate
        
        # Amplitude from velocity (0-127 -> 0-0.2)
        amplitude = (velocity / 127.0) * 0.2
        
        # Generate waveform with harmonics for richer sound
        wave = amplitude * np.sin(2 * np.pi * freq * t)
        wave += amplitude * 0.5 * np.sin(2 * np.pi * freq * 2 * t)  # 2nd harmonic
        wave += amplitude * 0.25 * np.sin(2 * np.pi * freq * 3 * t)  # 3rd harmonic
        
        # Apply envelope
        attack_ms = 10
        release_ms = 50
        attack_samples = int(attack_ms / 1000.0 * sample_rate)
        release_samples = int(release_ms / 1000.0 * sample_rate)
        
        if num_note_samples > attack_samples + release_samples:
            # Attack
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
            # Release
            wave[-release_samples:] *= np.linspace(1, 0, release_samples)
        elif num_note_samples > attack_samples:
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
            wave[attack_samples:] *= np.linspace(1, 0, num_note_samples - attack_samples)
        
        # Add to audio
        for i in range(num_note_samples):
            if start_sample + i < num_samples:
                audio[start_sample + i] += wave[i]
    
    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8
    
    # Convert to 16-bit
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Write WAV
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    return True

def main():
    fdmus_path = Path('game/FDMUS.DAT')
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    output_dir = Path('output/fdmus_wav')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Converting to WAV format...")
    
    # Convert all tracks with EVNT
    for i in range(count):
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
        
        events, tempo_data = parse_xmidi(evnt_data)
        
        if not events:
            continue
        
        # Check if we have any note events
        has_notes = any(e[1] == 'note_on' for e in events)
        if not has_notes:
            continue
        
        output_file = output_dir / f'track_{i:03d}.wav'
        
        if generate_wav(events, tempo_data, output_file):
            duration = output_file.stat().st_size / 88200  # Approx duration
            print(f"Track {i}: {len(events)} events, {duration:.1f}s -> {output_file}")
        else:
            print(f"Track {i}: Failed to generate")
    
    print(f"\nWAV files saved to: {output_dir}")

if __name__ == '__main__':
    main()
