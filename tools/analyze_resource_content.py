import struct

# 读取资源201和549
with open('d:/workspace/fd2_dat_freebuff/output/resource_201.bin', 'rb') as f:
    res201 = f.read()

with open('d:/workspace/fd2_dat_freebuff/output/resource_549.bin', 'rb') as f:
    res549 = f.read()

print('=== 资源201分析 ===')
print(f'大小: {len(res201)} bytes')
print(f'前64字节: {res201[:64].hex()}')
print()

# 检查是否全是0
if all(b == 0 for b in res201):
    print('资源201全是0 - 可能是空白资源或需要运行时填充')
else:
    print('资源201有实际数据')
print()

print('=== 资源549分析 ===')
print(f'大小: {len(res549)} bytes')

# 显示前200字节
print('前200字节:')
for i in range(0, min(200, len(res549)), 16):
    chunk = res549[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f'  0x{i:04X}: {hex_str:<48s} {ascii_str}')
print()

# 分析作为2字节指令表
print('作为2字节指令表 (前50项):')
for i in range(min(50, len(res549) // 2)):
    val = struct.unpack('<h', res549[i*2:i*2+2])[0]  # 有符号
    if i % 10 == 0:
        print()
    print(f'  [{i:3d}]={val:5d}', end='')
print('\n')

# 检查特殊值
print('特殊值检查 (-1, -2, -3, -4, -5, -6, -17, -18, -19, -20):')
special_values = [-1, -2, -3, -4, -5, -6, -17, -18, -19, -20]
for sv in special_values:
    positions = []
    for i in range(len(res549) // 2):
        val = struct.unpack('<h', res549[i*2:i*2+2])[0]
        if val == sv:
            positions.append(i)
    if positions:
        print(f'  值{sv:3d}: 出现在位置 {positions[:10]}{"..." if len(positions) > 10 else ""}')
print()

# 统计不同值的分布
print('值分布统计 (前100个条目):')
value_counts = {}
for i in range(min(100, len(res549) // 2)):
    val = struct.unpack('<h', res549[i*2:i*2+2])[0]
    value_counts[val] = value_counts.get(val, 0) + 1

sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
for val, count in sorted_values[:20]:
    print(f'  值{val:5d}: 出现{count}次')
