#ifndef FD2_SCENE_H
#define FD2_SCENE_H

#include "fd2_decoder.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Scene/Cutscene System
 *
 * Based on IDA MCP analysis of sub_1366A and sub_15F84.
 * Scenes are played sequentially to tell the story.
 * Each scene contains commands that control:
 *   - Character loading and positioning
 *   - Animation playback
 *   - Background rendering
 *   - Fade effects
 * ======================================================================== */

/* ---- Scene Command Types (from sub_15F84 analysis) ---- */
typedef enum {
    SCENE_CMD_END = 0xFF,          /* -1: End of scene */
    SCENE_CMD_LINE_BREAK = 0xFE,   /* -2: Switch to next line/layer */
    SCENE_CMD_CHAR_SPRITE = 0xEF,  /* -17: Load character sprite */
    SCENE_CMD_CHAR_SPRITE_ALT = 0xEE,  /* -18: Alternate sprite load */
    SCENE_CMD_CHAR_STATE_LOAD = 0xED,  /* -19: Load from character state */
    SCENE_CMD_CHAR_ANIM = 0xEC,    /* -20: Character animation */
    SCENE_CMD_MOVE = 0x00,         /* Regular move command */
    SCENE_CMD_WAIT = 0x01,         /* Wait/delay command */
    SCENE_CMD_FADE = 0x02,         /* Fade effect command */
    SCENE_CMD_SHOW = 0x03,         /* Show/hide element */
    SCENE_CMD_EFFECT = 0x04,       /* Special effect */
    SCENE_CMD_POSITION = 0x05,     /* Set position */
    SCENE_CMD_UNKNOWN = 0x06       /* Unknown command type */
} scene_cmd_type_t;

/* ---- Maximum parameters per command ---- */
#define SCENE_MAX_PARAMS 8

/* ---- Scene Command ---- */
typedef struct {
    u8  type;                  /* Command type (see scene_cmd_type_t) */
    u8  param_count;           /* Number of parameters */
    u16 params[SCENE_MAX_PARAMS];  /* Command parameters */
} scene_cmd_t;

/* ---- Scene Data ---- */
typedef struct {
    int scene_id;              /* Scene ID */
    u8  cmd_count;             /* Number of commands */
    const scene_cmd_t* commands;  /* Command list */
} scene_data_t;

/* ---- Character State (80 bytes per original dword_53A45) ---- */
typedef struct {
    u16 char_id;               /* Character ID */
    u16 sprite_id;             /* Sprite index in DATO.DAT */
    u8  action;                /* Current action/movement type */
    u8  frame;                 /* Animation frame */
    u8  frame_timer;           /* Frame timer */
    u8  visible;               /* Visibility flag */
    
    /* Position */
    u16 x;                     /* X position (screen coords) */
    u16 y;                     /* Y position (screen coords) */
    s16 dx;                    /* X movement delta per frame */
    s16 dy;                    /* Y movement delta per frame */
    
    /* Target position */
    u16 target_x;
    u16 target_y;
    
    /* Animation */
    u8  anim_id;               /* Animation sequence ID */
    u8  anim_frame;            /* Current animation frame */
    u8  anim_count;            /* Number of animation frames */
    u8  anim_speed;            /* Animation speed (frames per step) */
    
    /* State flags */
    u8  moving;                /* Is currently moving */
    u8  talking;               /* Is showing dialog */
    u8  reserved[54];          /* Padding to 80 bytes */
} scene_char_state_t;

/* ---- Scene Player State ---- */
struct raw_scene;
struct raw_scene {
    int scene_id;
    const u8* raw_data;
    size_t raw_size;
};

typedef struct {
    /* Current scene */
    int current_scene_id;      /* Currently playing scene ID */
    size_t current_cmd_idx;    /* Current offset in raw data */
    int cmd_step;              /* Step within current command */
    int anim_frame;            /* Current animation frame (0-6) */
    int total_commands;        /* Total commands in scene */
    
    /* Scene data */
    const struct raw_scene* raw_scene;  /* Pointer to raw scene data */
    const u8* scene_data_ptr;      /* Current position in raw data */
    
    /* Character states */
    scene_char_state_t characters[32];  /* Max 32 characters */
    int num_characters;
    
    /* Rendering */
    int bg_layer;              /* Background layer */
    int render_mode;           /* Render mode flags */
    
    /* Timing */
    u32 cmd_timer;             /* Command execution timer */
    u32 frame_count;           /* Frame counter */
    u32 scene_done_frame;      /* Frame when scene commands finished */
    
    /* Flags */
    bool playing;              /* Is currently playing */
    bool paused;               /* Is paused */
    bool skip_requested;       /* User requested skip */
} scene_player_t;

/* ---- Raw Scene Data (for export) ---- */

/*
 * Get the raw scenes table for export tools.
 */
const struct raw_scene* scene_get_all_scenes(size_t* out_count);

/* ---- Scene ID Constants (from sub_3231B analysis) ---- */
#define SCENE_OPENING        99  /* Opening animation */
#define SCENE_INTRO_START   100  /* Intro scene start */
#define SCENE_INTRO_END     105  /* Intro scene end */
#define SCENE_BATTLE_START   90  /* Battle intro start */
#define SCENE_BATTLE_END     98  /* Battle intro end */
#define SCENE_FIELD_MAP      97  /* Battlefield map (main field scene) */

/* ---- Lifecycle ---- */

/*
 * Initialize scene player system.
 */
int scene_player_init(scene_player_t* player);

/*
 * Clean up scene player.
 */
void scene_player_shutdown(scene_player_t* player);

/*
 * Play a scene by ID.
 * Returns 0 on success, -1 if scene not found.
 */
int scene_player_play(scene_player_t* player, int scene_id);

/*
 * Update scene player (call every frame).
 * Returns true when scene is complete.
 */
bool scene_player_update(scene_player_t* player, u32 frame_time_ms);

/*
 * Render current scene to screen buffer.
 */
void scene_player_render(scene_player_t* player, u8* screen, int width, int height);

/*
 * Skip current scene.
 */
void scene_player_skip(scene_player_t* player);

/*
 * Get current scene ID.
 */
int scene_player_get_scene_id(const scene_player_t* player);

/*
 * Check if a scene is currently playing.
 */
bool scene_player_is_playing(const scene_player_t* player);

/* ---- Helper Functions ---- */

/*
 * Get scene data for a given scene ID.
 * Scene data is hardcoded based on IDA MCP analysis.
 */
const struct raw_scene* scene_get_raw_scene(int scene_id);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SCENE_H */
