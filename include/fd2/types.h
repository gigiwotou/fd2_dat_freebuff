#ifndef FD2_TYPES_H
#define FD2_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* ---- Basic Types ---- */
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int8_t   s8;
typedef int16_t  s16;
typedef int32_t  s32;
typedef int64_t  s64;

/* ---- Screen Constants ---- */
#define FD2_SCREEN_W       320
#define FD2_SCREEN_H       200
#define FD2_SCREEN_SIZE    (FD2_SCREEN_W * FD2_SCREEN_H)
#define FD2_PALETTE_COLORS 256
#define FD2_PALETTE_BYTES  (FD2_PALETTE_COLORS * 3)
#define FD2_DAT_MAGIC      "LLLLLL"
#define FD2_DAT_MAGIC_LEN  6

/* ---- Target Frame Rate ---- */
#define FD2_TARGET_FPS     60
#define FD2_FRAME_TIME_MS  (1000 / FD2_TARGET_FPS)

/* ---- Platform Abstraction ---- */

typedef struct fd2_video   fd2_video_t;
typedef struct fd2_audio   fd2_audio_t;
typedef struct fd2_input   fd2_input_t;
typedef struct fd2_filesys fd2_filesys_t;

/* ---- Simulation Types ---- */
typedef uint32_t entity_id_t;
#define FD2_INVALID_ENTITY ((entity_id_t)0xFFFFFFFF)

/* ---- Event Types ---- */
typedef enum {
    /* Core game events */
    EVENT_NONE = 0,
    EVENT_ENTITY_MOVED,
    EVENT_ENTITY_SELECTED,
    EVENT_DAMAGE_DEALT,
    EVENT_ENTITY_DIED,
    EVENT_SCRIPT_TRIGGERED,
    EVENT_DIALOG_STARTED,
    EVENT_DIALOG_FINISHED,
    EVENT_BATTLE_STARTED,
    EVENT_BATTLE_FINISHED,
    EVENT_MAP_LOADED,
    EVENT_MENU_SELECTED,

    /* MOD extension events */
    EVENT_MOD_CUSTOM_0 = 100,
    EVENT_MOD_CUSTOM_1,
    EVENT_MOD_CUSTOM_2,
    EVENT_MOD_CUSTOM_3,

    EVENT_COUNT
} fd2_event_type_t;

#define EVENT_DATA_SIZE 256

typedef struct {
    fd2_event_type_t type;
    u32              timestamp;
    u8               data[EVENT_DATA_SIZE];
} fd2_event_t;

typedef void (*fd2_event_handler_t)(const fd2_event_t* event, void* user_data);

/* ---- Game States ---- */
typedef enum {
    FD2_STATE_NONE = 0,
    FD2_STATE_INIT,
    FD2_STATE_INTRO,
    FD2_STATE_MENU,
    FD2_STATE_DEMO,
    FD2_STATE_CHAR_SELECT,
    FD2_STATE_CUTSCENE,
    FD2_STATE_BATTLE,
    FD2_STATE_VICTORY,
    FD2_STATE_CONTINUE,
    FD2_STATE_GAME_OVER,
    FD2_STATE_QUIT,
    FD2_STATE_COUNT
} fd2_state_t;

/* ---- Input Actions ---- */
typedef enum {
    FD2_ACTION_NONE = 0,
    FD2_ACTION_UP,
    FD2_ACTION_DOWN,
    FD2_ACTION_LEFT,
    FD2_ACTION_RIGHT,
    FD2_ACTION_A,
    FD2_ACTION_B,
    FD2_ACTION_C,
    FD2_ACTION_D,
    FD2_ACTION_START,
    FD2_ACTION_ESCAPE,
    FD2_ACTION_COIN,
    FD2_ACTION_DEBUG_GRID,
    FD2_ACTION_COUNT
} fd2_action_t;

/* ---- MOD Types ---- */
#define FD2_MOD_ID_LEN    64
#define FD2_MOD_NAME_LEN  128
#define FD2_MOD_VER_LEN   16
#define FD2_MOD_AUTHOR_LEN 64
#define FD2_MAX_MODS      64
#define FD2_MAX_ENTITIES  1024

typedef struct fd2_mod      fd2_mod_t;
typedef struct fd2_mod_mgr  fd2_mod_mgr_t;
typedef struct fd2_mod_api  fd2_mod_api_t;

typedef int  (*fd2_mod_init_fn)(void);
typedef void (*fd2_mod_update_fn)(void);
typedef void (*fd2_mod_shutdown_fn)(void);

struct fd2_mod {
    char              id[FD2_MOD_ID_LEN];
    char              name[FD2_MOD_NAME_LEN];
    char              version[FD2_MOD_VER_LEN];
    char              author[FD2_MOD_AUTHOR_LEN];

    fd2_mod_init_fn    init;
    fd2_mod_update_fn  update;
    fd2_mod_shutdown_fn shutdown;

    bool              overrides_data;
    bool              adds_scripts;
    bool              adds_events;
    bool              adds_ui;

    void*             user_data;
};

#endif /* FD2_TYPES_H */
