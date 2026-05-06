#ifndef FD2_PLATFORM_TIME_H
#define FD2_PLATFORM_TIME_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Time Interface ---- */

typedef struct {
    u32  (*get_ticks_ms)(void);
    u64  (*get_ticks_us)(void);
    void (*delay_ms)(u32 ms);
    void (*delay_us)(u32 us);
} fd2_time_iface_t;

/* Get the platform time interface (implemented by platform/sdl_time.c) */
const fd2_time_iface_t* fd2_platform_get_time(void);

#ifdef __cplusplus
}
#endif

#endif /* FD2_PLATFORM_TIME_H */
