import struct
from pathlib import Path

def analyze_raw_bytes():
    dat_path = Path('d:/workspace/fd2_dat_freebuff/tools/output/FDMUS.DAT')
    data = dat_path.read_bytes()
    
    # FDMUS header: magic(4) + version(4) + music_count(4) + table_offset(4)
    mus_offset = 0x10
    music_count = struct.unpack('>I', data[mus_offset:mus_offset+4])[0]
    table_offset = struct.unpack('>I', data[mus_offset+4:mus_offset+8])[0]
    
    print(f"Music count: {music_count}")
    print(f"Table offset: {table_offset:#x}")
    
    # Analyze music 11 (which user says is close to correct)
    for idx in [10, 11, 12]:
        entry_offset = table_offset + idx * 8
        pos = struct.unpack('>I', data[entry_offset:entry_offset+4])[0]
        size = struct.unpack('>I', data[entry_offset+4:entry_offset+8])[0]
        
        print(f"\n{'='*70}")
        print(f"Music {idx}: pos={pos:#x}, size={size}")
        print(f"{'='*70}")
        
        evnt_pos = data.find(b'EVNT', pos, pos+size)
        if evnt_pos < 0:
            print("  No EVNT found")
            continue
            
        chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        print(f"EVNT at: {evnt_pos:#x}, size: {chunk_size}")
        
        pos_evnt = evnt_pos + 8
        
        # Print first 100 bytes
        print(f"\nFirst 100 bytes from EVNT:")
        for i in range(0, min(100, chunk_size), 16):
            chunk = data[pos_evnt+i:pos_evnt+i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"  {pos_evnt+i:04X}: {hex_str:<48} {ascii_str}")
        
        # Parse first 10 events manually
        print(f"\nParsing first 10 events:")
        p = pos_evnt
        end = pos_evnt + chunk_size
        running_status = None
        
        for evt_num in range(10):
            if p >= end:
                break
            
            # Parse delta time
            delta_start = p
            delta = 0
            delta_byte_count = 0
            delta_bytes = []
            
            while p < end and delta_byte_count < 10:
                byte = data[p]
                delta_bytes.append(byte)
                p += 1
                delta_byte_count += 1
                delta = (delta << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            
            print(f"\n  Event {evt_num}:")
            print(f"    Delta bytes: {' '.join(f'{b:02X}' for b in delta_bytes)} = {delta}")
            
            if p >= end:
                break
            
            # Status byte
            status = data[p]
            p += 1
            
            if status == 0xFF:
                # Meta event
                if p >= end:
                    break
                meta_type = data[p]
                p += 1
                print(f"    Meta type: 0x{meta_type:02X}")
                
                # Parse length (variable length in XMIDI)
                length = 0
                len_bytes = []
                while p < end:
                    byte = data[p]
                    len_bytes.append(byte)
                    p += 1
                    length = (length << 7) | byte
                    if not (byte & 0x80):
                        break
                print(f"    Length bytes: {' '.join(f'{b:02X}' for b in len_bytes)} = {length}")
                
                if length > 0:
                    meta_data = data[p:p+length]
                    p += length
                    print(f"    Data: {' '.join(f'{b:02X}' for b in meta_data)}")
                    
                    if meta_type == 0x51 and length == 3:
                        tempo_raw = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                        print(f"    Tempo raw: {tempo_raw}, standard: {tempo_raw // 16}")
                else:
                    print(f"    [End of Track]")
                    break
                    
            elif status >= 0x80:
                # New status byte
                running_status = status
                command = status & 0xF0
                channel = status & 0xF
                print(f"    Status: 0x{status:02X} (cmd=0x{command:02X}, ch={channel})")
                
                if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    if p + 1 < end:
                        b1 = data[p]
                        b2 = data[p+1]
                        p += 2
                        print(f"    Data: {b1}, {b2}")
                elif command in (0xC0, 0xD0):
                    if p < end:
                        b1 = data[p]
                        p += 1
                        print(f"    Data: {b1}")
            else:
                # Running status
                if running_status:
                    command = running_status & 0xF0
                    channel = running_status & 0xF
                    print(f"    Running status: 0x{running_status:02X} (cmd=0x{command:02X}, ch={channel})")
                    print(f"    Data byte: 0x{status:02X}")
                    
                    if command in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                        # Need second data byte
                        if p < end:
                            b2 = data[p]
                            p += 1
                            print(f"    Second data: {b2}")
                    # else: single data byte commands already have it

if __name__ == '__main__':
    analyze_raw_bytes()
