#ifndef FD2_GAME_H
#define FD2_GAME_H

#include "fd2_decoder.h"
#include "fd2_input.h"
#include "fd2_render.h"
#include "fd2_audio.h"
#include "fd2_resources.h"
#include "fd2_afm.h"
#include "fd2_scene.h"
#include "fd2_sprite.h"
#include "fd2_icon_b24.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Game State Machine
 *
 * The game runs through a series of states:
 *   INTRO → MENU → CHARACTER_SELECT → BATTLE → RESULTS → ...
 *
 * Each state has enter(), update(), and exit() functions.
 * update() returns the next state to transition to (or itself to stay).
 * ======================================================================== */

/* ---- Game States ---- */
typedef enum {
    FD2_STATE_NONE = 0,
    FD2_STATE_INIT,           /* Loading resources, one-shot setup */
    FD2_STATE_INTRO,          /* Opening animation (sub_1F894) */
    FD2_STATE_MENU,           /* Main menu (sub_1FF79 / sub_20421) */
    FD2_STATE_DEMO,           /* Demo/attract mode (sub_117E7 state 28/57) */
    FD2_STATE_CHAR_SELECT,    /* Character selection */
    FD2_STATE_CUTSCENE,       /* Cutscene playback (sub_1366A + sub_15F84) */
    FD2_STATE_BATTLE,         /* In-game fight (sub_10010) */
    FD2_STATE_VICTORY,        /* Round/match result */
    FD2_STATE_CONTINUE,       /* Continue screen */
    FD2_STATE_GAME_OVER,      /* Game over */
    FD2_STATE_QUIT,           /* Clean exit */
    FD2_STATE_COUNT
} fd2_state_t;

/* ---- Forward declarations ---- */
struct fd2_game;

/* ---- State Interface ---- */
typedef struct fd2_state_ops {
    /* Called once when entering this state. Allocates state-local data. */
    void (*enter)(struct fd2_game* game);

    /* Called every frame. Returns next state (or same state to stay). */
    fd2_state_t (*update)(struct fd2_game* game);

    /* Called once when leaving this state. Frees state-local data. */
    void (*exit)(struct fd2_game* game);
} fd2_state_ops_t;

/* ---- Game Context ----
 *
 * This is the central game object, analogous to the original game's
 * global variables (0x53BFB, 0x53AE9, etc.) but bundled into
 * a single struct for clean ownership and testability.
 */
typedef struct fd2_game {
    /* ---- Core systems (initialized by game_init) ---- */
    fd2_input_t      input;        /* Input state */
    fd2_render_t     render;       /* Rendering pipeline */
    fd2_audio_t      audio;        /* Audio system */
    fd2_resources_t  resources;    /* Resource manager */

    /* ---- State machine ---- */
    fd2_state_t      current_state;
    fd2_state_t      next_state;
    const fd2_state_ops_t* state_ops[FD2_STATE_COUNT];
    void*            state_data;   /* Opaque pointer for current state's local data */

    /* ---- Game state (maps to original globals) ---- */
    int              selected_char;    /* byte_51E63[n17] - selected character */
    int              opponent_char;    /* Current opponent */
    int              num_fighters;     /* n6_0 - number of fighters in roster */
    int              current_fighter;  /* dword_53AE9 - current fighter index */
    int              game_mode;        /* n17 - 0=single, 1=vs, 2=demo */
    int              round;            /* Current round number */
    int              difficulty;       /* dword_53BEF */
    int              map_index;        /* Current battle map index (e.g., 97 for first story level) */

    /* ---- Battle save data (from Continue) ---- */
    int              from_save;        /* Whether entering battle from save file */
    int              save_char_count;  /* Number of characters in save (n6_0) */
    u8               save_char_positions[64][2];  /* Real-time x, y from FD2.SAV (n8_1 offsets 0,1) */
    u8               save_char_icons[64];         /* Icon IDs from FD2.SAV (n8_1 offset 7) */
    u8               save_char_full_data[64][80]; /* Full 80-byte char data from FD2.SAV */

    /* ---- Timing ---- */
    u32              frame_count;      /* Global frame counter */
    u32              last_tick;        /* Last frame timestamp (SDL_GetTicks) */
    int              running;          /* 0 = quit requested */

    /* ---- Cutscene state ---- */
    scene_player_t   scene_player;     /* Scene/cutscene playback */
    int              cutscene_sequence[32];  /* Scene sequence to play */
    int              cutscene_count;   /* Number of scenes in sequence */
    int              cutscene_index;   /* Current scene index in sequence */

    /* ---- Misc ---- */
    char             data_dir[512];    /* Path to game data directory */
} fd2_game_t;

/* ---- Lifecycle ---- */

/*
 * Initialize the game: create window, load resources, set initial state.
 * data_dir: path to directory containing DAT files (e.g., "game/")
 * Returns 0 on success, -1 on failure.
 */
int fd2_game_init(fd2_game_t* game, const char* data_dir);

/*
 * Run the main game loop. Blocks until the game exits.
 * Returns 0 on normal exit, -1 on error.
 */
int fd2_game_run(fd2_game_t* game);

/*
 * Shut down and free all resources.
 */
void fd2_game_shutdown(fd2_game_t* game);

/* ---- State Registration ---- */

/*
 * Register state operations for a given state ID.
 * The game comes with built-in states; this allows overriding.
 */
void fd2_game_register_state(fd2_game_t* game, fd2_state_t state,
                              const fd2_state_ops_t* ops);

/* ---- Utility ---- */

/*
 * Build a full path relative to the game's data directory.
 * Returns a thread-local static buffer; not safe across calls.
 */
const char* fd2_game_data_path(fd2_game_t* game, const char* filename);

/*
 * Request the game to quit (sets running = 0).
 */
void fd2_game_request_quit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_GAME_H */
