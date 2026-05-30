"""
分析索引1的真实结构
"""
import struct

def analyze_idx1_real_structure():
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
    
    print(f"索引1数据大小: {len(idx1_data)} 字节")
    print(f"完整数据(前100字节): {idx1_data[:100].hex()}")
    
    # 解析5字节头
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    palette_window = idx1_data[4]
    
    print(f"\n头: w={w}, h={h}, palette_window={palette_window}")
    
    # 字节5开始的数据
    remaining_data = idx1_data[5:]
    print(f"\n剩余数据大小: {len(remaining_data)} 字节")
    print(f"剩余数据(前80字节): {remaining_data[:80].hex()}")
    
    # 尝试不同方式解析
    print(f"\n=== 尝试解析为4字节偏移量(小端) ===")
    offset_count = len(remaining_data) // 4
    print(f"可能的偏移量数量: {offset_count}")
    
    offsets_list = []
    for i in range(min(30, offset_count)):
        addr = i * 4
        # 小端读取
        off = struct.unpack('<I', remaining_data[addr:addr+4])[0]
        offsets_list.append(off)
    
    print(f"前30个偏移量:")
    for i, off in enumerate(offsets_list):
        print(f"  [{i}] 0x{off:08x} = {off}")
    
    # 检查偏移量是否在合理范围
    if offsets_list:
        max_off = max(offsets_list[:30])
        print(f"\n前30个偏移量的最大值: {max_off}")
        print(f"索引1数据大小: {len(idx1_data)}")
        
        if max_off < len(idx1_data):
            print("✓ 偏移量在数据范围内")
        else:
            print("✗ 偏移量超出数据范围")
        
        # 检查是否是递增的
        is_increasing = all(offsets_list[i] < offsets_list[i+1] for i in range(len(offsets_list)-1))
        print(f"偏移量是否递增: {is_increasing}")
    
    # 另一种可能：索引1就是普通Tile，但RLE数据格式特殊
    print(f"\n=== 尝试作为普通Tile解析 ===")
    rle_data = idx1_data[5:]
    print(f"RLE数据大小: {len(rle_data)}")
    print(f"RLE前20字节: {rle_data[:20].hex()}")
    
    # 手动解析RLE
    print(f"\nRLE操作解析:")
    src_idx = 0
    count = 0
    while src_idx < len(rle_data) and count < 30:
        ctrl = rle_data[src_idx]
        src_idx += 1
        
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        op_count = (ctrl & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                op_type = "FILL"
                if src_idx < len(rle_data):
                    data_val = rle_data[src_idx]
                    src_idx += 1
                    print(f"  [{count}] 0x{ctrl:02x} -> FILL({op_count}, val=0x{data_val:02x})")
                else:
                    print(f"  [{count}] 0x{ctrl:02x} -> FILL({op_count}) [数据不足]")
            else:
                op_type = "COPY"
                if src_idx < len(rle_data):
                    data_val = rle_data[src_idx]
                    src_idx += 1
                    print(f"  [{count}] 0x{ctrl:02x} -> COPY({op_count}, val=0x{data_val:02x})")
                else:
                    print(f"  [{count}] 0x{ctrl:02x} -> COPY({op_count}) [数据不足]")
        else:
            if bit6 == 0:
                op_type = "COPY"
                # 读取op_count个字节
                print(f"  [{count}] 0x{ctrl:02x} -> COPY({op_count})")
                src_idx += op_count
            else:
                op_type = "SKIP"
                print(f"  [{count}] 0x{ctrl:02x} -> SKIP({op_count})")
        
        count += 1
    
    # 计算解码后的非零像素
    print(f"\n=== 计算解码后的像素 ===")
    expected_pixels = w * h
    dst = [0] * expected_pixels
    dst_idx = 0
    src_idx = 0
    
    while dst_idx < expected_pixels and src_idx < len(rle_data):
        ctrl = rle_data[src_idx]
        src_idx += 1
        
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        op_count = (ctrl & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                # FILL
                if src_idx < len(rle_data):
                    val = rle_data[src_idx]
                    src_idx += 1
                    for _ in range(op_count):
                        if dst_idx < expected_pixels:
                            dst[dst_idx] = val
                            dst_idx += 1
            else:
                # COPY
                if src_idx < len(rle_data):
                    val = rle_data[src_idx]
                    src_idx += 1
                    for _ in range(op_count):
                        if dst_idx < expected_pixels:
                            dst[dst_idx] = val
                            dst_idx += 1
        else:
            if bit6 == 0:
                # COPY
                for _ in range(op_count):
                    if dst_idx < expected_pixels and src_idx < len(rle_data):
                        dst[dst_idx] = rle_data[src_idx]
                        src_idx += 1
                        dst_idx += 1
            else:
                # SKIP
                dst_idx += op_count
    
    non_zero = sum(1 for p in dst if p != 0)
    print(f"非零像素: {non_zero}/{expected_pixels}")
    
    print(f"\n图像预览:")
    for row in range(h):
        line = "  "
        for col in range(w):
            idx = row * w + col
            val = dst[idx]
            line += "." if val == 0 else "#"
        print(line)

if __name__ == "__main__":
    analyze_idx1_real_structure()
