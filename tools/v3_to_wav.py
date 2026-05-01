#!/usr/bin/env python3
"""Generate WAV from V3 MIDI files for playback"""
import struct
import numpy as np
from pathlib import Path
from mido import MidiFile
import sounddevice as sd

def midi_to_wav(midi_path, output_path=None, sample_rate=22050):
    """Convert MIDI to WAV"""
    mid = MidiFile(str(midi_path))
    
    if mid.type != 0:
        print(f"  Skipping non-type-0 MIDI")
        return False
    
    ppqn = mid.ticks_per_beat
    track = mid.tracks[0]
    
    # Calculate tempo and timing
    tempo = 500000  # default 120 BPM
    abs_tick = 0
    events = []  # (abs_time, type, data)
    
    for msg in track:
        abs_tick += msg.time
        
        if hasattr(msg, 'type') and msg.type == 'set_tempo':
            tempo = msg.tempo
        elif hasattr(msg, 'type') and msg.type in ('note_on', 'note_off', 'control_change', 'program_change'):
            events.append((abs_tick, msg.type, msg))
    
    if not events:
        return False
    
    # Convert to seconds
    seconds_per_tick = tempo / 1000000.0 / ppqn
    
    # Find max time
    max_tick = events[-1][0]
    duration_sec = max_tick * seconds_per_tick
    
    # Generate audio
    audio = np.zeros(int(duration_sec * sample_rate), dtype=np.float32)
    
    # Simple sine wave synthesis
    active_notes = {}  # note -> (start_sample, freq)
    
    for abs_tick, msg_type, msg in events:
        time_sec = abs_tick * seconds_per_tick
        start_sample = int(time_sec * sample_rate)
        
        if msg_type == 'note_on' and msg.velocity > 0:
            freq = 440 * (2 ** ((msg.note - 69) / 12.0))
            active_notes[msg.note] = (start_sample, freq, msg.velocity / 127.0)
        elif msg_type == 'note_off' or (msg_type == 'note_on' and msg.velocity == 0):
            if msg.note in active_notes:
                start_sample, freq, vol = active_notes.pop(msg.note)
                # Generate note
                end_sample = start_sample
                note_duration = 0.1  # default 100ms
                
                # Find next event for this note
                for next_tick, next_type, next_msg in events:
                    if next_tick > abs_tick:
                        end_sample = int(next_tick * seconds_per_tick * sample_rate)
                        note_duration = (end_sample - start_sample) / sample_rate
                        break
                
                if note_duration > 0 and note_duration < 2.0:
                    t = np.arange(int(note_duration * sample_rate)) / sample_rate
                    note = vol * 0.3 * np.sin(2 * np.pi * freq * t)
                    
                    # Apply envelope
                    attack = min(0.01, note_duration / 4)
                    release = min(0.05, note_duration / 4)
                    env = np.ones(len(note))
                    
                    if len(env) > int(attack * sample_rate):
                        env[:int(attack * sample_rate)] = np.linspace(0, 1, int(attack * sample_rate))
                    if len(env) > int(release * sample_rate):
                        env[-int(release * sample_rate):] = np.linspace(1, 0, int(release * sample_rate))
                    
                    note *= env
                    
                    # Mix into audio
                    end_idx = min(start_sample + len(note), len(audio))
                    audio[start_sample:end_idx] += note[:end_idx-start_sample]
    
    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8
    
    # Save as WAV
    if output_path:
        import wave
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        print(f"  Saved: {output_path}")
        return True
    
    return False

output_dir = Path("output/fdmus_midi_v3")

for midi_file in sorted(output_dir.glob("track_*.mid"))[:5]:
    wav_path = output_dir / f"{midi_file.stem}.wav"
    print(f"Converting {midi_file.name}...")
    midi_to_wav(midi_file, wav_path)
