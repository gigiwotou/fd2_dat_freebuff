#!/usr/bin/env python3
"""
FD2 Audio Player - 纯Python标准库版
生成WAV文件并使用系统默认播放器播放
不依赖numpy/sounddevice等第三方库
"""

import struct
import wave
import math
import os
import tempfile
import subprocess
from pathlib import Path

class SimpleSynth:
    """简单MIDI合成器 - 纯Python"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def note_to_freq(self, note):
        """MIDI音符转频率 A4=69=440Hz"""
        return 440.0 * (2.0 ** ((note - 69) / 12.0))
    
    def generate_note(self, freq, duration_sec, velocity=64):
        """生成单个音符的PCM数据"""
        num_samples = int(self.sample_rate * duration_sec)
        if num_samples <= 0:
            return []
        
        volume = (velocity / 127.0) * 0.3
        
        # 使用多个正弦波模拟音色（基波+泛音）
        samples = []
        for i in range(num_samples):
            t = i / self.sample_rate
            # 基波
            val = 0.5 * math.sin(2 * math.pi * freq * t)
            # 二次泛音
            val += 0.3 * math.sin(4 * math.pi * freq * t)
            # 三次泛音
            val += 0.2 * math.sin(6 * math.pi * freq * t)
            val *= volume
            # 限制范围
            val = max(-1.0, min(1.0, val))
            # 转换为16位整数
            samples.append(int(val * 32767))
        
        return samples

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

class FD2Player:
    """FD2音频播放器"""
    
    def __init__(self):
        self.parser = XMidiParser()
        self.synth = SimpleSynth()
        
    def convert_and_play(self, filepath, max_duration=5.0):
        """转换并播放XMIDI文件"""
        print(f"\n{'='*60}")
        print(f"Loading: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        events = self.parser.parse(data)
        if not events:
            print("  No events found")
            return False
        
        note_events = [(d, s, b1, b2) for d, s, b1, b2 in events 
                      if (s & 0xF0) in (0x80, 0x90)]
        
        if not note_events:
            print("  No note events")
            return False
        
        print(f"  Found {len(note_events)} notes, synthesizing...")
        
        wav_path = self._synthesize_to_wav(note_events, max_duration)
        if not wav_path:
            return False
        
        print(f"  Playing WAV: {wav_path}")
        self._play_wav(wav_path)
        
        return True
    
    def _synthesize_to_wav(self, events, max_duration):
        """将音符事件合成为WAV文件"""
        tempo = 500000  # 120 BPM
        ticks_per_sec = 60000000.0 / tempo
        
        total_samples = int(self.synth.sample_rate * max_duration)
        audio = [0] * total_samples
        
        current_time = 0.0
        
        for delta, status, note, velocity in events:
            current_time += delta / ticks_per_sec
            
            if current_time > max_duration:
                break
            
            command = status & 0xF0
            
            if command == 0x90 and velocity > 0:
                freq = self.synth.note_to_freq(note)
                samples = self.synth.generate_note(freq, 0.2, velocity)
                
                start = int(current_time * self.synth.sample_rate)
                
                for i in range(len(samples)):
                    idx = start + i
                    if idx < total_samples:
                        audio[idx] += samples[i]
            
            elif command == 0x51:
                if note > 0:
                    tempo = note
                    ticks_per_sec = 60000000.0 / tempo
        
        # 归一化
        max_val = max(abs(v) for v in audio) if audio else 1
        if max_val > 0:
            audio = [int(v * 32767 / max_val * 0.8) for v in audio]
        
        # 写入WAV文件
        wav_path = os.path.join(tempfile.gettempdir(), "fd2_track.wav")
        with wave.open(wav_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.synth.sample_rate)
            
            for sample in audio:
                wav_file.writeframes(struct.pack('<h', sample))
        
        return wav_path
    
    def _play_wav(self, wav_path):
        """播放WAV文件"""
        try:
            # Windows - 使用默认播放器
            os.startfile(wav_path)
            print("  Playing... (press Ctrl+C to stop)")
            import time
            time.sleep(5)
        except Exception as e:
            print(f"  Playback error: {e}")

def main():
    track_dir = Path("output/fdmus_tracks")
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print("="*60)
    print("FD2 Audio Player - 纯Python标准库版")
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
                    player.convert_and_play(tracks[idx])
                else:
                    print("无效编号")
        except KeyboardInterrupt:
            print("\n已停止")
            continue
        except EOFError:
            break

if __name__ == "__main__":
    main()
