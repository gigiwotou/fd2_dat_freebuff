#ifndef FD2_LMI1_H
#define FD2_LMI1_H

#include "fd2_decoder.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * LMI1 — 第三種容器格式（LLLLLL 與 AFM 之外）
 *
 * FDOTHER.DAT 內有 7 個資源是 LMI1 bank：#3 #5 #6 #9 #13 #14 #29
 *   #3  count=23   #5  count=138  #6  count=230
 *   #9  count=12   #13 count=28   #14 count=32   #29 count=24
 *
 * 佈局（對齊 fd2_re remake/internal/fdother/lmi1.go 的 ParseLMI1）：
 *   +0..3   magic "LMI1"
 *   +4..5   uint16 LE  count（項目數）
 *   +6      偏移表，count 項 uint32 LE
 *   每項:   uint16 width, uint16 height, 之後接 high-run RLE 像素流
 *
 * 像素流從 entry+4 開始，解到 width*height 個像素即止。
 * 注意 fd2_re 明確註解：目錄只給起點、不給壓縮流終點，重複可能跨到下一個
 * entry；原生 0x4e916 的 width*height 迴圈滿了就停，多餘的重複狀態直接丟棄。
 *
 * high-run RLE 規則（與 DATO 頭像同一套，見 fd2_rle_decode_portrait）：
 *   c <= 0xC0 : 字面像素，值 = c
 *   c >  0xC0 : 重複 (c - 0xC0) 次下一個 byte
 * 注意與 fd2_afm_rle_palette 的 `(b & 0xC0) == 0xC0` 判定在 b == 0xC0 時
 * 行為不同：本格式下 0xC0 是字面值 0xC0，不是 count=0 的重複。
 * ========================================================================== */

#define FD2_LMI1_MAGIC     "LMI1"
#define FD2_LMI1_MAGIC_LEN 4

typedef struct {
    int  width;
    int  height;
    u32  offset;   /* entry 在資源內的起點 */
    u32  end;      /* 下一個 entry 起點；最後一項為資源大小 */
} fd2_lmi1_entry_t;

typedef struct {
    int               count;
    fd2_lmi1_entry_t* entries;
} fd2_lmi1_t;

/**
 * fd2_lmi1_is_magic — 判斷資料是否為 LMI1 bank
 * @return 1 是, 0 否
 */
int fd2_lmi1_is_magic(const u8* data, u32 size);

/**
 * fd2_lmi1_open — 讀取 LMI1 目錄
 *
 * 會驗證 count 非零、表不越界、且每個 entry 偏移遞增且落在資源內，
 * 與 fd2_re ParseLMI1 的檢查一致。
 *
 * @return 0 成功（需用 fd2_lmi1_close 釋放）, -1 失敗
 */
int fd2_lmi1_open(const u8* data, u32 size, fd2_lmi1_t* out);

/**
 * fd2_lmi1_close — 釋放 fd2_lmi1_open 配置的資源
 */
void fd2_lmi1_close(fd2_lmi1_t* bank);

/**
 * fd2_lmi1_decode_entry — 解碼單一 entry 的像素
 *
 * @param dst_capacity dst 可容納位元組數，至少需 width*height
 * @return 解出的像素數（應等於 width*height）, -1 失敗
 */
int fd2_lmi1_decode_entry(const u8* data, u32 size,
                          const fd2_lmi1_t* bank, int index,
                          u8* dst, int dst_capacity);

#ifdef __cplusplus
}
#endif

#endif /* FD2_LMI1_H */
