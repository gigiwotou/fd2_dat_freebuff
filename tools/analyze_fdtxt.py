import struct

def read_dat(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data[:6] != b'LLLLLL':
        print('不是有效的DAT文件')
        return None, None
    offset_count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(offset_count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    return data, offsets

def analyze_resource(data, offsets, index):
    if index < 0 or index >= len(offsets) - 1:
        return None
    
    start = offsets[index]
    end = offsets[index + 1]
    res = data[start:end]
    
    results = []
    
    # 方式1: 作为WORD数组
    if len(res) % 2 == 0:
        words = []
        for i in range(0, len(res), 2):
            word = struct.unpack_from('<h', res, i)[0]
            words.append(word)
        
        if any(w > 0 and w < 2000 for w in words):
            results.append(('word_array', words))
    
    results.append(('byte_array', list(res)))
    
    # 方式3: 尝试直接作为GBK字符串
    try:
        gbk_str = res.decode('gbk', errors='ignore')
        if len(gbk_str.strip()) > 0:
            results.append(('gbk', gbk_str))
    except:
        pass
    
    # 方式4: 尝试作为ASCII字符串
    try:
        ascii_str = res.decode('ascii', errors='ignore')
        if len(ascii_str.strip()) > 0:
            results.append(('ascii', ascii_str))
    except:
        pass
    
    return {
        'index': index,
        'size': len(res),
        'start': start,
        'end': end,
        'decodings': results
    }

def main():
    data, offsets = read_dat('game/FDTXT.DAT')
    if data:
        print(f'FDTXT.DAT 索引数: {len(offsets) - 1}')
        
        with open('output/fdtxt_analysis.txt', 'w', encoding='utf-8') as out:
            for i in range(len(offsets) - 1):
                analysis = analyze_resource(data, offsets, i)
                if analysis:
                    out.write(f'=== 索引 {i} ===\n')
                    out.write(f'大小: {analysis["size"]} 字节\n')
                    out.write(f'偏移: 0x{analysis["start"]:08X} - 0x{analysis["end"]:08X}\n')
                    
                    for dec_type, content in analysis['decodings']:
                        out.write(f'  [{dec_type}]:\n')
                        if isinstance(content, list):
                            if len(content) > 32:
                                out.write(f'    {content[:32]}... (共{len(content)}个)\n')
                            else:
                                out.write(f'    {content}\n')
                        else:
                            if len(content) > 100:
                                out.write(f'    {content[:100]}...\n')
                            else:
                                out.write(f'    {content}\n')
                    
                    out.write('\n')
        
        print('分析结果已保存到 output/fdtxt_analysis.txt')

if __name__ == '__main__':
    main()