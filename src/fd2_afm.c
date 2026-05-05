/**
 * AFM (Animation File Manager) Decoder Implementation
 *
 * Decodes animations stored in ANI.DAT using the AFM format.
 * Based on sub_20421 (player) and sub_36FF4 (frame dispatch).
 *
 * Command dispatch table (funcs_37012):
 *   0x00 = sub_36E3D: Fill palette with single color (768 bytes)
 *   0x01 = sub_36E57: Copy palette (768 bytes direct)
 *   0x02 = sub_36E65: RLE decode palette (768 bytes)
 *   0x03 = sub_36EA7: Multi-segment copy to palette
 *   0x04 = sub_36EE0: Fill entire frame (64000 bytes) with color
 *   0x05 = sub_36F08: Direct copy frame data (64000 bytes)
 *   0x06 = sub_36F24: RLE decode frame data (64000 bytes)
 *   0x07 = sub_36F69: Pixel set (individual pixels at specific offsets)
 *   0x08 = sub_36F82: RLE pixel fill (run-length fill at specific offsets)
 *   0x09 = sub_36FAC: Multi-segment copy to frame
 */

#include "fd2_afm.h"
#include "fd2_render.h"
#include "fd2_resources.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* ========================================================================
 * Internal Command Handlers
 *
 * Each handler receives the current data pointer and returns the number
 * of source bytes consumed. The original game uses ESI register advancement
 * which we replicate by returning byte counts.
 * ======================================================================== */

/* ---- cmd 0x00: Fill palette with single color (sub_36E3D) ----
 * Reads 1 byte, fills all 768 palette bytes with that value.
 */
static int cmd_fill_palette(fd2_afm_t* afm, const u8* data, u32 avail) {
    (void)avail;  /* Only needs 1 byte, checked before call */
    u8 value = data[0];
    memset(afm->palette, value, FD2_PALETTE_BYTES);
    return 1;
}

/* ---- cmd 0x01: Copy palette (sub_36E57) ----
 * Copies 768 bytes directly into the palette buffer.
 */
static int cmd_copy_palette(fd2_afm_t* afm, const u8* data, u32 avail) {
    if (avail < FD2_PALETTE_BYTES) return -1;
    memcpy(afm->palette, data, FD2_PALETTE_BYTES);
    return FD2_PALETTE_BYTES;
}

/* ---- cmd 0x02: RLE decode palette (sub_36E65) ----
 * Decodes RLE data into 768 palette bytes.
 * RLE format: if (byte & 0xC0) == 0xC0 → count = byte & 0x3F, value = next byte
 *             else → literal byte value
 */
static int cmd_rle_palette(fd2_afm_t* afm, const u8* data, u32 avail) {
    (void)avail;
    int written = 0;
    int consumed = 0;

    while (written < FD2_PALETTE_BYTES) {
        u8 byte = data[consumed++];
        if ((byte & 0xC0) == 0xC0) {
            /* RLE run */
            int count = byte & 0x3F;
            u8 value = data[consumed++];
            int fill = (written + count > FD2_PALETTE_BYTES)
                       ? (FD2_PALETTE_BYTES - written) : count;
            memset(afm->palette + written, value, fill);
            written += count;
        } else {
            /* Literal */
            afm->palette[written++] = byte;
        }
    }

    return consumed;
}

/* ---- cmd 0x03: Multi-segment copy to palette (sub_36EA7) ----
 * Reads segment count, then for each segment:
 *   1 byte: starting color index (offset = index * 3)
 *   1 byte: number of colors (N colors = N * 3 bytes)
 *   N*3 bytes: raw palette data
 */
static int cmd_multi_palette(fd2_afm_t* afm, const u8* data, u32 avail) {
    if (avail < 1) return -1;
    int consumed = 0;
    int seg_count = data[consumed++];

    for (int s = 0; s < seg_count; s++) {
        /* Each segment header: 1 byte color_idx + 1 byte num_colors = 2 */
        if ((u32)(consumed + 2) > avail) return -1;
        int color_idx = data[consumed++];
        int num_colors = data[consumed++];
        int byte_count = num_colors * 3;

        if ((u32)(consumed + byte_count) > avail) return -1;
        int dst_offset = color_idx * 3;
        if (dst_offset + byte_count <= FD2_PALETTE_BYTES) {
            memcpy(afm->palette + dst_offset, data + consumed, byte_count);
        }
        consumed += byte_count;
    }

    return consumed;
}

