"""1:1复制sub_4E22A逻辑 - 根据IDA MCP反编译代码"""
import struct
import os
from PIL import Image

fdother_path = 'game/FDOTHER.DAT'
with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析索引表
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

print(f"索引1资源大小: {len(res_data)}")

# 解析头部
# 根据数据: 38 01 00 00 1c 03 00 00 00 05 00 00 e4 06 00 00
# 正确解析：
w = struct.unpack_from('<H', res_data, 0)[0]  # 0x0138 = 312
h = struct.unpack_from('<H', res_data, 2)[0]  # 0x0000 = 0 ???
palette_window = res_data[4]  # 0x1C = 28

# 根据MCP分析，索引1是多图标资源，格式应该是：
# [width:2][height:2][palette_window:1][unknown:1][offsets...]
# 但w=312, h=0看起来不对

# 让我检查索引0
print(f"\n索引0: {offsets[0]} - {offsets[1]}, 大小 {offsets[1]-offsets[0]}")
idx0_data = data[offsets[0]:offsets[1]]
print(f"索引0前20字节: {idx0_data[:20].hex(' ')}")
# 索引0前4字节: 18 00 18 00 = 24x24
# 第5字节: 14 = 20 (palette_window)
# 所以索引0格式是 [w:2][h:2][pal:1]

# 索引1前几个字节: 38 01 00 00 1c 03
# 如果按同样格式：w=0x0138=312, h=0, pal=28
# 但h=0不合理

# 尝试另一种解析：
# 38 01 = 312 (总宽度，所有图标排成一行)
# 00 00 = 0 (???)
# 1C = 28 (palette_window)
# 03 = padding

# 或者：
# 38 01 = 312
# 00 00 1C = ???
# 03 = 图标数量???

# 根据之前分析，索引1有20个图标，每个24x24
# 让我直接解析偏移表

print("\n解析偏移表（从偏移6开始）:")
pos = 6
icon_offsets = []
while pos + 4 <= len(res_data):
    off = struct.unpack_from('<I', res_data, pos)[0]
    if off == 0 or off > len(res_data):
        break
    icon_offsets.append(off)
    pos += 4
    if len(icon_offsets) > 100:
        break

print(f"找到 {len(icon_offsets)} 个偏移")
print(f"前10个偏移: {icon_offsets[:10]}")

if len(icon_offsets) > 1:
    sizes = [icon_offsets[i+1] - icon_offsets[i] for i in range(min(5, len(icon_offsets)-1))]
    print(f"前5个图标大小: {sizes}")

