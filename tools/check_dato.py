import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

# Parse header
magic = data[0:6]
count = struct.unpack('<I', data[6:10])[0]
print(f'Magic: {magic}')
print(f'Resource count: {count}')

# Check first few resources for dimensions (first 4 bytes = width, height)
print(f'\nFirst 20 resources:')
for i in range(min(20, count-1)):
    off_start = struct.unpack('<I', data[10+i*4:14+i*4])[0]
    off_end = struct.unpack('<I', data[10+(i+1)*4:14+(i+1)*4])[0]
    
    if off_start >= len(data) or off_end > len(data):
        print(f'  [{i}] invalid offset')
        continue
    
    res_size = off_end - off_start
    if res_size < 4:
        print(f'  [{i}] too small ({res_size} bytes)')
        continue
    
    # Check dimensions (little-endian WORDs)
    w = struct.unpack('<H', data[off_start:off_start+2])[0]
    h = struct.unpack('<H', data[off_start+2:off_start+4])[0]
    
    print(f'  [{i}] offset={off_start}, size={res_size}, w={w}, h={h}')
