#!/usr/bin/env python3
"""
FD2 XMIDI to WAV Converter - Fixed duration handling
"""

import struct
import math
import wave
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
                    pos += length
                    
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
                    else:
                        pass
                        
            elif command in (0xC0, 0xD0):
                if pos <= end:
                    pos += 1
                    
        else:
            if running_status is None:
                continue
                
            command = running_status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                pos += 2
            elif command in (0xC0, 0xD0):
                pass
    
    return events, tempo_data

def midi_note_to_freq(note):
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))

def generate_wav_fixed(events, tempo_data, output_path, sample_rate=22050):
    """Generate WAV using duration field from Note On events"""
    if not events:
        return False
    
    tempo = 500000
    if tempo_data and len(tempo_data) == 3:
        tempo = (tempo_data[0] << 16) | (tempo_data[1] << 8) | tempo_data[2]
    
    ppqn = 480
    seconds_per_tick = tempo / 1000000.0 / ppqn
    
    # Use duration field to determine note length
    notes = []  # (start_tick, duration_ticks, note, velocity, channel)
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
            
            # In XMIDI, duration field defines how long the note plays
            if duration > 0:
                notes.append((current_tick, duration, note, velocity, channel))
                
        # Ignore note_off events since we have duration field
    
    if not notes:
        return False
    
    # Calculate total duration
    max_tick = max(start + dur for start, dur, _, _, _ in notes)
    total_seconds = max_tick * seconds_per_tick
    
    if total_seconds <= 0 or total_seconds > 300:
        return False
    
    num_samples = int(total_seconds * sample_rate)
    audio = [0.0] * num_samples
    
    print(f"  {len(notes)} notes, {total_seconds:.2f}s duration")
    
    for start_tick, duration_ticks, note, velocity, channel in notes:
        freq = midi_note_to_freq(note)
        
        start_sample = int(start_tick * seconds_per_tick * sample_rate)
        end_sample = int((start_tick + duration_ticks) * seconds_per_tick * sample_rate)
        
        start_sample = max(0, min(start_sample, num_samples - 1))
        end_sample = max(start_sample + 1, min(end_sample, num_samples))
        
        num_note_samples = end_sample - start_sample
        if num_note_samples <= 0:
            continue
        
        amplitude = (velocity / 127.0) * 0.15
        
        for i in range(num_note_samples):
            t = i / sample_rate
            sample = amplitude * math.sin(2 * math.pi * freq * t)
            sample += amplitude * 0.3 * math.sin(2 * math.pi * freq * 2 * t)
            
            # Envelope
            attack = min(50, num_note_samples // 4)
            release = min(50, num_note_samples // 4)
            
            if i < attack:
                sample *= i / attack
            elif i > num_note_samples - release:
                sample *= (num_note_samples - i) / release
            
            if start_sample + i < num_samples:
                audio[start_sample + i] += sample
    
    # Normalize
    max_val = max(abs(s) for s in audio)
    if max_val > 0:
        scale = 0.8 / max_val
        audio = [s * scale for s in audio]
    
    # Convert to 16-bit
    audio_int16 = []
    for s in audio:
        val = int(s * 32767)
        val = max(-32768, min(32767, val))
        audio_int16.append(struct.pack('<h', val))
    
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(audio_int16))
    
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
    
    print("Converting XMIDI to WAV (fixed duration)...")
    
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
        
        has_notes = any(e[1] == 'note_on' for e in events)
        if not has_notes:
            continue
        
        output_file = output_dir / f'track_{i:03d}.wav'
        
        if generate_wav_fixed(events, tempo_data, output_file):
            file_size = output_file.stat().st_size
            duration = file_size / 44100.0
            print(f"Track {i}: {len(events)} events, {duration:.2f}s -> {output_file}")

if __name__ == '__main__':
    main()
