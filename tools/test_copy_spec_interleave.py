#!/usr/bin/env python3
"""简化测试 - 验证COPY_SPEC间隔写入理论"""

print("="*70)
print("验证COPY_SPEC间隔写入理论")
print("="*70)

# 模拟24x24图像
width = 24
height = 24
expected = width * height  # 576

# 模拟RLE数据 - 前几个操作
# 假设第一个操作是COPY_SPEC, count=5, value=100
# 根据汇编: 每次循环dst前进1,写入1,但消耗2个位置

def test_copy_spec_interleave():
    """测试COPY_SPEC的间隔写入效果"""
    dst = [0] * 20  # 假设20个位置
    
    # COPY_SPEC: count=5, value=0xAA
    count = 5
    value = 0xAA
    
    dst_idx = 0
    remaining = 20
    
    print(f"初始: dst_idx=0, remaining={remaining}")
    print(f"执行COPY_SPEC count={count}, value=0x{value:02x}")
    
    for i in range(count):
        if remaining <= 0:
            break
        # 写入1个值
        dst[dst_idx] = value
        print(f"  循环{i}: dst[{dst_idx}] = 0x{value:02x}")
        dst_idx += 1  # 前进1
        
        # 但消耗2个位置!
        remaining -= 2
        print(f"    消耗2个位置, remaining={remaining}")
        
        if i < count - 1 and remaining > 0:
            # 跳过下一个位置(不写入,保持0)
            dst_idx += 1
            print(f"    跳过位置{dst_idx-1}, 下一个写入位置={dst_idx}")
    
    print(f"\n结果: {dst}")
    print(f"非零: {sum(1 for x in dst if x != 0)}")
    
    # 可视化
    for i in range(0, len(dst), 10):
        chunk = dst[i:i+10]
        print(f"  [{i:2d}-{i+9:2d}]: {' '.join(f'{x:02x}' if x else '..' for x in chunk)}")

test_copy_spec_interleave()

print("\n" + "="*70)
print("这个间隔写入模式解释了为什么图像显示为零散像素!")
print("COPY_SPEC在偶数索引位置写入,奇数索引位置保持0(或反之)")
print("="*70)

# 现在测试实际的24x24图像
print("\n" + "="*70)
print("测试24x24图像效果")
print("="*70)

# 假设前30个操作都是COPY_SPEC,每个count=2
dst = [0] * 576
dst_idx = 0
remaining = 576

for op in range(30):
    if remaining <= 0:
        break
    count = 2
    value = 100 + op
    
    for i in range(count):
        if remaining <= 0:
            break
        dst[dst_idx] = value
        dst_idx += 1
        remaining -= 2
        if i < count - 1 and remaining > 0:
            dst_idx += 1

# 渲染为图像
from PIL import Image

# 创建灰度图像查看效果
img = Image.new('L', (width, height))
for y in range(height):
    for x in range(width):
        idx = y * width + x
        img.putpixel((x, y), dst[idx] if dst[idx] < 256 else 255)

img.save('output/idx1_copy_spec_interleave_test.png')
print("保存测试图像: output/idx1_copy_spec_interleave_test.png")

# 统计
non_zero = sum(1 for x in dst if x != 0)
print(f"\n非零像素: {non_zero}/{expected}")
print(f"填充率: {non_zero/expected*100:.1f}%")

# 显示前5行
print("\n前5行像素分布:")
for y in range(5):
    row = dst[y*width:(y+1)*width]
    print(f"  行{y:2d}: {''.join('█' if x else '·' for x in row)}")
