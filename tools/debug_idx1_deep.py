"""
深入分析索引1的Tile头结构和RLE数据
"""
import struct

def analyze_idx1_deep():
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
    
    print(f"索引1原始数据:")
    print(f"大小: {len(idx1_data)}")
    print(f"完整数据(前100字节hex): {idx1_data[:100].hex()}")
    
    # 解析前几个字节
    print(f"\n逐字节分析:")
    for i in range(min(20, len(idx1_data))):
        print(f"  字节{i}: 0x{idx1_data[i]:02x} ({idx1_data[i]})")
    
    # 尝试不同的头格式解析
    print(f"\n=== 尝试5字节头格式 ===")
    w5 = idx1_data[0] | (idx1_data[1] << 8)
    h5 = idx1_data[2] | (idx1_data[3] << 8)
    pal5 = idx1_data[4]
    print(f"宽: {w5}, 高: {h5}, 调色板窗口: {pal5}")
    rle5 = idx1_data[5:]
    print(f"RLE数据大小: {len(rle5)}")
    print(f"RLE前20字节: {rle5[:20].hex()}")
    
    print(f"\n=== 尝试8字节头格式 ===")
    if len(idx1_data) >= 8:
        w8 = idx1_data[0] | (idx1_data[1] << 8)
        h8 = idx1_data[2] | (idx1_data[3] << 8)
        pal8 = idx1_data[4] | (idx1_data[5] << 8)
        extra8 = idx1_data[6] | (idx1_data[7] << 8)
        print(f"宽: {w8}, 高: {h8}, 调色板窗口: {pal8}, 额外字段: {extra8}")
        rle8 = idx1_data[8:]
        print(f"RLE数据大小: {len(rle8)}")
        print(f"RLE前20字节: {rle8[:20].hex()}")
    
    # 分析RLE数据模式
    print(f"\n=== RLE数据分析 ===")
    # 使用5字节头的RLE数据
    rle = rle5
    print(f"RLE控制字节序列(前30个):")
    idx = 0
    count = 0
    while idx < len(rle) and count < 30:
        ctrl = rle[idx]
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        op_count = (ctrl & 0x3F) + 1
        
        op_type = "UNKNOWN"
        if bit7 == 0:
            if bit6 == 0:
                op_type = "FILL"
            else:
                op_type = "SKIP"
        else:
            if bit6 == 0:
                op_type = "COPY"
            else:
                op_type = "SKIP"
        
        extra = ""
        if op_type == "FILL" or op_type == "COPY":
            if idx + 1 < len(rle):
                extra = f", 数据字节: 0x{rle[idx+1]:02x}"
        
        print(f"  偏移{idx}: 0x{ctrl:02x} -> {op_type}(count={op_count}){extra}")
        
        if op_type == "FILL":
            idx += 2  # ctrl + 1 data byte
        elif op_type == "COPY":
            idx += 1 + op_count  # ctrl + count data bytes
        else:  # SKIP
            idx += 1  # only ctrl byte
        
        count += 1

if __name__ == "__main__":
    analyze_idx1_deep()
