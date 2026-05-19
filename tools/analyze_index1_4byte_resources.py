import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

fd.seek(offset_idx1)
data = fd.read(size)

print('=== FDOTHER.DAT索引1 - 4字节资源表分析 ===')
print(f'大小: {size} bytes\n')

# 前0x46字节是4字节资源偏移表
print('4字节资源偏移表 (前0x46字节):')
num_entries = 0x46 // 4
for i in range(num_entries):
    off = i * 4
    if off + 4 <= len(data):
        val = struct.unpack('<I', data[off:off+4])[0]
        if i + 1 < num_entries:
            next_val = struct.unpack('<I', data[off+4:off+8])[0]
            res_size = next_val - val
        else:
            res_size = 0x46 - off
        print(f'  资源[{i:2d}] 0x{off:04X} -> 0x{val:06X} (大小{res_size} bytes)')
print()

# 提取并分析资源1-10
print('=== 分析资源1-10 ===')
for rid in range(1, 11):
    off = rid * 4
    if off + 8 <= len(data):
        res_off = struct.unpack('<I', data[off:off+4])[0]
        next_off = struct.unpack('<I', data[off+4:off+8])[0]
        res_size = next_off - res_off
        
        print(f'\n资源{rid}:')
        print(f'  偏移: 0x{res_off:06X}')
        print(f'  大小: {res_size} bytes')
        
        if res_off < size and res_size > 0:
            chunk = data[res_off:res_off+min(32, res_size)]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'  前32字节: {hex_str}')
            
            # 检查是否是图像（前2字节宽，2字节高）
            if res_size >= 4:
                w = struct.unpack('<H', data[res_off:res_off+2])[0]
                h = struct.unpack('<H', data[res_off+2:res_off+4])[0]
                if 0 < w < 400 and 0 < h < 300:
                    print(f'  可能是图像: 宽{w} x 高{h}')
                    
                    # 保存资源
                    out_file = f'd:/workspace/fd2_dat_freebuff/output/index1_resource_{rid}.bin'
                    with open(out_file, 'wb') as out:
                        out.write(data[res_off:res_off + res_size])
                    print(f'  已保存: {out_file}')
print()

fd.close()
