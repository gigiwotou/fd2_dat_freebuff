import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# 解析资源偏移
fdshap_rc = struct.unpack_from('<I', fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    fdshap_offsets.append(struct.unpack_from('<I', fdshap, 10 + i * 4)[0])

# 分析资源0（调色板）
res0_start = fdshap_offsets[0]
res0_end = fdshap_offsets[1] if 1 < len(fdshap_offsets) else len(fdshap)
res0_size = res0_end - res0_start

print(f"=== FDSHAP 资源0 (调色板) 详细分析 ===")
print(f"起始: {res0_start}")
print(f"大小: {res0_size} 字节")
print(f"\n前100字节 (十六进制):")
for i in range(0, min(100, res0_size), 16):
    chunk = fdshap[res0_start+i:res0_start+i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")

# 尝试解析为不同的结构
print(f"\n\n可能的结构分析:")
print(f"1. 如果是256色调色板 (768字节):")
if res0_size >= 768:
    palette_data = fdshap[res0_start:res0_start+768]
    print(f"   前16色 (RGB):")
    for i in range(0, 48, 3):
        r, g, b = palette_data[i], palette_data[i+1], palette_data[i+2]
        print(f"   色{i//3}: ({r}, {g}, {b})")

print(f"\n2. 如果是300色 (900字节):")
if res0_size >= 900:
    print(f"   剩余字节: {res0_size - 900}")

print(f"\n3. 如果是4字节条目:")
entry_count = res0_size // 4
print(f"   {entry_count} 个4字节条目")
print(f"   前10个条目:")
for i in range(min(10, entry_count)):
    pos = res0_start + i * 4
    b0, b1, b2, b3 = fdshap[pos], fdshap[pos+1], fdshap[pos+2], fdshap[pos+3]
    val16 = struct.unpack_from('<H', fdshap, pos)[0]
    val32 = struct.unpack_from('<I', fdshap, pos)[0]
    print(f"   条目{i}: [{b0:02x} {b1:02x} {b2:02x} {b3:02x}] 16bit={val16}, 32bit={val32}")

# 分析资源1（瓦片集）
res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2] if 2 < len(fdshap_offsets) else len(fdshap)
res1_size = res1_end - res1_start

print(f"\n\n=== FDSHAP 资源1 (瓦片集) 详细分析 ===")
print(f"起始: {res1_start}")
print(f"大小: {res1_size} 字节")

# 头部
tile_w = struct.unpack_from('<H', fdshap, res1_start)[0]
tile_h = struct.unpack_from('<H', fdshap, res1_start + 2)[0]
tile_count = struct.unpack_from('<H', fdshap, res1_start + 4)[0]

print(f"\n头部:")
print(f"  Byte 0-1: tile_width = {tile_w}")
print(f"  Byte 2-3: tile_height = {tile_h}")
print(f"  Byte 4-5: tile_count = {tile_count}")

# 验证偏移表
tile_offsets = []
pos = res1_start + 6
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from('<I', fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        tile_offsets.append(offset_val)
    else:
        break
    pos += 4

print(f"  实际找到瓦片数: {len(tile_offsets)}")
print(f"  匹配: {'是' if len(tile_offsets) == tile_count else '否'}")

# 分析前几个瓦片
print(f"\n前5个瓦片:")
for i in range(min(5, len(tile_offsets))):
    tile_offset = tile_offsets[i]
    if i + 1 < len(tile_offsets):
        tile_size = tile_offsets[i + 1] - tile_offset
    else:
        tile_size = res1_size - tile_offset
    
    print(f"  瓦片{i}: 偏移={tile_offset}, 大小={tile_size} 字节")
    
    # 读取瓦片数据的前几个字节
    tile_data_start = res1_start + tile_offset
    tile_data = fdshap[tile_data_start:tile_data_start + min(16, tile_size)]
    print(f"    前16字节: {tile_data.hex(' ')}")
