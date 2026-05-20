import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

# Check first 100 resources to understand structure
print(f'Total file size: {len(data)}')
print(f'Resource count from header: {struct.unpack("<I", data[6:10])[0]}')

# Check first resource raw bytes
off0 = struct.unpack('<I', data[10:14])[0]
off1 = struct.unpack('<I', data[14:18])[0]
print(f'\nResource 0: offset={off0}, end={off1}, size={off1-off0}')
print(f'First 32 bytes: {data[off0:off0+32].hex()}')

# Check if there's a sub-structure like FDTXT
sub_count = struct.unpack('<H', data[off0:off0+2])[0]
print(f'Possible sub-count (first 2 bytes): {sub_count}')

# Check what value is at byte 6-9 (could be count)
val = struct.unpack('<I', data[6:10])[0]
print(f'Header bytes 6-9 as uint32: {val}')

# Check different interpretation: maybe first 2 bytes are something else
# Let's check resource sizes
print(f'\nResource sizes (first 50):')
for i in range(min(50, val-1)):
    off_start = struct.unpack('<I', data[10+i*4:14+i*4])[0]
    off_end = struct.unpack('<I', data[10+(i+1)*4:14+(i+1)*4])[0]
    
    if off_start >= len(data) or off_end > len(data) or off_start >= off_end:
        print(f'  [{i}] invalid (start={off_start}, end={off_end})')
        continue
    
    res_size = off_end - off_start
    # Check first few bytes
    first_bytes = data[off_start:off_start+4].hex()
    print(f'  [{i}] size={res_size}, first4={first_bytes}')
