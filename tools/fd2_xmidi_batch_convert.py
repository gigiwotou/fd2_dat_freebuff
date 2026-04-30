#!/usr/bin/env python3
"""
FD2 XMIDI 批量转换器 - 转换为标准MIDI文件
将所有提取的XMIDI音轨转换为标准MIDI格式
"""

import struct
import mido
import io
from io import BytesIO
from pathlib import Path

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
            # 解析delta时间
            delta = 0
            while pos < end:
                byte = data[pos]
                if byte >= 0x80:
                    break
                pos += 1
                delta = (delta << 7) | byte
            
            if pos >= end:
                break
            
            # 解析状态字节
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
            tempo_raw = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
            # FD2将tempo值乘以16存储，需要除以16得到标准MIDI tempo
            # 从IDA sub_43270分析: *(_DWORD *)(dword_543E0 + 108) = 16 * dword_543F4;
            tempo = max(1, tempo_raw // 16)
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

def convert_xmidi_to_midi(xmidi_data):
    """将XMIDI数据转换为标准MIDI"""
    parser = XMidiParser()
    events = parser.parse(xmidi_data)
    
    if not events:
        return None
    
    mid = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    has_tempo = False
    for delta, status, byte1, byte2 in events:
        if status == 0xFF and byte1 == 0x51:
            track.append(mido.MetaMessage('set_tempo', tempo=byte2, time=max(0, delta)))
            has_tempo = True
            break
    
    if not has_tempo:
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    
    for delta, status, byte1, byte2 in events:
        if status == 0xFF:
            if byte1 == 0x2F:
                track.append(mido.MetaMessage('end_of_track', time=max(0, delta)))
                break
            elif byte1 in (0x51, 0x58, 0x59):
                continue
        else:
            command = status & 0xF0
            channel = status & 0xF
            
            if command == 0x90:
                if byte2 > 0:
                    track.append(mido.Message('note_on', note=byte1, velocity=byte2, 
                                            channel=channel, time=max(0, delta)))
                else:
                    track.append(mido.Message('note_off', note=byte1, velocity=0, 
                                            channel=channel, time=max(0, delta)))
            elif command == 0x80:
                track.append(mido.Message('note_off', note=byte1, velocity=byte2, 
                                        channel=channel, time=max(0, delta)))
            elif command == 0xB0:
                track.append(mido.Message('control_change', control=byte1, value=byte2, 
                                        channel=channel, time=max(0, delta)))
            elif command == 0xC0:
                track.append(mido.Message('program_change', program=byte1, 
                                        channel=channel, time=max(0, delta)))
            elif command == 0xE0:
                pitch = (byte2 << 7) | byte1
                track.append(mido.Message('pitchwheel', pitch=pitch - 8192, 
                                        channel=channel, time=max(0, delta)))
    
    if not any(isinstance(m, mido.MetaMessage) and m.type == 'end_of_track' for m in track):
        track.append(mido.MetaMessage('end_of_track', time=0))
    
    buf = BytesIO()
    mid.save(file=buf)
    return buf.getvalue()

def main():
    track_dir = Path("output/fdmus_tracks")
    output_dir = Path("output/fdmus_midi_standard")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tracks = sorted(track_dir.glob("track_*.bin"))
    
    print("="*60)
    print("FD2 XMIDI 批量转换为标准MIDI")
    print("="*60)
    print(f"\n找到 {len(tracks)} 个音轨")
    print(f"输出目录: {output_dir}\n")
    
    success_count = 0
    empty_count = 0
    
    for i, track in enumerate(tracks):
        print(f"[{i:3d}] {track.name}...", end=" ")
        
        with open(track, 'rb') as f:
            data = f.read()
        
        midi_data = convert_xmidi_to_midi(data)
        
        if midi_data:
            midi_path = output_dir / f"track_{i:03d}.mid"
            with open(midi_path, 'wb') as f:
                f.write(midi_data)
            print(f"OK ({len(midi_data)} bytes)")
            success_count += 1
        else:
            print("EMPTY")
            empty_count += 1
    
    print(f"\n{'='*60}")
    print(f"转换完成!")
    print(f"  成功: {success_count} 个")
    print(f"  空文件: {empty_count} 个")
    print(f"  输出目录: {output_dir}")
    print(f"\n可以使用专业MIDI播放器播放这些文件")

if __name__ == "__main__":
    main()
