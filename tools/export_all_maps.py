#!/usr/bin/env python3
"""批量导出所有地图（正确版 - 基于test_map_fixed_palette.py）"""
import struct
import sys
from pathlib import Path
from PIL import Image

# 配置
GAME_DIR = Path(__file__).parent.parent / "game"
OUTPUT_DIR = Path(__file__).parent.parent / "output/maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FDFIELD_PATH = GAME_DIR / "FDFIELD.DAT"
FDSHAP_PATH = GAME_DIR / "FDSHAP.DAT"
FDOTHER_PATH = GAME_DIR / "FDOTHER.DAT"


def parse_dat_offsets_format2(file_data):
    """
    解析DAT文件的资源偏移表（格式2：无显式计数）
    所有DAT文件都使用这种格式
    """
    magic = file_data[:6]
    if magic != b"LLLLLL":
        raise ValueError(f"Invalid magic: {magic}")
    
    offsets = []
    pos = 6
    while pos < len(file_data) - 4:
        offset = struct.unpack_from("<I", file_data, pos)[0]
        if offset > pos and offset < len(file_data):
            offsets.append(offset)
        else:
            break
        pos += 4
    
    return offsets


def rle_decompress_ida(src: bytes, width: int, height: int) -> bytes:
    """基于IDA sub_4E98D的RLE解压缩"""
    dst = bytearray(width * height)
    p = 0
    src_end = len(src)
    
    for row in range(height):
        row_dst = row * width
        count = width
        
        while count > 0 and p < src_end:
            value = src[p]
            p += 1
            count_1 = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 and bit6:
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count >= 2:
                            if row_dst + 1 < len(dst):
                                dst[row_dst + 1] = fill
                            row_dst += 2
                            count -= 2
                        else:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
            else:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count > 0:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
    
    return bytes(dst)


def parse_terrain_id_ida(terrain_data_4bytes):
    """基于IDA sub_4DF4C的地形ID计算"""
    byte0 = terrain_data_4bytes[0]
    byte1 = terrain_data_4bytes[1]
    terrain_id = byte0 | ((byte1 & 0x03) << 8)
    return terrain_id


def parse_tile_offsets_ida(tile_set_data):
    """基于IDA sub_1ACF3的瓦片偏移表解析"""
    if len(tile_set_data) < 6:
        return None
    
    tile_width = struct.unpack_from("<H", tile_set_data, 0)[0]
    tile_height = struct.unpack_from("<H", tile_set_data, 2)[0]
    tile_count = struct.unpack_from("<H", tile_set_data, 4)[0]
    
    tile_offsets = []
    pos = 6
    
    for i in range(tile_count):
        if pos + 4 > len(tile_set_data):
            break
        offset_val = struct.unpack_from("<I", tile_set_data, pos)[0]
        tile_offsets.append(offset_val)
        pos += 4
    
    return tile_offsets, tile_width, tile_height, tile_count


def palette_6bit_to_8bit(palette_6bit: bytes) -> list:
    """Convert 6-bit VGA palette to 8-bit RGB"""
    palette_8bit = []
    for i in range(0, len(palette_6bit), 3):
        r = palette_6bit[i]
        g = palette_6bit[i + 1]
        b = palette_6bit[i + 2]
        
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        
        r8 = min(255, max(0, r8))
        g8 = min(255, max(0, g8))
        b8 = min(255, max(0, b8))
        
        palette_8bit.append((r8, g8, b8))
    
    return palette_8bit


