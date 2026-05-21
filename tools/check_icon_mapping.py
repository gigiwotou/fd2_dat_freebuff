import struct

# 读取 DATO.DAT
with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

# 解析索引数量
count = struct.unpack('<I', data[6:10])[0]
print(f'DATO.DAT 索引数量: {count}')

# 分析所有索引条目的有效性
valid_count = 0
invalid_count = 0
last_valid = -1

for i in range(count - 1):
    offset = 10 + i * 4
    start = struct.unpack('<I', data[offset:offset+4])[0]
    end = struct.unpack('<I', data[offset+4:offset+8])[0]
    
    if start < len(data) and end <= len(data) and end > start:
        valid_count += 1
        last_valid = i
    else:
        invalid_count += 1
        if invalid_count <= 5:
            print(f'  无效索引[{i}]: start={start}, end={end}')

print(f'有效索引: {valid_count} (0-{last_valid})')
print(f'无效索引: {invalid_count}')

# 检查索引0（角色数据库）
off0 = struct.unpack('<I', data[10:14])[0]
off1 = struct.unpack('<I', data[14:18])[0]
db_data = data[off0:off1]
entry_count = len(db_data) // 80

print(f'\n角色数据库:')
print(f'  偏移: {off0}-{off1}')
print(f'  大小: {len(db_data)}')
print(f'  条目数: {entry_count}')

# 检查所有角色的 icon_id（偏移7）
icon_ids = []
for i in range(entry_count):
    if i * 80 + 7 < len(db_data):
        icon_id = db_data[i * 80 + 7]
        icon_ids.append(icon_id)

print(f'\n角色 icon_id 分布:')
print(f'  最小值: {min(icon_ids)}')
print(f'  最大值: {max(icon_ids)}')
print(f'  唯一值数量: {len(set(icon_ids))}')

# 统计大于139的icon_id
large_ids = [id for id in icon_ids if id > 139]
print(f'  大于139的icon_id数量: {len(large_ids)}')
if large_ids:
    print(f'  大于139的icon_id: {sorted(set(large_ids))}')

# 显示前20个角色的icon_id
print(f'\n前20个角色的icon_id:')
for i in range(min(20, entry_count)):
    icon_id = db_data[i * 80 + 7]
    name_bytes = db_data[i * 80:i * 80 + 6]
    name = name_bytes.decode('gbk', errors='replace').strip()
    print(f'  角色[{i:2d}]: icon_id={icon_id:3d}, 名称={name}')
