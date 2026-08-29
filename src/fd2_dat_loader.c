/**
 * FD2 DAT文件加载器 - 统一实现
 *
 * 基于IDA Pro sub_111BA汇编代码1:1还原
 */

#include "../include/fd2_dat_loader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================================
 * 文件级操作
 * ============================================================================ */

u8* fd2_dat_loader_load_file(const char* path, u32* out_size) {
    if (!path) return NULL;

    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "fd2_dat_loader_load_file: cannot open %s\n", path);
        if (out_size) *out_size = 0;
        return NULL;
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (size <= 0) {
        fprintf(stderr, "fd2_dat_loader_load_file: invalid file size %ld\n", size);
        fclose(f);
        if (out_size) *out_size = 0;
        return NULL;
    }

    u8* data = (u8*)malloc((size_t)size);
    if (!data) {
        fclose(f);
        if (out_size) *out_size = 0;
        return NULL;
    }

    if (fread(data, 1, (size_t)size, f) != (size_t)size) {
        fprintf(stderr, "fd2_dat_loader_load_file: read error\n");
        free(data);
        fclose(f);
        if (out_size) *out_size = 0;
        return NULL;
    }
    fclose(f);

    if (out_size) *out_size = (u32)size;
    return data;
}

/* sub_111BA: 加载DAT文件中指定资源
 *
 * 1. fopen(filename, "rb")
 * 2. fseek to offset table entry: 4 * index + 6
 * 3. fread 8 bytes: offset(4) + next_offset(4)
 * 4. size = next_offset - offset
 * 5. malloc(size)
 * 6. fseek to resource data
 * 7. fread resource data
 * 8. fclose, return pointer
 */
u8* fd2_dat_loader_load_resource(const char* filename, byte* prev_buf,
                                  int resource_idx, dword* out_size) {
    if (!filename || resource_idx < 0) {
        if (out_size) *out_size = 0;
        return NULL;
    }

    /* Free old resource pointer if provided (IDA: if (a6) free(a6)) */
    if (prev_buf) {
        free(prev_buf);
    }

    FILE* fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "\n\n File not found %s!!! \n\n", filename);
        if (out_size) *out_size = 0;
        return NULL;
    }

    /* Seek to offset table entry: 4 * index + 6 */
    if (fseek(fp, 4 * resource_idx + 6, SEEK_SET) != 0) {
        fprintf(stderr, "fd2_dat_loader_load_resource: seek error for index %d\n", resource_idx);
        fclose(fp);
        if (out_size) *out_size = 0;
        return NULL;
    }

    /* Read 8 bytes: offset (4 bytes) + next_offset (4 bytes) */
    u32 offsets[2];
    if (fread(offsets, 1, 8, fp) != 8) {
        fprintf(stderr, "fd2_dat_loader_load_resource: failed to read offset for index %d\n", resource_idx);
        fclose(fp);
        if (out_size) *out_size = 0;
        return NULL;
    }

    u32 offset = offsets[0];
    u32 next_offset = offsets[1];
    u32 size = next_offset - offset;

    if (out_size) *out_size = size;

    /* Allocate memory for the resource */
    u8* buffer = (u8*)malloc(size);
    if (!buffer) {
        fprintf(stderr, "Out of Memory at Load %s Number:%d!!\n", filename, resource_idx);
        fclose(fp);
        return NULL;
    }

    /* Seek to resource data */
    fseek(fp, offset, SEEK_SET);

    /* Read resource data */
    if (fread(buffer, 1, size, fp) != size) {
        fprintf(stderr, "fd2_dat_loader_load_resource: failed to read resource %d (size=%u)\n",
                resource_idx, size);
        free(buffer);
        fclose(fp);
        if (out_size) *out_size = 0;
        return NULL;
    }
    fclose(fp);

    return buffer;
}

/* 加载DAT文件中的调色板(资源0或7) */
int fd2_dat_loader_load_palette(const char* filename, byte palette[768]) {
    if (!filename || !palette) return -1;

    FILE* f = fopen(filename, "rb");
    if (!f) return -1;

    /* Read header */
    char magic[FD2_DAT_MAGIC_LEN];
    if (fread(magic, 1, FD2_DAT_MAGIC_LEN, f) != FD2_DAT_MAGIC_LEN) {
        fclose(f);
        return -1;
    }
    if (memcmp(magic, FD2_DAT_MAGIC_STR, FD2_DAT_MAGIC_LEN) != 0) {
        fclose(f);
        return -1;
    }

    u32 resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return -1;
    }

    /* Read offset table */
    u32* offsets = (u32*)malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return -1;
    }
    fseek(f, 10, SEEK_SET);
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        return -1;
    }

    /* Try resource 7 first (palette), then resource 0 */
    int palette_res = 7;
    if (palette_res >= resource_count) {
        palette_res = 0;
    }

    u32 start = offsets[palette_res];
    fseek(f, start, SEEK_SET);
    size_t read = fread(palette, 1, FD2_PALETTE_BYTES, f);
    free(offsets);
    fclose(f);

    return (read == FD2_PALETTE_BYTES) ? 0 : -1;
}

