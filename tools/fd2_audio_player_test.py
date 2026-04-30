#!/usr/bin/env python3
"""
FD2 Audio Player - 自动测试版
直接播放第一个有效音轨并生成WAV文件
"""

import struct
import wave
import math
import os
import tempfile
from pathlib import Path
import time

class SimpleSynth:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def note_to_freq(self, note):
        return 440.0 * (2.0 ** ((note - 69) / 12.0))
    
    def generate_note(self, freq, duration_sec, velocity=64):
        num_samples = int(self.sample_rate * duration_sec)
        if num_samples <= 0:
            return []
        
        volume = (velocity / 127.0) * 0.3
        samples = []
        for i in range(num_samples):
            t = i / self.sample_rate
            val = 0.5 * math.sin(2 * math.pi * freq * t)
            val += 0.3 * math.sin(4 * math.pi * freq * t)
            val += 0.2 * math.sin(6 * math.pi * freq * t)
            val *= volume
            val = max(-1.0, min(1.0, val))
            samples.append(int(val * 32767))
        
        return samples

class XMidiParser:
    def parse(self, data):
        self.events = []
        evnt_pos = data.find(b'EVNT')
        if evnt_pos < 0:
            return self.events
        
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        pos = evnt_pos + 8
        end = pos + chunk_size
        
        while pos < end:
            delta = 0
            while pos < end:
                byte = data[pos]
                if byte >= 0x80:
                    break
                pos += 1
                delta = (delta << 7) | byte
            
            if pos >= end:
                break
            
            status = data[pos]
            pos += 1
            
            if status == 0xFF:
                pos = self._parse_meta(data, pos, end, delta)
            elif status >= 0x80:
                pos = self._parse_channel(data, pos, end, delta, status)
        
        return self.events
    
    def _parse_meta(self, data, pos, end, delta):
        if pos >= end:
            return pos
        meta_type = data[pos]
        pos += 1
        length = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            length = (length << 7) | byte
            if not (byte & 0x80):
                break
        
        data_bytes = data[pos:pos+length]
        pos += length
        
        if meta_type == 0x2F:
            self.events.append((delta, 0xFF, 0x2F, 0))
        elif meta_type == 0x51 and length == 3:
            tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
            self.events.append((delta, 0xFF, 0x51, tempo))
        return pos
    
    def _parse_channel(self, data, pos, end, delta, status):
        command = status & 0xF0
        if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            if pos + 1 < end:
                b1 = max(0, min(127, data[pos]))
                b2 = max(0, min(127, data[pos+1]))
                pos += 2
                self.events.append((delta, status, b1, b2))
        elif command in (0xC0, 0xD0):
            if pos < end:
                b1 = max(0, min(127, data[pos]))
                pos += 1
                self.events.append((delta, status, b1, 0))
        return pos

def play_track(filepath, max_duration=5.0):
    print(f"Loading: {filepath}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    parser = XMidiParser()
    events = parser.parse(data)
    
    if not events:
        print("  No events found")
        return False
    
    note_events = [(d, s, b1, b2) for d, s, b1, b2 in events 
                  if (s & 0xF0) in (0x80, 0x90)]
    
    if not note_events:
        print("  No note events")
        return False
    
    print(f"  Found {len(note_events)} notes, synthesizing...")
    
    synth = SimpleSynth()
    tempo = 500000
    ticks_per_sec = 60000000.0 / tempo
    
    total_samples = int(synth.sample_rate * max_duration)
    audio = [0] * total_samples
    
    current_time = 0.0
    
    for delta, status, note, velocity in note_events:
        current_time += delta / ticks_per_sec
        
        if current_time > max_duration:
            break
        
        command = status & 0xF0
        
        if command == 0x90 and velocity > 0:
            freq = synth.note_to_freq(note)
            samples = synth.generate_note(freq, 0.2, velocity)
            
            start = int(current_time * synth.sample_rate)
            
            for i in range(len(samples)):
                idx = start + i
                if idx < total_samples:
                    audio[idx] += samples[i]
        
        elif command == 0x51:
            if note > 0:
                tempo = note
                ticks_per_sec = 60000000.0 / tempo
    
    max_val = max(abs(v) for v in audio) if audio else 1
    if max_val > 0:
        audio = [int(v * 32767 / max_val * 0.8) for v in audio]
    
    wav_path = os.path.join(tempfile.gettempdir(), "fd2_track.wav")
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(synth.sample_rate)
        
        for sample in audio:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"  WAV saved: {wav_path}")
    print(f"  Playing... (will auto-stop in 5 seconds)")
    
    os.startfile(wav_path)
    time.sleep(5)
    
    return True

def main():
    track_dir = Path("output/fdmus_tracks")
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print("="*60)
    print("FD2 Audio Player - 自动测试")
    print("="*60)
    
    # 自动播放前3个有效音轨
    for idx in [0, 2, 5]:
        if idx < len(tracks):
            print(f"\n{'='*60}")
            print(f"Now playing: {tracks[idx].name}")
            if play_track(tracks[idx]):
                print("  Done!")
            else:
                print("  Failed")

if __name__ == "__main__":
    main()
