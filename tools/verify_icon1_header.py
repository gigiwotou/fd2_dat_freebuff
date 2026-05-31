"""验证索引1图标数据是否包含宽高头"""
import struct
import os

# 加载FDOTHER.DAT
fdother_path = 'game/FDOTHER.DAT'
with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析索引表
magic = data[:6]
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 索引1的资源数据
idx = 1
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else len(data)
res_data = data[start:end]

print(f"索引1资源大小: {len(res_data)} 字节")

# 解析索引1头部
w = struct.unpack_from('<H', res_data, 0)[0]
h = struct.unpack_from('<H', res_data, 2)[0]
palette_window = res_data[4]

print(f"索引1外头: {w}x{h}, palette_window={palette_window}")

# 解析偏移表
offset_table_start = 6
icon_offsets = []
pos = offset_table_start
while pos + 4 <= len(res_data):
    off = struct.unpack_from('<I', res_data, pos)[0]
    if off > len(res_data):
        break
    icon_offsets.append(off)
    pos += 4

print(f"图标数量: {len(icon_offsets)}")

# 检查第一个图标数据
if len(icon_offsets) > 1:
    icon0_start = icon_offsets[0]
    icon1_start = icon_offsets[1]
    icon0_data = res_data[icon0_start:icon1_start]
    
    print(f"\n图标0:")
    print(f"  起始偏移: {icon0_start}")
    print(f"  大小: {len(icon0_data)} 字节")
    print(f"  前20字节: {icon0_data[:20].hex()}")
    
    # 假设前4字节是宽高头
    if len(icon0_data) >= 4:
        icon_w = struct.unpack_from('<H', icon0_data, 0)[0]
        icon_h = struct.unpack_from('<H', icon0_data, 2)[0]
        print(f"  如果前4字节是宽高头: {icon_w}x{icon_h}")
        print(f"  剩余数据大小: {len(icon0_data) - 4} 字节")
        print(f"  期望像素数: {icon_w * icon_h}")
        
        # 检查是否符合24x24
        if icon_w == 24 and icon_h == 24:
            print(f"  ✓ 确认是24x24图标！")
            print(f"  RLE数据从偏移4开始")
        else:
            print(f"  ✗ 不是24x24")
            
            # 尝试直接使用24x24，不读宽高头
            expected_pixels = 24 * 24
            print(f"  如果直接使用24x24（不读头），RLE数据大小应约为: {expected_pixels}~{expected_pixels*2}字节")
            print(f"  实际数据大小: {len(icon0_data)} 字节")

# 检查第二个图标
if len(icon_offsets) > 2:
    icon1_start = icon_offsets[1]
    icon2_start = icon_offsets[2]
    icon1_data = res_data[icon1_start:icon2_start]
    
    print(f"\n图标1:")
    print(f"  起始偏移: {icon1_start}")
    print(f"  大小: {len(icon1_data)} 字节")
    print(f"  前20字节: {icon1_data[:20].hex()}")
    
    if len(icon1_data) >= 4:
        icon_w = struct.unpack_from('<H', icon1_data, 0)[0]
        icon_h = struct.unpack_from('<H', icon1_data, 2)[0]
        print(f"  如果前4字节是宽高头: {icon_w}x{icon_h}")
