import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f'DATO.DAT: {count} resources, file size: {len(data)}')

# Analyze resources 0, 10, 100 to find common structure
for idx in [0, 1, 2, 10, 100]:
    if idx >= count - 1:
        continue
    off = struct.unpack('<I', data[10+idx*4:14+idx*4])[0]
    end = struct.unpack('<I', data[10+(idx+1)*4:14+(idx+1)*4])[0]
    size = end - off
    
    print(f'\n=== Resource {idx} at {hex(off)}, size={size} ===')
    
    # First 4 bytes
    dword0 = struct.unpack('<I', data[off:off+4])[0]
    # Check if first 4 bytes could be 2 WORDs
    word0 = struct.unpack('<H', data[off:off+2])[0]
    word2 = struct.unpack('<H', data[off+2:off+4])[0]
    
    print(f'  Bytes 0-3: {data[off:off+4].hex()} = DWORD:{dword0}, WORD0:{word0}, WORD2:{word2}')
    
    # Check bytes 4-7
    dword4 = struct.unpack('<I', data[off+4:off+8])[0]
    word4 = struct.unpack('<H', data[off+4:off+6])[0]
    word6 = struct.unpack('<H', data[off+6:off+8])[0]
    print(f'  Bytes 4-7: {data[off+4:off+8].hex()} = DWORD:{dword4}, WORD4:{word4}, WORD6:{word6}')
    
    # Check bytes 8-11
    dword8 = struct.unpack('<I', data[off+8:off+12])[0]
    word8 = struct.unpack('<H', data[off+8:off+10])[0]
    word10 = struct.unpack('<H', data[off+10:off+12])[0]
    print(f'  Bytes 8-11: {data[off+8:off+12].hex()} = DWORD:{dword8}, WORD8:{word8}, WORD10:{word10}')
    
    # Check bytes 12-15
    dword12 = struct.unpack('<I', data[off+12:off+16])[0]
    word12 = struct.unpack('<H', data[off+12:off+14])[0]
    word14 = struct.unpack('<H', data[off+14:off+16])[0]
    print(f'  Bytes 12-15: {data[off+12:off+16].hex()} = DWORD:{dword12}, WORD12:{word12}, WORD14:{word14}')
    
    # Check bytes 16-19
    dword16 = struct.unpack('<I', data[off+16:off+20])[0]
    word16 = struct.unpack('<H', data[off+16:off+18])[0]
    word18 = struct.unpack('<H', data[off+18:off+20])[0]
    print(f'  Bytes 16-19: {data[off+16:off+20].hex()} = DWORD:{dword16}, WORD16:{word16}, WORD18:{word18}')
    
    # If dword0=16, maybe there are 16 4-byte entries in a table?
    if dword0 == 16:
        print(f'  Table of 16 4-byte entries at byte 4:')
        for i in range(min(16, (size-4)//4)):
            val = struct.unpack('<I', data[off+4+i*4:off+8+i*4])[0]
            print(f'    [{i}] {val} (0x{val:08X})')
