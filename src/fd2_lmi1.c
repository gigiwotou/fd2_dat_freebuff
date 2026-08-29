/**
 * FD2 LMI1 — 第三種容器格式解析器
 *
 * 對齊 fd2_re remake/internal/fdother/lmi1.go（ParseLMI1 / decodeLMI1Pixels）。
 * 詳見 include/fd2_lmi1.h 的的格式說明。
 */

#include "fd2_lmi1.h"
#include <stdlib.h>
#include <string.h>

int fd2_lmi1_is_magic(const u8* data, u32 size) {
    if (!data || size < FD2_LMI1_MAGIC_LEN) return 0;
    return memcmp(data, FD2_LMI1_MAGIC, FD2_LMI1_MAGIC_LEN) == 0 ? 1 : 0;
}

int fd2_lmi1_open(const u8* data, u32 size, fd2_lmi1_t* out) {
    if (!data || !out) return -1;
    memset(out, 0, sizeof(*out));

    if (!fd2_lmi1_is_magic(data, size)) return -1;
    if (size < 6) return -1;

    u32 count = (u32)data[4] | ((u32)data[5] << 8);
    u32 table_end = 6 + count * 4;

    /* count == 0 或表越界 -> 拒絕（與 fd2_re 相同） */
    if (count == 0 || table_end > size) return -1;

    fd2_lmi1_entry_t* ents =
        (fd2_lmi1_entry_t*)calloc(count, sizeof(fd2_lmi1_entry_t));
    if (!ents) return -1;

    u32 previous = table_end;
    for (u32 i = 0; i < count; i++) {
        u32 off = (u32)data[6 + 4 * i]       |
                  ((u32)data[6 + 4 * i + 1] << 8)  |
                  ((u32)data[6 + 4 * i + 2] << 16) |
                  ((u32)data[6 + 4 * i + 3] << 24);
        u32 end = size;
        if (i + 1 < count) {
            end = (u32)data[6 + 4 * (i + 1)]       |
                  ((u32)data[6 + 4 * (i + 1) + 1] << 8)  |
                  ((u32)data[6 + 4 * (i + 1) + 2] << 16) |
                  ((u32)data[6 + 4 * (i + 1) + 3] << 24);
        }

        /* off 必須遞增、至少 4 位元組放得下寬高、且不越界 */
        if (off < previous || off + 4 > end || end > size) {
            free(ents);
            return -1;
        }

        int w = (int)((u32)data[off] | ((u32)data[off + 1] << 8));
        int h = (int)((u32)data[off + 2] | ((u32)data[off + 3] << 8));

        /* Sanity-bound the dimensions.
         *
         * FDOTHER #3 matches the "LMI1" magic and has a self-consistent
         * 23-entry directory with a fixed 256-byte stride, but its entries
         * carry NO width/height header - the first bytes are already RLE
         * opcodes (0xC1 0x08 ...), so they decode to garbage dimensions
         * such as 49416x50371. Without this bound a caller sizing a buffer
         * from w*h would try to allocate ~2.3 GB.
         *
         * The bound is generous for UI cells (1M px ~= 1024x1024) and makes
         * #3 fail here, so it falls back to RAW instead of being promoted
         * to a bank it is not. #3's real layout is still unconfirmed. */
        if (w <= 0 || h <= 0 || w > 1024 || h > 1024) {
            free(ents);
            return -1;
        }

        ents[i].width  = w;
        ents[i].height = h;
        ents[i].offset = off;
        ents[i].end    = end;
        previous = off;
    }

    out->count   = (int)count;
    out->entries = ents;
    return 0;
}

void fd2_lmi1_close(fd2_lmi1_t* bank) {
    if (!bank) return;
    free(bank->entries);
    bank->entries = NULL;
    bank->count = 0;
}

/**
 * high-run RLE（0x4e916），與 DATO 頭像同一套演算法。
 *   c <= 0xC0 : 字面像素，值 = c
 *   c >  0xC0 : 重複 (c - 0xC0) 次下一個 byte
 *
 * 原生行為：目的端 width*height 填滿即停，跨過 entry 邊界的殘餘重複狀態
 * 直接丟棄（fd2_re 註解明確描述）。這裡以 want 為界複製同樣的截斷行為。
 */
static int decode_pixels(const u8* stream, u32 avail, int want, u8* dst) {
    int written = 0;
    u32 pos = 0;

    while (written < want) {
        if (pos >= avail) return -1;          /* 資料流提前結束 */

        u8 c = stream[pos++];
        if (c <= 0xC0) {
            dst[written++] = c;
            continue;
        }

        int run = (int)c - 0xC0;
        if (pos >= avail) return -1;          /* 重複缺少像素值 */

        u8 v = stream[pos++];
        int remain = want - written;
        if (run > remain) run = remain;       /* 目的端邊界截斷 */

        memset(dst + written, v, (size_t)run);
        written += run;
    }
    return written;
}

int fd2_lmi1_decode_entry(const u8* data, u32 size,
                          const fd2_lmi1_t* bank, int index,
                          u8* dst, int dst_capacity) {
    if (!data || !bank || !dst || index < 0 || index >= bank->count) return -1;

    const fd2_lmi1_entry_t* e = &bank->entries[index];
    int want = e->width * e->height;
    if (want <= 0 || want > dst_capacity) return -1;

    /* 像素流從 entry+4 開始；可用長度以「所屬資源尾端」為界，
     * 因為 fd2_re 註解指出重複可能跨過下一個目錄偏移。 */
    u32 start = e->offset + 4;
    if (start > size) return -1;

    return decode_pixels(data + start, size - start, want, dst);
}