/* ---- cmd 0x04: Fill entire frame with color (sub_36EE0) ----
 * Reads 1 byte, fills all 64000 frame bytes with that value.
 */
static int cmd_fill_frame(fd2_afm_t* afm, const u8* data, u32 avail) {
    (void)avail;
    u8 value = data[0];
    memset(afm->frame, value, FD2_SCREEN_SIZE);
    return 1;
}

/* ---- cmd 0x05: Direct copy frame data (sub_36F08) ----
 * Copies 64000 bytes directly into the frame buffer.
 */
static int cmd_copy_frame(fd2_afm_t* afm, const u8* data, u32 avail) {
    if (avail < FD2_SCREEN_SIZE) return -1;
    memcpy(afm->frame, data, FD2_SCREEN_SIZE);
    return FD2_SCREEN_SIZE;
}

/* ---- cmd 0x06: RLE decode frame (sub_36F24) ----
 * Decodes RLE data into 64000 frame bytes.
 * Same RLE format as cmd 0x02 but targeting the frame buffer.
 */
static int cmd_rle_frame(fd2_afm_t* afm, const u8* data, u32 avail) {
    (void)avail;
    int written = 0;
    int consumed = 0;

    while (written < FD2_SCREEN_SIZE) {
        u8 byte = data[consumed++];
        if ((byte & 0xC0) == 0xC0) {
            /* RLE run */
            int count = byte & 0x3F;
            u8 value = data[consumed++];
            int fill = (written + count > FD2_SCREEN_SIZE)
                       ? (FD2_SCREEN_SIZE - written) : count;
            memset(afm->frame + written, value, fill);
            written += count;
        } else {
            /* Literal */
            afm->frame[written++] = byte;
        }
    }

    return consumed;
}

/* ---- cmd 0x07: Pixel set (sub_36F69) ----
 * Reads pixel count (16-bit), then for each pixel:
 *   16-bit offset + 8-bit color value
 * Sets frame[offset] = color for each pixel.
 */
static int cmd_pixel_set(fd2_afm_t* afm, const u8* data, u32 avail) {
    if (avail < 2) return -1;
    int consumed = 0;
    int count = data[consumed] | (data[consumed + 1] << 8);
    consumed += 2;

    /* Each pixel: 2 bytes offset + 1 byte color = 3 bytes */
    if (avail < (u32)(2 + count * 3)) return -1;

    for (int i = 0; i < count; i++) {
        int offset = data[consumed] | (data[consumed + 1] << 8);
        consumed += 2;
        u8 color = data[consumed++];
        if (offset >= 0 && offset < FD2_SCREEN_SIZE) {
            afm->frame[offset] = color;
        }
    }

    return consumed;
}

/* ---- cmd 0x08: RLE pixel fill (sub_36F82) ----
 * Reads segment count (16-bit), then for each segment:
 *   16-bit offset + 8-bit run length + 8-bit fill value
 * Fills frame[offset..offset+count] with fill value.
 */
static int cmd_rle_pixel_fill(fd2_afm_t* afm, const u8* data, u32 avail) {
    if (avail < 2) return -1;
    int consumed = 0;
    int seg_count = data[consumed] | (data[consumed + 1] << 8);
    consumed += 2;

    for (int s = 0; s < seg_count; s++) {
        /* Each segment: 2 bytes offset + 1 byte run_len + 1 byte value = 4 */
        if ((u32)(consumed + 4) > avail) return -1;
        int offset = data[consumed] | (data[consumed + 1] << 8);
        consumed += 2;
        int run_len = data[consumed++];
        u8 value = data[consumed++];

        if (offset >= 0 && offset + run_len <= FD2_SCREEN_SIZE) {
            memset(afm->frame + offset, value, run_len);
        }
    }

    return consumed;
}

/* ---- cmd 0x09: Multi-segment copy to frame (sub_36FAC) ----
 * Reads segment count (16-bit), then for each segment:
 *   16-bit offset + 8-bit byte count + N raw bytes
 * Copies N bytes from source to frame at offset.
 */