/* ============================================================================
 * 内存级操作
 * ============================================================================ */

int fd2_dat_loader_get_resource_count(const u8* data, u32 data_size) {
    if (!data || data_size < 10) return -1;

    if (memcmp(data, FD2_DAT_MAGIC_STR, FD2_DAT_MAGIC_LEN) != 0) {
        return -1;
    }

    /* The u32 at +6 is NOT a resource count. It is the byte offset where the
     * offset table ends -- equivalently, the start offset of resource 0.
     *
     * Layout (verified against every .DAT in the original distribution):
     *   +0..5   magic "LLLLLL"
     *   +6      offset table, N entries of u32
     *   +6+4N   resource 0  (== table_end)
     *   ...
     * The last table entry is an end-of-file sentinel equal to the file size,
     * not a real resource.
     *
     *   N          = (table_end - 6) / 4
     *   resources  = N - 1
     *
     * e.g. FDOTHER.DAT: table_end=422 -> N=104 -> 103 resources
     *      (the old code returned 422, over-reporting by ~4x, which silently
     *      disabled every "index >= resource_count" bound check).
     */
    u32 table_end;
    memcpy(&table_end, data + 6, 4);

    if (table_end < 10 || table_end > data_size) {
        return -1;
    }

    u32 entries = (table_end - 6) / 4;
    if (entries < 1) {
        return -1;
    }

    return (int)(entries - 1);
}

int fd2_dat_loader_parse_entries(const u8* data, u32 data_size,
                                  u32** out_offsets, int* out_count) {
    if (!data || !out_offsets || !out_count) return -1;

    *out_offsets = NULL;
    *out_count = 0;

    if (data_size < 14) {
        fprintf(stderr, "fd2_dat_loader_parse_entries: data too small (%u bytes)\n", data_size);
        return -1;
    }

    /* Check magic "LLLLLL" */
    if (memcmp(data, FD2_DAT_MAGIC_STR, FD2_DAT_MAGIC_LEN) != 0) {
        fprintf(stderr, "fd2_dat_loader_parse_entries: invalid magic\n");
        return -1;
    }

    /* Read resource count at byte 6 */
    u32 resource_count = data[6] | (data[7] << 8) | (data[8] << 16) | (data[9] << 24);

    if (resource_count == 0 || resource_count > 5000) {
        fprintf(stderr, "fd2_dat_loader_parse_entries: invalid resource count (%u)\n", resource_count);
        return -1;
    }

    /* Check if we have enough data for the offset table */
    if (10 + resource_count * 4 > data_size) {
        fprintf(stderr, "fd2_dat_loader_parse_entries: not enough data for %u resources\n", resource_count);
        return -1;
    }

    u32* offsets = (u32*)malloc(resource_count * sizeof(u32));
    if (!offsets) return -1;

    /* Read offsets from byte 10 onwards */
    for (u32 i = 0; i < resource_count; i++) {
        u32 pos = 10 + i * 4;
        offsets[i] = data[pos] | (data[pos+1] << 8) |
                     (data[pos+2] << 16) | (data[pos+3] << 24);
    }

    *out_offsets = offsets;
    *out_count = (int)resource_count;
    return 0;
}

int fd2_dat_loader_parse_entries_format2(const u8* data, u32 data_size,
                                          int max_count,
                                          u32** out_offsets, int* out_count) {
    if (!data || !out_offsets || !out_count || max_count <= 0) return -1;

    *out_offsets = NULL;
    *out_count = 0;

    u32* offsets = (u32*)malloc((size_t)max_count * sizeof(u32));
    if (!offsets) return -1;

    int count = 0;
    u32 pos = 6;
    while (pos + 4 <= data_size && count < max_count) {
        u32 offset = data[pos] | (data[pos+1] << 8) |
                     (data[pos+2] << 16) | (data[pos+3] << 24);

        if (offset > data_size) {
            break;
        }

        offsets[count] = offset;
        count++;
        pos += 4;
    }

    *out_offsets = offsets;
    *out_count = count;
    return 0;
}

const u8* fd2_dat_loader_get_resource(const u8* data, u32 data_size,
                                       const u32* offsets, int count,
                                       int index, u32* out_size) {
    if (!data || !offsets || index < 0 || index >= count - 1) {
        if (out_size) *out_size = 0;
        return NULL;
    }

    u32 start = offsets[index];
    u32 end = offsets[index + 1];

    if (start >= data_size || end > data_size || end <= start) {
        if (out_size) *out_size = 0;
        return NULL;
    }

    if (out_size) *out_size = end - start;
    return data + start;
}

/* ============================================================================
 * 辅助函数
 * ============================================================================ */

void fd2_dat_loader_get_dimensions(const byte* data, int* width, int* height) {
    if (!data || !width || !height) {
        if (width) *width = 0;
        if (height) *height = 0;
        return;
    }

    /* 4字节头: width[2] + height[2] (小端) */
    *width = data[0] | (data[1] << 8);
    *height = data[2] | (data[3] << 8);
}
