"""
对比Python和viewer的RLE解码结果
"""
import struct

def decompress_rle_correct(src, dst_size):
    """根据汇编代码精确实现RLE解码（value_1=-1模式）"""
    dst = [0] * dst_size
    dst_idx = 0
    src_idx = 0
    src_size = len(src)
    
    while dst_idx < dst_size and src_idx < src_size:
        ctrl = src[src_idx]
        src_idx += 1
        
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        count = (ctrl & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                # FILL: 读取1个值，填充count个位置
                if src_idx < src_size:
                    val = src[src_idx]
                    src_idx += 1
                    for _ in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = val
                            dst_idx += 1
            else:
                # COPY特殊: 读取1个值，循环写入count次
                if src_idx < src_size:
                    val = src[src_idx]
                    src_idx += 1
                    for _ in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = val
                            dst_idx += 1
        else:
            if bit6 == 0:
                # COPY标准: 从src复制count个字节
                for _ in range(count):
                    if dst_idx < dst_size and src_idx < src_size:
                        dst[dst_idx] = src[src_idx]
                        src_idx += 1
                        dst_idx += 1
            else:
                # SKIP: 跳过count个位置
                dst_idx += count
    
    return dst

def analyze_idx1_with_palette_window():
    """使用正确的palette_window分析索引1"""
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
    
    # 解析5字节头
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    palette_window = idx1_data[4]
    
    rle_data = idx1_data[5:]
    expected_pixels = w * h
    
    print(f"索引1: {w}x{h}, palette_window={palette_window}")
    print(f"RLE数据大小: {len(rle_data)}")
    
    # 解码
    decoded = decompress_rle_correct(rle_data, expected_pixels)
    non_zero = sum(1 for p in decoded if p != 0)
    
    print(f"非零像素: {non_zero}/{expected_pixels}")
    
    # 应用palette_window
    print(f"\n应用palette_window={palette_window}后的值:")
    adjusted = [(palette_window + p) & 0xFF for p in decoded]
    adjusted_non_zero = sum(1 for p in adjusted if p != 0)
    print(f"调整后非零像素: {adjusted_non_zero}/{expected_pixels}")
    
    # 打印原始值和应用palette_window后的值对比
    print(f"\n前20个像素值对比:")
    for i in range(min(20, expected_pixels)):
        print(f"  [{i}] 原始: {decoded[i]:3d} (0x{decoded[i]:02x}) -> 调整后: {adjusted[i]:3d} (0x{adjusted[i]:02x})")
    
    # 打印图像预览（应用palette_window后）
    print(f"\n图像预览(应用palette_window后):")
    for row in range(h):
        line = "  "
        for col in range(w):
            idx = row * w + col
            val = adjusted[idx]
            line += "." if val == 0 else "#"
        print(line)
    
    # 统计不同值的分布
    from collections import Counter
    value_counts = Counter(adjusted)
    print(f"\n像素值分布(前10):")
    for val, count in value_counts.most_common(10):
        print(f"  值{val:3d} (0x{val:02x}): {count}个像素")
    
    return decoded, adjusted, w, h, palette_window

if __name__ == "__main__":
    analyze_idx1_with_palette_window()
