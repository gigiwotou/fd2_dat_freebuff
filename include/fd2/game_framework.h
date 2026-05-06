#ifndef FD2_GAME_FRAMEWORK_H
#define FD2_GAME_FRAMEWORK_H

#include "fd2/types.h"
#include "fd2/platform_video.h"
#include "fd2/platform_audio.h"
#include "fd2/platform_input.h"
#include "fd2/platform_file.h"
#include "fd2/platform_time.h"
#include "fd2/event_bus.h"
#include "fd2/sim/entity.h"
#include "fd2/sim/systems.h"
#include "fd2/dialog.h"
#include "fd2/npc.h"
#include "fd2/event_system.h"
#include "fd2/battle_system.h"
#include "fd2/mod/loader.h"
#include "fd2/mod/api.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Modern Game Framework ----
 * Integrates all Phase 1-6 systems into a unified framework.
 * Platform-independent game core.
 */

typedef enum {
    FD2_GS_INIT = 0,
    FD2_GS_TITLE,
    FD2_GS_INTRO,
    FD2_GS_MENU,
    FD2_GS_BATTLE,
    FD2_GS_DIALOG,
    FD2_GS_SCENE,
    FD2_GS_GAME_OVER,
    FD2_GS_QUIT,
} fd2_game_state_t;

typedef struct {
    /* Game state */
    fd2_game_state_t  state;
    fd2_game_state_t  prev_state;
    bool              running;
    u32               frame_count;
    u32               tick_count;

    /* Core systems */
    fd2_entity_mgr_t  entity_mgr;
    fd2_event_bus_t   event_bus;
    fd2_dialog_box_t  dialog;
    fd2_npc_system_t  npc_system;
    fd2_event_system_t event_system;
    fd2_battle_t      battle;
    fd2_mod_mgr_t     mod_mgr;

    /* Screen buffer */
    u8                screen[FD2_SCREEN_SIZE];
    u8                palette[FD2_PALETTE_BYTES];

    /* Data paths */
    char              data_dir[256];
    char              mods_dir[256];

    /* Timing */
    u32               last_frame_time;
    u32               frame_time;
} fd2_game_framework_t;

/* Initialize the game framework */
int  fd2_game_framework_init(fd2_game_framework_t* game,
                             const char* data_dir,
                             const char* mods_dir);

void fd2_game_framework_shutdown(fd2_game_framework_t* game);

/* Main update loop - call every frame */
void fd2_game_framework_update(fd2_game_framework_t* game,
                               const fd2_input_iface_t* input,
                               fd2_input_t* input_state,
                               const fd2_video_iface_t* video,
                               fd2_video_t* video_state,
                               const fd2_audio_iface_t* audio,
                               fd2_audio_t* audio_state);

/* Render to screen buffer */
void fd2_game_framework_render(fd2_game_framework_t* game);

/* State management */
void fd2_game_framework_set_state(fd2_game_framework_t* game, fd2_game_state_t state);
fd2_game_state_t fd2_game_framework_get_state(const fd2_game_framework_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_GAME_FRAMEWORK_H */
