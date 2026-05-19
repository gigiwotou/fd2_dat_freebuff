import struct
import sys

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

fd.seek(offset_idx1)
data = fd.read(size)

print(f'索引1大小: {size} bytes')
print()

# 资源ID映射到2字节偏移表
# 从0x46开始是2字节偏移表
print('提取资源201, 205, 549, 550的图形数据:')
print()

resources = {
    201: 'slot边框-选中',
    205: 'slot边框-未选中',
    549: '文字-场景编号',
    550: '文字-其他信息',
}

for rid, desc in resources.items():
    # 从0x46开始的2字节偏移表
    offset_in_table = 0x46 + rid * 2
    if offset_in_table + 2 <= len(data):
        res_offset = struct.unpack('<H', data[offset_in_table:offset_in_table+2])[0]
        
        # 获取下一个资源的偏移来确定大小
        next_offset_in_table = 0x46 + (rid + 1) * 2
        if next_offset_in_table + 2 <= len(data):
            next_res_offset = struct.unpack('<H', data[next_offset_in_table:next_offset_in_table+2])[0]
            res_size = next_res_offset - res_offset
        else:
            res_size = len(data) - res_offset
        
        print(f'资源ID {rid:3d} ({desc}):')
        print(f'  偏移表位置: 0x{offset_in_table:04X}')
        print(f'  数据偏移: 0x{res_offset:04X} ({res_offset})')
        print(f'  大小: {res_size} bytes')
        
        # 保存资源数据到文件
        if res_offset < len(data) and res_size > 0:
            output_file = f'd:/workspace/fd2_dat_freebuff/output/resource_{rid}_{desc.replace(" ", "_")}.bin'
            with open(output_file, 'wb') as out:
                out.write(data[res_offset:res_offset + res_size])
            print(f'  已保存到: {output_file}')
            
            # 分析前16字节（可能是宽度/高度）
            if res_size >= 4:
                w = struct.unpack('<H', data[res_offset:res_offset+2])[0]
                h = struct.unpack('<H', data[res_offset+2:res_offset+4])[0]
                print(f'  可能的宽度: {w}, 高度: {h}')
                
                # 如果是图像，显示前几行像素数据
                if w > 0 and w < 400 and h > 0 and h < 300:
                    print(f'  图像数据起始偏移: 0x{res_offset + 4:04X}')
                    # 显示前4行
                    for row in range(min(4, h)):
                        row_start = res_offset + 4 + row * w
                        if row_start + w <= len(data):
                            row_data = data[row_start:row_start + min(16, w)]
                            hex_str = ' '.join(f'{b:02X}' for b in row_data)
                            print(f'    行{row:2d}: {hex_str}')
        print()

# 分析索引1的整体结构
print('索引1结构分析:')
print(f'  0x0000-0x0045: 头部信息 (70字节)')
print(f'    前2字节: 0x{struct.unpack("<H", data[0:2])[0]:04X}')
print(f'    0x38处: 0x{struct.unpack("<H", data[0x38:0x3A])[0]:04X}')
print(f'    0x3A处: 0x{struct.unpack("<H", data[0x3A:0x3C])[0]:04X}')
print(f'    0x46处: 0x{struct.unpack("<H", data[0x46:0x48])[0]:04X}')
print(f'  0x0046-: 2字节偏移表')
print()

# 检查偏移表的最大值
max_offset = 0
for i in range(100):
    off = 0x46 + i * 2
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        if val > max_offset:
            max_offset = val

print(f'  前100个资源偏移最大值: 0x{max_offset:04X} ({max_offset})')
print(f'  索引1可用空间: 0x{len(data):04X} ({len(data)})')

fd.close()
