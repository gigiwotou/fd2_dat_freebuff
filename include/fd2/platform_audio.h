#ifndef FD2_PLATFORM_AUDIO_H
#define FD2_PLATFORM_AUDIO_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Audio Interface ---- */

typedef struct {
    int (*init)(fd2_audio_t** out_audio);
    void (*shutdown)(fd2_audio_t* audio);

    int (*play_music)(fd2_audio_t* audio, int track_id, int loops);
    void (*stop_music)(fd2_audio_t* audio);
    void (*set_music_volume)(fd2_audio_t* audio, int volume_0_to_128);
    void (*fade_music)(fd2_audio_t* audio, int ms);
    bool (*is_music_playing)(fd2_audio_t* audio);

    int (*play_sfx)(fd2_audio_t* audio, int sfx_id);
    void (*set_sfx_volume)(fd2_audio_t* audio, int volume_0_to_128);

    void (*set_music_path)(fd2_audio_t* audio, const char* fdmus_path);
    void (*toggle_mute)(fd2_audio_t* audio);
} fd2_audio_iface_t;

/* Get the platform audio interface (implemented by platform/sdl_audio.c) */
const fd2_audio_iface_t* fd2_platform_get_audio(void);

#ifdef __cplusplus
}
#endif

#endif /* FD2_PLATFORM_AUDIO_H */
