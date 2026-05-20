import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f'FDOTHER.DAT: {count} resources, file size: {len(data)}')

# 分析所有资源，找出可能的调色板
for i in range(count-1):
    off_start = struct.unpack('<I', data[10+i*4:14+i*4])[0]
    off_end = struct.unpack('<I', data[10+(i+1)*4:14+(i+1)*4])[0]
    size = off_end - off_start
    
    # 标记768字节资源(256色*3字节)
    if size == 768:
        print(f'\n=== Resource {i} (PALETTE, {size} bytes) ===')
        # 读取前3个颜色
        for j in range(3):
            r, g, b = struct.unpack('<BBB', data[off_start + j*3:off_start + j*3 + 3])
            print(f'  Color {j}: R={r:3d} G={g:3d} B={b:3d}')
        
        # 检查是否有肤色色调（人物头像常用）
        skin_count = 0
        for j in range(256):
            r, g, b = struct.unpack('<BBB', data[off_start + j*3:off_start + j*3 + 3])
            # 肤色特征：R较高，G中等，B较低
            if r > 30 and 15 <= g <= 45 and b < 25:
                skin_count += 1
        print(f'  Skin-tone colors: {skin_count}')
    
    if i < 15 or size == 768:
        if size != 768:
            print(f'Resource {i}: size={size}')
