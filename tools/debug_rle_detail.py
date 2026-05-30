"""
详细分析索引1的RLE解码问题
根据MCP sub_4E98D汇编代码精确实现
"""
import struct

def analyze_idx1():
    # 读取FDOTHER.DAT
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
    
    # 索引1的数据
    start = offsets[1]
    end = offsets[2]
    
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(start)
        idx1_data = f.read(end - start)
    
    print(f"索引1数据大小: {len(idx1_data)} 字节")
    print(f"前32字节: {idx1_data[:32].hex()}")
    
    # 解析头
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    print(f"宽: {w}, 高: {h}, 预期像素: {w*h}")
    
    # 检查字节5
    byte5 = idx1_data[5]
    print(f"字节5: 0x{byte5:02x} ({byte5})")
    
    if byte5 != 0:
        # 8字节头
        header_size = 8
        palette_window = idx1_data[4] | (idx1_data[5] << 8)
        rle_data = idx1_data[8:]
    else:
        # 5字节头
        header_size = 5
        palette_window = idx1_data[4]
        rle_data = idx1_data[5:]
    
    print(f"头大小: {header_size}, 调色板窗口: {palette_window}")
    print(f"RLE数据大小: {len(rle_data)}")
    
    # RLE解码 - 根据MCP sub_4E98D精确实现
    def decompress_rle_mcp(src, dst_size, palette_window=-1):
        """
        根据MCP sub_4E98D汇编代码精确实现
        使用左移进位方式判断bit7和bit6
        """
        dst = [0] * dst_size
        dst_idx = 0
        src_idx = 0
        src_size = len(src)
        
        ops = []
        
        while dst_idx < dst_size and src_idx < src_size:
            ctrl_byte = src[src_idx]
            src_idx += 1
            
            # 使用左移进位方式
            # bit7 = (ctrl_byte >> 7) & 1
            # bit6 = (ctrl_byte >> 6) & 1
            bit7 = 1 if ctrl_byte & 0x80 else 0
            bit6 = 1 if ctrl_byte & 0x40 else 0
            count = (ctrl_byte & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL: 读取下一个字节作为填充值，填充count个像素
                    if src_idx < src_size:
                        fill_val = src[src_idx]
                        src_idx += 1
                        if palette_window != -1:
                            fill_val = (palette_window + fill_val) & 0xFF
                        for _ in range(count):
                            if dst_idx < dst_size:
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                        ops.append(f"FILL({count}, val=0x{fill_val:02x})")
                else:
                    # SKIP: 跳过count个像素
                    dst_idx += count
                    ops.append(f"SKIP({count})")
            else:
                if bit6 == 0:
                    # COPY: 复制count个字节
                    copied = []
                    for _ in range(count):
                        if dst_idx < dst_size and src_idx < src_size:
                            val = src[src_idx]
                            src_idx += 1
                            if palette_window != -1:
                                val = (palette_window + val) & 0xFF
                            dst[dst_idx] = val
                            dst_idx += 1
                            copied.append(val)
                    ops.append(f"COPY({count})")
                else:
                    # SKIP: 跳过count个像素
                    dst_idx += count
                    ops.append(f"SKIP({count})")
        
        return dst, ops
    
    expected_pixels = w * h
    decoded, ops = decompress_rle_mcp(rle_data, expected_pixels, palette_window)
    
    print(f"\n解码操作总数: {len(ops)}")
    print(f"解码像素数: {len(decoded)}/{expected_pixels}")
    
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"非零像素: {non_zero}")
    
    # 显示前20个操作
    print(f"\n前20个RLE操作:")
    for i, op in enumerate(ops[:20]):
        print(f"  {i}: {op}")
    
    # 显示图像
    print(f"\n解码图像预览:")
    for row in range(h):
        line = "    "
        for col in range(w):
            idx = row * w + col
            if idx < len(decoded):
                val = decoded[idx]
                line += "." if val == 0 else "#"
        print(line)
    
    return decoded, w, h

if __name__ == "__main__":
    decoded, w, h = analyze_idx1()