static int cmd_multi_copy_frame(fd2_afm_t* afm, const u8* data, u32 avail) {
    if (avail < 2) return -1;
    int consumed = 0;
    int seg_count = data[consumed] | (data[consumed + 1] << 8);
    consumed += 2;

    for (int s = 0; s < seg_count; s++) {
        /* Each segment header: 2 bytes offset + 1 byte count = 3 */
        if ((u32)(consumed + 3) > avail) return -1;
        int offset = data[consumed] | (data[consumed + 1] << 8);
        consumed += 2;
        int byte_count = data[consumed++];
        if ((u32)(consumed + byte_count) > avail) return -1;
        if (offset >= 0 && offset + byte_count <= FD2_SCREEN_SIZE) {
            memcpy(afm->frame + offset, data + consumed, byte_count);
        }
        consumed += byte_count;
    }

    return consumed;
}

/* ---- Command dispatch table ---- */
typedef int (*afm_cmd_fn)(fd2_afm_t* afm, const u8* data, u32 avail);

static const afm_cmd_fn afm_commands[10] = {
    cmd_fill_palette,       /* 0x00 */
    cmd_copy_palette,       /* 0x01 */
    cmd_rle_palette,        /* 0x02 */
    cmd_multi_palette,      /* 0x03 */
    cmd_fill_frame,         /* 0x04 */
    cmd_copy_frame,         /* 0x05 */
    cmd_rle_frame,          /* 0x06 */
    cmd_pixel_set,          /* 0x07 */
    cmd_rle_pixel_fill,     /* 0x08 */
    cmd_multi_copy_frame,   /* 0x09 */
};

/* ========================================================================
 * Frame Dispatch (sub_36FF4)
 *
 * Executes 'param' commands from the frame data.
 * Each command reads a command byte, dispatches to the handler,
 * and advances the data pointer by the number of bytes consumed.
 * ======================================================================== */
static int dispatch_frame(fd2_afm_t* afm, u16 param, const u8* data, u32 data_size) {
    const u8* ptr = data;
    const u8* end = data + data_size;

    for (u16 i = 0; i < param; i++) {
        if (ptr >= end) {
            fprintf(stderr, "fd2_afm: ran past frame data at cmd %u\n", i);
            return -1;
        }

        u8 cmd = *ptr++;
        if (cmd >= 10) {
            fprintf(stderr, "fd2_afm: unknown command 0x%02X at cmd %u\n", cmd, i);
            return -1;
        }

        int consumed = afm_commands[cmd](afm, ptr, (u32)(end - ptr));
        if (consumed < 0) {
            return -1;
        }
        ptr += consumed;
    }

    return 0;
}

/* ========================================================================
 * Public API
 * ======================================================================== */

void fd2_afm_init(fd2_afm_t* afm) {
    if (!afm) return;
    memset(afm, 0, sizeof(*afm));
}

int fd2_afm_open(fd2_afm_t* afm, const u8* resource_data, u32 resource_size) {
    if (!afm || !resource_data) return -1;

    if (resource_size < FD2_AFM_HEADER_SIZE) {
        fprintf(stderr, "fd2_afm_open: resource too small (%u < %d)\n",
                resource_size, FD2_AFM_HEADER_SIZE);
        return -1;
    }

    /* Verify AFM signature in header */
    if (memcmp(resource_data, "AFM", 3) != 0) {
        fprintf(stderr, "fd2_afm_open: not an AFM resource (no signature)\n");
        return -1;
    }

    afm->data = resource_data;
    afm->data_size = resource_size;
    afm->offset = FD2_AFM_DATA_OFF;  /* First frame starts after 173-byte header */

    /* Read frame count from header offset 0xA5 (165) */
    afm->total_frames = (u16)(resource_data[FD2_AFM_FRAMES_OFF])
                      | (u16)(resource_data[FD2_AFM_FRAMES_OFF + 1] << 8);
    afm->current_frame = 0;

    return 0;
}

void fd2_afm_rewind(fd2_afm_t* afm) {
    if (!afm) return;
    afm->offset = FD2_AFM_DATA_OFF;
    afm->current_frame = 0;
}

