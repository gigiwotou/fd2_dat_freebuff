#!/usr/bin/env python3
"""
Debug XMIDI parsing with correct delta time understanding from IDA
"""

import struct
from pathlib import Path

def debug_track_11():
    fdmus_path = Path('game/FDMUS.DAT')
    with open(fdmus_path, 'rb') as f:
        data = f.read()
    
    count = struct.unpack('<I', data[6:10])[0]
    offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]
    
    start = offsets[11]
    end = offsets[12] if 12 < count else len(data)
    track = data[start:end]
    
    evnt_pos = track.find(b'EVNT')
    evnt_size = struct.unpack('>I', track[evnt_pos+4:evnt_pos+8])[0]
    data_start = evnt_pos + 8
    
    print(f"Track 11: {len(track)} bytes")
    print(f"EVNT at {evnt_pos:#x}, size={evnt_size}")
    print()
    print("Raw EVNT data (first 80 bytes):")
    for i in range(0, 80, 16):
        chunk = track[data_start+i:data_start+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  +{i:03X}: {hex_str:<48} {ascii_str}")
    print()
    
    # Parse with single-byte delta
    print("Parsing with single-byte delta:")
    pos = data_start
    evt_num = 0
    running_status = None
    
    while pos < data_start + evnt_size and evt_num < 20:
        # Check if this is a delta byte (<0x80) or status (>=0x80)
        byte = track[pos]
        
        if byte < 0x80:
            # This is delta time
            delta = byte
            pos += 1
            print(f"Event {evt_num}: delta={delta}")
        else:
            # No delta byte (delta=0), this is status
            delta = 0
            print(f"Event {evt_num}: delta=0 (implicit)")
        
        if pos >= data_start + evnt_size:
            break
        
        status = track[pos]
        pos += 1
        
        if status == 0xFF:
            # Meta
            if pos >= data_start + evnt_size:
                break
            meta_type = track[pos]
            pos += 1
            
            # Length is VLQ
            length = 0
            count = 0
            while pos < data_start + evnt_size and count < 4:
                b = track[pos]
                pos += 1
                count += 1
                length = (length << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            
            if meta_type == 0x2F:
                print(f"  Meta 0x2F: End of Track")
                break
            elif meta_type == 0x51:
                if pos + 3 <= data_start + evnt_size:
                    tempo = (track[pos] << 16) | (track[pos+1] << 8) | track[pos+2]
                    pos += 3
                    print(f"  Meta 0x51: Tempo={tempo} ({60000000/tempo:.1f} BPM)")
            else:
                if pos + length <= data_start + evnt_size:
                    meta_data = track[pos:pos+length]
                    pos += length
                    print(f"  Meta 0x{meta_type:02X}: len={length}, data={' '.join(f'{b:02X}' for b in meta_data)}")
                    
        elif status >= 0x80:
            # New status
            running_status = status
            command = status & 0xF0
            
            if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                if pos + 2 <= data_start + evnt_size:
                    b1 = track[pos]
                    b2 = track[pos+1]
                    pos += 2
                    
                    if command == 0x90:
                        if b2 > 0:
                            # Duration is VLQ
                            duration = 0
                            count = 0
                            while pos < data_start + evnt_size and count < 4:
                                b = track[pos]
                                pos += 1
                                count += 1
                                duration = (duration << 7) | (b & 0x7F)
                                if not (b & 0x80):
                                    break
                            print(f"  NoteOn ch={status&0xF} n={b1} v={b2} dur={duration}")
                        else:
                            print(f"  NoteOff ch={status&0xF} n={b1}")
                    elif command == 0x80:
                        print(f"  NoteOff ch={status&0xF} n={b1}")
                    else:
                        print(f"  MIDI 0x{status:02X} {b1} {b2}")
            elif command in (0xC0, 0xD0):
                if pos <= data_start + evnt_size:
                    b1 = track[pos]
                    pos += 1
                    print(f"  MIDI 0x{status:02X} {b1}")
        else:
            # Running status
            if running_status:
                command = running_status & 0xF0
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    b1 = status
                    if pos < data_start + evnt_size:
                        b2 = track[pos]
                        pos += 1
                        
                        if command == 0x90:
                            if b2 > 0:
                                duration = 0
                                count = 0
                                while pos < data_start + evnt_size and count < 4:
                                    b = track[pos]
                                    pos += 1
                                    count += 1
                                    duration = (duration << 7) | (b & 0x7F)
                                    if not (b & 0x80):
                                        break
                                print(f"  NoteOn(R) ch={running_status&0xF} n={b1} v={b2} dur={duration}")
                            else:
                                print(f"  NoteOff(R) ch={running_status&0xF} n={b1}")
                        else:
                            print(f"  MIDI(R) 0x{running_status:02X} {b1} {b2}")
                elif command in (0xC0, 0xD0):
                    print(f"  MIDI(R) 0x{running_status:02X} {status}")
        
        evt_num += 1

if __name__ == '__main__':
    debug_track_11()