def sub_4E22A_decode_1to1(src_data, width=24, height=24):
    """1:1复制sub_4E22A反编译代码
    
    编码格式（通过检查高2位决定）：
    - 00xxxxxx (bit7=0, bit6=0): 填充模式 memset
    - 01xxxxxx (bit7=0, bit6=1): 跳跃模式 dst += count
    - 10xxxxxx (bit7=1, bit6=0): 复制模式 qmemcpy
    - 11xxxxxx (bit7=1, bit6=1): 交替模式 dst += 2
    
    count = (value & 0x3F) + 1
    """
    dst = bytearray(width * height)
    src_idx = 0
    dst_idx = 0
    
    # 外层循环：24行 (n24 = bl = 24)
    for row in range(height):
        # 内层循环：每行24像素 (n24_1 = bh = 24)
        pixels_in_row = width
        
        while pixels_in_row > 0:
            if src_idx >= len(src_data):
                break
            
            # value = *src++ (lodsb)
            value = src_data[src_idx]
            src_idx += 1
            
            # v9 = 2 * value (shl)
            v9 = (value << 1) & 0xFF
            
            # 检查bit7 (CF标志)
            if value & 0x80:
                # bit7=1: 跳转到11xxxxxx或10xxxxxx处理
                v10 = (v9 << 1) & 0x100  # 检查bit6
                count = ((value << 2) & 0xFF)  # 4 * value
                
                if v10:
                    # bit6=1: 11xxxxxx - 交替模式
                    count = (count >> 2) + 1
                    if src_idx < len(src_data):
                        pixel_value = src_data[src_idx]
                        src_idx += 1
                    else:
                        break
                    
                    # 交替写入：dst += 2
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                            dst_idx += 2
                    pixels_in_row -= count
                else:
                    # bit6=0: 10xxxxxx - 复制模式
                    count = (count >> 2) + 1
                    pixels_in_row -= count
                    
                    # qmemcpy(dst, src, count)
                    if src_idx + count <= len(src_data):
                        dst[dst_idx:dst_idx+count] = src_data[src_idx:src_idx+count]
                        src_idx += count
                        dst_idx += count
                    else:
                        break
            else:
                # bit7=0: 继续检查bit6
                v10 = (v9 << 1) & 0x100  # 检查bit6
                
                if v10:
                    # bit6=1: 01xxxxxx - 跳跃模式
                    count = ((value << 2) & 0xFF)
                    count = (count >> 2) + 1
                    pixels_in_row -= count
                    pixels_in_row -= count  # 注意：减了两次！
                    
                    if src_idx < len(src_data):
                        pixel_value = src_data[src_idx]
                        src_idx += 1
                    else:
                        break
                    
                    # 间隔写入：*v11 = value; dst = v11 + 1; (dst += 2)
                    # 但这里逻辑不同，让我重新检查反编译代码
                    # 反编译显示：n24_1 -= count两次，然后循环写入
                    # 这是一个特殊的间隔写入模式
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                            dst_idx += 2
                else:
                    # bit6=0: 00xxxxxx - 填充模式
                    count = ((value << 2) & 0xFF)
                    count = (count >> 2) + 1
                    pixels_in_row -= count
                    
                    if src_idx < len(src_data):
                        pixel_value = src_data[src_idx]
                        src_idx += 1
                    else:
                        break
                    
                    # memset(dst, value, count)
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                            dst_idx += 1
        
        # 行结束，移动到下一行
        # dst += arg8 - 24 (arg8是pitch)
        # 对于24x24图标，pitch=24，所以dst += 0
        dst_idx = (row + 1) * width
    
    return bytes(dst)

# 加载调色板
pal_data = data[offsets[0]:offsets[1]]
palette = []
for i in range(256):
    r = (pal_data[i*3] << 2) | (pal_data[i*3] >> 4)
    g = (pal_data[i*3+1] << 2) | (pal_data[i*3+1] >> 4)
    b = (pal_data[i*3+2] << 2) | (pal_data[i*3+2] >> 4)
    palette.append((r, g, b))

palette_window = 28

# 测试解码前5个图标
os.makedirs('output', exist_ok=True)

for i in range(min(5, len(icon_offsets) - 1)):
    icon_start = icon_offsets[i]
    icon_end = icon_offsets[i + 1]
    icon_data = res_data[icon_start:icon_end]
    
    print(f"\n图标{i}:")
    print(f"  偏移: {icon_start} - {icon_end}")
    print(f"  大小: {len(icon_data)}")
    print(f"  前10字节: {icon_data[:10].hex(' ')}")
    
    decoded = sub_4E22A_decode_1to1(icon_data, width=24, height=24)
    
    if len(decoded) == 24 * 24:
        non_zero = sum(1 for p in decoded if p != 0)
        print(f"  解码成功: {non_zero} 个非零像素")
        
        # 创建图像
        img = Image.new('RGB', (24, 24))
        for y in range(24):
            for x in range(24):
                idx = y * 24 + x
                pal_idx = decoded[idx]
                pal_idx = (pal_idx + palette_window) & 0xFF
                if pal_idx < 256:
                    img.putpixel((x, y), palette[pal_idx])
        
        img.save(f'output/icon{i}_sub_4e22a_1to1.png')
        print(f"  已保存: output/icon{i}_sub_4e22a_1to1.png")
    else:
        print(f"  解码失败: 像素数 {len(decoded)} != 576")
