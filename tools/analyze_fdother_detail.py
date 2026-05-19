import struct
import sys

filename = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
with open(filename, 'rb') as f:
    data = f.read()

print('FDOTHER.DAT资源详细分析')
print('='*60)

# FDOTHER.DAT结构：
# - 前0x46字节：可能是头部信息
# - 从0x46开始：2字节资源偏移表

def get_resource_offset(resource_id):
    table_off = 0x46 + resource_id * 2
    if table_off + 2 > len(data):
        return None
    return struct.unpack('<H', data[table_off:table_off+2])[0]

# 分析关键资源
for rid in [201, 205, 549, 550, 514, 76, 19]:
    off = get_resource_offset(rid)
    if off is None:
        print(f'\n资源{rid}: 无法获取偏移')
        continue
    
    # 获取下一个资源的偏移来计算大小
    next_off = get_resource_offset(rid + 1)
    if next_off is not None:
        size = next_off - off if next_off > off else 0
    else:
        size = len(data) - off
    
    print(f'\n资源{rid}:')
    print(f'  偏移: 0x{off:X} ({off})')
    print(f'  大小: {size} bytes')
    
    if off < len(data) and size > 0:
        # 显示前64字节
        print(f'  内容 (前64字节):')
        for i in range(0, min(64, size), 16):
            hex_str = ' '.join(f'{data[off+i+j]:02X}' for j in range(16) if i+j < size)
            print(f'    {i:4d}: {hex_str}')
        
        # 尝试解析为16位指令（如果是脚本资源）
        if rid in [201, 205, 549, 550]:
            print(f'  16位指令解析:')
            for i in range(0, min(60, size), 2):
                val = struct.unpack('<h', data[off+i:off+i+2])[0]
                print(f'    [{i//2:3d}] = {val:6d} (0x{val & 0xFFFF:04X})')
