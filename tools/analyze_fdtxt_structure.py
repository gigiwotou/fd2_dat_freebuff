"""分析FDTXT.DAT资源集结构，确认哪个资源集是第一关"""
import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_fdtxt():
    with open(FDTXT_PATH, 'rb') as f:
        # 文件头6字节
        header = f.read(6)
        print(f"文件头: {header.hex()}")
        
        # 资源集数量
        f.seek(6)
        count_bytes = f.read(4)
        count = struct.unpack('<I', count_bytes)[0]
        print(f"资源集总数: {count}")
        
        # 分析每个资源集
        print(f"\n=== 资源集分析 ===")
        for i in range(min(count, 10)):  # 只看前10个资源集
            offset_pos = 10 + i * 4
            f.seek(offset_pos)
            offset = struct.unpack('<I', f.read(4))[0]
            f.seek(offset_pos + 4)
            end_offset = struct.unpack('<I', f.read(4))[0]
            
            size = end_offset - offset
            f.seek(offset)
            
            # 读取子项数量
            sub_count_bytes = f.read(2)
            sub_count = struct.unpack('<h', sub_count_bytes)[0]
            
            print(f"资源集 {i}: 偏移={offset}, 大小={size}字节, 子项数={sub_count}")
            
            # 读取第一个子项的前几个字节
            if sub_count > 0:
                # 读取偏移表
                offsets = []
                for j in range(sub_count):
                    off_bytes = f.read(2)
                    off = struct.unpack('<h', off_bytes)[0]
                    offsets.append(off)
                
                # 读取第一个子项的前32字节
                f.seek(offset + offsets[0])
                data = f.read(64)
                print(f"  子项偏移: {offsets[:5]}...")  # 只显示前5个
                
                # 分析控制码
                text_preview = []
                for k in range(0, min(32, len(data)), 2):
                    word = struct.unpack('<h', data[k:k+2])[0]
                    if word == -1:
                        text_preview.append("TEXT_END")
                    elif word == -2:
                        text_preview.append("NEWLINE")
                    elif word == -3:
                        text_preview.append("WAIT_KEY")
                    elif word == -17:
                        text_preview.append("PORTRAIT_F")
                    elif word == -18:
                        text_preview.append("PORTRAIT_S")
                    elif word == -19:
                        text_preview.append("CHAR_F")
                    elif word == -20:
                        text_preview.append("CHAR_S")
                    elif 0x3000 <= word <= 0x9FFF:  # CJK字符范围
                        text_preview.append(f"[字符{word}]")
                    else:
                        text_preview.append(f"0x{word:X}")
                
                print(f"  第一个子项前32字节: {' '.join(text_preview[:10])}")
        
        print(f"\n=== 资源集33分析（如果有）===")
        if count > 33:
            for i in [1, 2, 33]:
                offset_pos = 10 + i * 4
                f.seek(offset_pos)
                offset = struct.unpack('<I', f.read(4))[0]
                f.seek(offset_pos + 4)
                end_offset = struct.unpack('<I', f.read(4))[0]
                
                size = end_offset - offset
                f.seek(offset)
                
                sub_count_bytes = f.read(2)
                sub_count = struct.unpack('<h', sub_count_bytes)[0]
                
                print(f"资源集 {i}: 偏移={offset}, 大小={size}字节, 子项数={sub_count}")

if __name__ == "__main__":
    analyze_fdtxt()
