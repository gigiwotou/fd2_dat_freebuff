"""调试索引1的详细结构"""
import struct

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
    
    # 索引1的范围
    start = offsets[1]
    end = offsets[2]
    size = end - start
    
    print(f"索引1: 偏移 {start} - {end}, 大小 {size}")
    
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(start)
        idx1_data = f.read(size)
        
    print(f"总大小: {len(idx1_data)} 字节")
    print(f"前16字节: {idx1_data[:16].hex()}")
    
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    print(f"宽度: {w}, 高度: {h}")
    print(f"预期像素数: {w * h}")
    
    byte4 = idx1_data[4]
    byte5 = idx1_data[5] if len(idx1_data) > 5 else 0
    print(f"字节4: 0x{byte4:02x} ({byte4})")
    print(f"字节5: 0x{byte5:02x} ({byte5})")
    
    # 根据字节5判断头格式
    if byte5 != 0:
        header_size = 8
        palette_window = idx1_data[4] | (idx1_data[5] << 8)
        print(f"检测为8字节头, palette_window={palette_window}")
    else:
        header_size = 5
        palette_window = idx1_data[4]
        print(f"检测为5字节头, palette_window={palette_window}")
    
    rle_data = idx1_data[header_size:]
    print(f"RLE数据大小: {len(rle_data)} 字节")
    print(f"RLE前32字节: {rle_data[:32].hex()}")
    
    # 手动解码RLE
    def decompress_rle_debug(src, width, height, palette_window=-1):
        expected = width * height
        dst = [0] * expected
        dst_idx = 0
        src_idx = 0
        src_size = len(src)
        
        operations = []
        
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
                        operations.append(f"FILL({count}, val=0x{fill_val:02x})")
                else:
                    # SKIP
                    dst_idx += count
                    operations.append(f"SKIP({count})")
            else:
                if bit6 == 0:
                    # COPY
                    copied_vals = []
                    for i in range(count):
                        if dst_idx < expected and src_idx < src_size:
                            val = src[src_idx]
                            src_idx += 1
                            if palette_window != -1:
                                val = (palette_window + val) & 0xFF
                            dst[dst_idx] = val
                            dst_idx += 1
                            copied_vals.append(val)
                    operations.append(f"COPY({count}, vals={[hex(v) for v in copied_vals[:5]]}...)")
                else:
                    # SKIP
                    dst_idx += count
                    operations.append(f"SKIP({count})")
        
        return dst, operations
    
    decoded, ops = decompress_rle_debug(rle_data, w, h, palette_window)
    
    print(f"\nRLE操作序列(前20个):")
    for i, op in enumerate(ops[:20]):
        print(f"  {i}: {op}")
    
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"\n解码结果: {len(decoded)}/{w*h} 像素, 非零像素={non_zero}")
    
    # 显示图像
    print("\n图像预览:")
    for row in range(h):
        line = ""
        for col in range(w):
            idx = row * w + col
            if idx < len(decoded):
                val = decoded[idx]
                if val == 0:
                    line += "."
                else:
                    line += "#"
        print(f"  {line}")
