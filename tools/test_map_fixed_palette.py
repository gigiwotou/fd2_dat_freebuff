#!/usr/bin/env python3
"""
测试工具：基于IDA MCP分析结果验证地图解析（修复调色板）

关键修复：
1. FDSHAP.DAT使用格式2（无计数）解析资源偏移表
2. 地图调色板从FDOTHER.DAT加载，不是从FDSHAP.DAT
3. 地图0使用FDOTHER.DAT资源0（768字节调色板）
"""

import struct
import sys
from pathlib import Path
from PIL import Image

# 配置
GAME_DIR = Path(__file__).parent.parent / "game"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

FDFIELD_PATH = GAME_DIR / "FDFIELD.DAT"
FDSHAP_PATH = GAME_DIR / "FDSHAP.DAT"
FDOTHER_PATH = GAME_DIR / "FDOTHER.DAT"

TILE_WIDTH = 24
TILE_HEIGHT = 24


def parse_dat_offsets_format2(file_data):
    """
    解析DAT文件的资源偏移表（格式2：无显式计数）
    
    格式：
    - Byte 0-5: 魔数 "LLLLLL"
    - Byte 6+: 资源偏移表，每个条目4字节DWORD
    - 当偏移值无效时停止
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
    """
    基于IDA sub_4E98D的RLE解压缩
    
    4种操作模式（通过count字节的bit7和bit6判断）：
    - 00 (FILL):    填充count个像素
    - 01 (ALTERNATE): 交替写入，dst+=2
    - 10 (COPY):    复制count个像素
    - 11 (SKIP):    跳过count个像素
    """
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
    """
    基于IDA sub_4DF4C的地形ID计算
    
    原始数据：每个瓦片4字节
    - byte[0-1]: 地形ID（16位小端序）
    - byte[2]: 地形变体（5位，需要&0x1F）
    - byte[3]: 未知（设置为0xFF）
    
    IDA公式：byte[0] | ((byte[1] & 3) << 8)
    范围：0-1023（10位）
    """
    byte0 = terrain_data_4bytes[0]
    byte1 = terrain_data_4bytes[1]
    
    terrain_id = byte0 | ((byte1 & 0x03) << 8)
    return terrain_id


def parse_tile_offsets_ida(tile_set_data):
    """
    基于IDA sub_1ACF3的瓦片偏移表解析
    
    FDSHAP瓦片集头部结构：
    - Byte 0-1: tile_width (WORD)
    - Byte 2-3: tile_height (WORD)
    - Byte 4-5: tile_count (WORD)
    - Byte 6+: DWORD offset entries
      公式：*(DWORD*)(FDSHAP_DAT + 4 * tile_index + 6)
    """
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


def load_palette_from_fdother(map_id):
    """
    从FDOTHER.DAT加载地图调色板
    
    根据IDA分析sub_25EBB：
    - 游戏初始化时加载FDOTHER.DAT资源0作为全局调色板
    - 资源0是768字节的标准6-bit RGB调色板
    """
    with open(FDOTHER_PATH, "rb") as f:
        fdother_data = f.read()
    
    fdother_offsets = parse_dat_offsets_format2(fdother_data)
    
    # 地图0使用资源0（全局调色板）
    palette_res_idx = 0
    
    if palette_res_idx >= len(fdother_offsets):
        print(f"  [ERROR] 调色板资源 {palette_res_idx} 不存在")
        return None
    
    palette_start = fdother_offsets[palette_res_idx]
    palette_end = fdother_offsets[palette_res_idx + 1] if palette_res_idx + 1 < len(fdother_offsets) else len(fdother_data)
    palette_data = fdother_data[palette_start:palette_end]
    
    if len(palette_data) < 768:
        print(f"  [ERROR] 调色板资源大小不足: {len(palette_data)} < 768")
        return None
    
    print(f"  从FDOTHER.DAT资源#{palette_res_idx}加载调色板 ({len(palette_data)} 字节)")
    
    palette = palette_6bit_to_8bit(palette_data[:768])
    return palette


def test_map_ida_verified(map_id=0):
    """
    使用IDA验证的方法测试地图
    """
    print(f"{'='*60}")
    print(f"基于IDA分析验证地图 {map_id}（修复调色板）")
    print(f"{'='*60}\n")
    
    # 1. 读取FDFIELD.DAT
    print("[1] 读取FDFIELD.DAT...")
    with open(FDFIELD_PATH, "rb") as f:
        fdfield_data = f.read()
    print(f"  文件大小: {len(fdfield_data)} 字节\n")
    
    # 2. 解析FDFIELD资源
    print("[2] 解析FDFIELD资源...")
    fdfield_offsets = parse_dat_offsets_format2(fdfield_data)
    resource_count = len(fdfield_offsets)
    print(f"  资源数量: {resource_count}")
    print(f"  地图数量: {resource_count // 3}\n")
    
    # 3. 获取地图资源（每个地图3个资源）
    print("[3] 获取地图资源...")
    layout_res_idx = map_id * 3
    control_res_idx = map_id * 3 + 1
    spawn_res_idx = map_id * 3 + 2
    
    if layout_res_idx + 2 >= resource_count:
        print(f"  错误：地图 {map_id} 的资源不存在")
        return
    
    layout_start = fdfield_offsets[layout_res_idx]
    control_start = fdfield_offsets[control_res_idx]
    spawn_start = fdfield_offsets[spawn_res_idx]
    
    layout_end = fdfield_offsets[layout_res_idx + 1] if layout_res_idx + 1 < resource_count else len(fdfield_data)
    control_end = fdfield_offsets[control_res_idx + 1] if control_res_idx + 1 < resource_count else len(fdfield_data)
    
    layout_data = fdfield_data[layout_start:layout_end]
    control_data = fdfield_data[control_start:control_end]
    spawn_data = fdfield_data[spawn_start:]
    
    print(f"  Layout资源 (#{layout_res_idx}): 偏移={layout_start}, 大小={len(layout_data)} 字节")
    print(f"  Control资源 (#{control_res_idx}): 偏移={control_start}, 大小={len(control_data)} 字节")
    print(f"  Spawn资源 (#{spawn_res_idx}): 偏移={spawn_start}\n")
    
    # 4. 解析地图尺寸
    print("[4] 解析地图尺寸...")
    map_width = struct.unpack_from("<H", layout_data, 0)[0]
    map_height = struct.unpack_from("<H", layout_data, 2)[0]
    total_tiles = map_width * map_height
    
    print(f"  地图宽度: {map_width} 瓦片")
    print(f"  地图高度: {map_height} 瓦片")
    print(f"  总瓦片数: {total_tiles}\n")
    
    # 5. 获取terrain_set_id
    print("[5] 获取terrain_set_id...")
    terrain_set_id = control_data[0]
    print(f"  terrain_set_id: {terrain_set_id}\n")
    
    # 6. 读取FDSHAP.DAT
    print("[6] 读取FDSHAP.DAT...")
    with open(FDSHAP_PATH, "rb") as f:
        fdshap_data = f.read()
    
    # 修复：使用格式2解析（无计数）
    fdshap_offsets = parse_dat_offsets_format2(fdshap_data)
    fdshap_resource_count = len(fdshap_offsets)
    print(f"  资源数量: {fdshap_resource_count}\n")
    
    # 7. 获取瓦片集（从FDOTHER加载调色板）
    print("[7] 获取瓦片集...")
    tile_set_res_idx = terrain_set_id * 2  # 偶数索引是瓦片集
    
    if tile_set_res_idx >= fdshap_resource_count:
        print(f"  错误：瓦片集资源 {tile_set_res_idx} 不存在")
        return
    
    tile_set_start = fdshap_offsets[tile_set_res_idx]
    tile_set_end = fdshap_offsets[tile_set_res_idx + 1] if tile_set_res_idx + 1 < fdshap_resource_count else len(fdshap_data)
    
    tile_set_data = fdshap_data[tile_set_start:tile_set_end]
    print(f"  瓦片集资源 (#{tile_set_res_idx}): {len(tile_set_data)} 字节\n")
    
    # 8. 加载调色板（从FDOTHER.DAT）
    print("[8] 加载调色板（从FDOTHER.DAT）...")
    palette = load_palette_from_fdother(map_id)
    if palette is None:
        print("  [ERROR] 加载调色板失败，使用灰度调色板")
        palette = [(i, i, i) for i in range(256)]
    else:
        print(f"  解析了 {len(palette)} 个调色板条目\n")
    
    # 9. 解析瓦片偏移表（IDA验证方法）
    print("[9] 解析瓦片偏移表（IDA验证）...")
    tile_info = parse_tile_offsets_ida(tile_set_data)
    if tile_info is None:
        print("  错误：解析失败")
        return
    
    tile_offsets, tile_w, tile_h, tile_count = tile_info
    print(f"  瓦片尺寸: {tile_w}x{tile_h}")
    print(f"  瓦片数量: {tile_count}")
    print(f"  找到 {len(tile_offsets)} 个瓦片偏移\n")
    
    # 10. 解析地形ID（IDA验证公式）
    print("[10] 解析地形ID（IDA验证公式）...")
    terrain_ids = []
    pos = 4  # Layout数据从byte 4开始是瓦片数据
    
    for i in range(total_tiles):
        if pos + 4 > len(layout_data):
            break
        
        terrain_4bytes = layout_data[pos:pos+4]
        terrain_id = parse_terrain_id_ida(terrain_4bytes)
        terrain_ids.append(terrain_id)
        pos += 4
    
    unique_terrain_ids = set(terrain_ids)
    min_tid = min(terrain_ids) if terrain_ids else 0
    max_tid = max(terrain_ids) if terrain_ids else 0
    
    print(f"  解析了 {len(terrain_ids)} 个瓦片")
    print(f"  唯一地形ID数量: {len(unique_terrain_ids)}")
    print(f"  地形ID范围: {min_tid} - {max_tid}")
    
    if max_tid >= tile_count:
        print(f"  [INFO] 地形ID范围超过瓦片数量，使用 mod {tile_count} 映射")
        print(f"         这将使所有地形ID映射到有效瓦片索引\n")
    else:
        print(f"  [OK] 地形ID在瓦片范围内\n")
    
    # 11. 生成地图图像
    print("[11] 生成地图图像...")
    map_image = Image.new("RGB", (map_width * tile_w, map_height * tile_h), (0, 0, 0))
    
    rendered_count = 0
    
    for tile_index in range(len(terrain_ids)):
        terrain_id = terrain_ids[tile_index]
        tile_idx = terrain_id % tile_count  # 关键：使用模运算映射地形ID到瓦片索引
        
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
    
    print(f"  渲染了 {rendered_count}/{total_tiles} 个瓦片\n")
    
    # 12. 保存结果
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"map_{map_id}_fixed_palette.png"
    map_image.save(output_path)
    print(f"[12] 保存地图图像: {output_path}\n")
    
    # 13. 生成统计信息
    print("[13] 统计信息:")
    print(f"  地图尺寸: {map_width}x{map_height}")
    print(f"  瓦片尺寸: {tile_w}x{tile_h}")
    print(f"  总瓦片数: {total_tiles}")
    print(f"  渲染瓦片: {rendered_count}")
    print(f"  地形ID范围: {min_tid}-{max_tid}")
    print(f"  唯一地形ID: {len(unique_terrain_ids)}")
    print(f"  可用瓦片: {tile_count}")
    print(f"  图像大小: {map_image.width}x{map_image.height} 像素\n")


if __name__ == "__main__":
    map_id = 0
    if len(sys.argv) > 1:
        try:
            map_id = int(sys.argv[1])
        except ValueError:
            print(f"用法: {sys.argv[0]} [map_id]")
            sys.exit(1)
    
    test_map_ida_verified(map_id)
