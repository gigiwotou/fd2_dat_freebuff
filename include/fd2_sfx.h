/**
 * FD2 Sound Effect System
 * 
 * Based on IDA MCP analysis:
 * - FDOTHER.DAT index 31: nested DAT containing 62 sound effects
 * - Each sound is 8-bit unsigned PCM audio data (center value 0x80 = silence)
 * - Original game uses Windows waveOut API (sub_45E21, sub_41EC1)
 * - Cross-platform implementation uses SDL audio
 * 
 * Sound effect format:
 * - Raw 8-bit unsigned PCM samples
 * - Sample rate: 11025 Hz (typical for DOS games of this era)
 * - Mono channel
 */

#ifndef FD2_SFX_H
#define FD2_SFX_H

#include "fd2_types.h"
#include <stdbool.h>

/* Sound effect resource constants */
#define FD2_SFX_DAT_INDEX    31   /* Index in FDOTHER.DAT */
#define FD2_SFX_COUNT        62   /* Total number of sound effects */
#define FD2_SFX_SAMPLE_RATE  11025 /* Sample rate in Hz */
#define FD2_SFX_FORMAT       AUDIO_U8 /* 8-bit unsigned PCM */
#define FD2_SFX_CHANNELS     1    /* Mono */

/* Maximum concurrent playing sounds */
#define FD2_SFX_MAX_PLAYING  8

/* Sound effect structure */
typedef struct {
    int   index;        /* Sound effect index (0-61) */
    byte* data;         /* PCM sample data */
    dword size;         /* Sample data size in bytes */
    bool  loaded;       /* Whether loaded successfully */
} fd2_sfx_t;

/* Playing sound instance */
typedef struct {
    int    sfx_index;   /* Sound effect index */
    int    position;    /* Current playback position */
    int    length;      /* Total sample length */
    float  volume;      /* Volume (0.0 - 1.0) */
    bool   active;      /* Whether currently playing */
} fd2_sfx_playing_t;

/* Sound effect manager */
typedef struct {
    fd2_sfx_t          sounds[FD2_SFX_COUNT];    /* Loaded sounds */
    fd2_sfx_playing_t  playing[FD2_SFX_MAX_PLAYING]; /* Active instances */
    const char*        fdother_path;              /* Path to FDOTHER.DAT */
    float              master_volume;              /* Master volume (0.0 - 1.0) */
    bool               initialized;                /* Whether initialized */
    bool               muted;                      /* Muted flag */
} fd2_sfx_manager_t;

/* ========================================================================
 * Public API
 * ======================================================================== */

/* Initialize sound effect manager */
int fd2_sfx_init(fd2_sfx_manager_t* mgr, const char* fdother_path);

/* Shutdown sound effect manager */
void fd2_sfx_shutdown(fd2_sfx_manager_t* mgr);

/* Load a specific sound effect */
int fd2_sfx_load(fd2_sfx_manager_t* mgr, int sfx_index);

/* Load all sound effects */
int fd2_sfx_load_all(fd2_sfx_manager_t* mgr);

/* Play a sound effect (returns playing slot index, -1 on failure) */
int fd2_sfx_play(fd2_sfx_manager_t* mgr, int sfx_index);

/* Play a sound effect with volume (0-128) */
int fd2_sfx_play_volume(fd2_sfx_manager_t* mgr, int sfx_index, int volume);

/* Stop a specific playing sound */
void fd2_sfx_stop(fd2_sfx_manager_t* mgr, int slot_index);

/* Stop all playing sounds */
void fd2_sfx_stop_all(fd2_sfx_manager_t* mgr);

/* Set master volume (0-128) */
void fd2_sfx_set_volume(fd2_sfx_manager_t* mgr, int volume);

/* Toggle mute */
void fd2_sfx_toggle_mute(fd2_sfx_manager_t* mgr);

/* Get sound effect info */
const fd2_sfx_t* fd2_sfx_get(const fd2_sfx_manager_t* mgr, int sfx_index);

/* Check if a sound effect is loaded */
bool fd2_sfx_is_loaded(const fd2_sfx_manager_t* mgr, int sfx_index);

/* Update playing sounds (call regularly) */
void fd2_sfx_update(fd2_sfx_manager_t* mgr);

/* Global SFX manager (for integration with audio system) */
extern fd2_sfx_manager_t* g_sfx_mgr;

#endif /* FD2_SFX_H */
