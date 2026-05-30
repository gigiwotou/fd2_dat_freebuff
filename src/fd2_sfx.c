/**
 * FD2 Sound Effect System Implementation
 * 
 * Loads and plays sound effects from FDOTHER.DAT index 31 (nested DAT).
 * Each sound effect is 8-bit unsigned PCM audio data.
 * 
 * Cross-platform implementation using SDL audio callback for mixing.
 */

#include "fd2_sfx.h"
#include "fd2_dat.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * Internal Data
 * ======================================================================== */

fd2_sfx_manager_t* g_sfx_mgr = NULL;
static SDL_AudioDeviceID  g_sfx_dev = 0;
static SDL_mutex*         g_sfx_mutex = NULL;

/* ========================================================================
 * Audio Callback - Mixes all playing sounds
 * ======================================================================== */

static void sfx_audio_callback(void* userdata, Uint8* stream, int len) {
    (void)userdata;
    
    if (!g_sfx_mgr || !g_sfx_mutex) {
        memset(stream, 0x80, len); /* Silence for 8-bit unsigned */
        return;
    }
    
    SDL_LockMutex(g_sfx_mutex);
    
    /* Initialize buffer with silence (0x80 = center for 8-bit unsigned) */
    memset(stream, 0x80, len);
    
    /* Mix all active sounds */
    for (int slot = 0; slot < FD2_SFX_MAX_PLAYING; slot++) {
        fd2_sfx_playing_t* p = &g_sfx_mgr->playing[slot];
        if (!p->active) continue;
        
        const fd2_sfx_t* sfx = &g_sfx_mgr->sounds[p->sfx_index];
        if (!sfx->loaded || !sfx->data) {
            p->active = false;
            continue;
        }
        
        float vol = p->volume * g_sfx_mgr->master_volume;
        if (g_sfx_mgr->muted) vol = 0.0f;
        
        int samples_to_play = len;
        int remaining = p->length - p->position;
        if (samples_to_play > remaining) samples_to_play = remaining;
        
        for (int i = 0; i < samples_to_play; i++) {
            byte sample = sfx->data[p->position];
            p->position++;
            
            /* Convert unsigned to signed, apply volume, convert back */
            int signed_sample = (int)sample - 128;
            int mixed = (int)(signed_sample * vol);
            
            /* Add to buffer with clipping */
            int buf_val = (int)stream[i] - 128 + mixed;
            if (buf_val > 127) buf_val = 127;
            if (buf_val < -128) buf_val = -128;
            stream[i] = (byte)(buf_val + 128);
        }
        
        /* Check if sound finished */
        if (p->position >= p->length) {
            p->active = false;
        }
    }
    
    SDL_UnlockMutex(g_sfx_mutex);
}

/* ========================================================================
 * Internal Helper - Extract sub-resource from nested DAT
 * ======================================================================== */

static const byte* extract_sfx_from_fdother(const char* path, int sfx_index, dword* out_size) {
    if (!path || sfx_index < 0 || sfx_index >= FD2_SFX_COUNT || !out_size) return NULL;
    
    /* Load FDOTHER.DAT */
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "sfx: cannot open %s\n", path);
        return NULL;
    }
    
    /* Read header */
    char magic[6];
    if (fread(magic, 1, 6, f) != 6 || memcmp(magic, "LLLLLL", 6) != 0) {
        fprintf(stderr, "sfx: invalid FDOTHER magic\n");
        fclose(f);
        return NULL;
    }
    
    /* Read main resource count */
    dword res_count;
    if (fread(&res_count, 4, 1, f) != 1) {
        fprintf(stderr, "sfx: cannot read resource count\n");
        fclose(f);
        return NULL;
    }
    
    /* Check if index 31 exists */
    if (FD2_SFX_DAT_INDEX >= res_count) {
        fprintf(stderr, "sfx: index %d out of range\n", FD2_SFX_DAT_INDEX);
        fclose(f);
        return NULL;
    }
    
    /* Get offset of index 31 */
    dword main_offsets[2];
    fseek(f, 10 + FD2_SFX_DAT_INDEX * 4, SEEK_SET);
    if (fread(&main_offsets[0], 4, 1, f) != 1) {
        fclose(f);
        return NULL;
    }
    if (FD2_SFX_DAT_INDEX + 1 < res_count) {
        fseek(f, 10 + (FD2_SFX_DAT_INDEX + 1) * 4, SEEK_SET);
        fread(&main_offsets[1], 4, 1, f);
    } else {
        fseek(f, 0, SEEK_END);
        main_offsets[1] = ftell(f);
    }
    
    /* Load nested DAT */
    dword nested_size = main_offsets[1] - main_offsets[0];
    byte* nested_data = (byte*)malloc(nested_size);
    if (!nested_data) {
        fclose(f);
        return NULL;
    }
    
    fseek(f, main_offsets[0], SEEK_SET);
    if (fread(nested_data, 1, nested_size, f) != nested_size) {
        free(nested_data);
        fclose(f);
        return NULL;
    }
    fclose(f);
    
    /* Parse nested DAT header */
    if (nested_size < 10 || memcmp(nested_data, "LLLLLL", 6) != 0) {
        fprintf(stderr, "sfx: invalid nested DAT magic\n");
        free(nested_data);
        return NULL;
    }
    
    dword nested_count = ((dword*)nested_data)[1]; /* Offset 6 */
    if (sfx_index >= (int)nested_count) {
        fprintf(stderr, "sfx: sfx_index %d out of range (count=%u)\n", sfx_index, nested_count);
        free(nested_data);
        return NULL;
    }
    
    /* Get offset table */
    dword* offsets = (dword*)(nested_data + 10);
    dword start = offsets[sfx_index];
    dword end = (sfx_index + 1 < nested_count) ? offsets[sfx_index + 1] : nested_size;
    
    dword size = end - start;
    if (size == 0 || size > nested_size) {
        fprintf(stderr, "sfx: invalid size %u for sfx %d\n", size, sfx_index);
        free(nested_data);
        return NULL;
    }
    
    /* Copy sound data */
    byte* sfx_data = (byte*)malloc(size);
    if (sfx_data) {
        memcpy(sfx_data, nested_data + start, size);
        *out_size = size;
    }
    
    free(nested_data);
    return sfx_data;
}

