import struct
import sys

filename = sys.argv[1] if len(sys.argv) > 1 else 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
with open(filename, 'rb') as f:
    data = f.read()

print(f'文件大小: {len(data)} (0x{len(data):X})')

# 查看文件头部
print('\n=== 头部 (0x000-0x100) ===')
for i in range(0, 0x100, 16):
    hex_s = ' '.join(f'{data[i+j]:02X}' for j in range(16) if i+j < len(data))
    print(f'{i:04X}: {hex_s}')

# 解析2字节索引表
print('\n=== 关键资源分析 ===')
for rid in [0, 1, 2, 3, 19, 74, 76, 77, 201, 205, 514, 549, 550]:
    off = 0x46 + rid * 2
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'资源{rid:3d} @ 0x{off:04X} = 0x{val:04X} ({val})')
