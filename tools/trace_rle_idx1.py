#!/usr/bin/env python3
"""
详细跟踪索引1的RLE解码过程
"""
import struct

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    f.seek(4 * 1 + 6)
    data = f.read(8)
    start_offset, end_offset = struct.unpack('<II', data)
    size = end_offset - start_offset
    
    f.seek(start_offset)
    res_data = f.read(size)
    
    width = struct.unpack('<H', res_data[0:2])[0]
    height = struct.unpack('<H', res_data[2:4])[0]
    pal_window = res_data[4]
    
    rle_data = res_data[5:]
    
    print("="*70)
    print("索引1 RLE数据详细跟踪")
    print(f"Tile: {width}x{height}, palette_window={pal_window}")
    print(f"RLE数据大小: {len(rle_data)}")
    print("="*70)
    
    # 前50个RLE字节
    print(f"\nRLE数据前50字节:")
    for i in range(min(50, len(rle_data))):
        b = rle_data[i]
        print(f"  [{i:2d}] 0x{b:02x} ({b:3d})")
    
    print("\n" + "="*70)
    print("逐步跟踪RLE解码 (前20个操作)")
    print("="*70)
    
    src_idx = 0
    dst_idx = 0
    row = 0
    remaining = width
    dst = [0] * (width * height)
    
    for op_num in range(30):
        if remaining <= 0:
            # 换行
            row += 1
            if row >= height:
                print(f"\n行{row}: 解码完成")
                break
            remaining = width
            dst_idx = row * width
            print(f"\n--- 行{row} 开始 ---")
        
        if src_idx >= len(rle_data):
            print(f"\nRLE数据耗尽")
            break
        
        ctrl = rle_data[src_idx]
        src_idx += 1
        
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        count = (ctrl & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                op_name = "FILL"
                # 读取填充值
                if src_idx < len(rle_data):
                    fill_val = rle_data[src_idx]
                    src_idx += 1
                else:
                    fill_val = 0
                
                actual_count = min(count, remaining)
                for i in range(actual_count):
                    dst[dst_idx] = fill_val
                    dst_idx += 1
                
                remaining -= actual_count
                
                print(f"操作{op_num:2d}: {op_name:10s} ctrl=0x{ctrl:02x}, count={count}, 填充值=0x{fill_val:02x}, 实际填充={actual_count}, dst_idx={dst_idx}, remaining={remaining}")
                
            else:
                op_name = "COPY_SPEC"
                # 读取值
                if src_idx < len(rle_data):
                    value = rle_data[src_idx]
                    src_idx += 1
                else:
                    value = 0
                
                total_consume = count * 2
                actual_count = count
                if total_consume > remaining:
                    actual_count = remaining // 2
                    total_consume = actual_count * 2
                
                for i in range(actual_count):
                    dst[dst_idx] = value
                    dst_idx += 2
                
                remaining -= total_consume
                
                print(f"操作{op_num:2d}: {op_name:10s} ctrl=0x{ctrl:02x}, count={count}, 值=0x{value:02x}, 实际写入={actual_count}, 消耗={total_consume}, dst_idx={dst_idx}, remaining={remaining}")
                
        else:
            if bit6 == 0:
                op_name = "COPY_STD"
                actual_count = min(count, remaining, len(rle_data) - src_idx)
                
                for i in range(actual_count):
                    dst[dst_idx] = rle_data[src_idx]
                    src_idx += 1
                    dst_idx += 1
                
                remaining -= actual_count
                
                print(f"操作{op_num:2d}: {op_name:10s} ctrl=0x{ctrl:02x}, count={count}, 实际复制={actual_count}, dst_idx={dst_idx}, remaining={remaining}")
                
            else:
                op_name = "SKIP"
                actual_count = min(count, remaining)
                dst_idx += actual_count
                remaining -= actual_count
                
                print(f"操作{op_num:2d}: {op_name:10s} ctrl=0x{ctrl:02x}, count={count}, 实际跳过={actual_count}, dst_idx={dst_idx}, remaining={remaining}")
    
    # 显示前3行的解码结果
    print("\n" + "="*70)
    print("前3行解码结果:")
    print("="*70)
    
    for y in range(min(3, height)):
        row_start = y * width
        row_end = row_start + width
        row_data = dst[row_start:row_end]
        
        # 用字符表示
        chars = []
        for p in row_data:
            if p == 0:
                chars.append('·')
            elif p < 32:
                chars.append('.')
            elif p < 64:
                chars.append('o')
            elif p < 128:
                chars.append('O')
            else:
                chars.append('#')
        
        non_zero = sum(1 for p in row_data if p != 0)
        print(f"行{y:2d} ({non_zero:2d}非零): {''.join(chars)}")
        
        # 显示原始值
        values = []
        for p in row_data:
            values.append(f"{p:3d}")
        print(f"  原始值: {' '.join(values[:12])}...")