/* ========================================================================
 * Public API Implementation
 * ======================================================================== */

int fd2_sfx_init(fd2_sfx_manager_t* mgr, const char* fdother_path) {
    if (!mgr || !fdother_path) return -1;
    
    memset(mgr, 0, sizeof(*mgr));
    mgr->fdother_path = fdother_path;
    mgr->master_volume = 1.0f;
    mgr->initialized = false;
    
    /* Initialize playing slots */
    for (int i = 0; i < FD2_SFX_MAX_PLAYING; i++) {
        mgr->playing[i].active = false;
    }
    
    /* Initialize SDL audio */
    if (!SDL_WasInit(SDL_INIT_AUDIO)) {
        if (SDL_InitSubSystem(SDL_INIT_AUDIO) < 0) {
            fprintf(stderr, "sfx: SDL audio init failed: %s\n", SDL_GetError());
            return -1;
        }
    }
    
    /* Create mutex */
    g_sfx_mutex = SDL_CreateMutex();
    if (!g_sfx_mutex) {
        fprintf(stderr, "sfx: mutex creation failed\n");
        return -1;
    }
    
    /* Open audio device */
    SDL_AudioSpec want, got;
    memset(&want, 0, sizeof(want));
    want.freq = FD2_SFX_SAMPLE_RATE;
    want.format = FD2_SFX_FORMAT;
    want.channels = FD2_SFX_CHANNELS;
    want.samples = 512;
    want.callback = sfx_audio_callback;
    
    g_sfx_dev = SDL_OpenAudioDevice(NULL, 0, &want, &got, 0);
    if (!g_sfx_dev) {
        fprintf(stderr, "sfx: SDL_OpenAudioDevice failed: %s\n", SDL_GetError());
        SDL_DestroyMutex(g_sfx_mutex);
        g_sfx_mutex = NULL;
        return -1;
    }
    
    g_sfx_mgr = mgr;
    mgr->initialized = true;
    
    /* Start audio playback */
    SDL_PauseAudioDevice(g_sfx_dev, 0);
    
    printf("sfx: initialized (%d max playing, %d Hz)\n", FD2_SFX_MAX_PLAYING, FD2_SFX_SAMPLE_RATE);
    return 0;
}

void fd2_sfx_shutdown(fd2_sfx_manager_t* mgr) {
    if (!mgr) return;
    
    /* Stop audio */
    if (g_sfx_dev) {
        SDL_PauseAudioDevice(g_sfx_dev, 1);
        SDL_CloseAudioDevice(g_sfx_dev);
        g_sfx_dev = 0;
    }
    
    /* Free loaded sounds */
    for (int i = 0; i < FD2_SFX_COUNT; i++) {
        if (mgr->sounds[i].data) {
            free(mgr->sounds[i].data);
            mgr->sounds[i].data = NULL;
            mgr->sounds[i].loaded = false;
        }
    }
    
    /* Cleanup */
    if (g_sfx_mutex) {
        SDL_DestroyMutex(g_sfx_mutex);
        g_sfx_mutex = NULL;
    }
    
    g_sfx_mgr = NULL;
    mgr->initialized = false;
    
    printf("sfx: shutdown\n");
}

