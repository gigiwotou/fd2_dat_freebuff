"""重新精确分析资源7的子资源数 + 首子项是否能被 viewer 找到"""
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

# 算出 C 端 valid_count (不加 -1)
valid_count = 0
for j in range(count):
    if 10 + j*4 + 4 > size:
        break
    off = struct.unpack('<I', data[start+10+j*4:start+14+j*4])[0]
    if off < 10 + count*4 or off > size:
        break
    valid_count += 1

print('valid_count(含末尾) = %d' % valid_count)

# 详细列出每个偏移 + 子资源大小
print('\n--- 所有有效偏移和子资源 ---')
for j in range(valid_count):
    off = struct.unpack('<I', data[start+10+j*4:start+14+j*4])[0]
    if j + 1 < valid_count:
        next_off = struct.unpack('<I', data[start+14+j*4:start+18+j*4])[0]
    else:
        next_off = size
    sub_size = next_off - off
    is_last_marker = (off == size)
    print('  Off[%d] = 0x%04x, sub_size = %d%s' % (
        j, off, sub_size, '  (结束标记 off==size)' if is_last_marker else ''))
    if sub_size > 0:
        w = data[start+off] | (data[start+off+1]<<8)
        h = data[start+off+2] | (data[start+off+3]<<8)
        print('    -> 4字节头 w=%d, h=%d' % (w, h))

# 关键问题: viewer 中 viewer.c 的 fdother_nested_calculate_valid_count 末尾
#   if (last_off == size && valid_count > 1) valid_count--;
# 这把 Off[6]=size 的结束标记减掉, 所以变成 6
# 实际游戏代码可能不减, 把 7 个偏移都当有效子项
# 假设减1错: 应该 7 个子项, 但 Sub 6 (off=size) 实际数据=0 字节

print('\n--- 子项1的4字节头 ---')
off0 = struct.unpack('<I', data[start+10:start+14])[0]
off1 = struct.unpack('<I', data[start+14:start+18])[0]
sub_data = data[start+off0:start+off1]
print('Sub 0 first 32 bytes: %s' % ' '.join('%02x' % b for b in sub_data[:32]))
print('  w=%d, h=%d' % (sub_data[0]|(sub_data[1]<<8), sub_data[2]|(sub_data[3]<<8)))

# 同时也查一下游戏代码是不是用 declared_count - 1 还是 valid_count
# 7 个有效偏移 Off[0..6], Off[6]=res_size 是结束哨兵
# 游戏代码: sub_2FF01(sub_2D80D等)
# 实际子项数 = valid_count - 1 (去掉哨兵)  -- 我之前的判断
# 但用户说少了一个 = 7
# 矛盾, 需要查游戏代码
