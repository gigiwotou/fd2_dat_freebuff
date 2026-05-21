import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)

# 加载角色数据库
off0 = struct.unpack('<I', data[10:14])[0]
off1 = struct.unpack('<I', data[14:18])[0]
db_data = data[off0:off1]
db_size = off1 - off0
entry_count = db_size // 80

print(f'角色数据库: {entry_count} 个条目')

# 查找icon_id在有效范围内(0-138)的角色
print('\n查找icon_id在0-138范围内的角色:')
valid_chars = []
for i in range(entry_count):
    icon_id = db_data[i * 80 + 7]
    if icon_id < 139:
        valid_chars.append((i, icon_id))
        if len(valid_chars) <= 20:
            print(f'  角色[{i}]: icon_id={icon_id}')

print(f'\n共找到{len(valid_chars)}个有效角色')

# 检查FDTXT中哪些资源集使用TEXT_CHAR_F或TEXT_PORTRAIT_F/S
with open('game/FDTXT.DAT', 'rb') as f:
    fdtxt = f.read()

fdtxt_count = struct.unpack('<I', fdtxt[6:10])[0]
print(f'\nFDTXT资源集数量: {fdtxt_count}')

# 分析前10个资源集
for res_idx in range(min(10, fdtxt_count)):
    rs = struct.unpack('<I', fdtxt[10 + res_idx * 4:14 + res_idx * 4])[0]
    re = struct.unpack('<I', fdtxt[10 + (res_idx + 1) * 4:14 + (res_idx + 1) * 4])[0] if res_idx + 1 < fdtxt_count else len(fdtxt)
    
    if rs >= len(fdtxt):
        continue
        
    rd = fdtxt[rs:re]
    if len(rd) < 2:
        continue
    
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    
    for sub_idx in range(min(sub_count, 3)):
        off = struct.unpack_from('<h', rd, 2 + sub_idx * 2)[0]
        next_off = struct.unpack_from('<h', rd, 2 + (sub_idx + 1) * 2)[0] if sub_idx + 1 < sub_count else len(rd)
        
        text_data = rd[off:next_off]
        
        # 查找控制码
        i = 0
        has_portrait = False
        while i + 2 <= len(text_data):
            word = struct.unpack_from('<h', text_data, i)[0]
            if word in (-17, -18, -19, -20):  # TEXT_PORTRAIT_F/S, TEXT_CHAR_F/S
                has_portrait = True
                param = struct.unpack_from('<h', text_data, i + 2)[0] if i + 4 <= len(text_data) else 0
                print(f'  资源集{res_idx}子项{sub_idx}: 控制码={word}, 参数={param}')
                break
            i += 2
