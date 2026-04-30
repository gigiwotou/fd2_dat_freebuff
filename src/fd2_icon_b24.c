/*
 * fd2_icon_b24.c - FDICON.B24 icon loader for FD2
 * 
 * Based on IDA sub_11019 (0x11019) decompilation.
 * 
 * FDICON.B24 file format:
 * - Bytes 0-5: Header (skipped by fseek to 6)
 * - Bytes 6+: Offset table (1680 DWORDs = 140 icons × 12 offsets + 4 extra)
 * - Icon data: starts at the first icon's offset
 * 
 * Each icon has 12 segments/frames with their own file offsets.
 * Data size = next_icon_offset[0] - current_icon_offset[0]
 */

#include "fd2_icon_b24.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FDICON_MAX_ICONS 140
#define FDICON_SEGMENTS_PER_ICON 12
#define FDICON_OFFSET_TABLE_SIZE 6720  /* 1680 DWORDs */
#define FDICON_BUFFER_SIZE 207362      /* 0x32A02 from IDA */
#define FDICON_HEADER_RESERVE 1920     /* Reserved space at buffer start */

/* Global state (matching game's global variables) */
static unsigned char* g_icon_buffer = NULL;      /* dword_53A61 - main icon buffer */
static unsigned int g_cached_ids[FDICON_MAX_ICONS]; /* dword_53B17 - cached icon IDs */
static int g_cached_count = 0;                   /* dword_53BDF - number of cached icons */
static unsigned char* g_buf_ptr = NULL;          /* buf - write pointer in buffer */
static unsigned int* g_file_offsets = NULL;      /* offset table from file */
static FILE* g_icon_file = NULL;                 /* FDICON.B24 file handle */
static int g_total_icons = 0;                    /* total icons in file */

/*
 * Initialize the FDICON.B24 system
 * Based on IDA: every call to sub_11019 reads the offset table,
 * but we optimize by reading it once during init.
 */
int fd2_icon_init(const char* fdicon_path) {
    FILE* fp;
    long file_size;
    int i;

    if (g_icon_file != NULL) {
        return 0;  /* Already initialized */
    }

    fp = fopen(fdicon_path, "rb");
    if (!fp) {
        fprintf(stderr, "fd2_icon_init: failed to open %s\n", fdicon_path);
        return -1;
    }

    /* Get file size for validation */
    fseek(fp, 0, SEEK_END);
    file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    /* Read offset table: 6720 bytes starting at offset 6 */
    g_file_offsets = (unsigned int*)malloc(FDICON_OFFSET_TABLE_SIZE);
    if (!g_file_offsets) {
        fprintf(stderr, "fd2_icon_init: out of memory for offset table\n");
        fclose(fp);
        return -1;
    }

    fseek(fp, 6, SEEK_SET);
    if (fread(g_file_offsets, 1, FDICON_OFFSET_TABLE_SIZE, fp) != FDICON_OFFSET_TABLE_SIZE) {
        fprintf(stderr, "fd2_icon_init: failed to read offset table\n");
        free(g_file_offsets);
        fclose(fp);
        return -1;
    }

    /* Calculate total number of valid icons */
    g_total_icons = 0;
    for (i = 0; i < FDICON_MAX_ICONS; i++) {
        unsigned int first_offset = g_file_offsets[i * FDICON_SEGMENTS_PER_ICON];
        /* Check if offset is reasonable (must be >= 6 and < file_size) */
        if (first_offset < 6 || (unsigned long)first_offset >= (unsigned long)file_size) {
            break;
        }
        g_total_icons++;
    }

    printf("fd2_icon_init: %d icons found in %s (file size: %ld bytes)\n",
           g_total_icons, fdicon_path, file_size);

    /* Allocate main icon buffer (matching IDA: malloc(0x32A00 + 2)) */
    g_icon_buffer = (unsigned char*)malloc(FDICON_BUFFER_SIZE);
    if (!g_icon_buffer) {
        fprintf(stderr, "fd2_icon_init: out of memory for icon buffer\n");
        free(g_file_offsets);
        fclose(fp);
        return -1;
    }

    /* Initialize state */
    g_cached_count = 0;
    g_buf_ptr = NULL;
    g_icon_file = fp;
    memset(g_cached_ids, 0xFF, sizeof(g_cached_ids));

    printf("fd2_icon_init: buffer allocated (%d bytes)\n", FDICON_BUFFER_SIZE);

    return 0;
}

