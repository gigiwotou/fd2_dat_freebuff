/**
 * SDL2 Audio Platform Implementation
 * Wraps SDL2 audio for music and SFX playback.
 * Note: SDL_mixer integration pending - using SDL audio API directly.
 */

#define _GNU_SOURCE
#include "fd2/platform_audio.h"
#include "fd2/types.h"
#include <SDL2/SDL.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

struct fd2_audio {
    char  fdmus_path[512];
    int   music_volume;
    int   sfx_volume;
    bool  muted;
    bool  initialized;
};

static int sdl_audio_init(fd2_audio_t** out_audio) {
    fd2_audio_t* audio = (fd2_audio_t*)calloc(1, sizeof(fd2_audio_t));
    if (!audio) return -1;

    if (SDL_InitSubSystem(SDL_INIT_AUDIO) < 0) {
        fprintf(stderr, "sdl_audio: SDL_InitSubSystem(AUDIO) failed: %s (non-fatal)\n", SDL_GetError());
        audio->initialized = false;
        *out_audio = audio;
        return 0;
    }

    audio->music_volume = 128;
    audio->sfx_volume = 128;
    audio->muted = false;
    audio->initialized = true;

    *out_audio = audio;
    return 0;
}

static void sdl_audio_shutdown(fd2_audio_t* audio) {
    if (!audio) return;
    if (audio->initialized) {
        SDL_PauseAudio(1);
    }
    free(audio);
}

static int sdl_audio_play_music(fd2_audio_t* audio, int track_id, int loops) {
    if (!audio || !audio->initialized) return -1;

    fprintf(stderr, "sdl_audio: music playback requires SDL_mixer (track %d, loops %d)\n", track_id, loops);
    return -1;
}

static void sdl_audio_stop_music(fd2_audio_t* audio) {
    if (!audio || !audio->initialized) return;
}

static void sdl_audio_set_music_volume(fd2_audio_t* audio, int volume_0_to_128) {
    if (!audio) return;
    audio->music_volume = volume_0_to_128;
}

static void sdl_audio_fade_music(fd2_audio_t* audio, int ms) {
    if (!audio || !audio->initialized) return;
    fprintf(stderr, "sdl_audio: fade requires SDL_mixer\n");
}

static bool sdl_audio_is_music_playing(fd2_audio_t* audio) {
    if (!audio || !audio->initialized) return false;
    return false;
}

static int sdl_audio_play_sfx(fd2_audio_t* audio, int sfx_id) {
    if (!audio || !audio->initialized) return -1;

    fprintf(stderr, "sdl_audio: SFX playback requires SDL_mixer (sfx %d)\n", sfx_id);
    return -1;
}

static void sdl_audio_set_sfx_volume(fd2_audio_t* audio, int volume_0_to_128) {
    if (!audio) return;
    audio->sfx_volume = volume_0_to_128;
}

static void sdl_audio_set_music_path(fd2_audio_t* audio, const char* fdmus_path) {
    if (!audio || !fdmus_path) return;
    snprintf(audio->fdmus_path, sizeof(audio->fdmus_path), "%s", fdmus_path);
}

static void sdl_audio_toggle_mute(fd2_audio_t* audio) {
    if (!audio) return;
    audio->muted = !audio->muted;
}

static const fd2_audio_iface_t g_sdl_audio_iface = {
    .init              = sdl_audio_init,
    .shutdown          = sdl_audio_shutdown,
    .play_music        = sdl_audio_play_music,
    .stop_music        = sdl_audio_stop_music,
    .set_music_volume  = sdl_audio_set_music_volume,
    .fade_music        = sdl_audio_fade_music,
    .is_music_playing  = sdl_audio_is_music_playing,
    .play_sfx          = sdl_audio_play_sfx,
    .set_sfx_volume    = sdl_audio_set_sfx_volume,
    .set_music_path    = sdl_audio_set_music_path,
    .toggle_mute       = sdl_audio_toggle_mute,
};

const fd2_audio_iface_t* fd2_platform_get_audio(void) {
    return &g_sdl_audio_iface;
}
