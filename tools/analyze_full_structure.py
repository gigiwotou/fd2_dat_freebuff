"""
详细分析嵌套 DAT 的完整结构，理解偏移表和数据块的关系
"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    # 分析索引 82 (scene_0)
    index = 82
    start = offsets[index]
    end = offsets[index + 1]
    f.seek(start)
    resource_data = f.read(end - start)
    
    print(f"资源大小: {len(resource_data)} 字节")
    
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    print(f"偏移数量字段: {offset_count}")
    
    # 从偏移表往后找所有合理的偏移
    offset_table_start = 10
    
    # 偏移表里存储的是每个数据块的起始偏移
    # 第一个偏移后的数据到第二个偏移，依此类推
    # 但"偏移数量"字段可能不是实际的偏移条目数
    
    # 打印前200字节的原始数据
    print(f"\n前 200 字节 hex dump:")
    for i in range(0, 200, 16):
        hex_str = resource_data[i:i+16].hex()
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in resource_data[i:i+16])
        print(f"  {i:4d}: {hex_str}  {ascii_str}")
    
    # 分析偏移表
    print(f"\n偏移表分析:")
    for i in range(offset_count):
        offset_addr = 10 + i * 4
        if offset_addr + 4 > len(resource_data):
            break
        offset_val = struct.unpack("<I", resource_data[offset_addr:offset_addr + 4])[0]
        
        # 判断是否是有效偏移
        is_valid = offset_val >= (10 + offset_count * 4) and offset_val < len(resource_data)
        status = "[OK]" if is_valid else "[INVALID]"
        print(f"  偏移[{i:2d}] @ {offset_addr:5d} = {offset_val:6d} {status}")
