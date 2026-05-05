#ifndef FD2_AFM_H
#define FD2_AFM_H

#include "fd2_decoder.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Forward declarations */
typedef struct fd2_render fd2_render_t;
typedef struct fd2_resources fd2_resources_t;

/* ========================================================================
 * AFM (Animation File Manager) Decoder
 *
 * Decodes animations stored in ANI.DAT using the AFM format.
 * Based on sub_20421 (player) and sub_36FF4 (frame dispatch).
 *
 * The AFM format stores frame-by-frame animations with an internal
 * command system that updates a 320x200 frame buffer and 256-color palette.
 * ======================================================================== */

/* ---- AFM Constants ---- */
#define FD2_AFM_HEADER_SIZE  173    /* AFM header is 173 bytes */
#define FD2_AFM_FRAME_HDR    8      /* Frame header is 8 bytes */
#define FD2_AFM_TITLE_OFF    0x51   /* Title string offset in header */
#define FD2_AFM_FRAMES_OFF   0xA5   /* Frame count offset in header */
#define FD2_AFM_DATA_OFF     0xAD   /* First frame data offset (173 = 0xAD) */

/* ---- AFM Context ---- */
typedef struct fd2_afm {
    /* Resource data pointer (from fd2_dat_get_resource on ANI.DAT) */
    const u8*   data;
    u32         data_size;
    u32         offset;           /* Current read position */

    /* Animation info */
    u16         total_frames;
    u16         current_frame;

    /* Decoding buffers */
    u8          palette[FD2_PALETTE_BYTES];    /* 768 bytes (6-bit VGA) */
    u8          frame[FD2_SCREEN_SIZE];        /* 64000 bytes (indexed) */
} fd2_afm_t;

/* ---- Lifecycle ---- */

/*
 * Initialize AFM context (zeroes all buffers).
 */
void fd2_afm_init(fd2_afm_t* afm);

/*
 * Open an AFM animation from raw ANI.DAT resource data.
 * Parses the 173-byte header, extracts frame count.
 * Returns 0 on success, -1 on error.
 */
int fd2_afm_open(fd2_afm_t* afm, const u8* resource_data, u32 resource_size);

/*
 * Reset to first frame (rewind).
 */
void fd2_afm_rewind(fd2_afm_t* afm);

/* ---- Frame Decoding ---- */

/*
 * Decode the next frame in the animation.
 * Dispatches commands from the frame data to update palette/frame buffers.
 * Call this once per animation tick.
 * Returns 0 on success, -1 when animation is complete or on error.
 */
int fd2_afm_decode_next_frame(fd2_afm_t* afm);

/*
 * Check if all frames have been decoded.
 */
bool fd2_afm_is_done(const fd2_afm_t* afm);

/* ---- Accessors ---- */

/*
 * Get the current frame buffer (320x200 indexed pixels).
 */
const u8* fd2_afm_get_frame(const fd2_afm_t* afm);

/*
 * Get the current palette (768 bytes, 6-bit VGA values).
 */
const u8* fd2_afm_get_palette(const fd2_afm_t* afm);

/* ---- AFM-Specific RLE ---- */

/*
 * AFM RLE decompression (different from sub_4E98D).
 * Format: if (byte & 0xC0) == 0xC0 → RLE: count = byte & 0x3F, value = next byte
 *         else → literal: byte is the value
 * Returns number of source bytes consumed, or -1 on error.
 */
int fd2_afm_rle_decode(const u8* src, u32 src_size, u8* dst, u32 dst_size);

/* ---- AFM Player (sub_20421) ---- */

/*
 * Play an AFM animation from ANI.DAT resource.
 * 对应原游戏 sub_20421 (地址: 0x20421)
 * 
 * 原游戏逻辑:
 *   1. 分配768字节调色板缓冲和64000字节帧缓冲
 *   2. 调用sub_36FD3初始化缓冲
 *   3. 打开ANI.DAT文件，定位到动画索引
 *   4. 读取173字节头，获取帧数
 *   5. 循环播放每一帧:
 *      - 读取8字节帧头
 *      - 读取帧数据
 *      - 调用sub_36FF4分发命令
 *      - 延迟a6毫秒
 *      - 如果a7非零，检查键盘输入
 *      - 调用sub_4E381刷新屏幕
 *   6. 释放资源，关闭文件
 *
 * 参数:
 *   anim_index - ANI.DAT中的动画索引 (1=开场动画)
 *   frame_delay - 每帧延迟毫秒数
 *   check_input - 是否检查键盘输入 (1=是, 0=否)
 *   render - 渲染器
 *   resources - 资源管理器
 *
 * 返回: 0=正常播放完成, 1=用户按键中断
 */
int fd2_afm_play(int anim_index, int frame_delay, int check_input,
                 fd2_render_t* render, fd2_resources_t* resources);

#ifdef __cplusplus
}
#endif

#endif /* FD2_AFM_H */
