"""
根据MCP汇编代码逐行精确分析RLE解码
"""
import struct

def decompress_rle_assembly_exact(src, dst_size, value_1):
    """
    根据MCP sub_4E98D汇编代码逐行精确实现
    
    汇编代码流程:
    1. lodsb - 读取控制字节
    2. shl cl, 1 - 左移1位，检查CF(bit7)
    3. jb loc_4EA17 - 如果CF=1(bit7=1)，跳转
    4. shl cl, 1 - 再次左移，检查CF(bit6)
    5. jb loc_4EA00 - 如果CF=1(bit6=1)，跳转
    6. 否则继续执行FILL操作
    
    所以:
    - bit7=0, bit6=0 → FILL
    - bit7=0, bit6=1 → COPY (特殊)
    - bit7=1, bit6=0 → COPY (标准)
    - bit7=1, bit6=1 → SKIP
    """
    dst = [0] * dst_size
    dst_idx = 0
    src_idx = 0
    src_size = len(src)
    
    ops = []
    
    # 判断模式
    if value_1 == -1:
        mode = "DIRECT"
    elif value_1 > 0xFF:
        mode = "REMAP"
        byte1_value_1 = (value_1 >> 8) & 0xFF
    else:
        mode = "MONO"
        mono_value = value_1
    
    print(f"模式: {mode}")
    
    while dst_idx < dst_size and src_idx < src_size:
        ctrl_byte = src[src_idx]
        src_idx += 1
        
        bit7 = (ctrl_byte >> 7) & 1
        bit6 = (ctrl_byte >> 6) & 1
        count = (ctrl_byte & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                # FILL操作
                if src_idx < src_size:
                    data_byte = src[src_idx]
                    src_idx += 1
                    
                    if mode == "DIRECT":
                        fill_val = data_byte
                    elif mode == "REMAP":
                        fill_val = value_1 + ((byte1_value_1 + data_byte) & 7)
                        fill_val = fill_val & 0xFF
                    else:
                        fill_val = mono_value
                    
                    for _ in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = fill_val
                            dst_idx += 1
                    ops.append(f"FILL({count}, val=0x{fill_val:02x})")
            else:
                # bit7=0, bit6=1 → COPY (特殊)
                # 根据汇编代码：count = count - cx - cx (双倍count？)
                # 然后循环写入
                copied = []
                if src_idx < src_size:
                    data_byte = src[src_idx]
                    src_idx += 1
                    
                    if mode == "DIRECT":
                        val = data_byte
                    elif mode == "REMAP":
                        val = value_1 + ((byte1_value_1 + data_byte) & 7)
                        val = val & 0xFF
                    else:
                        val = mono_value
                    
                    # 注意：这里count可能需要调整
                    actual_count = count
                    for _ in range(actual_count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = val
                            dst_idx += 1
                            copied.append(val)
                    ops.append(f"COPY_SPEC({actual_count}, val=0x{val:02x})")
        else:
            # bit7=1
            if bit6 == 0:
                # COPY操作 (标准)
                copied = []
                for _ in range(count):
                    if dst_idx < dst_size and src_idx < src_size:
                        data_byte = src[src_idx]
                        src_idx += 1
                        
                        if mode == "DIRECT":
                            val = data_byte
                        elif mode == "REMAP":
                            val = value_1 + ((byte1_value_1 + data_byte) & 7)
                            val = val & 0xFF
                        else:
                            val = mono_value
                        
                        dst[dst_idx] = val
                        dst_idx += 1
                        copied.append(val)
                ops.append(f"COPY({count})")
            else:
                # SKIP操作
                dst_idx += count
                ops.append(f"SKIP({count})")
    
    return dst, ops


if __name__ == "__main__":
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
    
    idx1_start = offsets[1]
    idx1_end = offsets[2]
    
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(idx1_start)
        idx1_data = f.read(idx1_end - idx1_start)
    
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    byte4 = idx1_data[4]
    byte5 = idx1_data[5] if len(idx1_data) > 5 else 0
    
    if byte5 != 0:
        header_size = 8
        palette_window = byte4 | (byte5 << 8)
        rle_data = idx1_data[8:]
    else:
        header_size = 5
        palette_window = byte4
        rle_data = idx1_data[5:]
    
    print(f"索引1: {w}x{h}, 头大小: {header_size}, 调色板窗口: {palette_window}")
    print(f"RLE数据大小: {len(rle_data)}")
    print(f"RLE前20字节: {rle_data[:20].hex()}")
    
    expected = w * h
    decoded, ops = decompress_rle_assembly_exact(rle_data, expected, -1)
    
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"\n非零像素: {non_zero}/{expected}")
    
    print(f"\n前15个操作:")
    for i, op in enumerate(ops[:15]):
        print(f"  {i}: {op}")
    
    print(f"\n图像预览:")
    for row in range(min(h, 24)):
        line = "  "
        for col in range(min(w, 24)):
            idx = row * w + col
            if idx < len(decoded):
                val = decoded[idx]
                line += "." if val == 0 else "#"
        print(line)
