"""1:1复制sub_4E22A逻辑来解码索引1的图标"""
import struct
import os
from PIL import Image

# 加载FDOTHER.DAT
fdother_path = 'game/FDOTHER.DAT'
with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析索引表
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

# 解析索引1头部
w = struct.unpack_from('<H', res_data, 0)[0]
h = struct.unpack_from('<H', res_data, 2)[0]
palette_window = res_data[4]

print(f"索引1: {w}x{h}, palette_window={palette_window}")

# 解析偏移表
icon_offsets = []
pos = 6
while pos + 4 <= len(res_data):
    off = struct.unpack_from('<I', res_data, pos)[0]
    if off > len(res_data):
        break
    icon_offsets.append(off)
    pos += 4

print(f"图标数量: {len(icon_offsets)}")

# 1:1实现sub_4E22A解码逻辑
def sub_4E22A_decode(src_data, width=24, height=24, pitch=24):
    """按照sub_4E22A汇编代码1:1实现
    参数:
        src_data: RLE压缩数据
        width: 图标宽度 (24)
        height: 图标高度 (24)
        pitch: 目标行间距
    返回:
        解码后的像素数组
    """
    # 初始化目标缓冲区
    dst = [0] * (width * height)
    dst_idx = 0  # 当前写入位置
    src_idx = 0  # 当前读取位置
    
    # 汇编中的变量映射:
    # bl = 24 (行数计数器)
    # bh = 24 (当前行剩余像素数)
    # cl = 临时寄存器
    # edx = pitch - 24 (行间距调整)
    
    row_stride = pitch - width  # 每行结束后需要跳过的字节数
    
    for row in range(height):
        pixels_in_row = width  # bh = 24
        
        while pixels_in_row > 0:
            if src_idx >= len(src_data):
                break
            
            # 4e242: lodsb - 读取控制字节
            al = src_data[src_idx]
            src_idx += 1
            
            # 4e243-4e245: mov cl, al; shl cl, 1
            cl = (al << 1) & 0xFF
            
            # 4e247: jb loc_4E271 - 检查bit7
            if al & 0x80:
                # bit7=1: 跳转到4E271
                # 4e271: shl cl, 1
                cl = (cl << 1) & 0xFF
                
                # 4e273: jb loc_4E284 - 检查bit6
                if al & 0x40:
                    # bit6=1: 模式 11xxxxxx - 跳过像素（透明）
                    # 4e284: shr cl, 2
                    count = (cl >> 2) + 1
                    # 4e287: inc cl
                    # 4e289: add edi, ecx - 跳过目标位置
                    dst_idx += count
                    # 4e28b: sub bh, cl
                    pixels_in_row -= count
                else:
                    # bit6=0: 模式 10xxxxxx - 复制像素块
                    # 4e275: shr cl, 2
                    count = (cl >> 2) + 1
                    # 4e278: inc cl
                    # 4e27a: sub bh, cl
                    pixels_in_row -= count
                    
                    # 4e27c: rep movsb - 从源复制count个字节到目标
                    if src_idx + count <= len(src_data):
                        for i in range(count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = src_data[src_idx]
                                src_idx += 1
                                dst_idx += 1
                    else:
                        break
            else:
                # bit7=0: 继续检查bit6
                # 4e249: shl cl, 1
                cl = (cl << 1) & 0xFF
                
                # 4e24b: jb loc_4E25D - 检查bit6
                if al & 0x40:
                    # bit6=1: 模式 01xxxxxx - 重复像素
                    # 4e25d: shr cl, 2
                    count = (cl >> 2) + 1
                    # 4e260: inc cl
                    # 4e262: sub bh, cl
                    pixels_in_row -= count
                    # 4e264: sub bh, cl - 注意这里减了两次！
                    pixels_in_row -= count
                    
                    # 4e266: lodsb - 读取像素值
                    if src_idx < len(src_data):
                        pixel = src_data[src_idx]
                        src_idx += 1
                    else:
                        break
                    
                    # 4e267-4e269: 循环写入像素（间隔写入）
                    # inc edi; stosb; loop
                    # 这个循环每次写入一个像素然后跳过下一个位置
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel
                            dst_idx += 2  # 注意这里是+2！
                else:
                    # bit6=0: 模式 00xxxxxx - 填充像素
                    # 4e24d: shr cl, 2
                    count = (cl >> 2) + 1
                    # 4e250: inc cl
                    # 4e252: sub bh, cl
                    pixels_in_row -= count
                    
                    # 4e254: lodsb - 读取像素值
                    if src_idx < len(src_data):
                        pixel = src_data[src_idx]
                        src_idx += 1
                    else:
                        break
                    
                    # 4e255: rep stosb - 重复写入像素值
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel
                            dst_idx += 1
        
        # 行结束，移动到下一行
        # 4e291: add edi, edx (edx = pitch - 24)
        dst_idx += row_stride
    
    return dst

# 加载主调色板（索引0）
pal_start = offsets[0]
pal_end = offsets[1]
pal_data = data[pal_start:pal_end]
palette = []
for i in range(256):
    r = (pal_data[i*3] << 2) | (pal_data[i*3] >> 4)
    g = (pal_data[i*3+1] << 2) | (pal_data[i*3+1] >> 4)
    b = (pal_data[i*3+2] << 2) | (pal_data[i*3+2] >> 4)
    palette.append((r, g, b))

# 测试解码第一个图标
if len(icon_offsets) >= 2:
    icon0_start = icon_offsets[0]
    icon1_start = icon_offsets[1]
    icon0_data = res_data[icon0_start:icon1_start]
    
    print(f"\n图标0:")
    print(f"  起始偏移: {icon0_start}")
    print(f"  数据大小: {len(icon0_data)}")
    print(f"  前20字节: {icon0_data[:20].hex()}")
    
    # 使用sub_4E22A解码
    decoded = sub_4E22A_decode(icon0_data, width=24, height=24, pitch=24)
    print(f"  解码后像素数: {len(decoded)}")
    print(f"  非零像素数: {sum(1 for p in decoded if p != 0)}")
    print(f"  像素值范围: {min(decoded)} - {max(decoded)}")
    
    # 创建图像
    img = Image.new('RGB', (24, 24))
    for y in range(24):
        for x in range(24):
            idx = y * 24 + x
            if idx < len(decoded):
                pal_idx = decoded[idx]
                # 应用palette_window
                pal_idx = (pal_idx + palette_window) & 0xFF
                if pal_idx < 256:
                    img.putpixel((x, y), palette[pal_idx])
    
    # 保存图像
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    img.save(f'{output_dir}/icon0_sub_4e22a.png')
    print(f"  图像已保存: {output_dir}/icon0_sub_4e22a.png")

# 测试解码前5个图标
for i in range(min(5, len(icon_offsets) - 1)):
    icon_start = icon_offsets[i]
    icon_end = icon_offsets[i + 1]
    icon_data = res_data[icon_start:icon_end]
    
    decoded = sub_4E22A_decode(icon_data, width=24, height=24, pitch=24)
    
    if len(decoded) == 24 * 24:
        img = Image.new('RGB', (24, 24))
        for y in range(24):
            for x in range(24):
                idx = y * 24 + x
                pal_idx = decoded[idx]
                pal_idx = (pal_idx + palette_window) & 0xFF
                if pal_idx < 256:
                    img.putpixel((x, y), palette[pal_idx])
        
        img.save(f'{output_dir}/icon{i}_sub_4e22a.png')
        print(f"图标{i}: 已保存")
