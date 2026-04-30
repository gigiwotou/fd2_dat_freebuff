#!/usr/bin/env python3
"""
深度分析XMIDI原始数据 - 找出所有事件类型和时序问题
"""

import struct
from pathlib import Path

def deep_analyze(filepath):
    print(f"\n{'='*70}")
    print(f"File: {filepath.name} ({filepath.stat().st_size} bytes)")
    print(f"{'='*70}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        print("  No EVNT")
        return
    
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    print(f"EVNT: pos={evnt_pos:#x}, size={chunk_size}")
    
    # 统计所有事件类型
    event_types = {}
    note_on_count = 0
    note_off_count = 0
    meta_count = 0
    cc_count = 0
    prog_count = 0
    tempo_events = []
    total_delta = 0
    first_note_delta = None
    
    # 解析所有事件
    events_list = []
    running_status = None
    event_num = 0
    
    pos_temp = pos
    while pos_temp < end and event_num < 200:
        # 解析delta
        delta_start = pos_temp
        delta = 0
        delta_bytes = 0
        while pos_temp < end:
            byte = data[pos_temp]
            delta_bytes += 1
            pos_temp += 1
            delta = (delta << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        
        if pos_temp >= end:
            break
        
        total_delta += delta
        
        status = data[pos_temp]
        pos_temp += 1
        
        if status == 0xFF:
            meta_type = data[pos_temp]
            pos_temp += 1
            length = 0
            while pos_temp < end:
                byte = data[pos_temp]
                pos_temp += 1
                length = (length << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            data_bytes = data[pos_temp:pos_temp+length]
            pos_temp += length
            
            if meta_type == 0x2F:
                events_list.append((event_num, delta, 'end_of_track'))
                break
            elif meta_type == 0x51 and length == 3:
                tempo = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                tempo_events.append((event_num, delta, tempo))
                events_list.append((event_num, delta, f'tempo={tempo}'))
            else:
                events_list.append((event_num, delta, f'meta_0x{meta_type:02X}'))
            meta_count += 1
            event_num += 1
            
        elif status >= 0x80:
            running_status = status
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos_temp + 1 < end:
                    b1 = data[pos_temp]
                    b2 = data[pos_temp+1]
                    pos_temp += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            if first_note_delta is None:
                                first_note_delta = total_delta
                            note_on_count += 1
                            events_list.append((event_num, delta, f'note_on ch={channel} n={b1} v={b2}'))
                        else:
                            note_off_count += 1
                            events_list.append((event_num, delta, f'note_off ch={channel} n={b1}'))
                    elif command == 0xB0:
                        cc_count += 1
                        events_list.append((event_num, delta, f'CC ch={channel} ctrl={b1} val={b2}'))
                    elif command == 0xE0:
                        events_list.append((event_num, delta, f'pitch ch={channel}'))
                    else:
                        events_list.append((event_num, delta, f'cmd_0x{command:02X}'))
            elif command in (0xC0, 0xD0):
                if pos_temp < end:
                    b1 = data[pos_temp]
                    pos_temp += 1
                    if command == 0xC0:
                        prog_count += 1
                        events_list.append((event_num, delta, f'prog ch={channel} p={b1}'))
                    else:
                        events_list.append((event_num, delta, f'aftertouch'))
            event_num += 1
            
        else:
            # Running status
            if running_status:
                command = running_status & 0xF0
                channel = running_status & 0xF
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    if pos_temp + 1 < end:
                        b1 = data[pos_temp]
                        b2 = data[pos_temp+1]
                        pos_temp += 2
                        
                        if command == 0x90:
                            if b2 > 0:
                                if first_note_delta is None:
                                    first_note_delta = total_delta
                                note_on_count += 1
                                events_list.append((event_num, delta, f'note_on(RS) ch={channel} n={b1} v={b2}'))
                            else:
                                note_off_count += 1
                                events_list.append((event_num, delta, f'note_off(RS) ch={channel} n={b1}'))
                        elif command == 0xB0:
                            cc_count += 1
                            events_list.append((event_num, delta, f'CC(RS) ch={channel} ctrl={b1} val={b2}'))
                        else:
                            events_list.append((event_num, delta, f'cmd_0x{command:02X}(RS)'))
                elif command in (0xC0, 0xD0):
                    if pos_temp < end:
                        b1 = data[pos_temp]
                        pos_temp += 1
                        if command == 0xC0:
                            prog_count += 1
                            events_list.append((event_num, delta, f'prog(RS) ch={channel} p={b1}'))
                        else:
                            events_list.append((event_num, delta, f'aftertouch(RS)'))
                event_num += 1
            else:
                print(f"  ERROR: byte 0x{status:02X} without running status at pos {pos_temp-1:#x}")
                break
    
    # 输出统计
    print(f"\n事件统计:")
    print(f"  Note On:  {note_on_count}")
    print(f"  Note Off: {note_off_count}")
    print(f"  CC:       {cc_count}")
    print(f"  Program:  {prog_count}")
    print(f"  Meta:     {meta_count}")
    
    if tempo_events:
        print(f"\nTempo事件:")
        for num, delta, tempo in tempo_events:
            bpm = 60000000 / tempo if tempo > 0 else 0
            print(f"  [#{num}] delta={delta:<8} raw_tempo={tempo} tempo/16={tempo//16} BPM={60000000/(tempo//16):.0f}")
    
    print(f"\n总delta: {total_delta}")
    if first_note_delta is not None:
        print(f"第一个音符delta: {first_note_delta}")
    
    # 显示前30个事件
    print(f"\n前30个事件:")
    for num, delta, desc in events_list[:30]:
        print(f"  [#{num:<3}] d={delta:<8} {desc}")

def main():
    track_dir = Path("output/fdmus_tracks")
    
    # 分析用户说能播放的track 11
    for idx in [0, 2, 5, 11]:
        track_file = track_dir / f"track_{idx:03d}.bin"
        if track_file.exists():
            deep_analyze(track_file)

if __name__ == "__main__":
    main()
