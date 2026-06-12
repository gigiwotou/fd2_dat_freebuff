"""验证 tile 10 (3x16) 和其他报告错误的tile的实际解码情况"""
import struct
fdother_path = r"D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
with open(fdother_path, "rb") as f:
    data = f.read()

idx5_offset = struct.unpack_from("<I", data, 6 + 5 * 4)[0]
table_idx = 6 + 5 * 4 + 4
while table_idx + 4 <= len(data):
    next_off = struct.unpack_from("<I", data, table_idx)[0]
    if next_off == 0 or next_off > len(data):
        break
    table_idx += 4
idx5_end = struct.unpack_from("<I", data, table_idx)[0]
res5 = data[idx5_offset:idx5_end]
tile_count = struct.unpack_from("<H", res5, 4)[0]
tile_offsets = [struct.unpack_from("<I", res5, 6 + i * 4)[0] for i in range(tile_count + 1)]


def decode_4ebff_strict(src, src_size, w, h):
    sp = 4
    out = bytearray(w * h)
    ah = 0
    al = 0
    for row in range(h):
        for col in range(w):
            if ah == 0:
                if sp >= src_size: return None
                al = src[sp]; sp += 1
                if al > 0xC0:
                    ah = (al - 0xC1) & 0xFF
                    if sp >= src_size: return None
                    al = src[sp]; sp += 1
            else:
                ah = (ah - 1) & 0xFF
            out[row * w + col] = al
    if sp != src_size: return None
    return list(out)


def decode_4e_strict(src, src_size, w, h):
    s = src[4:]
    data_size = src_size - 4
    if data_size <= 0: return None
    pos = 0
    out = bytearray(w * h)
    out_idx = 0
    total = w * h
    while out_idx < total and pos < data_size:
        c = s[pos]; pos += 1
        top2 = c & 0xC0
        count = (((4 * c) & 0xFF) >> 2) + 1
        if top2 == 0x00:
            if pos >= data_size: return None
            v = s[pos]; pos += 1
            for k in range(min(count, total - out_idx)):
                if v: out[out_idx] = v
                out_idx += 1
        elif top2 == 0x40:
            if pos >= data_size: return None
            v = s[pos]; pos += 1
            max_k = (total - out_idx + 1) // 2
            for k in range(min(count, max_k)):
                if v: out[out_idx] = v
                out_idx += 2
            if out_idx > total: out_idx = total
        elif top2 == 0x80:
            for k in range(min(count, total - out_idx)):
                if pos >= data_size: return None
                v = s[pos]; pos += 1
                if v: out[out_idx] = v
                out_idx += 1
        else:
            out_idx += count
    if out_idx != total: return None
    if pos != data_size: return None
    return list(out)


# 测试所有用户报告的 tile
report_tiles = [10, 14, 16, 18, 19, 55, 56, 57, 58, 59, 60, 61, 62, 63]

out_lines = []
out_lines.append(f"=== 用户报告的'原本正确现在错误'的tile分析 ===")
out_lines.append(f"{'idx':>3} {'w':>4} {'h':>4} {'size':>5} {'sub4ebff':>10} {'4e':>5} {'uncomp':>7} {'chosen':>10} {'first_data'}")
out_lines.append("-" * 110)
for ti in report_tiles:
    off = tile_offsets[ti]
    size = tile_offsets[ti+1] - off
    if off + 4 > len(res5):
        continue
    w, h = struct.unpack_from("<HH", res5, off)
    src = res5[off:off+size]
    r1 = decode_4ebff_strict(src, size, w, h)
    r2 = decode_4e_strict(src, size, w, h)
    expected = 4 + w * h
    r3 = None
    if size >= expected:
        # uncomp
        r3 = list(src[4:4 + w * h])
    # 模拟 fd2_rle_lmi1_decode_tile_auto 的逻辑
    chosen = "FAIL"
    chosen_pixels = None
    if r1 is not None:
        chosen = "sub4ebff"
        chosen_pixels = r1
    elif r2 is not None:
        chosen = "4e"
        chosen_pixels = r2
    elif r3 is not None:
        chosen = "uncomp"
        chosen_pixels = r3
    first_data = ' '.join(f'{b:02x}' for b in src[4:24])
    out_lines.append(f"{ti:>3} {w:>4} {h:>4} {size:>5} {str(r1 is not None):>10} {str(r2 is not None):>5} {str(r3 is not None):>7} {chosen:>10} {first_data}")

with open(r'D:/workspace/fd2_dat_freebuff/output/regression_check.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines) + '\n')
print('OK')
