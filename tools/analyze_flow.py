"""分析FDTXT第一个资源集的子项0的完整控制流"""
import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_flow():
    with open(FDTXT_PATH, 'rb') as f:
        f.seek(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        print("=== 资源集1 子项0 完整控制流 ===\n")
        
        # 资源集1偏移
        rs = struct.unpack('<I', f.read(4))[0]
        re = struct.unpack('<I', f.read(4))[0]
        
        f.seek(rs)
        sub_count = struct.unpack('<h', f.read(2))[0]
        
        offsets = []
        for i in range(sub_count):
            off = struct.unpack('<h', f.read(2))[0]
            offsets.append(off)
        
        print(f"子项数量: {sub_count}")
        print(f"子项偏移: {offsets[:10]}...\n")
        
        # 分析子项0
        f.seek(rs + offsets[0])
        data = f.read(offsets[1] - offsets[0])
        
        pos = 0
        ctrl_map = {
            -1: "TEXT_END",
            -2: "NEWLINE",
            -3: "NEWLINE2+WAIT",
            -4: "RECURSE1",
            -5: "RECURSE2",
            -6: "SHOW_NUM",
            -17: "PORTRAIT_F",
            -18: "PORTRAIT_S",
            -19: "CHAR_F",
            -20: "CHAR_S",
        }
        
        print("控制码序列:")
        print("=" * 60)
        line_num = 0
        while pos < len(data):
            word = struct.unpack('<h', data[pos:pos+2])[0]
            pos += 2
            
            if word in ctrl_map:
                label = ctrl_map[word]
                extra = ""
                if word in [-17, -18, -19, -20]:
                    extra_val = struct.unpack('<h', data[pos:pos+2])[0]
                    extra = f" (参数={extra_val})"
                    pos += 2
                elif word == -6:
                    extra_val = struct.unpack('<h', data[pos:pos+2])[0]
                    extra = f" (数值={extra_val})"
                    pos += 2
                print(f"  {pos//2-1}: {label}{extra}")
                if word == -1:
                    print("  *** TEXT_END - 应该等待输入 ***")
            elif 0x3000 <= word <= 0x9FFF:
                # 中文字符
                try:
                    ch = bytes([word & 0xFF, (word >> 8) & 0xFF]).decode('big5', errors='replace')
                    print(f"  {pos//2-1}: [字符: {ch}]")
                except:
                    print(f"  {pos//2-1}: [0x{word:04X}]")
            else:
                print(f"  {pos//2-1}: [未知: 0x{word:04X}]")
            
            line_num += 1
            if line_num > 100:
                print("  ... (截断)")
                break

if __name__ == "__main__":
    analyze_flow()
