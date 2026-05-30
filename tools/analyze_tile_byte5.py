#!/usr/bin/env python3
"""
分析所有TILE资源的字节5值，找出区分5字节头和8字节头的规律
"""
import struct

# 读取FDOTHER.DAT
dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
with open(dat_path, 'rb') as f:
    data = f.read()

# 解析索引表
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 收集所有tile资源（包括嵌套DAT中的）
all_tiles = []

def collect_tiles_from_nested(nested_data, parent_idx):
    """从嵌套DAT中收集tile"""
    if len(nested_data) < 14:
        return
    
    nested_count = struct.unpack_from('<I', nested_data, 6)[0]
    if nested_count > 1000 or nested_count == 0:
        return
    
    # 偏移表开始位置
    table_start = 10
    
    for i in range(nested_count):
        offset_addr = table_start + i * 4
        if offset_addr + 8 > len(nested_data):
            break
        
        tile_start = struct.unpack_from('<I', nested_data, offset_addr)[0]
        tile_end = struct.unpack_from('<I', nested_data, offset_addr + 4)[0]
        
        if tile_start >= len(nested_data) or tile_end > len(nested_data) or tile_end <= tile_start:
            continue
        
        tile_data = nested_data[tile_start:tile_end]
        if len(tile_data) < 8:
            continue
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        
        # 检查宽高是否合理
        if 0 < w <= 512 and 0 < h <= 512:
            all_tiles.append({
                'idx': f'{parent_idx}_{i}',
                'w': w,
                'h': h,
                'data': tile_data,
                'size': len(tile_data)
            })

# 遍历所有顶级资源
for idx in range(count):
    res_start = offsets[idx]
    res_end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
    res_size = res_end - res_start
    
    if res_size < 14 or res_start >= len(data) or res_start >= len(data):
        continue
    
    # 安全地切片
    actual_end = min(res_end, len(data))
    res = data[res_start:actual_end]
    
    if len(res) < 8:
        continue
    
    # 检查是否是嵌套DAT（前6字节是"LLLLLL"，第7-10字节是资源数）
    if res[:6] == b'LLLLLL':
        collect_tiles_from_nested(res, idx)
        continue
    
    w = struct.unpack_from('<H', res, 0)[0]
    h = struct.unpack_from('<H', res, 2)[0]
    
    # 检查宽高是否合理
    if 0 < w <= 512 and 0 < h <= 512:
        all_tiles.append({
            'idx': str(idx),
            'w': w,
            'h': h,
            'data': res,
            'size': len(res)
        })

print('='*120)
print(f'分析所有TILE资源（共{len(all_tiles)}个，包括嵌套DAT中的tile）')
print('='*120)
print(f'{"索引":<12} {"宽":<5} {"高":<5} {"总大小":<8} {"字节4":<5} {"字节5":<5} {"字节6":<5} {"字节7":<5} {"4-5(2B)":<10} {"6-7(2B)":<10}')
print('-'*120)

# 显示所有tile的字节4-7
for tile in all_tiles:
    res = tile['data']
    if len(res) < 8:
        continue
    
    byte4 = res[4]
    byte5 = res[5]
    byte6 = res[6]
    byte7 = res[7]
    
    pal_win = struct.unpack_from('<H', res, 4)[0]
    extra = struct.unpack_from('<H', res, 6)[0]
    
    print(f'{tile["idx"]:<12} {tile["w"]:<5} {tile["h"]:<5} {tile["size"]:<8} {byte4:<5} {byte5:<5} {byte6:<5} {byte7:<5} {pal_win:<10} {extra:<10}')

# 按字节5值分组统计
print('\n' + '='*120)
print('按字节5值分组统计')
print('='*120)

byte5_groups = {}
for tile in all_tiles:
    res = tile['data']
    if len(res) < 6:
        continue
    
    byte5 = res[5]
    byte4 = res[4]
    
    if byte5 not in byte5_groups:
        byte5_groups[byte5] = {'count': 0, 'byte4_values': []}
    
    byte5_groups[byte5]['count'] += 1
    byte5_groups[byte5]['byte4_values'].append(byte4)

print(f'{"字节5":<8} {"总数":<8} {"字节4值分布"}')
print('-'*60)

for b5 in sorted(byte5_groups.keys()):
    g = byte5_groups[b5]
    unique_b4 = sorted(set(g['byte4_values']))
    print(f'{b5:<8} {g["count"]:<8} {unique_b4}')

# 分析可能的规律
print('\n' + '='*120)
print('规律分析')
print('='*120)

# 统计字节5=0和非0的情况
b5_zero = sum(1 for tile in all_tiles if len(tile['data']) >= 6 and tile['data'][5] == 0)
b5_nonzero = sum(1 for tile in all_tiles if len(tile['data']) >= 6 and tile['data'][5] != 0)

print(f'字节5=0的tile数量: {b5_zero}')
print(f'字节5!=0的tile数量: {b5_nonzero}')

# 查看字节4的分布
byte4_values = [tile['data'][4] for tile in all_tiles if len(tile['data']) >= 5]
print(f'\n字节4的值分布:')
print(f'  最小值: {min(byte4_values)}')
print(f'  最大值: {max(byte4_values)}')
print(f'  唯一值数量: {len(set(byte4_values))}')
print(f'  常见值: {sorted(set(byte4_values))[:20]}')

# 检查字节5=0的tile，字节4是否可能是调色板偏移（单字节）
print('\n\n假设:')
print('- 字节5=0: 5字节头格式 [w:2][h:2][pal_offset:1][RLE数据]')
print('- 字节5!=0: 8字节头格式 [w:2][h:2][pal_win:2][extra:2][RLE数据]')
