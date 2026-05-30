"""详细分析索引1和索引2的结构"""
import struct

def analyze_resource(name, start, end, offsets):
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(start)
        data = f.read(end - start)
    
    print(f"\n{'='*60}")
    print(f"分析 {name}: 偏移 {start}-{end}, 大小 {len(data)} 字节")
    print(f"{'='*60}")
    
    if len(data) < 8:
        print("数据太小，无法分析")
        return
    
    # 读取宽高
    w = data[0] | (data[1] << 8)
    h = data[2] | (data[3] << 8)
    print(f"宽度: {w}, 高度: {h}")
    print(f"预期像素数: {w * h}")
    
    # 分析字节4-7
    print(f"字节4-7: {data[4:8].hex()}")
    print(f"  字节4: 0x{data[4]:02x} ({data[4]})")
    print(f"  字节5: 0x{data[5]:02x} ({data[5]})")
    print(f"  字节6: 0x{data[6]:02x} ({data[6]})")
    print(f"  字节7: 0x{data[7]:02x} ({data[7]})")
    
    # 尝试5字节头
    palette_5 = data[4]
    rle_5 = data[5:]
    print(f"\n假设5字节头:")
    print(f"  调色板窗口: {palette_5}")
    print(f"  RLE数据大小: {len(rle_5)}")
    print(f"  RLE前16字节: {rle_5[:16].hex()}")
    
    # 尝试8字节头
    palette_8 = data[4] | (data[5] << 8)
    rle_8 = data[8:]
    print(f"\n假设8字节头:")
    print(f"  调色板窗口: {palette_8}")
    print(f"  RLE数据大小: {len(rle_8)}")
    print(f"  RLE前16字节: {rle_8[:16].hex()}")
    
    # RLE解码测试
    def decompress_rle_test(src, width, height, palette_window):
        expected = width * height
        dst = [0] * expected
        dst_idx = 0
        src_idx = 0
        src_size = len(src)
        
        ops = []
        
        while dst_idx < expected and src_idx < src_size:
            ctrl = src[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    if src_idx < src_size:
                        fill_val = src[src_idx]
                        src_idx += 1
                        if palette_window != -1:
                            fill_val = (palette_window + fill_val) & 0xFF
                        for i in range(count):
                            if dst_idx < expected:
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                        ops.append(f"FILL({count}, val=0x{fill_val:02x})")
                else:
                    # SKIP
                    dst_idx += count
                    ops.append(f"SKIP({count})")
            else:
                if bit6 == 0:
                    # COPY
                    for i in range(count):
                        if dst_idx < expected and src_idx < src_size:
                            val = src[src_idx]
                            src_idx += 1
                            if palette_window != -1:
                                val = (palette_window + val) & 0xFF
                            dst[dst_idx] = val
                            dst_idx += 1
                    ops.append(f"COPY({count})")
                else:
                    # SKIP
                    dst_idx += count
                    ops.append(f"SKIP({count})")
        
        return dst, ops
    
    # 测试5字节头
    print(f"\n测试5字节头RLE解码:")
    decoded_5, ops_5 = decompress_rle_test(rle_5, w, h, palette_5)
    non_zero_5 = sum(1 for p in decoded_5 if p != 0)
    print(f"  操作数: {len(ops_5)}")
    print(f"  解码像素: {len(decoded_5)}/{w*h}")
    print(f"  非零像素: {non_zero_5}")
    print(f"  前10个操作: {ops_5[:10]}")
    
    # 显示图像
    print(f"  图像预览:")
    for row in range(h):
        line = "    "
        for col in range(w):
            idx = row * w + col
            if idx < len(decoded_5):
                val = decoded_5[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    # 测试8字节头
    print(f"\n测试8字节头RLE解码:")
    decoded_8, ops_8 = decompress_rle_test(rle_8, w, h, palette_8)
    non_zero_8 = sum(1 for p in decoded_8 if p != 0)
    print(f"  操作数: {len(ops_8)}")
    print(f"  解码像素: {len(decoded_8)}/{w*h}")
    print(f"  非零像素: {non_zero_8}")
    print(f"  前10个操作: {ops_8[:10]}")
    
    # 显示图像
    print(f"  图像预览:")
    for row in range(h):
        line = "    "
        for col in range(w):
            idx = row * w + col
            if idx < len(decoded_8):
                val = decoded_8[idx]
                line += "." if val == 0 else "#"
        print(line)

# 读取偏移表
with open("game/FDOTHER.DAT", "rb") as f:
    f.seek(6)
    
    offsets = []
    while True:
        data = f.read(4)
        if len(data) < 4:
            break
        off = struct.unpack('<I', data)[0]
        if off > 10000000:
            break
        offsets.append(off)
        if len(offsets) > 103:
            break

# 分析索引1
analyze_resource("索引1 (TILE 24x24)", offsets[1], offsets[2], offsets)

# 分析索引2的子资源0
# 先分析索引2的偏移表结构
with open("game/FDOTHER.DAT", "rb") as f:
    f.seek(offsets[2])
    idx2_data = f.read(offsets[3] - offsets[2])

print(f"\n索引2总大小: {len(idx2_data)} 字节")

# 读取前10个偏移值
for i in range(10):
    if i * 4 + 4 <= len(idx2_data):
        off = struct.unpack('<I', idx2_data[i*4:i*4+4])[0]
        print(f"  偏移[{i}] = {off}")

# 获取第一个子资源
first_off = struct.unpack('<I', idx2_data[0:4])[0]
second_off = struct.unpack('<I', idx2_data[4:8])[0]
sub0_data = idx2_data[first_off:second_off]

print(f"\n索引2子资源0: 偏移 {first_off}-{second_off}, 大小 {len(sub0_data)}")
analyze_resource("索引2子资源0", 0, len(sub0_data), [])
