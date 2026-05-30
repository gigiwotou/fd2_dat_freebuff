"""
根据MCP sub_4E98D汇编代码精确分析RLE解码
"""
import struct

def decompress_rle_from_assembly(src, dst_size, value_1):
    """
    根据MCP sub_4E98D汇编代码精确实现
    
    参数:
        src: RLE源数据
        dst_size: 目标像素数 (width * height)
        value_1: 调色板窗口参数 (-1表示不应用调色板)
    
    返回:
        解码后的像素数组
    """
    dst = [0] * dst_size
    dst_idx = 0
    src_idx = 0
    src_size = len(src)
    
    ops = []
    
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
                if value_1 == -1:
                    # value_1 == -1: 直接读取下一个字节作为填充值
                    if src_idx < src_size:
                        fill_val = src[src_idx]
                        src_idx += 1
                        for _ in range(count):
                            if dst_idx < dst_size:
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                        ops.append(f"FILL({count}, val=0x{fill_val:02x})")
                else:
                    # value_1 != -1: 使用公式计算填充值
                    # value = value_1 + ((BYTE1(value_1) + v20) & 7)
                    # BYTE1(value_1)是value_1的高字节
                    # v20是从src读取的字节
                    if src_idx < src_size:
                        v20 = src[src_idx]
                        src_idx += 1
                        byte1_value_1 = (value_1 >> 8) & 0xFF
                        fill_val = value_1 + ((byte1_value_1 + v20) & 7)
                        # 注意：这里fill_val可能超过255，需要& 0xFF
                        fill_val = fill_val & 0xFF
                        for _ in range(count):
                            if dst_idx < dst_size:
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                        ops.append(f"FILL({count}, val=0x{fill_val:02x}, formula)")
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
                        if value_1 != -1:
                            # 应用调色板窗口公式
                            byte1_value_1 = (value_1 >> 8) & 0xFF
                            val = value_1 + ((byte1_value_1 + val) & 7)
                            val = val & 0xFF
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
    
    # 尝试不同的解码方式
    expected_pixels = w * h
    
    # 方式1: value_1 = -1 (不应用调色板)
    print(f"\n--- 解码方式1: value_1=-1 ---")
    decoded1, ops1 = decompress_rle_from_assembly(rle_data, expected_pixels, -1)
    non_zero1 = sum(1 for p in decoded1 if p != 0)
    print(f"非零像素: {non_zero1}/{expected_pixels}")
    
    # 方式2: value_1 = palette_window (原始值)
    print(f"\n--- 解码方式2: value_1={palette_window} ---")
    decoded2, ops2 = decompress_rle_from_assembly(rle_data, expected_pixels, palette_window)
    non_zero2 = sum(1 for p in decoded2 if p != 0)
    print(f"非零像素: {non_zero2}/{expected_pixels}")
    
    # 方式3: value_1 = palette_window作为16位值
    print(f"\n--- 解码方式3: value_1={palette_window} (16位) ---")
    # 检查palette_window是否应该作为16位值使用
    # 根据汇编代码，value_1是int类型，可能是16位或32位
    
    # 显示前10个操作
    print(f"\n前10个RLE操作:")
    for i, op in enumerate(ops1[:10]):
        print(f"  {i}: {op}")
    
    # 显示图像预览 (方式1)
    print(f"\n解码图像预览 (方式1):")
    for row in range(min(h, 24)):
        line = "  "
        for col in range(min(w, 24)):
            idx = row * w + col
            if idx < len(decoded1):
                val = decoded1[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    # 显示图像预览 (方式2)
    print(f"\n解码图像预览 (方式2):")
    for row in range(min(h, 24)):
        line = "  "
        for col in range(min(w, 24)):
            idx = row * w + col
            if idx < len(decoded2):
                val = decoded2[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    return decoded1, decoded2, w, h


if __name__ == "__main__":
    # 分析索引1
    print("=" * 50)
    print("分析索引1 (图标 24x24)")
    print("=" * 50)
    analyze_resource(1)
    
    # 分析索引2的第一个子资源
    print("\n" + "=" * 50)
    print("分析索引2 (偏移表)")
    print("=" * 50)
    
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
    
    idx2_start = offsets[2]
    idx2_end = offsets[3]
    
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(idx2_start)
        idx2_data = f.read(idx2_end - idx2_start)
    
    print(f"索引2大小: {len(idx2_data)} 字节")
    
    # 解析偏移表 (前312字节是78个偏移值)
    offset_table_size = 312
    offset_count = 78
    
    offsets_list = []
    for i in range(offset_count):
        addr = i * 4
        if addr + 4 <= len(idx2_data):
            off = idx2_data[addr] | (idx2_data[addr+1] << 8) | \
                  (idx2_data[addr+2] << 16) | (idx2_data[addr+3] << 24)
            offsets_list.append(off)
    
    print(f"偏移表: {len(offsets_list)}个偏移值")
    print(f"前5个偏移: {[hex(o) for o in offsets_list[:5]]}")
    
    # 分析第一个子资源
    if len(offsets_list) >= 2:
        sub_start = offsets_list[0]
        sub_end = offsets_list[1]
        sub_size = sub_end - sub_start
        
        print(f"\n第一个子资源: 偏移{sub_start}-{sub_end}, 大小{sub_size}")
        
        if sub_start + sub_size <= len(idx2_data):
            sub_data = idx2_data[sub_start:sub_start + sub_size]
            print(f"子资源数据大小: {len(sub_data)}")
            print(f"前16字节: {sub_data[:16].hex()}")
            
            # 尝试解析为Tile
            if len(sub_data) >= 5:
                w = sub_data[0] | (sub_data[1] << 8)
                h = sub_data[2] | (sub_data[3] << 8)
                print(f"可能的Tile尺寸: {w}x{h}")
                
                byte4 = sub_data[4]
                byte5 = sub_data[5] if len(sub_data) > 5 else 0
                
                if byte5 != 0:
                    header_size = 8
                    palette_window = byte4 | (byte5 << 8)
                    rle_data = sub_data[8:]
                else:
                    header_size = 5
                    palette_window = byte4
                    rle_data = sub_data[5:]
                
                print(f"头格式: {header_size}字节, 调色板窗口: {palette_window}")
                
                expected_pixels = w * h
                decoded, ops = decompress_rle_from_assembly(rle_data, expected_pixels, -1)
                non_zero = sum(1 for p in decoded if p != 0)
                print(f"非零像素: {non_zero}/{expected_pixels}")
                
                print(f"\n子资源图像预览:")
                for row in range(min(h, 20)):
                    line = "  "
                    for col in range(min(w, 24)):
                        idx = row * w + col
                        if idx < len(decoded):
                            val = decoded[idx]
                            line += "." if val == 0 else "#"
                    print(line)
