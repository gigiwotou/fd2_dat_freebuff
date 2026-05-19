import struct
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)
print('文件大小:', file_size, '字节')
print()

# 前6字节是魔数
magic = data[:6]
print('魔数:', magic)

# 偏移6处的4字节是资源数量
count = struct.unpack_from('<I', data, 6)[0]
print('偏移表数量:', count)
print()

# 读取所有偏移
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 找出实际有效的资源数量（偏移小于文件大小）
print('=== 检查有效偏移 ===')
valid_count = 0
for i, off in enumerate(offsets):
    if off < file_size:
        valid_count = i + 1
    else:
        if i < 40:
            print('偏移[%d] = 0x%X (无效，>=文件大小)' % (i, off))
        break

print('有效偏移数量:', valid_count)
print()

# 分析每个资源集的大小
print('=== 资源集分析 ===')
for i in range(valid_count):
    start = offsets[i]
    end = offsets[i+1] if (i+1 < len(offsets) and offsets[i+1] < file_size) else file_size
    size = end - start
    
    # 读取资源集头部
    # 假设资源集结构也是标准DAT格式：魔数(6) + 子资源数量(4) + 子偏移表
    if start + 10 <= file_size:
        set_magic = data[start:start+6]
        sub_count = struct.unpack_from('<I', data, start+6)[0]
        
        print('资源集 %2d: 偏移=0x%08X, 大小=%6d 字节, 子资源=%d' % (i, start, size, sub_count))
        
        # 如果是有效资源集，分析子资源
        if sub_count > 0 and sub_count < 100 and start + 10 + (sub_count + 1) * 4 <= file_size:
            # 读取子资源偏移
            sub_offsets = []
            for j in range(sub_count + 1):
                sub_off = struct.unpack_from('<I', data, start + 10 + j * 4)[0]
                sub_offsets.append(sub_off)
            
            # 第一个子资源的大小
            if len(sub_offsets) > 1:
                first_sub_size = sub_offsets[1] - sub_offsets[0]
                print('    子资源0: 偏移=%d, 大小=%d' % (sub_offsets[0], first_sub_size))
    else:
        print('资源集 %2d: 偏移=0x%08X, 大小=%6d 字节' % (i, start, size))