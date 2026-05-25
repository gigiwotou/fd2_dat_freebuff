#!/usr/bin/env python3
"""
正确解析嵌套DAT并提取tile图像
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/nested_dat_tiles_v3"
os.makedirs(output_dir, exist_ok=True)

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取主索引表
NUM_INDICES = 422
main_offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    main_offsets.append(offset)

# 获取索引63
idx63_start = main_offsets[63]
idx63_end = main_offsets[64] if 64 < len(main_offsets) else len(data)
nested_dat = data[idx63_start:idx63_end]

print(f"索引63:")
print(f"  主DAT偏移: 0x{idx63_start:08X} ({idx63_start})")
print(f"  嵌套DAT大小: {len(nested_dat)}")

# 读取嵌套DAT头部
magic = nested_dat[:6]
resource_count = struct.unpack_from('<I', nested_dat, 6)[0]
print(f"  Magic: {magic}")
print(f"  [6-9] 值: {resource_count}")

# 尝试正确解析嵌套DAT索引表
# 假设索引表格式是 [offset:4] 从偏移10开始
print(f"\n解析嵌套DAT索引表（格式：[offset:4]）")
nested_offsets_start = 10
valid_offsets = []
for i in range(resource_count):
    addr = nested_offsets_start + i * 4
    if addr + 4 > len(nested_dat):
        print(f"  [{i}] 地址超出范围")
        break
    offset = struct.unpack_from('<I', nested_dat, addr)[0]
    if offset < len(nested_dat):
        valid_offsets.append((i, offset))
    else:
        print(f"  [{i}] 偏移 {offset} 超出嵌套DAT范围，停止解析")
        break

print(f"  找到 {len(valid_offsets)} 个有效偏移")

# 提取每个偏移处的tile数据
print(f"\n提取tile数据")
for idx, (resource_idx, offset) in enumerate(valid_offsets[:30]):
    # 获取下一个偏移作为大小
    if idx + 1 < len(valid_offsets):
        next_offset = valid_offsets[idx + 1][1]
        size = next_offset - offset
    else:
        size = len(nested_dat) - offset
    
    if offset + 4 > len(nested_dat):
        continue
    
    # 尝试解析为tile数据 (w, h, pixel_data)
    w = struct.unpack_from('<H', nested_dat, offset)[0]
    h = struct.unpack_from('<H', nested_dat, offset + 2)[0]
    
    if 0 < w <= 320 and 0 < h <= 200:
        pixel_size = w * h
        if offset + 4 + pixel_size <= len(nested_dat):
            pixel_data = nested_dat[offset + 4:offset + 4 + pixel_size]
            print(f"  [{resource_idx}] 偏移 {offset}: {w}x{h}, 像素数 {pixel_size}")
            
            # 创建图像（使用增强对比度的方式）
            # 先尝试灰度图
            img = Image.new('L', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(pixel_data):
                        # 直接使用索引值作为灰度
                        img.putpixel((x, y), pixel_data[px_idx])
            
            # 保存
            img_path = os.path.join(output_dir, f"tile_{resource_idx}_{offset}_{w}x{h}.png")
            img.save(img_path)
        else:
            print(f"  [{resource_idx}] 偏移 {offset}: {w}x{h} - 像素数据不完整")
    else:
        print(f"  [{resource_idx}] 偏移 {offset}: 不是tile数据 (w={w}, h={h})")

print(f"\n完成！图像已保存到: {output_dir}")
