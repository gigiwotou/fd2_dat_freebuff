"""分析FDOTHER.DAT的偏移表结构"""
import struct
import os

def analyze_fdother_structure(data_dir):
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        # 读取前20字节
        header = f.read(20)
        print(f"文件头20字节:")
        print(f"  十六进制: {' '.join(f'{b:02x}' for b in header)}")
        print(f"  ASCII: {header.decode('ascii', errors='replace')}")
        
        # 尝试不同的解析方式
        print("\n尝试解析偏移表...")
        
        # 方式1: 假设前10字节是Magic+count
        f.seek(10)
        count_bytes = f.read(4)
        count = struct.unpack("<I", count_bytes)[0]
        print(f"\n方式1: 偏移10处读取count = {count}")
        
        if count < 1000:  # 合理的count范围
            f.seek(14)
            # 读取前10个偏移
            print("前10个偏移:")
            for i in range(10):
                offset_bytes = f.read(4)
                offset = struct.unpack("<I", offset_bytes)[0]
                print(f"  [{i}] 0x{offset:X} ({offset})")
                
                # 计算下一个偏移来推断大小
                if i < 4:  # 只检查前几个
                    next_offset_bytes = f.read(4)
                    next_offset = struct.unpack("<I", next_offset_bytes)[0]
                    size = next_offset - offset
                    f.seek(-4, 1)  # 回退4字节
                    print(f"      大小: {size} 字节")
        else:
            print(f"  count={count} 不合理，尝试其他方式...")
            
        # 方式2: 假设前4字节是Magic，接下来4字节是count
        f.seek(4)
        count2 = struct.unpack("<I", f.read(4))[0]
        print(f"\n方式2: 偏移4处读取count = {count2}")
        
        if count2 < 1000:
            f.seek(8)
            print("前10个偏移:")
            for i in range(10):
                offset_bytes = f.read(4)
                offset = struct.unpack("<I", offset_bytes)[0]
                print(f"  [{i}] 0x{offset:X} ({offset})")
        else:
            print(f"  count={count2} 不合理")
            
        # 方式3: 直接扫描文件，查找可能的偏移模式
        print("\n方式3: 扫描文件查找偏移模式...")
        f.seek(0)
        file_size = os.path.getsize(path)
        print(f"  文件大小: {file_size} 字节")
        
        # 读取前100字节来查找模式
        f.seek(0)
        data = f.read(200)
        print(f"  前200字节:")
        for i in range(0, min(200, len(data)), 16):
            hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
            print(f"    {i:04x}: {hex_str:<48s} {ascii_str}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    analyze_fdother_structure(data_dir)
