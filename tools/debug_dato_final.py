import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)

# 检查索引表的结束点
# 索引135应该指向文件末尾
idx = 135
off_start = struct.unpack('<I', data[10 + idx * 4:14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4:14 + (idx + 1) * 4])[0]
print(f'索引[135]: start={off_start}, end={off_end}')
print(f'  文件大小={file_size}')
print(f'  start==file_size: {off_start == file_size}')

# 检查索引136
idx = 136
off_start = struct.unpack('<I', data[10 + idx * 4:14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4:14 + (idx + 1) * 4])[0]
print(f'\n索引[136]: start={off_start}, end={off_end}')

# 看看从偏移16开始的数据是否是头像资源
print(f'\n检查偏移16处的数据:')
header = struct.unpack('<I', data[16:20])[0]
print(f'  偏移16-19: {data[16:20].hex()} = {header}')

# 检查索引136对应的资源结构
if off_start < file_size and off_end <= file_size:
    res_data = data[off_start:off_end]
    res_size = off_end - off_start
    print(f'  资源大小: {res_size}')
    if res_size >= 20:
        hdr_size = struct.unpack('<I', res_data[0:4])[0]
        f0 = struct.unpack('<I', res_data[4:8])[0]
        f1 = struct.unpack('<I', res_data[8:12])[0]
        f2 = struct.unpack('<I', res_data[12:16])[0]
        w = struct.unpack('<H', res_data[16:18])[0]
        h = struct.unpack('<H', res_data[18:20])[0]
        print(f'  头部大小: {hdr_size}')
        print(f'  帧偏移: {f0}, {f1}, {f2}')
        print(f'  宽高: {w}x{h}')

# 检查我们需要的索引196对应的角色数据
# 根据IDA分析，icon_id来自角色数据库的偏移7
# 但是FDTXT中的TEXT_CHAR_F使用char_db_index来获取icon_id
# 让我们看看char_db_index=10时获取的icon_id是什么

# 加载DATO索引0（角色数据库）
dato_off0 = struct.unpack('<I', data[10:14])[0]
dato_off1 = struct.unpack('<I', data[14:18])[0]
db_data = data[dato_off0:dato_off1]
db_size = dato_off1 - dato_off0
entry_count = db_size // 80
print(f'\n角色数据库:')
print(f'  范围: {dato_off0}-{dato_off1}')
print(f'  大小: {db_size}')
print(f'  条目数: {entry_count}')

# 检查角色索引10的icon_id（偏移7）
if 10 < entry_count:
    char_data = db_data[10 * 80:(10 + 1) * 80]
    icon_id = char_data[7]
    name_bytes = char_data[0:6]
    print(f'\n角色[10]:')
    print(f'  名字字节: {name_bytes.hex()}')
    print(f'  icon_id (偏移7): {icon_id}')
    print(f'  偏移8: {char_data[8]}')

# 检查这个icon_id是否在有效范围内
valid_idx = icon_id < 139
print(f'  icon_id有效: {valid_idx} (icon_id={icon_id})')

# 如果有效，检查对应的头像资源
if valid_idx:
    off_start = struct.unpack('<I', data[10 + icon_id * 4:14 + icon_id * 4])[0]
    off_end = struct.unpack('<I', data[10 + (icon_id + 1) * 4:14 + (icon_id + 1) * 4])[0]
    print(f'  头像资源: start={off_start}, end={off_end}')
    if off_start < file_size and off_end <= file_size:
        res_size = off_end - off_start
        print(f'  资源大小: {res_size}')