def export_map(map_id):
    """导出单个地图"""
    # 读取FDFIELD.DAT
    with open(FDFIELD_PATH, "rb") as f:
        fdfield_data = f.read()
    
    fdfield_offsets = parse_dat_offsets_format2(fdfield_data)
    resource_count = len(fdfield_offsets)
    
    # 用户说地图数据在1, 4, 7, 10...（用户索引从1开始）
    # 转换为0开始：0, 3, 6, 9...
    # 对应：map_id * 3
    layout_res_idx = map_id * 3
    control_res_idx = map_id * 3 + 1
    spawn_res_idx = map_id * 3 + 2
    
    if spawn_res_idx >= resource_count:
        return None
    
    layout_start = fdfield_offsets[layout_res_idx]
    control_start = fdfield_offsets[control_res_idx]
    
    layout_end = fdfield_offsets[layout_res_idx + 1] if layout_res_idx + 1 < resource_count else len(fdfield_data)
    control_end = fdfield_offsets[control_res_idx + 1] if control_res_idx + 1 < resource_count else len(fdfield_data)
    
    layout_data = fdfield_data[layout_start:layout_end]
    control_data = fdfield_data[control_start:control_end]
    
    # 解析地图尺寸
    map_width = struct.unpack_from("<H", layout_data, 0)[0]
    map_height = struct.unpack_from("<H", layout_data, 2)[0]
    total_tiles = map_width * map_height
    
    # 获取terrain_set_id
    terrain_set_id = control_data[0]
    
    # 读取FDSHAP.DAT（使用格式2 - 无计数）
    with open(FDSHAP_PATH, "rb") as f:
        fdshap_data = f.read()
    
    fdshap_offsets = parse_dat_offsets_format2(fdshap_data)
    
    # 用户说瓦片集在1, 3, 5, 7...（用户索引从1开始）
    # 转换为0开始：0, 2, 4, 6...
    # 对应：terrain_set_id * 2
    tile_set_res_idx = terrain_set_id * 2
    
    if tile_set_res_idx >= len(fdshap_offsets):
        return None
    
    tile_set_start = fdshap_offsets[tile_set_res_idx]
    tile_set_end = fdshap_offsets[tile_set_res_idx + 1] if tile_set_res_idx + 1 < len(fdshap_offsets) else len(fdshap_data)
    tile_set_data = fdshap_data[tile_set_start:tile_set_end]
    
    # 加载调色板（从FDOTHER.DAT资源0 - 全局调色板）
    with open(FDOTHER_PATH, "rb") as f:
        fdother_data = f.read()
    
    fdother_offsets = parse_dat_offsets_format2(fdother_data)
    palette_data = fdother_data[fdother_offsets[0]:fdother_offsets[1]]
    palette = palette_6bit_to_8bit(palette_data[:768])
    
    # 解析瓦片
    tile_info = parse_tile_offsets_ida(tile_set_data)
    if tile_info is None:
        return None
    
    tile_offsets, tile_w, tile_h, tile_count = tile_info
    
    # 解析地形ID
    terrain_ids = []
    pos = 4
    for i in range(total_tiles):
        if pos + 4 > len(layout_data):
            break
        terrain_4bytes = layout_data[pos:pos+4]
        terrain_id = parse_terrain_id_ida(terrain_4bytes)
        terrain_ids.append(terrain_id)
        pos += 4
    
    # 生成地图图像
    map_image = Image.new("RGB", (map_width * tile_w, map_height * tile_h), (0, 0, 0))
    rendered_count = 0
    
    for tile_index in range(len(terrain_ids)):
        terrain_id = terrain_ids[tile_index]
        # 关键修复：直接使用terrain_id，不进行掩码
        # 地形ID范围都在瓦片集范围内（已通过验证）
        tile_idx = terrain_id
        
        if tile_idx < len(tile_offsets):
            offset = tile_offsets[tile_idx]
            if offset < len(tile_set_data):
                next_offset = tile_offsets[tile_idx + 1] if tile_idx + 1 < len(tile_offsets) else len(tile_set_data)
                compressed_data = tile_set_data[offset:next_offset]
                
                pixels = rle_decompress_ida(compressed_data, tile_w, tile_h)
                
                if len(pixels) == tile_w * tile_h:
                    y = tile_index // map_width
                    x = tile_index % map_width
                    
                    tile_img = Image.new("P", (tile_w, tile_h))
                    tile_img.putdata(pixels)
                    tile_img.putpalette([c for rgb in palette for c in rgb])
                    map_image.paste(tile_img, (x * tile_w, y * tile_h))
                    rendered_count += 1
    
    # 保存
    output_path = OUTPUT_DIR / f"map_{map_id}_v3.png"
    map_image.save(output_path)
    
    return {
        'id': map_id,
        'width': map_width,
        'height': map_height,
        'total': total_tiles,
        'rendered': rendered_count,
        'terrain_set': terrain_set_id,
        'tile_count': tile_count,
        'output': str(output_path)
    }


def main():
    print("="*70)
    print("批量导出所有地图（正确版 - 基于test_map_fixed_palette.py验证）")
    print("="*70)
    print()
    
    # 读取FDFIELD.DAT获取地图数量
    with open(FDFIELD_PATH, "rb") as f:
        fdfield_data = f.read()
    
    fdfield_offsets = parse_dat_offsets_format2(fdfield_data)
    map_count = len(fdfield_offsets) // 3
    
    print(f"地图总数: {map_count}\n")
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i in range(map_count):
        try:
            result = export_map(i)
            if result:
                results.append(result)
                print(f"[{i+1:2d}/{map_count}] 地图{i:2d}: {result['width']}x{result['height']} "
                      f"| 渲染 {result['rendered']}/{result['total']} 瓦片 "
                      f"| terrain_set={result['terrain_set']} "
                      f"| 瓦片数={result['tile_count']} "
                      f"| -> {result['output']}")
                success_count += 1
            else:
                print(f"[{i+1:2d}/{map_count}] 地图{i:2d}: [失败]")
                fail_count += 1
        except Exception as e:
            print(f"[{i+1:2d}/{map_count}] 地图{i:2d}: [错误] {e}")
            fail_count += 1
    
    print()
    print("="*70)
    print(f"导出完成: 成功 {success_count}/{map_count}, 失败 {fail_count}")
    print("="*70)
    
    # 统计信息
    if results:
        total_rendered = sum(r['rendered'] for r in results)
        total_tiles = sum(r['total'] for r in results)
        print(f"\n总瓦片数: {total_tiles}")
        print(f"总渲染瓦片: {total_rendered}")
        print(f"渲染率: {total_rendered/total_tiles*100:.1f}%")
        print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