int fd2_sfx_load(fd2_sfx_manager_t* mgr, int sfx_index) {
    if (!mgr || !mgr->initialized || sfx_index < 0 || sfx_index >= FD2_SFX_COUNT) {
        return -1;
    }
    
    fd2_sfx_t* sfx = &mgr->sounds[sfx_index];
    
    /* Already loaded */
    if (sfx->loaded && sfx->data) {
        return 0;
    }
    
    /* Free old data if any */
    if (sfx->data) {
        free(sfx->data);
        sfx->data = NULL;
    }
    
    /* Extract from FDOTHER.DAT */
    dword size;
    const byte* data = extract_sfx_from_fdother(mgr->fdother_path, sfx_index, &size);
    if (!data || size == 0) {
        fprintf(stderr, "sfx: failed to load sound %d\n", sfx_index);
        return -1;
    }
    
    sfx->index = sfx_index;
    sfx->data = (byte*)data;
    sfx->size = size;
    sfx->loaded = true;
    
    printf("sfx: loaded sound %d (%u bytes)\n", sfx_index, size);
    return 0;
}

int fd2_sfx_load_all(fd2_sfx_manager_t* mgr) {
    if (!mgr || !mgr->initialized) return -1;
    
    int loaded = 0;
    for (int i = 0; i < FD2_SFX_COUNT; i++) {
        if (fd2_sfx_load(mgr, i) == 0) {
            loaded++;
        }
    }
    
    printf("sfx: loaded %d/%d sounds\n", loaded, FD2_SFX_COUNT);
    return (loaded == FD2_SFX_COUNT) ? 0 : -1;
}

int fd2_sfx_play(fd2_sfx_manager_t* mgr, int sfx_index) {
    return fd2_sfx_play_volume(mgr, sfx_index, 128);
}

int fd2_sfx_play_volume(fd2_sfx_manager_t* mgr, int sfx_index, int volume) {
    if (!mgr || !mgr->initialized || sfx_index < 0 || sfx_index >= FD2_SFX_COUNT) {
        return -1;
    }
    
    fd2_sfx_t* sfx = &mgr->sounds[sfx_index];
    if (!sfx->loaded || !sfx->data) {
        /* Try to load on demand */
        if (fd2_sfx_load(mgr, sfx_index) != 0) {
            return -1;
        }
        sfx = &mgr->sounds[sfx_index];
    }
    
    /* Find free slot */
    int slot = -1;
    for (int i = 0; i < FD2_SFX_MAX_PLAYING; i++) {
        if (!mgr->playing[i].active) {
            slot = i;
            break;
        }
    }
    
    if (slot == -1) {
        fprintf(stderr, "sfx: no free playing slots\n");
        return -1;
    }
    
    /* Setup playing instance */
    SDL_LockMutex(g_sfx_mutex);
    mgr->playing[slot].sfx_index = sfx_index;
    mgr->playing[slot].position = 0;
    mgr->playing[slot].length = (int)sfx->size;
    mgr->playing[slot].volume = volume / 128.0f;
    mgr->playing[slot].active = true;
    SDL_UnlockMutex(g_sfx_mutex);
    
    return slot;
}

void fd2_sfx_stop(fd2_sfx_manager_t* mgr, int slot_index) {
    if (!mgr || slot_index < 0 || slot_index >= FD2_SFX_MAX_PLAYING) return;
    
    SDL_LockMutex(g_sfx_mutex);
    mgr->playing[slot_index].active = false;
    SDL_UnlockMutex(g_sfx_mutex);
}

void fd2_sfx_stop_all(fd2_sfx_manager_t* mgr) {
    if (!mgr) return;
    
    SDL_LockMutex(g_sfx_mutex);
    for (int i = 0; i < FD2_SFX_MAX_PLAYING; i++) {
        mgr->playing[i].active = false;
    }
    SDL_UnlockMutex(g_sfx_mutex);
}

void fd2_sfx_set_volume(fd2_sfx_manager_t* mgr, int volume) {
    if (!mgr) return;
    if (volume < 0) volume = 0;
    if (volume > 128) volume = 128;
    mgr->master_volume = volume / 128.0f;
}

void fd2_sfx_toggle_mute(fd2_sfx_manager_t* mgr) {
    if (!mgr) return;
    mgr->muted = !mgr->muted;
}

const fd2_sfx_t* fd2_sfx_get(const fd2_sfx_manager_t* mgr, int sfx_index) {
    if (!mgr || sfx_index < 0 || sfx_index >= FD2_SFX_COUNT) return NULL;
    return &mgr->sounds[sfx_index];
}

bool fd2_sfx_is_loaded(const fd2_sfx_manager_t* mgr, int sfx_index) {
    if (!mgr || sfx_index < 0 || sfx_index >= FD2_SFX_COUNT) return false;
    return mgr->sounds[sfx_index].loaded;
}

void fd2_sfx_update(fd2_sfx_manager_t* mgr) {
    if (!mgr) return;
    
    /* Update is handled in audio callback */
    /* This function can be used for additional periodic updates if needed */
}
