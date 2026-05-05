#ifndef FD2_TYPES_H
#define FD2_TYPES_H

#include <stdint.h>
#include <stdbool.h>

typedef uint8_t byte;
typedef uint16_t word;
typedef uint32_t dword;

/* VGA Mode 13h screen dimensions */
#define FD2_SCREEN_W   320
#define FD2_SCREEN_H   200
#define FD2_SCREEN_SIZE (FD2_SCREEN_W * FD2_SCREEN_H)  /* 64000 */

/* VGA Palette */
#define FD2_PALETTE_COLORS  256
#define FD2_PALETTE_BYTES   (FD2_PALETTE_COLORS * 3)  /* 768 */

/* Screen buffer offsets (matching original game addresses) */
#define FD2_SCREEN_VGA     655360    /* 0xA0000 - VGA framebuffer (decimal) */
#define FD2_BACKUP_OFFSET  0         /* n655360_0 - backup buffer */
#define FD2_RENDER_OFFSET   32904    /* n655360 + 32904 - render offset */
#define FD2_STRIDE_NORMAL   320      /* normal line stride */
#define FD2_STRIDE_WIDE     456      /* wide line stride (for effects) */

/* Image format constants */
#define FD2_CHAR_WIDTH     16
#define FD2_CHAR_HEIGHT    16
#define FD2_CHAR_BYTES     32        /* 16 rows x 2 bytes/row */

#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 200
#define PALETTE_SIZE 256

typedef struct {
    byte* data;
    dword size;
    int resource_count;
    int max_resources;
    dword* starts;
    dword* ends;
} DatHandle;

#endif
