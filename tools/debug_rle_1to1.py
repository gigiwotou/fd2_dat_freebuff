"""
根据MCP反编译代码1:1实现RLE解码
"""
import struct

def decompress_rle_1to1(src, dst_size, value_1):
    """
    根据MCP sub_4E98D反编译代码1:1实现
    
    参数:
        src: RLE源数据（不包含宽高头）
        dst_size: 目标像素数 (width * height)
        value_1: 调色板窗口参数
    
    返回:
        解码后的像素数组
    """
    dst = [0] * dst_size
    dst_idx = 0
    src_idx = 0
    src_size = len(src)
    
    # 判断模式
    if value_1 == -1:
        mode = "DIRECT"
    elif value_1 > 0xFF:
        mode = "REMAP"
        byte1_value_1 = (value_1 >> 8) & 0xFF
        byte0_value_1 = value_1 & 0xFF
    else:
        mode = "MONO"
        mono_value = value_1
    
    print(f"模式: {mode}, value_1={value_1}")
    
    while dst_idx < dst_size and src_idx < src_size:
        ctrl_byte = src[src_idx]
        src_idx += 1
        
        # 根据反编译代码精确判断
        # __CFSHL__(value, 1) 判断bit7（CF标志位）
        bit7 = 1 if ctrl_byte & 0x80 else 0
        # __CFSHL__(v12, 1) 判断bit6
        bit6 = 1 if ctrl_byte & 0x40 else 0
        
        # LOBYTE(count_1) = ((unsigned __int8)count_1 >> 2) + 1
        # count_1 = 4 * value, 然后 >> 2 + 1 = (ctrl & 0x3F) + 1
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
            else:
                # COPY特殊操作
                # count = count - count_1 - count_1 (双倍？)
                # 但反编译代码中count_1被重新计算
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
                    
                    # 注意：反编译代码中是循环写入
                    # do { v14 = dst + 1; *v14 = value; dst = v14 + 1; --count_1; } while (count_1);
                    # 但这里的循环似乎有问题，让我按照C代码逻辑
                    for _ in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = val
                            dst_idx += 1
        else:
            # bit7 == 1
            if bit6 == 0:
                # COPY标准操作
                # qmemcpy(dst, src, count_1)
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
            else:
                # SKIP操作
                # dst += count_1
                dst_idx += count
    
    return dst


def analyze_idx1_with_1to1():
    """使用1:1实现的RLE解码分析索引1"""
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
    
    print(f"索引1数据大小: {len(idx1_data)}")
    print(f"前50字节hex: {idx1_data[:50].hex()}")
    
    # 解析头
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
    
    print(f"尺寸: {w}x{h}, 头大小: {header_size}, 调色板窗口: {palette_window}")
    print(f"RLE数据大小: {len(rle_data)}")
    
    expected_pixels = w * h
    decoded = decompress_rle_1to1(rle_data, expected_pixels, -1)
    
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"\n非零像素: {non_zero}/{expected_pixels}")
    
    print(f"\n图像预览:")
    for row in range(min(h, 24)):
        line = "  "
        for col in range(min(w, 24)):
            idx = row * w + col
            if idx < len(decoded):
                val = decoded[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    return decoded, w, h


if __name__ == "__main__":
    analyze_idx1_with_1to1()
