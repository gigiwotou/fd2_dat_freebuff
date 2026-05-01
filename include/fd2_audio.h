#ifndef FD2_AUDIO_H
#define FD2_AUDIO_H

#include "fd2_decoder.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Audio System
 *
 * Based on IDA MCP analysis of the original game:
 *   - sub_3AEEE: AIL_start_sequence (MIDI music from FDMUS.DAT)
 *   - sub_39798: AIL_start_sample (digital SFX)
 *   - sub_43270: MIDI event parser with tempo*16 storage
 *
 * Implementation uses platform-native MIDI:
 *   - Windows: winmm.dll MIDI API
 *   - Linux/macOS: SDL_mixer (future)
 * ======================================================================== */

/* Maximum MIDI track size (64KB per track from FDMUS.DAT) */
#define FD2_MAX_MIDI_SIZE (64 * 1024)

/* ---- Audio State ---- */
typedef struct fd2_audio {
    bool    initialized;
    bool    muted;
    int     music_volume;     /* 0-128 */
    int     sfx_volume;       /* 0-128 */

    /* Music playback state */
    void*   midi_handle;      /* HMIDIOUT handle (Windows) */
    int     music_playing;    /* Track ID currently playing, -1 = none */
    int     music_loops;      /* Loop count: -1=infinite, 0=once, N=N+1 */
    int     current_loop;     /* Current loop iteration */

    /* MIDI data buffer (raw MIDI from FDMUS.DAT, already converted) */
    unsigned char* midi_data; /* Converted MIDI data */
    unsigned int   midi_size; /* Size of MIDI data */

    /* Resource manager path to FDMUS.DAT */
    const char* fdmus_path;   /* Path to FDMUS.DAT */
} fd2_audio_t;

/* ---- Lifecycle ---- */

/*
 * Initialize the audio subsystem.
 * Returns 0 on success, -1 on failure (non-fatal: game runs without sound).
 */
int fd2_audio_init(fd2_audio_t* audio);

/*
 * Shut down and free all audio resources.
 */
void fd2_audio_shutdown(fd2_audio_t* audio);

/*
 * Set the path to FDMUS.DAT for music playback.
 * Called by resources system after FDMUS.DAT is loaded.
 */
void fd2_audio_set_fdmus_path(fd2_audio_t* audio, const char* path);

/* ---- Music ---- */

/*
 * Play a MIDI/music track from FDMUS.DAT.
 * track_id: resource index in FDMUS.DAT
 * loops: -1 = infinite, 0 = play once, N = play N+1 times
 * Returns 0 on success, -1 on failure.
 */
int fd2_audio_play_music(fd2_audio_t* audio, int track_id, int loops);

/*
 * Stop currently playing music.
 */
void fd2_audio_stop_music(fd2_audio_t* audio);

/*
 * Set music volume (0-128).
 */
void fd2_audio_set_music_volume(fd2_audio_t* audio, int volume);

/*
 * Fade music out over the given milliseconds.
 */
void fd2_audio_fade_music(fd2_audio_t* audio, int ms);

/* ---- Sound Effects ---- */

/*
 * Play a sound effect.
 * sfx_id: index into the sound effects table
 * Returns 0 on success, -1 on failure.
 */
int fd2_audio_play_sfx(fd2_audio_t* audio, int sfx_id);

/*
 * Set SFX volume (0-128).
 */
void fd2_audio_set_sfx_volume(fd2_audio_t* audio, int volume);

/* ---- Utility ---- */

/*
 * Check if music is currently playing.
 */
bool fd2_audio_music_playing(const fd2_audio_t* audio);

/*
 * Toggle mute state.
 */
void fd2_audio_toggle_mute(fd2_audio_t* audio);

#ifdef __cplusplus
}
#endif

#endif /* FD2_AUDIO_H */
