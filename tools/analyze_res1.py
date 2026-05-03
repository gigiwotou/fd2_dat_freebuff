with open('game/FDOTHER.DAT', 'rb') as f:
    # Get resource 1 start
    f.seek(10)  # skip magic+count
    offsets = []
    for i in range(422):
        offset = int.from_bytes(f.read(4), 'little')
        offsets.append(offset)
    
    res1_start = offsets[1]
    res1_end = offsets[2] if len(offsets) > 1 else None
    res1_size = res1_end - res1_start if res1_end else 1000
    print("Resource 1: offset=%d (0x%04X), size=%d" % (res1_start, res1_start, res1_size))
    
    # Read resource 1 data
    f.seek(res1_start)
    res1_data = f.read(res1_size)
    
    # Parse internal offset table
    internal_offsets = []
    pos = 0
    while pos + 4 <= len(res1_data) - 4:
        off = int.from_bytes(res1_data[pos:pos+4], 'little')
        if off > 100000:  # Not a valid offset within resource 1
            break
        internal_offsets.append(off)
        pos += 4
    
    print("Resource 1 has %d internal offsets:" % len(internal_offsets))
    for i, off in enumerate(internal_offsets[:15]):
        print("  Sub-resource %d: offset within res1=%d (0x%04X), absolute=%d (0x%04X)" % (
            i, off, off, res1_start + off, res1_start + off))
    
    # Check first sub-resource
    if len(internal_offsets) > 0:
        sub0_off = internal_offsets[0]
        sub1_off = internal_offsets[1] if len(internal_offsets) > 1 else len(res1_data)
        f.seek(res1_start + sub0_off)
        sub0_data = f.read(sub1_off - sub0_off if sub1_off < len(res1_data) else 100)
        print("\nSub-resource 0 (at absolute offset %d):" % (res1_start + sub0_off))
        print(" ".join("%02X" % b for b in sub0_data[:32]))
        w = sub0_data[0] | (sub0_data[1] << 8)
        h = sub0_data[2] | (sub0_data[3] << 8)
        print("Dimensions: %dx%d" % (w, h))