/*
 * Load an icon into cache and return its cache index
 * 
 * Exact logic from IDA sub_11019(int icon_id, FILE* fd):
 * 1. Read offset table from file (optimized: we read once in init)
 * 2. Extract 13 offsets for this icon (12 segments + 1 for size calculation)
 * 3. Calculate data_size = v9[12] - v9[0]
 * 4. Check if icon_id is already in g_cached_ids[] -> return index if found
 * 5. If first icon (g_cached_count == 0):
 *    - Store icon_id in g_cached_ids[0]
 *    - fseek to v9[0], read data_size bytes to buffer + 1920
 *    - Store adjusted offsets in buffer[0..47] (12 DWORDs)
 *    - Set buf_ptr = 1920 + data_size
 *    - Increment g_cached_count
 *    - Return 0
 * 6. If subsequent icon:
 *    - Store icon_id in g_cached_ids[g_cached_count]
 *    - fseek to v9[0], read data_size bytes to buf_ptr + g_icon_buffer
 *    - Store adjusted offsets in buffer[g_cached_count * 12..]
 *    - buf_ptr += data_size
 *    - Increment g_cached_count
 *    - Return g_cached_count - 1
 * 
 * Returns: cache index on success, -1 on error
 */
int fd2_icon_get(int icon_id) {
    unsigned int v9[13];
    unsigned int data_start, data_end;
    unsigned int data_size;
    int buffer_start;
    int base_idx;
    int i;

    if (!g_icon_file || !g_file_offsets || !g_icon_buffer) {
        fprintf(stderr, "fd2_icon_get: not initialized\n");
        return -1;
    }

    if (icon_id < 0 || icon_id >= g_total_icons) {
        fprintf(stderr, "fd2_icon_get: icon_id %d out of range (max %d)\n",
                icon_id, g_total_icons);
        return -1;
    }

    /* Step 1: Extract 13 offsets for this icon */
    base_idx = icon_id * FDICON_SEGMENTS_PER_ICON;
    for (i = 0; i < 13; i++) {
        v9[i] = g_file_offsets[base_idx + i];
    }

    /* Step 2: Calculate data size */
    data_start = v9[0];
    data_end = v9[12];  /* Next icon's first offset */
    data_size = data_end - data_start;

    /* Step 3: Check if already cached */
    for (i = 0; i < g_cached_count; i++) {
        if (g_cached_ids[i] == icon_id) {
            return i;  /* Already cached, return index */
        }
    }

    /* Step 4: Cache full check */
    if (g_cached_count >= FDICON_MAX_ICONS) {
        fprintf(stderr, "fd2_icon_get: cache full (max %d)\n", FDICON_MAX_ICONS);
        return -1;
    }

    /* Step 5: Record cached icon ID */
    g_cached_ids[g_cached_count] = icon_id;

    /* Step 6: Determine buffer start position */
    if (g_cached_count == 0) {
        buffer_start = FDICON_HEADER_RESERVE;
    } else {
        buffer_start = (int)(g_buf_ptr - g_icon_buffer);
    }

    /* Step 7: Seek to icon data and read */
    if (fseek(g_icon_file, data_start, SEEK_SET) != 0) {
        fprintf(stderr, "fd2_icon_get: seek to %u failed\n", data_start);
        return -1;
    }

    if ((size_t)fread(g_icon_buffer + buffer_start, 1, data_size, g_icon_file) != data_size) {
        fprintf(stderr, "fd2_icon_get: read failed (expected %u bytes)\n", data_size);
        return -1;
    }

    /* Step 8: Store adjusted offsets in buffer */
    /* IDA logic: *(dword*)(dword_53A61 + 4 * (n12 + 12 * g_cached_count)) = v9[n12] - v9[0] + buffer_start */
    for (i = 0; i < FDICON_SEGMENTS_PER_ICON; i++) {
        unsigned int* offset_ptr = (unsigned int*)(g_icon_buffer + 4 * (i + FDICON_SEGMENTS_PER_ICON * g_cached_count));
        *offset_ptr = v9[i] - v9[0] + buffer_start;
    }

    /* Step 9: Update buffer pointer */
    if (g_cached_count == 0) {
        g_buf_ptr = g_icon_buffer + FDICON_HEADER_RESERVE + data_size;
    } else {
        g_buf_ptr += data_size;
    }

    /* Step 10: Increment cached count */
    int cache_index = g_cached_count;
    g_cached_count++;

    printf("fd2_icon_get: loaded icon %d -> cache index %d (size=%u, buffer_start=%d)\n",
           icon_id, cache_index, data_size, buffer_start);

    return cache_index;
}

