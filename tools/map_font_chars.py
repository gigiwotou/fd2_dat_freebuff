import struct
import sys

def map_font_chars(dat_path):
    """加载字体并建立索引->字符的映射"""
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # 解析DAT文件头
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源集数量: {count}")
    
    # 找到FONT.DAT资源（索引3）
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 假设字体在索引3
    font_start = offsets[3]
    font_end = offsets[4] if 4 < count else len(data)
    font_size = font_end - font_start
    
    char_count = font_size // 32  # 每个字符32字节
    print(f"字体大小: {font_size} 字节")
    print(f"字符数量: {char_count}")
    
    # 创建索引映射
    font_data = data[font_start:font_end]
    
    # 常用标点符号的索引
    # 根据游戏常见编码，查找特定字符
    chars_to_find = {
        '「': None,
        '」': None,
        '『': None,
        '』': None,
        '，': None,
        '。': None,
        '！': None,
        '？': None,
        '、': None,
        '：': None,
        '；': None,
        '·': None,
    }
    
    # 检查特定索引（根据之前的分析）
    test_indices = [557, 558, 559, 560, 589, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610]
    
    print(f"\n检查特定索引的字符:")
    for idx in test_indices:
        if idx < char_count:
            cdata = font_data[idx * 32:(idx + 1) * 32]
            # 计算位图特征
            pixel_count = 0
            for row in range(16):
                bits = struct.unpack_from('<H', cdata, row * 2)[0]
                bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF)
                for col in range(16):
                    if bits & (1 << (15 - col)):
                        pixel_count += 1
            print(f"  索引 {idx}: {pixel_count} 像素点")
        else:
            print(f"  索引 {idx}: 超出范围")

if __name__ == '__main__':
    map_font_chars('game/FDOTHER.DAT')
