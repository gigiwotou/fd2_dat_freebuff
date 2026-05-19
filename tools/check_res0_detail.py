import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

res0 = struct.unpack('<I', data[10:14])[0]
print(f'Resource set 0 offset: {hex(res0)}')

# 分析前几个字节
print(f'\nRaw bytes at res0:')
for i in range(0, 50, 2):
    word = struct.unpack('<h', data[res0+i:res0+i+2])[0]
    print(f'  [{i}] {word} (0x{word & 0xFFFF:04X})')

# 检查 sub[0] 的内容
off0 = struct.unpack('<h', data[res0+2:res0+4])[0]
print(f'\nsub[0] offset: {off0}')
print(f'sub[0] first words:')
pos = res0 + off0
for i in range(0, 40, 2):
    word = struct.unpack('<h', data[pos+i:pos+i+2])[0]
    if word == -1:
        print(f'  [{i}] -1 (END)')
        break
    print(f'  [{i}] {word}')

# 检查 sub[10] 之后的内容
print(f'\nChecking sub-offsets around 10-12:')
for i in range(10, 14):
    off = struct.unpack('<h', data[res0+2+i*2:res0+4+i*2])[0]
    print(f'  sub[{i}] offset={off}')

# 检查从sub[10]结束后的数据
off10 = struct.unpack('<h', data[res0+2+10*2:res0+4+10*2])[0]
pos10 = res0 + off10
print(f'\nsub[10] starts at byte {off10} (absolute: {hex(pos10)})')
# 找到sub[10]的结束位置
i = 0
while True:
    word = struct.unpack('<h', data[pos10+i:pos10+i+2])[0]
    if word == -1:
        print(f'  sub[10] ends at relative byte {off10+i+2}')
        break
    i += 2

# 检查sub[10]结束后紧跟的是什么
next_pos = pos10 + i + 2
next_word = struct.unpack('<h', data[next_pos:next_pos+2])[0]
print(f'  Next word after sub[10]: {next_word} at relative byte {next_pos - res0}')
