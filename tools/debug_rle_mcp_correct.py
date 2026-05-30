"""
根据MCP sub_4E98D汇编代码精确实现RLE解码器
"""
import struct

def decompress_rle_mcp_correct(src, dst_size, value_1):
    """
    根据MCP sub_4E98D汇编代码精确实现
    
    根据反编译代码分析：
    - value_1 == -1: 直接模式，直接读取像素值
    - value_1 > 0xFF: 重映射模式，使用调色板重映射
    - value_1 <= 0xFF: 单色模式，使用固定颜色
    
    参数:
        src: RLE源数据
        dst_size: 目标像素数 (width * height)
        value_1: 调色板窗口参数
    
    返回:
        解码后的像素数组
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
        # 在单色模式下，value_1被复制到ah和al
        # mov ah, al 指令
        mono_value = value_1
    
    print(f"解码模式: {mode}, value_1={value_1}")
    
    while dst_idx < dst_size and src_idx < src_size:
        ctrl_byte = src[src_idx]
        src_idx += 1
        
        # 根据汇编代码：shl cl, 1 / jb 判断bit7
        bit7_set = (ctrl_byte & 0x80) != 0
        # 再次shl cl, 1 / jb 判断bit6
        bit6_set = (ctrl_byte & 0x40) != 0
        
        # count = (ctrl_byte & 0x3F) + 1
        count = (ctrl_byte & 0x3F) + 1
        
        if not bit7_set:
            if not bit6_set:
                # FILL操作
                if mode == "DIRECT":
                    # 直接模式：读取下一个字节作为填充值
                    if src_idx < src_size:
                        fill_val = src[src_idx]
                        src_idx += 1
                        for _ in range(count):
                            if dst_idx < dst_size:
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                        ops.append(f"FILL({count}, val=0x{fill_val:02x})")
                elif mode == "REMAP":
                    # 重映射模式：value = value_1 + ((BYTE1(value_1) + v20) & 7)
                    if src_idx < src_size:
                        v20 = src[src_idx]
                        src_idx += 1
                        fill_val = value_1 + ((byte1_value_1 + v20) & 7)
                        fill_val = fill_val & 0xFF
                        for _ in range(count):
                            if dst_idx < dst_size:
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                        ops.append(f"FILL({count}, val=0x{fill_val:02x}, remap)")
                else:
                    # 单色模式：使用固定颜色
                    for _ in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = mono_value
                            dst_idx += 1
                    ops.append(f"FILL({count}, val=0x{mono_value:02x}, mono)")
            else:
                # SKIP操作
                dst_idx += count
                ops.append(f"SKIP({count})")
        else:
            if not bit6_set:
                # COPY操作
                copied = []
                for _ in range(count):
                    if dst_idx < dst_size and src_idx < src_size:
                        val = src[src_idx]
                        src_idx += 1
                        if mode == "DIRECT":
                            pass  # 直接使用val
                        elif mode == "REMAP":
                            val = value_1 + ((byte1_value_1 + val) & 7)
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


def analyze_resource(index, filepath="game/FDOTHER.DAT"):
    """分析指定索引的资源"""
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
    print(f"前32字节: {res_data[:32].hex()}")
    
    # 解析Tile头
    w = res_data[0] | (res_data[1] << 8)
    h = res_data[2] | (res_data[3] << 8)
    print(f"尺寸: {w}x{h}, 预期像素: {w*h}")
    
    # 检测头格式
    byte4 = res_data[4]
    byte5 = res_data[5] if len(res_data) > 5 else 0
    
    if byte5 != 0:
        # 8字节头
        header_size = 8
        palette_window = byte4 | (byte5 << 8)
        rle_data = res_data[8:]
    else:
        # 5字节头
        header_size = 5
        palette_window = byte4
        rle_data = res_data[5:]
    
    print(f"头格式: {header_size}字节, 调色板窗口原始值: {palette_window} (0x{palette_window:04x})")
    print(f"RLE数据大小: {len(rle_data)}")
    print(f"RLE前16字节: {rle_data[:16].hex()}")
    
    expected_pixels = w * h
    
    # 测试不同的value_1参数
    print(f"\n--- 测试value_1=-1 (直接模式) ---")
    decoded_direct, ops_direct = decompress_rle_mcp_correct(rle_data, expected_pixels, -1)
    non_zero_direct = sum(1 for p in decoded_direct if p != 0)
    print(f"非零像素: {non_zero_direct}/{expected_pixels}")
    
    print(f"\n--- 测试value_1={palette_window} ---")
    if palette_window > 0xFF:
        print(f"使用重映射模式")
    else:
        print(f"使用单色模式")
    decoded_pal, ops_pal = decompress_rle_mcp_correct(rle_data, expected_pixels, palette_window)
    non_zero_pal = sum(1 for p in decoded_pal if p != 0)
    print(f"非零像素: {non_zero_pal}/{expected_pixels}")
    
    # 显示前10个操作 (直接模式)
    print(f"\n前10个RLE操作 (直接模式):")
    for i, op in enumerate(ops_direct[:10]):
        print(f"  {i}: {op}")
    
    # 显示图像预览 (直接模式)
    print(f"\n解码图像预览 (直接模式):")
    for row in range(min(h, 24)):
        line = "  "
        for col in range(min(w, 24)):
            idx = row * w + col
            if idx < len(decoded_direct):
                val = decoded_direct[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    return decoded_direct, w, h, palette_window, rle_data


if __name__ == "__main__":
    print("=" * 60)
    print("根据MCP汇编代码精确分析索引1 (图标 24x24)")
    print("=" * 60)
    decoded, w, h, palette_window, rle_data = analyze_resource(1)
