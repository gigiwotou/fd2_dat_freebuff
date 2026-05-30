#!/usr/bin/env python3
"""测试所有可能的RLE映射组合并自动评分"""

import struct
from pathlib import Path
from PIL import Image
import numpy as np

FDOTHER_PATH = Path("game/FDOTHER.DAT")

# 定义4种操作
OP_FILL = 0
OP_COPY_SPEC = 1
OP_COPY_STD = 2
OP_SKIP = 3

OP_NAMES = {
    OP_FILL: "FILL",
    OP_COPY_SPEC: "COPY_SPEC",
    OP_COPY_STD: "COPY_STD",
    OP_SKIP: "SKIP"
}

def decode_rle_with_mapping(rle_data, w, h, mapping):
    """使用指定映射解码RLE"""
    dst = bytearray(w * h)
    dst_idx = 0
    src_idx = 0
    
    for row in range(h):
        remaining = w
        
        while remaining > 0 and src_idx < len(rle_data):
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            op = mapping.get((bit7, bit6), OP_FILL)
            
            if op == OP_FILL:
                actual_count = min(count, remaining)
                if src_idx < len(rle_data):
                    fill_val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual_count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = fill_val
                            dst_idx += 1
                remaining -= actual_count
                
            elif op == OP_COPY_SPEC:
                total_consume = count * 2
                actual_count = count
                if total_consume > remaining:
                    actual_count = remaining // 2
                    total_consume = actual_count * 2
                if src_idx < len(rle_data):
                    val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual_count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = val
                            dst_idx += 2
                remaining -= total_consume
                
            elif op == OP_COPY_STD:
                actual_count = min(count, remaining, len(rle_data) - src_idx)
                for i in range(actual_count):
                    if dst_idx < len(dst) and src_idx < len(rle_data):
                        dst[dst_idx] = rle_data[src_idx]
                        src_idx += 1
                        dst_idx += 1
                remaining -= actual_count
                
            elif op == OP_SKIP:
                actual_count = min(count, remaining)
                dst_idx += actual_count
                remaining -= actual_count
    
    return dst

def score_decoded(decoded, w, h):
    """给解码结果评分，高分表示更可能是正确的图像"""
    # 转换为numpy数组
    arr = np.array(decoded).reshape(h, w)
    
    score = 0.0
    
    # 1. 非零像素比例应该在合理范围 (5%-80%)
    non_zero_ratio = np.count_nonzero(arr) / (w * h)
    if 0.05 <= non_zero_ratio <= 0.80:
        score += 20
    elif 0.02 <= non_zero_ratio <= 0.90:
        score += 10
    
    # 2. 唯一值数量应该较少（图标通常使用少量颜色）
    unique_count = len(np.unique(arr))
    if unique_count <= 20:
        score += 30
    elif unique_count <= 40:
        score += 15
    elif unique_count <= 100:
        score += 5
    
    # 3. 检查空间连续性（相邻像素相关性）
    # 水平差异
    h_diff = np.abs(np.diff(arr, axis=1))
    h_similar = np.mean(h_diff == 0)
    if h_similar > 0.5:
        score += 20
    elif h_similar > 0.3:
        score += 10
    
    # 垂直差异
    v_diff = np.abs(np.diff(arr, axis=0))
    v_similar = np.mean(v_diff == 0)
    if v_similar > 0.5:
        score += 20
    elif v_similar > 0.3:
        score += 10
    
    # 4. 检查是否有对称性或规律性（可选）
    # 左上-右下对角线
    diag = np.diag(arr)
    if len(diag) > 0:
        diag_unique = len(np.unique(diag))
        if diag_unique <= 5:
            score += 5
    
    return score, non_zero_ratio, unique_count, h_similar, v_similar

def test_all_mappings():
    """测试所有可能的映射组合"""
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引0调色板
    idx0_data = data[offsets[0]:offsets[1]]
    
    # 索引1数据
    idx1_data = data[offsets[1]:offsets[2]]
    w = struct.unpack_from('<H', idx1_data, 0)[0]
    h = struct.unpack_from('<H', idx1_data, 2)[0]
    pw = idx1_data[4]
    
    print(f"索引1: {w}x{h}, palette_window={pw}")
    
    # RLE数据
    rle_data = idx1_data[5:]
    
    # 所有可能的映射组合 (4^4 = 256种)
    ops = [OP_FILL, OP_COPY_SPEC, OP_COPY_STD, OP_SKIP]
    op_list = list(itertools.product(ops, repeat=4))
    
    results = []
    
    for idx, (op00, op01, op10, op11) in enumerate(op_list):
        mapping = {
            (0, 0): op00,
            (0, 1): op01,
            (1, 0): op10,
            (1, 1): op11,
        }
        
        decoded = decode_rle_with_mapping(rle_data, w, h, mapping)
        score, nnr, uc, hs, vs = score_decoded(decoded, w, h)
        
        results.append({
            'idx': idx,
            'mapping': mapping,
            'score': score,
            'non_zero_ratio': nnr,
            'unique_count': uc,
            'h_similarity': hs,
            'v_similarity': vs,
            'decoded': decoded,
        })
    
    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"Top 10 最佳映射:")
    print(f"{'='*60}")
    
    for i, result in enumerate(results[:10]):
        print(f"\n排名 {i+1} (得分: {result['score']:.1f}):")
        for bits, op in sorted(result['mapping'].items()):
            print(f"  bit7={bits[0]}, bit6={bits[1]} -> {OP_NAMES[op]}")
        print(f"  非零比例: {result['non_zero_ratio']:.1%}")
        print(f"  唯一值数: {result['unique_count']}")
        print(f"  水平相似: {result['h_similarity']:.1%}")
        print(f"  垂直相似: {result['v_similarity']:.1%}")
        
        # 保存图像
        decoded = result['decoded']
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                pal_idx = decoded[idx]
                if pal_idx < 256:
                    r = idx0_data[pal_idx * 3]
                    g = idx0_data[pal_idx * 3 + 1]
                    b = idx0_data[pal_idx * 3 + 2]
                    img.putpixel((x, y), (r, g, b))
                else:
                    img.putpixel((x, y), (255, 0, 255))
        
        filename = f'output/idx1_top{i+1}_score{result["score"]:.0f}.png'
        img.save(filename)
        print(f"  已保存: {filename}")

import itertools
if __name__ == '__main__':
    test_all_mappings()
