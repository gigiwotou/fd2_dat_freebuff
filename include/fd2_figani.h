#ifndef FD2_FIGANI_H
#define FD2_FIGANI_H

#include "fd2_decoder.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * FIGANI — FIGANI.DAT 的戰鬥動畫格式
 *
 * 對齊 fd2_re remake/internal/figani/figani.go（Parse / decodeRLE）。
 *
 * 資源頭：
 *   +0      uint8  幀數 n   —— 注意是「單字節」！
 *   +1      uint8  prelude flag（原 0x29409 / 0x29510 各自獨立讀取）
 *   +2      uint8  prelude 幀數；若 byte1 != 0 則不得 > n
 *   +8      偏移表，n 項 uint32 LE
 *
 * 每幀 13 字節頭：
 *   +0..1   int16  X
 *   +2..3   int16  Y
 *   +4      原始位元組（未定語義，保留）
 *   +5      原始位元組（未定語義，保留）
 *   +6      uint8  Delay   —— 單字節！讀成 u16 會把 byte7 混進來
 *   +7      原始位元組（未定語義，保留）
 *   +9..10  uint16 Width
 *   +11..12 uint16 Height
 *   +13     像素流（four-mode RLE）
 *
 * four-mode RLE（與 fd2_rle.c 的 sub_4E98D 同一套語義）：
 *   ctrl = 讀 1 字節; count = (ctrl & 0x3F) + 1; mode = ctrl >> 6
 *     mode 0 (00) 填充    : 讀 1 字節值，連續寫 count 個，span = count
 *     mode 1 (01) 間隔填充: 讀 1 字節值，寫到 x+2*i+1，span = count*2
 *     mode 2 (10) 字面    : 讀 count 字節依次寫，span = count
 *     mode 3 (11) 透明    : 保留目的端，span = count
 *   逐行處理，每行 x 從 0 開始。
 *
 * 本格式同時輸出 mask（哪些像素被寫入），透明 span 不會產生 mask。
 * ========================================================================== */

typedef struct {
    int    x, y;
    int    width, height;
    int    delay;
    u8     raw4, raw5, raw7;
    u32    offset;   /* 幀在資源內的起點 */
} fd2_figani_frame_t;

typedef struct {
    int                  count;
    u8                   header1;   /* prelude flag */
    u8                   header2;   /* prelude 幀數 */
    u8                   header4;
    fd2_figani_frame_t*  frames;
} fd2_figani_t;

/**
 * fd2_figani_open — 解析 FIGANI 動畫目錄
 *
 * 會驗證 n 非零、表不越界、偏移遞增、幾何合法（w/h 在 1..1024）。
 * @return 0 成功（需 fd2_figani_close）, -1 失敗
 */
int fd2_figani_open(const u8* data, u32 size, fd2_figani_t* out);

void fd2_figani_close(fd2_figani_t* anim);

/**
 * fd2_figani_decode_frame — 解碼單一幀
 *
 * @param dst_pixels 至少 width*height；未寫入處填 0
 * @param dst_mask   至少 width*height；1 表示該像素有資料，0 表示透明
 *                   可傳 NULL 表示不需要 mask
 * @return 0 成功, -1 失敗
 */
int fd2_figani_decode_frame(const u8* data, u32 size,
                            const fd2_figani_t* anim, int index,
                            u8* dst_pixels, u8* dst_mask);

#ifdef __cplusplus
}
#endif

#endif /* FD2_FIGANI_H */
