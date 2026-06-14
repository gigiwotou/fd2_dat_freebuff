"""手动追踪子资源0的解码过程"""
import struct

FDOTHER_PATH = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"

with open(FDOTHER_PATH, "rb") as f:
    data = f.read()

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

sub_offsets = []
for i in range(78):
    off = struct.unpack_from("<I", idx2_data, i*4)[0]
    sub_offsets.append(off)

sub0_off = sub_offsets[0]
sub1_off = sub_offsets[1]
sub0_size = sub1_off - sub0_off
sub0_data = idx2_data[sub0_off:sub0_off+sub0_size]
rle_data = sub0_data[5:]

# 手动模拟汇编
# bx (16-bit) = 行剩余
# 初始 y=0 时 bx = width
# 每行开始 bx = width
# 移动到下一行时: edi += pitch (320)
# 但 pitch 通常 = width (单行缓冲)

# 假设: 单行 24 像素, 20 行
# 实际上, dst 缓冲可能是 24*20 = 480 字节
# 每行从 bx = 24 开始, 移动到下一行 bx = 24

w = 24
h = 20
src_idx = 0
n_src = len(rle_data)
dst = [0] * (w * h)  # 单缓冲
bx = 0  # 行剩余
arg8 = h  # 行计数

edi = 0  # dst 偏移
y = 0

print(f"手动追踪汇编逻辑:")
print(f"初始: edi=0, y=0")
print()

while y < h:
    # 行开始: bx = width
    bx = w
    if y > 0:
        edi += 0  # 假设单行缓冲 pitch = width, 不需要 edi += pitch - width
    print(f"--- y={y}, bx={bx} ---")
    while bx > 0:
        if src_idx >= n_src:
            print(f"  src_idx={src_idx} >= n_src={n_src}, 停止")
            break
        b = rle_data[src_idx]
        top2 = b & 0xC0
        cl = b
        cl = (cl << 1) & 0xFF
        cf1 = (b & 0x80) != 0
        if cf1:
            # b >= 0x80: 跳到 loc_4EA17
            cl = (cl << 1) & 0xFF
            cf2 = (b & 0x40) != 0
            if cf2:
                # b >= 0xC0: SKIP
                # shr cl, 2; inc cl
                count = ((b & 0x3F) + 1) & 0xFF
                # count = (b & 0x3F) + 1
                # add edi, ecx (即 edi += count)
                edi += count
                bx -= count
                src_idx += 1
                print(f"  [{src_idx-1:3d}] SKIP count={count} (b=0x{b:02X}), edi={edi}, bx={bx}")
            else:
                # 0x80 <= b < 0xC0: COPY
                # shr cl, 2; inc cl
                count = (b & 0x3F) + 1
                # sub bx, cx
                bx -= count
                # rep movsb: 从 src 复制 count 字节
                src_idx += 1
                values = []
                for k in range(count):
                    if src_idx < n_src:
                        v = rle_data[src_idx]
                        src_idx += 1
                        values.append(v)
                # 写入 dst
                for k, v in enumerate(values):
                    if edi + k < w * h:
                        dst[edi + k] = v
                edi += count
                print(f"  [{src_idx-count-1:3d}] COPY count={count} (b=0x{b:02X}), values={values[:5]}..., edi={edi}, bx={bx}")
        else:
            # 0x40 <= b < 0x80: FILL2 (再次 shl 后 CF=1)
            cl = (cl << 1) & 0xFF
            cf2 = (b & 0x40) != 0
            if cf2:
                # FILL2
                # shr cl, 2; inc cl
                count = (b & 0x3F) + 1
                # sub bx, cx 两次: bx -= 2*count
                bx -= 2 * count
                # lodsb 读 v
                src_idx += 1
                v = rle_data[src_idx]
                src_idx += 1
                # inc edi, stosb, loop
                # 写入 dst[edi+1], dst[edi+3], ..., dst[edi+2*count-1]
                for k in range(count):
                    pos = edi + 1 + k * 2
                    if pos < w * h:
                        dst[pos] = v
                edi += 2 * count
                print(f"  [{src_idx-2:3d}] FILL2 count={count} (b=0x{b:02X}) v=0x{v:02X}, edi={edi}, bx={bx}")
            else:
                # FILL (b < 0x40)
                # shr cl, 2; inc cl
                count = b + 1
                # sub bx, cx
                bx -= count
                # lodsb 读 v
                src_idx += 1
                v = rle_data[src_idx]
                src_idx += 1
                # rep stosb
                for k in range(count):
                    if edi + k < w * h:
                        dst[edi + k] = v
                edi += count
                print(f"  [{src_idx-2:3d}] FILL count={count} (b=0x{b:02X}) v=0x{v:02X}, edi={edi}, bx={bx}")
    y += 1

print()
print("最终 dst:")
for row in range(h):
    line = " ".join(f"{dst[row*w+col]:02X}" if dst[row*w+col] != 0 else ".." for col in range(w))
    print(f"  y={row:2d}: {line}")
