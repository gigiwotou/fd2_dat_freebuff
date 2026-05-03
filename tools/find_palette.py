import struct

# 读取FDOTHER.DAT
with open('game_data/FDOTHER.DAT', 'rb') as f:
    data = f.read()

# 解析头
magic = data[:6]
count = struct.unpack_from('<I', data, 6)[0]
print(f'FDOTHER.DAT: magic={magic}, resource_count={count}')

# 分析所有资源
for res_idx in range(count):
    offset = struct.unpack_from('<I', data, 10 + res_idx * 4)[0]
    if res_idx + 1 < count:
        next_offset = struct.unpack_from('<I', data, 10 + (res_idx + 1) * 4)[0]
        size = next_offset - offset
    else:
        size = len(data) - offset
    
    # 只打印可能是调色板的资源 (768字节)
    if size == 768:
        print(f'\n资源 #{res_idx}: offset=0x{offset:x}, size={size} bytes')
        print(f'  -> 可能是调色板 (768字节)')
        unique_colors = len(set(data[offset:offset+size]))
        print(f'  -> 唯一颜色数: {unique_colors}')
        print(f'  -> 前32字节: {data[offset:offset+32].hex(" ")}')
        
        # 检查6-bit范围 (0-63)
        byte_values = data[offset:offset+size]
        max_val = max(byte_values)
        min_val = min(byte_values)
        print(f'  -> 值范围: {min_val}-{max_val}')
        if max_val <= 63:
            print(f'  -> 可能是6-bit调色板')
        elif max_val <= 255:
            print(f'  -> 可能是8-bit调色板')
