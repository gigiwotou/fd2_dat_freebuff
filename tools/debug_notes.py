#!/usr/bin/env python3
"""
Debug note parsing for track 11
"""

import struct
from pathlib import Path

def debug_track_11_notes():
    fdmus_path = Path('game/FDMUS.DAT')
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    for track_idx in [10, 11, 12]:
        start = offsets[track_idx]
        end = offsets[track_idx+1] if track_idx+1 < count else len(data)
        track_data = data[start:end]
        
        evnt_pos = track_data.find(b'EVNT')
        if evnt_pos < 0:
            continue
        
        chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
        evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
        
        print(f"\n{'='*70}")
        print(f"Track {track_idx}: {len(evnt_data)} bytes EVNT data")
        print(f"{'='*70}")
        
        # Parse events and print note info
        pos = 0
        end = len(evnt_data)
        running_status = None
        current_tick = 0
        note_count = 0
        tempo = 500000
        
        while pos < end and note_count < 30:
            delta = 0
            first_byte = evnt_data[pos]
            
            if first_byte < 0x80:
                delta = first_byte
                pos += 1
                if pos >= end:
                    break
                status = evnt_data[pos]
                pos += 1
            else:
                status = first_byte
                pos += 1
            
            current_tick += delta
            
            if status == 0xFF:
                if pos >= end:
                    break
                
                meta_type = evnt_data[pos]
                pos += 1
                
                length = 0
                count = 0
                while pos < end and count < 4:
                    byte = evnt_data[pos]
                    pos += 1
                    count += 1
                    length = (length << 7) | (byte & 0x7F)
                    if not (byte & 0x80):
                        break
                
                if meta_type == 0x2F:
                    print(f"  [Tick {current_tick}] End of Track")
                    break
                elif meta_type == 0x51 and length == 3:
                    if pos + 3 <= end:
                        t0, t1, t2 = evnt_data[pos:pos+3]
                        tempo = (t0 << 16) | (t1 << 8) | t2
                        pos += 3
                        bpm = 60000000 / tempo
                        print(f"  [Tick {current_tick}] Tempo: {tempo} ({bpm:.1f} BPM)")
                else:
                    if pos + length <= end:
                        pos += length
                        
            elif status == 0xF0 or status == 0xF7:
                length = 0
                count = 0
                while pos < end and count < 4:
                    byte = evnt_data[pos]
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
                        b1 = evnt_data[pos]
                        b2 = evnt_data[pos + 1]
                        pos += 2
                        
                        if command == 0x90:
                            if b2 > 0:
                                duration = 0
                                count = 0
                                while pos < end and count < 4:
                                    byte = evnt_data[pos]
                                    pos += 1
                                    count += 1
                                    duration = (duration << 7) | (byte & 0x7F)
                                    if not (byte & 0x80):
                                        break
                                
                                note_count += 1
                                seconds = current_tick * (tempo / 1000000.0 / 480)
                                dur_seconds = duration * (tempo / 1000000.0 / 480)
                                print(f"  [Tick {current_tick}] NoteOn: note={b1} vel={b2} dur={duration} ({seconds:.2f}s, dur={dur_seconds:.2f}s)")
                            else:
                                print(f"  [Tick {current_tick}] NoteOff: note={b1}")
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
        
        print(f"\n  Total: {note_count} notes parsed")

if __name__ == '__main__':
    debug_track_11_notes()
