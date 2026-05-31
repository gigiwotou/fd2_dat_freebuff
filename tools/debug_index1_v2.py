"""调试索引1数据结构"""
import struct

fdother_path = 'game/FDOTHER.DAT'
with open(fdother_path, 'rb') as f:
    data = f.read()

# 索引表
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 索引1
idx = 1
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else len(data)
res_data = data[start:end]

print(f"索引1资源: 偏移 {start}-{end}, 大小 {len(res_data)}")
print(f"\n前30字节:")
for i in range(0, min(30, len(res_data)), 16):
    chunk = res_data[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {i:04x}: {hex_str:<48s}  {ascii_str}")

# 解析头部
print(f"\n解析:")
print(f"  [0-1] width: {struct.unpack_from('<H', res_data, 0)[0]} (0x{struct.unpack_from('<H', res_data, 0)[0]:04x})")
print(f"  [2-3] height: {struct.unpack_from('<H', res_data, 2)[0]} (0x{struct.unpack_from('<H', res_data, 2)[0]:04x})")
print(f"  [4] palette_window: {res_data[4]}")
print(f"  [5] byte5: {res_data[5]}")

# 尝试从偏移6读取作为4字节偏移
print(f"\n从偏移6开始读取4字节值:")
for i in range(6, min(30, len(res_data)), 4):
    if i + 4 <= len(res_data):
        val = struct.unpack_from('<I', res_data, i)[0]
        print(f"  偏移{i}: 0x{val:08x} = {val}")

# 根据数据分析，正确的格式应该是：
# [0-1]: width (24=0x18)
# [2-3]: height (24=0x18)  
# [4]: palette_window (20=0x14)
# 但实际数据是 38 01 00 00 1c 03

# 让我检查索引0的格式
idx0_data = data[offsets[0]:offsets[1]]
print(f"\n索引0前20字节:")
for i in range(0, min(20, len(idx0_data)), 16):
    chunk = idx0_data[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {i:04x}: {hex_str:<48s}  {ascii_str}")

# 索引0格式验证
print(f"\n索引0解析:")
w0 = struct.unpack_from('<H', idx0_data, 0)[0]
h0 = struct.unpack_from('<H', idx0_data, 2)[0]
pal0 = idx0_data[4]
print(f"  width={w0}, height={h0}, palette_window={pal0}")
print(f"  这应该是24x24图标，palette_window=20")

# 所以索引1可能是不同的格式！
# 让我检查索引1的前几个字节是否可能是宽度312（多图标排成一行）
# 312 = 13个24像素图标排成一行？不，应该是20个图标

# 或者索引1头部格式是：
# [0-1]: 总宽度 312 = 13 * 24 (13个图标?)
# [2-3]: 总高度 ??? 
# [4]: palette_window

# 根据MCP分析，sub_4E22A直接处理24x24图标
# 索引1应该存储的是20个24x24图标的RLE数据

# 让我尝试另一种解析：索引1没有宽高头，直接是偏移表
print(f"\n尝试：索引1直接从偏移0开始是偏移表")
icon_offsets = []
pos = 0
while pos + 4 <= len(res_data):
    off = struct.unpack_from('<I', res_data, pos)[0]
    if off == 0 or off > len(res_data):
        break
    icon_offsets.append(off)
    pos += 4
    if len(icon_offsets) > 50:
        break

print(f"找到 {len(icon_offsets)} 个偏移（从偏移0开始）")
if len(icon_offsets) > 0:
    print(f"前10个: {icon_offsets[:10]}")
    if len(icon_offsets) > 1:
        diffs = [icon_offsets[i+1] - icon_offsets[i] for i in range(min(5, len(icon_offsets)-1))]
        print(f"大小差异: {diffs}")
