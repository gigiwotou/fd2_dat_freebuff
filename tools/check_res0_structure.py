import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

res0 = struct.unpack('<I', data[10:14])[0]
print(f'Resource set 0 starts at: {hex(res0)}')

# 检查 sub[0] 到 sub[10] 的结束位置
sub_offsets = []
for i in range(11):
    off = struct.unpack('<h', data[res0+2+i*2:res0+4+i*2])[0]
    sub_offsets.append(off)

print('\nValid sub-offsets (0-10):')
for i, off in enumerate(sub_offsets):
    pos = res0 + off
    # 找到该子资源的结束位置
    j = 0
    while True:
        word = struct.unpack('<h', data[pos+j:pos+j+2])[0]
        if word == -1:
            print(f'  sub[{i}] offset={off}, length={j+2} bytes, ends at relative byte {off+j+2}')
            break
        j += 2

# sub[10] 结束后的位置
sub10_end = res0 + 4340 + 20  # sub[10] at 4340, length 20 bytes
print(f'\nAfter sub[10] ends at relative byte 4360:')
for i in range(0, 100, 2):
    word = struct.unpack('<h', data[res0+4360+i:res0+4362+i])[0]
    print(f'  [{4360+i}] {word}')

# 检查资源集1的偏移
res1 = struct.unpack('<I', data[14:18])[0]
print(f'\nResource set 1 starts at: {hex(res1)}')
res1_sc = struct.unpack('<h', data[res1:res1+2])[0]
print(f'Resource set 1 sub-count: {res1_sc}')

# 检查 res0 结束位置是否是 res1 开始
print(f'\nDistance between res0 and res1: {res1 - res0} bytes')

# 检查 sub[11] 的偏移 -18 是什么意思
print(f'\nsub[11] offset=-18 means what?')
# -18 = 0xFFEE，这是负数，可能表示特殊含义或错误

# 检查资源集0的总长度
res0_size = res1 - res0
print(f'Resource set 0 total size: {res0_size} bytes')

# 检查资源集0的字节48-50（子偏移表结束后）
print(f'\nAt res0+48 (after sub-offset table):')
word = struct.unpack('<h', data[res0+48:res0+50])[0]
print(f'  Word: {word}')

# 如果子偏移表只有11项（22字节）+ 2字节数量 = 24字节
# 那么子资源从字节24开始
print(f'\nIf sub-offset table has 11 entries:')
print(f'  Sub-offset table ends at byte: {2 + 11*2} = 24')
print(f'  First sub-resource starts at byte 24')

# 检查从字节24开始是否是 sub[0] 的内容
print(f'\nAt res0+24:')
word = struct.unpack('<h', data[res0+24:res0+26])[0]
print(f'  Word: {word}')
# sub[0] 的偏移是316，所以 sub[0] 在 res0+316
# 那 res0+24 到 res0+316 之间是什么？
print(f'  Bytes 24 to 316: {316-24} bytes gap')
print(f'  This suggests sub[0] is NOT at byte 24')
