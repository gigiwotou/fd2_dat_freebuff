#ifndef FD2_PLATFORM_VIDEO_H
#define FD2_PLATFORM_VIDEO_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Video Interface ---- */

typedef struct {
    int (*init)(fd2_video_t** out_video, int width, int height, int scale, const char* title);
    void (*shutdown)(fd2_video_t* video);

    void (*set_palette)(fd2_video_t* video, const u8* palette_8bit);
    void (*set_brightness)(fd2_video_t* video, int brightness_0_to_63);

    void (*upload_screen)(fd2_video_t* video, const u8* screen_buffer);
    void (*present)(fd2_video_t* video);

    void (*fill_screen)(fd2_video_t* video, u8 color);
    void (*blit)(fd2_video_t* video, const u8* pixels, int w, int h, int dx, int dy);
    void (*blit_trans)(fd2_video_t* video, const u8* pixels, int w, int h, int dx, int dy, u8 transparent);

    void (*toggle_fullscreen)(fd2_video_t* video);
    void (*process_events)(fd2_video_t* video);

    int width;
    int height;
    int scale;
} fd2_video_iface_t;

/* Get the platform video interface (implemented by platform/sdl_video.c) */
const fd2_video_iface_t* fd2_platform_get_video(void);

#ifdef __cplusplus
}
#endif

#endif /* FD2_PLATFORM_VIDEO_H */