/*
 * Get pointer to icon data in cache for a specific segment
 * 
 * The offsets are stored in the buffer at:
 *   buffer[cache_index * 12 * 4 + segment * 4]  (4 bytes each, 12 segments)
 * 
 * Returns: pointer to segment data, or NULL if invalid
 */
unsigned char* fd2_icon_get_segment(int cache_index, int segment) {
    unsigned int offset;
    unsigned int* offset_ptr;

    if (cache_index < 0 || cache_index >= g_cached_count) {
        fprintf(stderr, "fd2_icon_get_segment: invalid cache_index %d\n", cache_index);
        return NULL;
    }

    if (segment < 0 || segment >= FDICON_SEGMENTS_PER_ICON) {
        fprintf(stderr, "fd2_icon_get_segment: invalid segment %d\n", segment);
        return NULL;
    }

    /* Get the stored offset for this segment */
    offset_ptr = (unsigned int*)(g_icon_buffer + 4 * (segment + FDICON_SEGMENTS_PER_ICON * cache_index));
    offset = *offset_ptr;

    return g_icon_buffer + offset;
}

/*
 * Get the main icon buffer pointer (matching game's dword_53A61)
 */
unsigned char* fd2_icon_get_buffer(void) {
    return g_icon_buffer;
}

/*
 * Get current buffer usage in bytes
 */
int fd2_icon_get_buffer_size(void) {
    if (!g_buf_ptr) return 0;
    return (int)(g_buf_ptr - g_icon_buffer);
}

/*
 * Get number of cached icons
 */
int fd2_icon_get_cached_count(void) {
    return g_cached_count;
}

/*
 * Get total icon count from file
 */
int fd2_icon_get_count(void) {
    return g_total_icons;
}

/*
 * Get the cached icon ID for a given cache index
 */
int fd2_icon_get_cached_id(int cache_index) {
    if (cache_index < 0 || cache_index >= g_cached_count) {
        return -1;
    }
    return g_cached_ids[cache_index];
}

/*
 * Cleanup and free all resources
 */
void fd2_icon_shutdown(void) {
    if (g_icon_file) {
        fclose(g_icon_file);
        g_icon_file = NULL;
    }
    if (g_file_offsets) {
        free(g_file_offsets);
        g_file_offsets = NULL;
    }
    if (g_icon_buffer) {
        free(g_icon_buffer);
        g_icon_buffer = NULL;
    }
    g_cached_count = 0;
    g_total_icons = 0;
    g_buf_ptr = NULL;
    memset(g_cached_ids, 0xFF, sizeof(g_cached_ids));
}