int fd2_afm_decode_next_frame(fd2_afm_t* afm) {
    if (!afm || !afm->data) return -1;

    if (afm->current_frame >= afm->total_frames) {
        return -1;  /* Animation complete */
    }

    /* Read frame header (8 bytes): size(2) + param(2) + reserved(4) */
    if (afm->offset + FD2_AFM_FRAME_HDR > afm->data_size) {
        fprintf(stderr, "fd2_afm: truncated frame header at frame %u\n",
                afm->current_frame);
        return -1;
    }

    u16 frame_size = (u16)(afm->data[afm->offset])
                   | (u16)(afm->data[afm->offset + 1] << 8);
    u16 frame_param = (u16)(afm->data[afm->offset + 2])
                    | (u16)(afm->data[afm->offset + 3] << 8);
    /* Bytes 4-7 are reserved */
    afm->offset += FD2_AFM_FRAME_HDR;

    /* Read frame data */
    if (afm->offset + frame_size > afm->data_size) {
        fprintf(stderr, "fd2_afm: truncated frame data at frame %u "
                "(need %u, have %u)\n",
                afm->current_frame, frame_size,
                afm->data_size - afm->offset);
        return -1;
    }

    /* Dispatch frame commands (sub_36FF4) */
    if (frame_size > 0 && frame_param > 0) {
        if (dispatch_frame(afm, frame_param, afm->data + afm->offset, frame_size) != 0) {
            fprintf(stderr, "fd2_afm: dispatch failed at frame %u\n",
                    afm->current_frame);
            return -1;
        }
    }

    afm->offset += frame_size;
    afm->current_frame++;

    return 0;
}

bool fd2_afm_is_done(const fd2_afm_t* afm) {
    if (!afm) return true;
    return afm->current_frame >= afm->total_frames;
}

const u8* fd2_afm_get_frame(const fd2_afm_t* afm) {
    if (!afm) return NULL;
    return afm->frame;
}

const u8* fd2_afm_get_palette(const fd2_afm_t* afm) {
    if (!afm) return NULL;
    return afm->palette;
}

/* ========================================================================
 * sub_20421: AFM动画播放器 (原游戏 0x20421)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. sub_3702F(..., 56) - 初始化
 *   2. 如果a5==1, 加载FDOTHER.DAT索引78
 *   3. buf = malloc(768) - 调色板缓冲
 *   4. v8 = malloc(64000) - 帧缓冲
 *   5. sub_36FD3(64000, 655360, buf) - 初始化缓冲
 *   6. _rb_ = fopen("ANI.DAT", "rb")
 *   7. fseek(_rb_, 4*a5 + 6, 0) - 定位到动画索引
 *   8. sub_373CA(v8, 1u, 8, _rb_) - 读取8字节 (动画偏移)
 *   9. fseek(_rb_, *(DWORD*)v8, 0) - 定位到动画数据
 *   10. sub_373CA(v8, 1u, 173, _rb_) - 读取173字节头
 *   11. v15 = *(WORD*)(v8 + 165) - 获取帧数
 *   12. for (i=0; i<v15; ++i) {
 *         sub_373CA(v12, 1u, 8, _rb_) - 读取8字节帧头
 *         sub_373CA(v8, 1u, v12[0], _rb_) - 读取帧数据
 *         sub_36FF4(v12[1], v8) - 分发帧命令
 *         if (a5==1 && !i) sub_25A96(_FDOTHER.DAT_, 0, 1)
 *         j___delay(a6) - 延迟
 *         if (a7 && sub_10620()) break - 检查按键
 *         sub_4E381() - 刷新屏幕
 *       }
 *   13. free(buf), free(v8)
 *   14. if (_FDOTHER.DAT_) { sub_25A96(_FDOTHER.DAT_, -1, 1); free(_FDOTHER.DAT_); }
 *   15. fclose(_rb_)
 *
 * 参数:
 *   anim_index - ANI.DAT中的动画索引 (1=开场动画)
 *   frame_delay - 每帧延迟毫秒数
 *   check_input - 是否检查键盘输入 (1=是, 0=否)
 *   render - 渲染器
 *   resources - 资源管理器
 *
 * 返回: 0=正常播放完成, 1=用户按键中断
 * ======================================================================== */
