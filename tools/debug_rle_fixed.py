"""
根据MCP汇编代码精确实现RLE解码器 - 修正版本
"""
import struct

def decompress_rle_correct(src, dst_size, value_1):
    """
    根据MCP sub_4E98D汇编代码精确实现
    
    修正后的操作类型判断逻辑：
    - bit7=0, bit6=0: FILL (读取下一个字节作为填充值)
    - bit7=0, bit6=1: COPY (复制count个字节)
    - bit7=1, bit6=0: SKIP (跳过count个像素)
    - bit7=1, bit6=1: SKIP (跳过count个像素)
    
    参数:
        src: RLE源数据
        dst_size: 目标像素数 (width * height)
        value_1: 调色板窗口参数
    
    返回:
        解码后的像素数组和操作列表
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
        byte0_value_1 = value_1 & 0xFF
    else:
        mode = "MONO"
        mono_value = value_1
    
    print(f"解码模式: {mode}, value_1={value_1}")
    
    while dst_idx < dst_size and src_idx < src_size:
        ctrl_byte = src[src_idx]
        src_idx += 1
        
        # 根据汇编代码精确判断
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
                # COPY操作
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
            # bit7 == 1: SKIP操作
            dst_idx += count
            ops.append(f"SKIP({count})")
    
    return dst, ops


def analyze_resource_corrected(index, filepath="game/FDOTHER.DAT"):
    """分析指定索引的资源 - 使用修正后的算法"""
    with open(filepath, "rb") as f:
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
    
    if index >= len(offsets) - 1:
        print(f"索引{index}超出范围")
        return
    
    start = offsets[index]
    end = offsets[index + 1]
    
    with open(filepath, "rb") as f:
        f.seek(start)
        res_data = f.read(end - start)
    
    print(f"\n=== 资源 {index} 分析 ===")
    print(f"大小: {len(res_data)} 字节")
    
    # 解析Tile头
    w = res_data[0] | (res_data[1] << 8)
    h = res_data[2] | (res_data[3] << 8)
    print(f"尺寸: {w}x{h}, 预期像素: {w*h}")
    
    # 检测头格式
    byte4 = res_data[4]
    byte5 = res_data[5] if len(res_data) > 5 else 0
    
    if byte5 != 0:
        header_size = 8
        palette_window = byte4 | (byte5 << 8)
        rle_data = res_data[8:]
        print(f"8字节头格式, 调色板窗口: {palette_window} (0x{palette_window:04x})")
    else:
        header_size = 5
        palette_window = byte4
        rle_data = res_data[5:]
        print(f"5字节头格式, 调色板窗口: {palette_window}")
    
    print(f"RLE数据大小: {len(rle_data)}")
    print(f"RLE前16字节: {rle_data[:16].hex()}")
    
    expected_pixels = w * h
    
    # 测试直接模式 (value_1 = -1)
    print(f"\n--- 测试value_1=-1 (直接模式) ---")
    decoded, ops = decompress_rle_correct(rle_data, expected_pixels, -1)
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"非零像素: {non_zero}/{expected_pixels}")
    
    # 显示前15个操作
    print(f"\n前15个RLE操作:")
    for i, op in enumerate(ops[:15]):
        print(f"  {i}: {op}")
    
    # 显示图像预览
    print(f"\n解码图像预览:")
    for row in range(min(h, 24)):
        line = "  "
        for col in range(min(w, 24)):
            idx = row * w + col
            if idx < len(decoded):
                val = decoded[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    return decoded, w, h, palette_window, rle_data


if __name__ == "__main__":
    print("=" * 60)
    print("修正后的RLE解码器测试 - 索引1")
    print("=" * 60)
    analyze_resource_corrected(1)
