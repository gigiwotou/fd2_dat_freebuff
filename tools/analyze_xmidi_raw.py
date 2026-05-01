#!/usr/bin/env python3
"""
Analyze raw XMIDI EVNT data to understand event structure
"""

import struct
from pathlib import Path

def read_variable_length_hex(data, pos):
    """Read variable-length value, return (value, hex_bytes, new_pos)"""
    value = 0
    hex_bytes = []
    count = 0
    while count < 4 and pos < len(data):
        byte = data[pos]
        hex_bytes.append(byte)
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        count += 1
        if not (byte & 0x80):
            break
    
    return value, hex_bytes, pos

def analyze_evnt_raw(track_idx, evnt_data, max_events=50):
    """Analyze raw EVNT bytes"""
    print(f"\n{'='*70}")
    print(f"Track {track_idx}: {len(evnt_data)} bytes EVNT")
    print(f"{'='*70}")
    
    pos = 0
    end = len(evnt_data)
    event_count = 0
    running_status = None
    abs_tick = 0
    
    while pos < end and event_count < max_events:
        delta_start = pos
        
        # Read delta
        delta, delta_bytes, pos = read_variable_length_hex(evnt_data, pos)
        abs_tick += delta
        
        # Show delta bytes early
        delta_hex = ' '.join(f'{b:02X}' for b in delta_bytes)
        
        if pos >= end:
            break
        
        # Read status
        byte = evnt_data[pos]
        pos += 1
        
        if byte >= 0x80:
            status = byte
            running_status = status
            status_str = f"Status=0x{status:02X}"
        else:
            if running_status is None:
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | ERROR: No running status, byte=0x{byte:02X}")
                event_count += 1
                continue
            status = running_status
            pos -= 1
            status_str = f"Running=0x{status:02X}"
        
        status_type = status & 0xF0
        channel = status & 0x0F
        
        if status == 0xFF:
            # Meta event
            meta_type = evnt_data[pos]
            pos += 1
            
            length, length_bytes, pos = read_variable_length_hex(evnt_data, pos)
            length_hex = ' '.join(f'{b:02X}' for b in length_bytes)
            
            meta_data = evnt_data[pos:pos+length]
            pos += length
            
            meta_data_hex = ' '.join(f'{b:02X}' for b in meta_data[:8])
            
            if meta_type == 0x2F:
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | FF 2F END OF TRACK")
                break
            elif meta_type == 0x51 and length == 3:
                tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
                bpm = 60000000 / tempo if tempo > 0 else 0
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] Len=[{length_hex}] | FF 51 TEMPO={tempo} ({bpm:.1f} BPM)")
            else:
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] Len=[{length_hex}] | FF {meta_type:02X} META data=[{meta_data_hex}]")
                
        elif status >= 0xF0:
            if status == 0xF0 or status == 0xF7:
                length, length_bytes, pos = read_variable_length_hex(evnt_data, pos)
                length_hex = ' '.join(f'{b:02X}' for b in length_bytes)
                sysex_data = evnt_data[pos:pos+length]
                pos += length
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] Len=[{length_hex}] | {status:02X} SYSEX ({length} bytes)")
            else:
                data1 = evnt_data[pos]
                pos += 1
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} {data1:02X}")
                running_status = None
        else:
            if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 1 > end:
                    break
                data1 = evnt_data[pos]
                pos += 1
                data2 = evnt_data[pos]
                pos += 1
                
                if status_type == 0x90:
                    # Note On - read duration
                    duration, dur_bytes, pos = read_variable_length_hex(evnt_data, pos)
                    dur_hex = ' '.join(f'{b:02X}' for b in dur_bytes)
                    dur_info = f" Dur=[{dur_hex}]={duration}"
                    print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} NoteOn  Note={data1:3d} Vel={data2:3d}{dur_info}")
                elif status_type == 0x80:
                    print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} NoteOff Note={data1:3d} Vel={data2:3d}")
                elif status_type == 0xB0:
                    print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} CC      Ctrl={data1:3d} Val={data2:3d}")
                elif status_type == 0xC0:
                    print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} Program Prog={data1:3d}")
                elif status_type == 0xE0:
                    print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} PBend   LSB={data1} MSB={data2}")
                else:
                    print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} data=[{data1:02X} {data2:02X}]")
                    
            elif status_type in (0xC0, 0xD0):
                if pos >= end:
                    break
                data1 = evnt_data[pos]
                pos += 1
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} data=[{data1:02X}]")
            else:
                print(f"  [{event_count:3d}] tick={abs_tick:6d} | Delta=[{delta_hex}] | {status:02X} UNKNOWN")
        
        event_count += 1

def main():
    fdmus_path = Path("game/FDMUS.DAT")
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    # Analyze tracks 0, 2, 3, 10, 11 (the ones that converted)
    for track_idx in [0, 2, 3, 10, 11]:
        if track_idx >= count:
            continue
        
        start = offsets[track_idx]
        end = offsets[track_idx+1] if track_idx+1 < count else len(data)
        track_data = data[start:end]
        
        evnt_pos = track_data.find(b'EVNT')
        if evnt_pos < 0:
            print(f"Track {track_idx}: No EVNT chunk")
            continue
        
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        analyze_evnt_raw(track_idx, evnt_data, max_events=40)

if __name__ == "__main__":
    main()