int fd2_afm_play(int anim_index, int frame_delay, int check_input,
                 fd2_render_t* render, fd2_resources_t* resources) {
    if (!render || !resources) return -1;

    /* 1. 分配缓冲 (对应原游戏 malloc(768) 和 malloc(64000)) */
    u8* palette_buf = (u8*)malloc(768);
    u8* frame_buf = (u8*)malloc(FD2_SCREEN_SIZE);
    if (!palette_buf || !frame_buf) {
        free(palette_buf);
        free(frame_buf);
        return -1;
    }

    /* 2. 初始化缓冲 (对应原游戏 sub_36FD3) */
    memset(frame_buf, 0, FD2_SCREEN_SIZE);
    memset(palette_buf, 0, 768);

    /* 3. 加载ANI.DAT资源 */
    if (!fd2_resources_is_loaded(resources, FD2_DAT_ANI)) {
        if (fd2_resources_load_dat(resources, FD2_DAT_ANI) != 0) {
            fprintf(stderr, "fd2_afm_play: Failed to load ANI.DAT\n");
            free(palette_buf);
            free(frame_buf);
            return -1;
        }
    }

    const fd2_dat_t* ani_dat = fd2_resources_get_dat(resources, FD2_DAT_ANI);
    if (!ani_dat) {
        fprintf(stderr, "fd2_afm_play: ANI.DAT not available\n");
        free(palette_buf);
        free(frame_buf);
        return -1;
    }

    /* 4. 获取动画资源 (原游戏通过fseek定位到4*anim_index+6) */
    /* ANI.DAT索引表: 前6字节是头部, 然后每个索引4字节偏移 */
    u32 resource_size = 0;
    const u8* resource_data = fd2_resources_get(resources, FD2_DAT_ANI, anim_index, &resource_size);
    if (!resource_data || resource_size < FD2_AFM_HEADER_SIZE) {
        fprintf(stderr, "fd2_afm_play: Invalid ANI.DAT resource %d (size=%u)\n",
                anim_index, resource_size);
        free(palette_buf);
        free(frame_buf);
        return -1;
    }

    /* 5. 解析AFM头 (对应原游戏 sub_373CA读取173字节) */
    u16 total_frames = (u16)(resource_data[FD2_AFM_FRAMES_OFF])
                     | (u16)(resource_data[FD2_AFM_FRAMES_OFF + 1] << 8);

    printf("[AFM] Playing animation %d, %d frames\n", anim_index, total_frames);

    /* 6. 如果anim_index==1, 加载FDOTHER.DAT索引78 (原游戏逻辑) */
    const u8* fdother_78 = NULL;
    if (anim_index == 1) {
        u32 s78_size = 0;
        fdother_78 = fd2_resources_get(resources, FD2_DAT_FDOTHER, 78, &s78_size);
        /* TODO: sub_25A96(fdother_78, 0, 1) - 可能需要额外处理 */
    }

    /* 7. 播放循环 (对应原游戏 for i=0 to v15) */
    fd2_afm_t afm;
    fd2_afm_init(&afm);

    if (fd2_afm_open(&afm, resource_data, resource_size) != 0) {
        fprintf(stderr, "fd2_afm_play: Failed to open AFM animation\n");
        free(palette_buf);
        free(frame_buf);
        return -1;
    }

    int interrupted = 0;
    Uint32 last_frame_time = SDL_GetTicks();

    for (u16 i = 0; i < total_frames; i++) {
        /* 解码当前帧 */
        if (fd2_afm_decode_next_frame(&afm) != 0) {
            fprintf(stderr, "fd2_afm_play: Frame %d decode failed\n", i);
            break;
        }

        /* 渲染到屏幕 (对应原游戏 sub_4E381) */
        const u8* frame = fd2_afm_get_frame(&afm);
        const u8* pal = fd2_afm_get_palette(&afm);

        if (frame) {
            memcpy(render->screen, frame, FD2_SCREEN_SIZE);
        }
        if (pal) {
            fd2_render_set_palette_6bit(render, pal);
        }
        fd2_render_present(render);

        /* 延迟 (对应原游戏 j___delay(a6)) */
        if (frame_delay > 0) {
            SDL_Delay(frame_delay);
        }

        /* 检查键盘输入 (对应原游戏 if (a7 && sub_10620()) break) */
        if (check_input) {
            SDL_Event event;
            while (SDL_PollEvent(&event)) {
                if (event.type == SDL_QUIT) {
                    interrupted = 1;
                    goto cleanup;
                }
                if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                    /* 任何按键都中断动画 */
                    interrupted = 1;
                    goto cleanup;
                }
            }
        }
    }

cleanup:
    /* 8. 释放资源 */
    free(palette_buf);
    free(frame_buf);

    /* 如果anim_index==1, 释放FDOTHER.DAT (对应原游戏逻辑) */
    if (anim_index == 1 && fdother_78) {
        /* TODO: sub_25A96(fdother_78, -1, 1); free(fdother_78); */
    }

    return interrupted ? 1 : 0;
}
