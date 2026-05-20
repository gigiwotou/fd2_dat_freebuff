import struct
import sys

def analyze_fdtxt_item(dat_path, res_idx, sub_idx):
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # Parse header
    file_size = len(data)
    count = struct.unpack_from('<I', data, 6)[0]
    
    print(f"文件大小: {file_size}")
    print(f"资源集数量: {count}")
    print()
    
    # Parse offsets
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    if res_idx < 0 or res_idx >= count:
        print(f"资源集索引超出范围: {res_idx}")
        return
    
    rs = offsets[res_idx]
    re = offsets[res_idx + 1] if res_idx + 1 < count else file_size
    
    print(f"资源集 {res_idx}:")
    print(f"  偏移: {rs} - {re}")
    print(f"  大小: {re - rs} 字节")
    
    # Parse sub count
    sub_count = struct.unpack_from('<h', data, rs)[0]
    print(f"  子项数量: {sub_count}")
    
    if sub_idx < 0 or sub_idx >= sub_count:
        print(f"子项索引超出范围: {sub_idx}")
        return
    
    # Parse sub offsets
    sub_offs = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', data, rs + 2 + i * 2)[0]
        sub_offs.append(off)
    
    ss = rs + sub_offs[sub_idx]
    se = rs + sub_offs[sub_idx + 1] if sub_idx + 1 < sub_count else re
    
    print(f"\n子项 {sub_idx}:")
    print(f"  文件偏移: {ss} - {se}")
    print(f"  大小: {se - ss} 字节")
    
    # Read raw bytes
    raw = data[ss:se]
    
    print(f"\n原始字节 (十六进制):")
    for i in range(0, len(raw), 16):
        chunk = raw[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  +{i:04d}: {hex_str}")
    
    # Parse as int16_t
    print(f"\n解析为 int16_t:")
    words = []
    for i in range(0, len(raw), 2):
        if i + 1 < len(raw):
            val = struct.unpack_from('<h', raw, i)[0]
            words.append(val)
    
    # Print with labels
    print(f"\n文本内容:")
    for i, val in enumerate(words):
        if val == -1:
            label = "TEXT_END"
        elif val == -2:
            label = "TEXT_NEWLINE"
        elif val == -3:
            label = "TEXT_NEWLINE2"
        elif val == -4:
            label = "TEXT_RECURSE1"
        elif val == -5:
            label = "TEXT_RECURSE2"
        elif val == -6:
            label = "TEXT_SHOW_NUM"
        elif val == -17:
            label = "TEXT_PORTRAIT_F"
        elif val == -18:
            label = "TEXT_PORTRAIT_S"
        elif val == -19:
            label = "TEXT_CHAR_F"
        elif val == -20:
            label = "TEXT_CHAR_S"
        elif val >= 0:
            label = f"CHAR({val})"
        else:
            label = f"UNKNOWN({val})"
        print(f"  [{i:3d}] {val:5d}  {label}")

if __name__ == '__main__':
    res_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    sub_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    analyze_fdtxt_item('game/FDTXT.DAT', res_idx, sub_idx)
