import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

res0 = struct.unpack('<I', data[10:14])[0]

print('Checking bytes 24 to 48 (12 WORDs):')
for i in range(24, 50, 2):
    word = struct.unpack('<h', data[res0+i:res0+i+2])[0]
    word_idx = (i - 24) // 2
    print(f'  [{word_idx}] offset {i}: {word} (0x{word & 0xFFFF:04X})')

print(f'\nSub-offset table at bytes 2-46 (22 entries, 44 bytes):')
# 字节2到46，共23个WORD（24个条目？不对）
# 字节2, 4, 6, ..., 46, 48 = 24个WORD
for i in range(2, 50, 2):
    word = struct.unpack('<h', data[res0+i:res0+i+2])[0]
    entry_idx = (i - 2) // 2
    print(f'  sub[{entry_idx}] at byte {i}: {word}')

print(f'\nKey insight:')
print(f'  Byte 0-1: sub-count = 24')
print(f'  Byte 2-45: sub-offset table (22 entries, 44 bytes)')
print(f'  Byte 46-47: ??? (value 356, 357)')

# 如果子数量是24，那么子偏移表应该有24个条目
# 字节2到字节49（24个WORD = 48字节）
# 但 res0+48 的值是 357，res0+46 是 356

# 检查 sub[10] 结束后的数据
print(f'\nAt byte 4360 (res0 end):')
print(f'  Word: {struct.unpack("<h", data[res0+4360:res0+4362])[0]}')
print(f'  This is resource set 1 sub-count = 34')

# 所以资源集0的实际结构是：
# 字节0-1: 子数量24
# 字节2-47: 24个子偏移（但只有前11个有效）
# 字节48-4359: 11个子资源数据
# 字节4360: 资源集1开始

# 验证：sub[0] 在字节316，那字节48到316之间是什么？
print(f'\nBytes 48 to 316 ({316-48} bytes):')
for i in range(48, 320, 2):
    word = struct.unpack('<h', data[res0+i:res0+i+2])[0]
    print(f'  [{i}] {word}')
    if i >= 60 and i <= 80:
        # 检查是否是某个子资源的内容
        pass
