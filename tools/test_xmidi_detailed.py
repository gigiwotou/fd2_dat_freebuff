#!/usr/bin/env python3
"""
Detailed XMIDI analysis based on IDA findings
"""

import struct
from pathlib import Path

def parse_vlq(data, pos, end, max_bytes=4):
    """Parse VLQ (IDA sub_424B0)"""
    value = 0
    count = 0
    
    while pos < end and count < max_bytes:
        byte = data[pos]
        pos += 1
        count += 1
        value = (value << 7) | (byte & 0x7F)
        
        if not (byte & 0x80):
            break
    
    return value, pos

def analyze_track(track_data, track_num):
    """Analyze a single track in detail"""
    print(f"\n{'='*70}")
    print(f"Track {track_num} ({len(track_data)} bytes)")
    print(f"{'='*70}")
    
    # Print first 100 bytes as hex dump
    print(f"\nFirst 100 bytes:")
    for i in range(0, min(100, len(track_data)), 16):
        chunk = track_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Find EVNT
    evnt_pos = track_data.find(b'EVNT')
    if evnt_pos < 0:
        print("  No EVNT found")
        return
    
    evnt_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
    print(f"\nEVNT: pos={evnt_pos:#x}, size={evnt_size}")
    
    data_start = evnt_pos + 8
    data_end = data_start + evnt_size
    
    # Parse events
    pos = data_start
    running_status = None
    event_num = 0
    
    print(f"\nEvents:")
    print(f"  {'#':>4} {'Delta':>8} {'Type':<12} {'Details'}")
    print(f"  {'-'*4} {'-'*8} {'-'*12} {'-'*50}")
    
    while pos < data_end and event_num < 50:
        # Parse delta
        delta_start = pos
        delta, pos = parse_vlq(track_data, delta_start, data_end, max_bytes=4)
        
        if pos >= data_end:
            break
        
        status = track_data[pos]
        pos += 1
        
        if status == 0xFF:
            # Meta
            if pos >= data_end:
                break
            meta_type = track_data[pos]
            pos += 1
            
            # Length (VLQ)
            length, pos = parse_vlq(track_data, pos, data_end, max_bytes=4)
            
            if meta_type == 0x2F:
                print(f"  {event_num:>4} {delta:>8} {'EndOfTrack':<12}")
                break
            elif meta_type == 0x51:
                if pos + 3 <= data_end:
                    t0, t1, t2 = track_data[pos:pos+3]
                    tempo = (t0 << 16) | (t1 << 8) | t2
                    pos += 3
                    bpm = 60000000 / tempo if tempo > 0 else 0
                    print(f"  {event_num:>4} {delta:>8} {'Tempo':<12} raw={tempo}, {bpm:.1f} BPM, raw/16={tempo//16}")
            else:
                if pos + length <= data_end:
                    data_bytes = track_data[pos:pos+length]
                    pos += length
                    print(f"  {event_num:>4} {delta:>8} {'Meta':<12} type=0x{meta_type:02X}, len={length}")
                    
        elif status == 0xF0 or status == 0xF7:
            # SysEx
            length, pos = parse_vlq(track_data, pos, data_end, max_bytes=4)
            if pos + length <= data_end:
                pos += length
            print(f"  {event_num:>4} {delta:>8} {'SysEx':<12} len={length}")
            
        elif status >= 0x80:
            # New status
            running_status = status
            command = status & 0xF0
            channel = status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 2 <= data_end:
                    b1 = track_data[pos]
                    b2 = track_data[pos + 1]
                    pos += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Note On - check for duration after
                            duration, pos = parse_vlq(track_data, pos, data_end, max_bytes=4)
                            print(f"  {event_num:>4} {delta:>8} {'NoteOn':<12} ch={channel} n={b1} v={b2} dur={duration}")
                        else:
                            print(f"  {event_num:>4} {delta:>8} {'NoteOff':<12} ch={channel} n={b1}")
                    elif command == 0x80:
                        print(f"  {event_num:>4} {delta:>8} {'NoteOff':<12} ch={channel} n={b1}")
                    else:
                        print(f"  {event_num:>4} {delta:>8} {'MIDI':<12} 0x{status:02X} {b1} {b2}")
                        
            elif command in (0xC0, 0xD0):
                if pos <= data_end:
                    b1 = track_data[pos]
                    pos += 1
                    print(f"  {event_num:>4} {delta:>8} {'MIDI':<12} 0x{status:02X} {b1}")
                    
        else:
            # Running status
            if running_status is None:
                print(f"  {event_num:>4} {delta:>8} {'Invalid':<12} no running status")
                continue
                
            command = running_status & 0xF0
            channel = running_status & 0xF
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                b1 = status
                if pos < data_end:
                    b2 = track_data[pos]
                    pos += 1
                    
                    if command == 0x90:
                        if b2 > 0:
                            duration, pos = parse_vlq(track_data, pos, data_end, max_bytes=4)
                            print(f"  {event_num:>4} {delta:>8} {'NoteOn(R)':<12} ch={channel} n={b1} v={b2} dur={duration}")
                        else:
                            print(f"  {event_num:>4} {delta:>8} {'NoteOff(R)':<12} ch={channel} n={b1}")
                    else:
                        print(f"  {event_num:>4} {delta:>8} {'MIDI(R)':<12} 0x{running_status:02X} {b1} {b2}")
                        
            elif command in (0xC0, 0xD0):
                print(f"  {event_num:>4} {delta:>8} {'MIDI(R)':<12} 0x{running_status:02X} {status}")
        
        event_num += 1

def main():
    fdmus_path = Path('game/FDMUS.DAT')
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    # Parse header
    count = struct.unpack('<I', data[6:10])[0]
    
    # Parse offsets
    offsets = []
    for i in range(count):
        offset = struct.unpack('<I', data[10 + i*4:14 + i*4])[0]
        offsets.append(offset)
    
    # Analyze tracks 10, 11, 12 (user mentioned track 11 works)
    for i in [10, 11, 12]:
        if i >= count:
            break
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        track_data = data[start:end]
        
        analyze_track(track_data, i)

if __name__ == '__main__':
    main()
