#!/usr/bin/env python3
"""
FD2 Audio Player - 使用真实音频合成
将XMIDI转换为WAV音频文件进行播放
"""

import struct
import numpy as np
import wave
import sounddevice as sd
from pathlib import Path
import time

class SimpleSynth:
    """简单的MIDI合成器"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def note_to_freq(self, note):
        """MIDI音符转频率"""
        return 440.0 * (2.0 ** ((note - 69) / 12.0))
    
    def generate_tone(self, freq, duration, velocity=64):
        """生成单音"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        volume = velocity / 127.0
        # 使用方波模拟复古音色
        wave = 0.3 * np.sin(2 * np.pi * freq * t)
        wave += 0.2 * np.sin(4 * np.pi * freq * t)
        wave += 0.1 * np.sin(6 * np.pi * freq * t)
        wave *= volume * 0.3
        # 添加淡入淡出
        attack = min(0.01, duration * 0.1)
        decay = min(0.02, duration * 0.2)
        if duration > attack + decay:
            fade_in = np.linspace(0, 1, int(self.sample_rate * attack))
            fade_out = np.linspace(1, 0, int(self.sample_rate * decay))
            wave[:len(fade_in)] *= fade_in
            wave[-len(fade_out):] *= fade_out
        return wave

class XMidiParser:
    """XMIDI解析器"""
    
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
        pos += length
        if meta_type == 0x2F:
            self.events.append((delta, 0xFF, 0x2F, 0))
        elif meta_type == 0x51 and length == 3:
            tempo = (data[pos-length] << 16) | (data[pos-length+1] << 8) | data[pos-length+2]
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

class FD2Player:
    """FD2音频播放器"""
    
    def __init__(self):
        self.parser = XMidiParser()
        self.synth = SimpleSynth()
        self.active_notes = {}
        
    def play_track(self, filepath, max_duration=5.0):
        """播放XMIDI音轨"""
        print(f"Loading: {filepath}")
        with open(filepath, 'rb') as f:
            data = f.read()
        
        events = self.parser.parse(data)
        if not events:
            print("  No events found")
            return False
        
        # 过滤出音符事件
        note_events = [(d, s, b1, b2) for d, s, b1, b2 in events 
                      if (s & 0xF0) in (0x80, 0x90)]
        
        if not note_events:
            print("  No note events found")
            return False
        
        print(f"  Found {len(note_events)} note events")
        
        # 合成音频
        print("  Synthesizing audio...")
        audio = self._synthesize(note_events, max_duration)
        
        if len(audio) == 0:
            print("  No audio generated")
            return False
        
        # 播放
        print(f"  Playing {len(audio)/self.synth.sample_rate:.1f}s of audio...")
        sd.play(audio, self.synth.sample_rate)
        sd.wait()
        print("  Done!")
        return True
    
    def _synthesize(self, events, max_duration):
        """将音符事件合成为音频"""
        total_samples = int(self.synth.sample_rate * max_duration)
        audio = np.zeros(total_samples, dtype=np.float32)
        
        tempo = 500000  # 默认120 BPM
        ticks_per_sec = 60000000 / tempo
        
        current_time = 0.0
        
        for delta, status, note, velocity in events:
            # 转换delta时间为秒
            current_time += delta / ticks_per_sec
            
            if current_time > max_duration:
                break
            
            command = status & 0xF0
            
            if command == 0x90 and velocity > 0:
                # Note On
                freq = self.synth.note_to_freq(note)
                tone = self.synth.generate_tone(freq, 0.3, velocity)
                
                # 混音
                start_sample = int(current_time * self.synth.sample_rate)
                end_sample = min(start_sample + len(tone), total_samples)
                if start_sample < total_samples:
                    audio[start_sample:end_sample] += tone[:end_sample-start_sample]
            
            elif command == 0x51:
                # Tempo change
                if note > 0:
                    tempo = note
                    ticks_per_sec = 60000000 / tempo
        
        # 归一化
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.8
        
        return audio

def main():
    track_dir = Path("output/fdmus_tracks")
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print("="*60)
    print("FD2 Audio Player - 真实合成版")
    print("="*60)
    
    player = FD2Player()
    
    # 显示可用音轨
    print(f"\n找到 {len(tracks)} 个音轨:")
    for i, t in enumerate(tracks[:20]):
        size = t.stat().st_size
        print(f"  [{i}] {t.name} ({size} bytes)")
    
    print("\n输入音轨编号播放，q退出:")
    
    while True:
        try:
            cmd = input("\n选择: ").strip()
            if cmd.lower() == 'q':
                break
            elif cmd.isdigit():
                idx = int(cmd)
                if 0 <= idx < len(tracks):
                    player.play_track(tracks[idx])
                else:
                    print("无效编号")
        except KeyboardInterrupt:
            print("\n已停止")
        except EOFError:
            break

if __name__ == "__main__":
    main()
