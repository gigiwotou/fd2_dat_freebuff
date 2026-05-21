import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)

# 加载角色数据库
off0 = struct.unpack_from('<I', data, 10)[0]
off1 = struct.unpack_from('<I', data, 14)[0]
db_data = data[off0:off1]
db_size = off1 - off0
entry_count = db_size // 80

# 检查特定char_db_index的icon_id
test_char_db_indexes = [5, 7, 8, 11, 12, 15, 16]
print('检查char_db_index对应的icon_id:')
for idx in test_char_db_indexes:
    if idx < entry_count:
        icon_id = db_data[idx * 80 + 7]
        valid = icon_id < 139
        print(f'  char_db_index={idx} → icon_id={icon_id} (有效: {valid})')

# 检查TEXT_PORTRAIT_F参数（直接DATO索引）
test_dato_indexes = [2, 3, 5, 8, 9, 12, 44, 46, 59, 60, 61, 62, 63, 69, 74, 76, 78, 83, 92, 93, 97, 102, 117, 118]
print(f'\n检查直接DATO索引:')
for idx in test_dato_indexes:
    off_start = struct.unpack_from('<I', data, 10 + idx * 4)[0]
    off_end = struct.unpack_from('<I', data, 10 + (idx + 1) * 4)[0]
    valid = off_start < file_size and off_end <= file_size
    print(f'  DATO索引={idx}: start={off_start}, end={off_end} (有效: {valid})')
    if valid and idx < 10:
        # 显示前几个有效索引的尺寸
        res_data = data[off_start:off_end]
        if len(res_data) >= 20:
            w = struct.unpack_from('<H', res_data, 16)[0]
            h = struct.unpack_from('<H', res_data, 18)[0]
            print(f'    尺寸: {w}x{h}')
