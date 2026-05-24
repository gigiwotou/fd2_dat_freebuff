"""检查嵌套 DAT 资源的实际数据格式"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))

# 加载索引 82
start = offsets[82]
end = offsets[83]
with open(fdother_path, "rb") as f:
    f.seek(start)
    data = f.read(end - start)

print(f"嵌套 DAT 总大小: {len(data)} 字节")
print(f"资源数量: {struct.unpack('<I', data[6:10])[0]}")

# 提取前 3 个有效资源
valid_offsets = [6587, 18611, 25484]

for idx, res_offset in enumerate(valid_offsets):
    res_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(data)
    res_size = res_end - res_offset
    res_data = data[res_offset:res_end]
    
    print(f"\n资源 {idx} (偏移 {res_offset}, 大小 {res_size} 字节):")
    print(f"  前 32 字节: {res_data[:32].hex()}")
    
    # 统计字节值分布
    byte_counts = {}
    for b in res_data:
        byte_counts[b] = byte_counts.get(b, 0) + 1
    
    # 显示最常见的 10 个字节值
    sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"  最常见字节值:")
    for byte_val, count in sorted_bytes:
        print(f"    0x{byte_val:02x}: {count} 次 ({count*100/len(res_data):.1f}%)")
    
    # 分析 RLE 结构
    # 如果字节值主要在 0x70-0x90 范围，可能是 8 位调色板索引的 RLE 数据
    mid_range = sum(1 for b in res_data if 0x70 <= b <= 0x90)
    print(f"  0x70-0x90 范围字节: {mid_range} ({mid_range*100/len(res_data):.1f}%)")
    
    # 检查是否有 0x00 或 0xFF 等控制字节
    control_bytes = sum(1 for b in res_data if b == 0x00 or b == 0xFF or (b >= 0x80 and b < 0xC0))
    print(f"  可能的控制字节: {control_bytes} ({control_bytes*100/len(res_data):.1f}%)")
