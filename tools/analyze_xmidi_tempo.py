#!/usr/bin/env python3
"""
分析XMIDI中的tempo值和时序信息
"""

import struct
from pathlib import Path

def analyze_xmidi_tempo(filepath):
    print(f"\n{'='*60}")
    print(f"File: {filepath.name}")
    print(f"{'='*60}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        print("  No EVNT found")
        return
    
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    print(f"EVNT size: {chunk_size} bytes")
    
    # 解析所有事件
    events = []
    tempo_events = []
    
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
            
            if meta_type == 0x51 and length == 3:
                tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                bpm = 60000000 / tempo if tempo > 0 else 0
                tempo_events.append((delta, tempo, bpm))
            elif meta_type == 0x58 and length == 4:
                events.append((delta, 'time_sig', data_bytes))
            elif meta_type == 0x2F:
                events.append((delta, 'end_of_track'))
                break
        elif status >= 0x80:
            command = status & 0xF0
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 < end:
                    b1 = data[pos]
                    b2 = data[pos+1]
                    pos += 2
                    if command == 0x90 and b2 > 0:
                        events.append((delta, 'note_on', b1, b2))
            elif command in (0xC0, 0xD0):
                if pos < end:
                    b1 = data[pos]
                    pos += 1
    
    # 输出tempo信息
    if tempo_events:
        print(f"\nTempo events: {len(tempo_events)}")
        for i, (delta, tempo, bpm) in enumerate(tempo_events[:5]):
            print(f"  [{i}] Delta={delta:<8} Tempo={tempo} BPM={bpm:.1f}")
    else:
        print(f"\nNo tempo events found (using default)")
    
    # 计算总时长
    total_delta = sum(e[0] for e in events if e[0] is not None)
    print(f"\nTotal delta ticks: {total_delta}")
    
    # 假设ticks_per_beat
    for ticks_per_beat in [120, 240, 480, 960]:
        tempo = 500000  # 120 BPM default
        seconds = (total_delta / ticks_per_beat) * (tempo / 1000000)
        print(f"  ticks_per_beat={ticks_per_beat}: {seconds:.1f}s ({seconds/60:.1f}min)")
    
    # 统计音符
    note_events = [e for e in events if e[1] == 'note_on']
    print(f"\nNote On events: {len(note_events)}")
    
    # 显示前5个音符的delta
    for i, (delta, *args) in enumerate(note_events[:5]):
        print(f"  [{i}] Delta={delta:<8} Note={args[0]} Vel={args[1]}")

def main():
    track_dir = Path("output/fdmus_tracks")
    
    # 分析用户提到的track 11和其它几个
    for idx in [0, 2, 5, 11]:
        track_file = track_dir / f"track_{idx:03d}.bin"
        if track_file.exists():
            analyze_xmidi_tempo(track_file)

if __name__ == "__main__":
    main()
