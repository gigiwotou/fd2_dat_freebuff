"""检查资源7的有效偏移和子资源格式"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    data = f.read()

# C 加载逻辑
table_offset = 6
max_resources = 0
while table_offset + 4 <= len(data):
    res_offset = struct.unpack('<I', data[table_offset:table_offset+4])[0]
    if res_offset == 0 or res_offset > len(data):
        break
    max_resources += 1
    table_offset += 4

offsets = []
for i in range(max_resources):
    offsets.append(struct.unpack('<I', data[6 + i*4:10 + i*4])[0])
offsets.append(len(data))

# 资源7
start = offsets[7]
end = offsets[8]
size = end - start
print('Res 7: start=%d, end=%d, size=%d' % (start, end, size))

count = struct.unpack('<I', data[start+6:start+10])[0]
print('declared_count=%d' % count)

# 算出 C 端 valid_count
valid_count = 0
for j in range(count):
    if 10 + j*4 + 4 > size:
        break
    off = struct.unpack('<I', data[start+10+j*4:start+14+j*4])[0]
    if off < 10 + count*4 or off > size:
        break
    valid_count += 1

# C 端末尾减1 (如果是结束标记)
last_off = struct.unpack('<I', data[start+10+(valid_count-1)*4:start+14+(valid_count-1)*4])[0]
print('last_off (valid_count[%d-1]) = 0x%04x' % (valid_count, last_off))
print('  last_off == size? %s' % (last_off == size))
effective_count = valid_count - 1 if (last_off == size and valid_count > 1) else valid_count
print('  effective sub-resource count: %d' % effective_count)

print('---')
print('有效偏移 (前 %d 个):' % valid_count)
for j in range(valid_count):
    off = struct.unpack('<I', data[start+10+j*4:start+14+j*4])[0]
    print('  Off[%d] = 0x%04x (%d)' % (j, off, off))

# 第一个子资源
print('---')
sub_off0 = struct.unpack('<I', data[start+10:start+14])[0]
sub_off1 = struct.unpack('<I', data[start+14:start+18])[0]
print('Sub0: offset=%d (0x%04x), next_offset=%d, size=%d' % (sub_off0, sub_off0, sub_off1, sub_off1 - sub_off0))
print('Sub0 first 16 bytes: %s' % ' '.join('%02x' % b for b in data[start+sub_off0:start+sub_off0+16]))
print('Sub0 4-byte header: w=%d, h=%d' % (
    data[start+sub_off0] | (data[start+sub_off0+1]<<8),
    data[start+sub_off0+2] | (data[start+sub_off0+3]<<8)
))
print('Sub0 byte 4 (would be palette_window in 5-byte TILE): 0x%02x' % data[start+sub_off0+4])

# 第8个偏移 (无效的 0xc80140)
print('---')
print('Off[7] = 0x%04x (declared 38, 实际是子资源0的像素数据被误读)' % struct.unpack('<I', data[start+10+7*4:start+14+7*4])[0])
