"""批量解码索引2的所有子资源，保存为图像"""
import struct
import os
import sys

# 检查 PIL 是否可用
try:
    from PIL import Image
except ImportError:
    print("PIL not available")
    sys.exit(1)

FDOTHER_PATH = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"
OUTPUT_DIR = "D:/workspace/fd2_dat_freebuff/output/index2_tiles"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(FDOTHER_PATH, "rb") as f:
    data = f.read()

# 解析主索引表
offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack_from("<I", data, pos)[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4

idx2_start = offsets[2]
idx2_end = offsets[3]
idx2_data = data[idx2_start:idx2_end]

# 解析调色板
pal_start = offsets[0]
pal_end = offsets[1]
pal_data = data[pal_start:pal_end]
palette = []
for i in range(256):
    r = pal_data[i*3]
    g = pal_data[i*3+1]
    b = pal_data[i*3+2]
    # 6位 -> 8位
    r = (r << 2) | (r >> 4)
    g = (g << 2) | (g >> 4)
    b = (b << 2) | (b >> 4)
    palette.append((r, g, b))

# 78个dword偏移表
sub_offsets = []
for i in range(78):
    off = struct.unpack_from("<I", idx2_data, i*4)[0]
    sub_offsets.append(off)
# 加上文件结束作为最后一个
sub_offsets.append(len(idx2_data))


def decode_rle_correct(src, w, h):
    """与 sub_4E98D 一致的 RLE 解码"""
    src_idx = 0
    n_src = len(src)
    pixels = []
    for y in range(h):
        row = [0] * w
        bx = w
        dst_idx = 0
        while bx > 0:
            if src_idx >= n_src:
                break
            b = src[src_idx]
            top2 = b & 0xC0
            if top2 == 0x00:
                # FILL
                count = b + 1
                v = src[src_idx + 1] if src_idx + 1 < n_src else 0
                src_idx += 2
                for i in range(min(count, w - dst_idx)):
                    row[dst_idx + i] = v
                dst_idx += count
                bx -= count
            elif top2 == 0x40:
                # FILL2
                count = (b & 0x3F) + 1
                v = src[src_idx + 1] if src_idx + 1 < n_src else 0
                src_idx += 2
                for i in range(count):
                    pos = dst_idx + 1 + i * 2
                    if pos < w:
                        row[pos] = v
                dst_idx += count * 2
                bx -= count * 2
            elif top2 == 0x80:
                # COPY
                count = (b & 0x3F) + 1
                src_idx += 1
                for i in range(min(count, w - dst_idx)):
                    if src_idx + i < n_src:
                        row[dst_idx + i] = src[src_idx + i]
                src_idx += count
                dst_idx += count
                bx -= count
            elif top2 == 0xC0:
                # SKIP
                count = (b & 0x3F) + 1
                src_idx += 1
                dst_idx += count
                bx -= count
        pixels.append(row)
    return pixels


# 解码所有子资源
print(f"索引2 大小: {idx2_end - idx2_start} 字节")
print(f"子资源数量: {len(sub_offsets) - 1}")
print(f"输出目录: {OUTPUT_DIR}")

# 创建一个网格图像展示所有子资源
GRID_COLS = 8
GRID_ROWS = (78 + GRID_COLS - 1) // GRID_COLS

# 找到最大尺寸
max_w, max_h = 0, 0
all_sub = []
for i in range(78):
    sub_off = sub_offsets[i]
    sub_size = sub_offsets[i+1] - sub_off
    if sub_off + 5 > len(idx2_data):
        continue
    sub_data = idx2_data[sub_off:sub_off+sub_size]
    if len(sub_data) < 5:
        continue
    w = struct.unpack_from("<H", sub_data, 0)[0]
    h = struct.unpack_from("<H", sub_data, 2)[0]
    win = sub_data[4]
    if w > 0 and h > 0 and w < 100 and h < 100:
        if w > max_w: max_w = w
        if h > max_h: max_h = h
        all_sub.append((i, sub_data, w, h, win))

print(f"有效子资源: {len(all_sub)}, 最大尺寸: {max_w}x{max_h}")

# 创建网格图像
grid_w = max_w * GRID_COLS + (GRID_COLS + 1) * 2
grid_h = max_h * GRID_ROWS + (GRID_ROWS + 1) * 2
grid_img = Image.new("RGB", (grid_w, grid_h), (32, 32, 32))
pixels_grid = grid_img.load()

# 解码并放置每个子资源
for idx, sub_data, w, h, win in all_sub:
    rle_data = sub_data[5:]
    pixels = decode_rle_correct(rle_data, w, h)

    # 应用调色板
    col = idx % GRID_COLS
    row = idx // GRID_COLS
    x0 = 2 + col * (max_w + 2)
    y0 = 2 + row * (max_h + 2)

    for y in range(h):
        for x in range(w):
            p = pixels[y][x]
            if p != 0:
                # 应用调色板窗口
                pal_idx = (p + win) & 0xFF
                if x0+x < grid_w and y0+y < grid_h:
                    pixels_grid[x0+x, y0+y] = palette[pal_idx]

grid_path = os.path.join(OUTPUT_DIR, "index2_all_grid.png")
grid_img.save(grid_path)
print(f"网格图像保存: {grid_path}")

# 单独保存每个子资源
for idx, sub_data, w, h, win in all_sub:
    rle_data = sub_data[5:]
    pixels = decode_rle_correct(rle_data, w, h)

    img = Image.new("RGB", (w, h), (32, 32, 32))
    img_pixels = img.load()
    for y in range(h):
        for x in range(w):
            p = pixels[y][x]
            if p != 0:
                pal_idx = (p + win) & 0xFF
                img_pixels[x, y] = palette[pal_idx]

    img_path = os.path.join(OUTPUT_DIR, f"sub_{idx:02d}_{w}x{h}.png")
    img.save(img_path)

print(f"单独图像保存: {len(all_sub)} 个")
