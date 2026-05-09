import struct

data = open('game/FDOTHER.DAT', 'rb').read()
print(f'文件大小: {len(data)}')
hdr = data[:6]
print(f'魔数: {hdr}')

if hdr == b'LLLLLL':
    cnt = struct.unpack('<I', data[6:10])[0]
    print(f'资源数量: {cnt}')
    
    for i in range(min(10, cnt)):
        off = struct.unpack('<I', data[10 + i*4:10 + i*4 + 4])[0]
        print(f'索引{i}偏移: {off} (0x{off:X})')
    
    if cnt > 5:
        off4 = struct.unpack('<I', data[10 + 4*4:10 + 4*4 + 4])[0]
        off5 = struct.unpack('<I', data[10 + 5*4:10 + 5*4 + 4])[0]
        size4 = off5 - off4
        
        print(f'\n索引4偏移: {off4} (0x{off4:X})')
        print(f'索引4大小: {size4}')
        
        res4 = data[off4:off4 + min(100, size4)]
        print(f'索引4前100字节: {res4[:100].hex(" ")}')
        
        if len(res4) >= 4:
            w = struct.unpack('<H', res4[0:2])[0]
            h = struct.unpack('<H', res4[2:4])[0]
            print(f'可能尺寸: {w}x{h}')
