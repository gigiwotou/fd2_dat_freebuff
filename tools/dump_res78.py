import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    f.read(10)
    offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(200)]
    f.seek(offsets[78])
    data = f.read(64)

print("res78前64字节详细分析:")
print("=" * 80)
for i in range(0, 64, 4):
    val_d = struct.unpack_from('<I', data, i)[0]
    val_w = struct.unpack_from('<H', data, i)[0]
    hex_bytes = ' '.join(f'{b:02x}' for b in data[i:i+4])
    print(f"  +{i:02x} (DWORD): {hex_bytes} = {val_d:10d} (0x{val_d:08x})")
    print(f"  +{i:02x} (WORD) :             {val_w:5d} (0x{val_w:04x})")

print(f"\n关键位置 (IDA sub_25A96使用):")
print(f"  *(res78+6)  = {struct.unpack_from('<I', data, 6)[0]}")
print(f"  *(res78+10) = {struct.unpack_from('<I', data, 10)[0]}")

print(f"\n完整十六进制:")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f"  {i:02x}: {hex_str}")
