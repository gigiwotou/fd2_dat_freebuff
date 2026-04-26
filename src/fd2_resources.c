/**
 * FD2 Resource Manager Implementation
 *
 * Centralizes access to all 11 DAT files used by the game.
 * Based on sub_25BF4 which loads all DAT files at startup.
 */

#include "fd2_resources.h"
#include <stdio.h>
#include <string.h>

/* ---- Filename Table ----
 *
 * Must match fd2_dat_id_t enum order.
 */
const char* fd2_dat_filenames[FD2_DAT_COUNT] = {
    "FDOTHER.DAT",   /* 0  - Title, menu, misc graphics + palettes */
    "FDTXT.DAT",     /* 1  - Text/font glyphs */
    "FDMUS.DAT",     /* 2  - MIDI music data */
    "FDSHAP.DAT",    /* 3  - Fighter sprites + palettes */
    "FDFIELD.DAT",   /* 4  - Stage/background field data */
    "BG.DAT",        /* 5  - Background images */
    "FIGANI.DAT",    /* 6  - Fighter animation frames */
    "TAI.DAT",       /* 7  - Character portraits */
    "DATO.DAT",      /* 8  - Game logic constants/data */
    "ANI.DAT",       /* 9  - AFM animation sequences */
    "FDICON.B24",    /* 10 - Icon data (B24 format) */
};

/* ---- Lifecycle ---- */

int fd2_resources_init(fd2_resources_t* res, const char* data_dir) {
    if (!res || !data_dir) return -1;

    memset(res, 0, sizeof(*res));
    strncpy(res->data_dir, data_dir, sizeof(res->data_dir) - 1);
    res->data_dir[sizeof(res->data_dir) - 1] = '\0';

    return 0;
}

void fd2_resources_shutdown(fd2_resources_t* res) {
    if (!res) return;

    for (int i = 0; i < FD2_DAT_COUNT; i++) {
        if (res->loaded[i]) {
            fd2_dat_free(&res->dats[i]);
            res->loaded[i] = false;
        }
    }
}

/* ---- Loading ---- */

int fd2_resources_load_dat(fd2_resources_t* res, fd2_dat_id_t id) {
    if (!res || id < 0 || id >= FD2_DAT_COUNT) return -1;

    /* Already loaded */
    if (res->loaded[id]) return 0;

    const char* path = fd2_resources_dat_path(res, id);
    if (!path) return -1;

    if (fd2_dat_load(&res->dats[id], path) != 0) {
        fprintf(stderr, "fd2_resources: failed to load %s\n",
                fd2_dat_filenames[id]);
        return -1;
    }

    res->loaded[id] = true;
    printf("fd2_resources: loaded %s (%u resources)\n",
           fd2_dat_filenames[id], res->dats[id].resource_count);
    return 0;
}

int fd2_resources_load_all(fd2_resources_t* res) {
    if (!res) return -1;

    int failures = 0;
    for (int i = 0; i < FD2_DAT_COUNT; i++) {
        if (fd2_resources_load_dat(res, (fd2_dat_id_t)i) != 0) {
            failures++;
        }
    }

    if (failures > 0) {
        fprintf(stderr, "fd2_resources: %d file(s) failed to load\n", failures);
    }
    return failures;
}

/* ---- Access ---- */

const fd2_dat_t* fd2_resources_get_dat(const fd2_resources_t* res, fd2_dat_id_t id) {
    if (!res || id < 0 || id >= FD2_DAT_COUNT) return NULL;
    if (!res->loaded[id]) return NULL;
    return &res->dats[id];
}

const u8* fd2_resources_get(const fd2_resources_t* res,
                            fd2_dat_id_t dat_id, int index,
                            u32* out_size) {
    const fd2_dat_t* dat = fd2_resources_get_dat(res, dat_id);
    if (!dat) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    return fd2_dat_get_resource(dat, index, out_size);
}

bool fd2_resources_is_loaded(const fd2_resources_t* res, fd2_dat_id_t id) {
    if (!res || id < 0 || id >= FD2_DAT_COUNT) return false;
    return res->loaded[id];
}

/* ---- Path Building ---- */

const char* fd2_resources_dat_path(const fd2_resources_t* res, fd2_dat_id_t id) {
    if (!res || id < 0 || id >= FD2_DAT_COUNT) return NULL;

    /* Thread-local static buffer for path result */
    static char path_buf[768];
    snprintf(path_buf, sizeof(path_buf), "%s/%s",
             res->data_dir, fd2_dat_filenames[id]);
    return path_buf;
}
