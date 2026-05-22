"""
分析FDTXT资源0/子项0的原始字节，理解TEXT_CHAR_F之后的数据结构
"""
import struct

def analyze_raw_bytes():
    with open("game/FDTXT.DAT", "rb") as f:
        fdtxt = f.read()
    
    count = struct.unpack_from('<I', fdtxt, 6)[0]
    offsets = [struct.unpack_from('<I', fdtxt, 10 + i*4)[0] for i in range(count)]
    
    res_data = fdtxt[offsets[0]:offsets[1]]
    sub_count = struct.unpack_from('<h', res_data, 0)[0]
    sub_offsets = [struct.unpack_from('<h', res_data, 2 + i*2)[0] for i in range(sub_count)]
    
    text_start = sub_offsets[0]
    text_end = sub_offsets[1]
    
    print(f"=== FDTXT资源0/子项0 原始字节分析 ===")
    print(f"文本范围: {text_start} - {text_end}")
    print()
    
    # 打印所有字节（十六进制和十进制）
    pos = text_start
    print(f"位置\t\t十六进制\t\t十进制\t\t说明")
    print("-" * 80)
    
    while pos < text_end:
        word = struct.unpack_from('<h', res_data, pos)[0]
        hex_bytes = res_data[pos:pos+2].hex()
        
        if word == -1:
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\tTEXT_END")
            pos += 2
            break
        elif word == -2:
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\tTEXT_NEWLINE")
            pos += 2
        elif word == -3:
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\tTEXT_NEWLINE2")
            pos += 2
        elif word == -19:
            cid = struct.unpack_from('<h', res_data, pos+2)[0]
            cid_hex = res_data[pos+2:pos+4].hex()
            print(f"0x{pos:04X} ({pos})\t{hex_bytes} {cid_hex}\t{word}, {cid}\tTEXT_CHAR_F(cid={cid})")
            pos += 4
        elif word == -20:
            cid = struct.unpack_from('<h', res_data, pos+2)[0]
            cid_hex = res_data[pos+2:pos+4].hex()
            print(f"0x{pos:04X} ({pos})\t{hex_bytes} {cid_hex}\t{word}, {cid}\tTEXT_CHAR_S(cid={cid})")
            pos += 4
        elif word == -17:
            pid = struct.unpack_from('<h', res_data, pos+2)[0]
            pid_hex = res_data[pos+2:pos+4].hex()
            print(f"0x{pos:04X} ({pos})\t{hex_bytes} {pid_hex}\t{word}, {pid}\tTEXT_PORTRAIT_F(pid={pid})")
            pos += 4
        elif word == -18:
            pid = struct.unpack_from('<h', res_data, pos+2)[0]
            pid_hex = res_data[pos+2:pos+4].hex()
            print(f"0x{pos:04X} ({pos})\t{hex_bytes} {pid_hex}\t{word}, {pid}\tTEXT_PORTRAIT_S(pid={pid})")
            pos += 4
        elif word == -4:
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\tTEXT_RECURSE1")
            pos += 2
        elif word == -5:
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\tTEXT_RECURSE2")
            pos += 2
        elif word == -6:
            val = struct.unpack_from('<h', res_data, pos+2)[0]
            val_hex = res_data[pos+2:pos+4].hex()
            print(f"0x{pos:04X} ({pos})\t{hex_bytes} {val_hex}\t{word}, {val}\tTEXT_SHOW_NUM")
            pos += 4
        elif word >= 0:
            # 普通字符
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\t字符[{word}]")
            pos += 2
        else:
            print(f"0x{pos:04X} ({pos})\t{hex_bytes}\t\t{word}\t\t???")
            pos += 2

if __name__ == "__main__":
    analyze_raw_bytes()
