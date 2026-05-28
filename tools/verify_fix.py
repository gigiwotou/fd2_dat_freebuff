"""验证修复后的索引逻辑"""
import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

rs = offsets[1]
rd = data[rs:]
res_size = offsets[2] - offsets[1]

print("=== 修复后的索引方式 ===")
print("资源1大小:", res_size)
print()

for sub_idx in range(5):
    offset = struct.unpack_from('<h', rd, sub_idx * 2)[0]
    print(f"sub {sub_idx}: 偏移 = {offset}")
    
    if offset < 0 or offset >= res_size:
        print(f"  -> 偏移无效，跳过")
        continue
    
    sub_data = rd[offset:]
    print(f"  -> 开头内容:")
    for i in range(min(8, len(sub_data) // 2)):
        val = struct.unpack_from('<h', sub_data, i * 2)[0]
        if val == -1:
            print(f"     [{i}] = TEXT_END")
            break
        elif val == -2:
            print(f"     [{i}] = NEWLINE")
        elif val == -3:
            print(f"     [{i}] = NEWLINE2")
        elif val in [-17, -18, -19, -20]:
            cmd = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
            next_val = struct.unpack_from('<h', sub_data, (i + 1) * 2)[0]
            print(f"     [{i}] = {cmd}({next_val})")
        elif val >= 0 and val < 0x8000:
            print(f"     [{i}] = 字符({val})")
