/**
 * FD2 FIGANI — FIGANI.DAT 戰鬥動畫解析器
 *
 * 對齊 fd2_re remake/internal/figani/figani.go（Parse / decodeRLE）。
 * 格式說明見 include/fd2_figani.h。
 */

#include "fd2_figani.h"
#include <stdlib.h>
#include <string.h>

int fd2_figani_open(const u8* data, u32 size, fd2_figani_t* out) {
    if (!data || !out) return -1;
    memset(out, 0, sizeof(*out));

    if (size < 12) return -1;

    /* 幀數是單字節。把它當 u16 讀會拒絕所有 prelude flag 被設定的原版動畫。 */
    int n = (int)data[0];
    if (n == 0 || 8 + 4 * (u32)n > size) return -1;

    if (data[1] != 0 && (int)data[2] > n) return -1;

    fd2_figani_frame_t* fr =
        (fd2_figani_frame_t*)calloc((size_t)n, sizeof(fd2_figani_frame_t));
    if (!fr) return -1;

    u32 previous = 8 + 4 * (u32)n;
    for (int i = 0; i < n; i++) {
        u32 p = 8 + 4 * (u32)i;
        u32 off = (u32)data[p]       | ((u32)data[p + 1] << 8) |
                  ((u32)data[p + 2] << 16) | ((u32)data[p + 3] << 24);
        u32 end = size;
        if (i + 1 < n) {
            u32 q = 8 + 4 * (u32)(i + 1);
            end = (u32)data[q]       | ((u32)data[q + 1] << 8) |
                  ((u32)data[q + 2] << 16) | ((u32)data[q + 3] << 24);
        }
        /* off 遞增、至少 13 字節放得下幀頭、且不越界 */
        if (off < previous || off + 13 > end || end > size) {
            free(fr);
            return -1;
        }

        int w = (int)((u32)data[off + 9]  | ((u32)data[off + 10] << 8));
        int h = (int)((u32)data[off + 11] | ((u32)data[off + 12] << 8));
        if (w <= 0 || h <= 0 || w > 1024 || h > 1024) {
            free(fr);
            return -1;
        }

        /* X/Y 是有號 16 位元（動畫可為負偏移） */
        int sx = (int)(s16)((u16)((u32)data[off] | ((u32)data[off + 1] << 8)));
        int sy = (int)(s16)((u16)((u32)data[off + 2] | ((u32)data[off + 3] << 8)));

        fr[i].x      = sx;
        fr[i].y      = sy;
        fr[i].width  = w;
        fr[i].height = h;
        /* Delay 是單字節；讀成 u16 會把 byte7 混進來（fd2_re 註解） */
        fr[i].delay  = (int)data[off + 6];
        fr[i].raw4   = data[off + 4];
        fr[i].raw5   = data[off + 5];
        fr[i].raw7   = data[off + 7];
        fr[i].offset = off;

        previous = off;
    }

    out->count   = n;
    out->header1 = data[1];
    out->header2 = data[2];
    out->header4 = data[4];
    out->frames  = fr;
    return 0;
}

void fd2_figani_close(fd2_figani_t* anim) {
    if (!anim) return;
    free(anim->frames);
    anim->frames = NULL;
    anim->count = 0;
}

int fd2_figani_decode_frame(const u8* data, u32 size,
                            const fd2_figani_t* anim, int index,
                            u8* dst_pixels, u8* dst_mask) {
    if (!data || !anim || !dst_pixels || index < 0 || index >= anim->count)
        return -1;

    const fd2_figani_frame_t* f = &anim->frames[index];
    int w = f->width, h = f->height;

    u32 start = f->offset + 13;
    if (start > size) return -1;

    const u8* src = data + start;
    u32 avail = size - start;
    u32 pos = 0;

    if (dst_pixels) memset(dst_pixels, 0, (size_t)w * h);
    if (dst_mask)   memset(dst_mask,   0, (size_t)w * h);

    for (int y = 0; y < h; y++) {
        int x = 0;
        while (x < w) {
            if (pos >= avail) return -1;          /* RLE 在行內耗盡 */

            u8 ctrl = src[pos++];
            int count = (int)(ctrl & 0x3F) + 1;
            int mode  = (int)(ctrl >> 6);
            int span  = (mode == 1) ? count * 2 : count;

            if (x + span > w) return -1;          /* 超出該行寬度 */

            u8* prow = dst_pixels + y * w;
            u8* mrow = dst_mask ? (dst_mask + y * w) : NULL;

            switch (mode) {
            case 0: {                              /* 填充 */
                if (pos >= avail) return -1;
                u8 v = src[pos++];
                for (int i = 0; i < count; i++) {
                    prow[x + i] = v;
                    if (mrow) mrow[x + i] = 1;
                }
                break;
            }
            case 1: {                              /* 間隔填充（寫奇數位） */
                if (pos >= avail) return -1;
                u8 v = src[pos++];
                for (int i = 0; i < count; i++) {
                    prow[x + 2 * i + 1] = v;
                    if (mrow) mrow[x + 2 * i + 1] = 1;
                }
                break;
            }
            case 2: {                              /* 字面 */
                if (pos + (u32)count > avail) return -1;
                for (int i = 0; i < count; i++) {
                    u8 v = src[pos++];
                    prow[x + i] = v;
                    if (mrow) mrow[x + i] = 1;
                }
                break;
            }
            default:                               /* 3: 透明，保留目的端 */
                break;
            }
            x += span;
        }
    }
    return 0;
}
