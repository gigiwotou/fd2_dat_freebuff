import struct, sys

path = 'd:/workspace/fd2_dat_freebuff/game/FDTXT.DAT'
with open(path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
print(f'FDTXT.DAT: {count} resources')

res0_start = struct.unpack_from('<I', data, 10)[0]
res0_end = struct.unpack_from('<I', data, 14)[0]
print(f'Resource 0: start=0x{res0_start:X}, size={res0_end - res0_start}')

res0 = data[res0_start:res0_end]
sub_count = struct.unpack_from('<h', res0, 0)[0]
print(f'Sub-texts: {sub_count}')

offsets = []
for i in range(sub_count):
    off = struct.unpack_from('<H', res0, 2 + i * 2)[0]
    offsets.append(off)

def get_words(res_data, sub_idx, offsets):
    start = offsets[sub_idx]
    end = offsets[sub_idx + 1] if sub_idx + 1 < len(offsets) else len(res_data)
    td = res_data[start:end]
    words = []
    for i in range(0, len(td), 2):
        if i + 2 <= len(td):
            w = struct.unpack_from('<h', td, i)[0]
            words.append(w)
    return words

# Check first few sub-texts
print('\n=== First 15 sub-texts ===')
for idx in range(min(15, sub_count)):
    words = get_words(res0, idx, offsets)
    print(f'  [{idx:3d}] {words[:20]}')

# Check around 500-550
print('\n=== Sub-texts 510-555 ===')
for idx in range(510, min(555, sub_count)):
    words = get_words(res0, idx, offsets)
    if len(words) > 0:
        print(f'  [{idx:3d}] len={len(words):3d}  {words[:15]}')

# Search for sub-texts with only positive words (likely display text)
print('\n=== Short display texts (all positive, 1-10 chars) ===')
for idx in range(sub_count):
    words = get_words(res0, idx, offsets)
    if 1 <= len(words) <= 10:
        all_pos = all(w >= 0 for w in words[:-1])  # last might be -1
        if all_pos:
            print(f'  [{idx:3d}] {words}')