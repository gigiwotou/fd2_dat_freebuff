import struct
import os

filepath = r"D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

if not os.path.exists(filepath):
    print("文件不存在")
    exit(1)

file_size = os.path.getsize(filepath)
print("=" * 80)
print("FDOTHER.DAT 文件分析")
print("=" * 80)
print(f"文件路径: {filepath}")
print(f"文件大小: {file_size} 字节 ({file_size / 1024:.1f} KB)")
print()

with open(filepath, 'rb') as f:
    data = f.read()

# 解析文件头
magic = data[0:6]
print("文件头:")
print(f"  魔数 (偏移0-5): {' '.join(f'{b:02X}' for b in magic)}")

resource_count = struct.unpack('<I', data[6:10])[0]
print(f"  资源数量 (偏移6-9): {resource_count}")
print()

# 解析偏移表
offset_table_start = 10
offsets = []

for i in range(resource_count):
    offset_pos = offset_table_start + i * 4
    if offset_pos + 4 > len(data):
        print(f"警告: 资源{i}的偏移超出文件范围")
        break
    res_offset = struct.unpack('<I', data[offset_pos:offset_pos+4])[0]
    offsets.append(res_offset)

data_start = offset_table_start + resource_count * 4
print(f"偏移表起始: {offset_table_start}")
print(f"数据区起始: {data_start}")
print()

# 打印前30个资源的偏移和大小
print("=" * 80)
print("前30个资源的偏移和大小")
print("=" * 80)
print(f"{'索引':<6} {'偏移':<10} {'偏移(十六进制)':<15} {'大小':<10} {'大小(十六进制)':<15}")
print("-" * 80)

for i in range(min(30, len(offsets))):
    current_offset = offsets[i]
    if i + 1 < len(offsets):
        size = offsets[i+1] - current_offset
    else:
        size = file_size - current_offset
    print(f"{i:<6} {current_offset:<10} 0x{current_offset:<13X} {size:<10} 0x{size:<13X}")

if len(offsets) > 30:
    print(f"... (共{len(offsets)}个资源)")
print()

# 读取每个资源的前4个字节
print("=" * 80)
print("每个资源的前4个字节（宽度x高度）")
print("=" * 80)
print(f"{'索引':<6} {'偏移':<10} {'宽度(LE)':<10} {'高度(LE)':<10} {'宽度(BE)':<10} {'高度(BE)':<10} {'疑似尺寸'}")
print("-" * 80)

for i in range(min(30, len(offsets))):
    current_offset = offsets[i]
    if current_offset + 4 > len(data):
        print(f"{i:<6} {current_offset:<10} [超出范围]")
        continue
    
    b0 = data[current_offset]
    b1 = data[current_offset + 1]
    b2 = data[current_offset + 2]
    b3 = data[current_offset + 3]
    
    width_le = struct.unpack('<H', data[current_offset:current_offset+2])[0]
    height_le = struct.unpack('<H', data[current_offset+2:current_offset+4])[0]
    
    width_be = struct.unpack('>H', data[current_offset:current_offset+2])[0]
    height_be = struct.unpack('>H', data[current_offset+2:current_offset+4])[0]
    
    size_str = ""
    if width_le == 320 and height_le == 200:
        size_str = "320x200 (LE)"
    elif width_le == 640 and height_le == 480:
        size_str = "640x480 (LE)"
    elif width_be == 320 and height_be == 200:
        size_str = "320x200 (BE)"
    elif width_be == 640 and height_be == 480:
        size_str = "640x480 (BE)"
    else:
        size_str = f"{width_le}x{height_le} (LE)"
    
    print(f"{i:<6} {current_offset:<10} {width_le:<10} {height_le:<10} {width_be:<10} {height_be:<10} {size_str}")

print()

# 重点关注索引 1,2,3,4,5,6,20 的资源
print("=" * 80)
print("重点关注资源: 索引 1,2,3,4,5,6,20")
print("=" * 80)

target_indices = [1, 2, 3, 4, 5, 6, 20]

for idx in target_indices:
    if idx >= len(offsets):
        print(f"\n--- 索引 {idx}: 超出范围 ---")
        continue
    
    current_offset = offsets[idx]
    if idx + 1 < len(offsets):
        size = offsets[idx+1] - current_offset
    else:
        size = file_size - current_offset
    
    print(f"\n{'='*60}")
    print(f"资源索引 {idx}")
    print(f"{'='*60}")
    print(f"文件偏移: {current_offset} (0x{current_offset:08X})")
    print(f"资源大小: {size} 字节 (0x{size:08X})")
    
    if current_offset + 16 <= len(data):
        header_bytes = data[current_offset:current_offset+16]
        print(f"前16字节: {' '.join(f'{b:02X}' for b in header_bytes)}")
        
        w16_le = struct.unpack('<H', header_bytes[0:2])[0]
        h16_le = struct.unpack('<H', header_bytes[2:4])[0]
        print(f"16位LE宽高: {w16_le} x {h16_le}")
        
        w16_be = struct.unpack('>H', header_bytes[0:2])[0]
        h16_be = struct.unpack('>H', header_bytes[2:4])[0]
        print(f"16位BE宽高: {w16_be} x {h16_be}")
        
        val32_0 = struct.unpack('<I', header_bytes[0:4])[0]
        val32_4 = struct.unpack('<I', header_bytes[4:8])[0]
        val32_8 = struct.unpack('<I', header_bytes[8:12])[0]
        val32_12 = struct.unpack('<I', header_bytes[12:16])[0]
        print(f"32位LE值[0-3]: {val32_0} (0x{val32_0:08X})")
        print(f"32位LE值[4-7]: {val32_4} (0x{val32_4:08X})")
        print(f"32位LE值[8-11]: {val32_8} (0x{val32_8:08X})")
        print(f"32位LE值[12-15]: {val32_12} (0x{val32_12:08X})")
    
    print(f"\n前128字节 Hex Dump:")
    dump_end = min(current_offset + 128, len(data))
    for pos in range(current_offset, dump_end, 16):
        hex_bytes = ' '.join(f'{b:02X}' for b in data[pos:pos+16])
        ascii_chars = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[pos:pos+16])
        print(f"  {pos - current_offset:04X}: {hex_bytes:<48} {ascii_chars}")
    
    print()

print("=" * 80)
print("文件统计信息")
print("=" * 80)

if offsets:
    last_offset = offsets[-1]
    if len(offsets) > 1:
        last_resource_size = file_size - last_offset
        print(f"最后一个资源索引: {len(offsets)-1}")
        print(f"最后一个资源偏移: {last_offset}")
        print(f"最后一个资源大小: {last_resource_size}")
    
    sizes = []
    for i in range(len(offsets) - 1):
        sizes.append(offsets[i+1] - offsets[i])
    sizes.append(file_size - offsets[-1])
    
    print(f"资源数量: {len(offsets)}")
    print(f"最小资源大小: {min(sizes)} 字节")
    print(f"最大资源大小: {max(sizes)} 字节")
    print(f"平均资源大小: {sum(sizes) / len(sizes):.1f} 字节")
    print(f"总数据大小: {sum(sizes)} 字节")

print(f"\n分析完成")
