/**
 * FD2 Scene/Cutscene Implementation
 *
 * Based on IDA MCP analysis of:
 *   sub_1366A - Scene player (0x1366A)
 *   sub_15F84 - Scene renderer (0x15F84)
 *   off_627D8 - Scene data table (hardcoded in exe)
 *
 * Scene data format (from IDA MCP):
 *   First byte: number of commands
 *   Each command:
 *     - byte0: command_type (high bit 0x80 = special command)
 *     - byte1: param_count
 *     - Following: param_count * 2 bytes (little-endian u16)
 */

#include "fd2_scene.h"
#include <string.h>
#include <stdio.h>
#include <SDL2/SDL.h>

/* ========================================================================
 * Scene Data Tables - Extracted from IDA MCP
 * ======================================================================== */

/* Scene 97 - Battlefield map (from IDA MCP at 0x6342F) */
static const u8 scene_97_raw[] = {
    0x03, 0x01, 0x01, 0x01, 0x00, 0x01, 0x01, 0x01, 0x01, 0x84, 0x02, 0x00,
    0x00, 0x01, 0x02, 0x09, 0x01, 0x03, 0x00, 0x03, 0x03, 0x03, 0x04, 0x03,
    0x01, 0x03, 0x00, 0x00, 0x03, 0x03, 0x04, 0x03, 0x01, 0x03, 0x00, 0x03,
    0x01, 0x03, 0x04, 0x03, 0x01, 0x04, 0x00, 0x03, 0x01, 0x03, 0x03, 0x00,
    0x04, 0x03, 0x01, 0x04, 0x00, 0x03, 0x01, 0x03, 0x03, 0x03, 0x04, 0x00,
    0x01, 0x04, 0x00, 0x00, 0x01, 0x03, 0x03, 0x03, 0x04, 0x03, 0x01, 0x04,
    0x00, 0x03, 0x01, 0x00, 0x03, 0x03, 0x04, 0x03, 0x01, 0x04, 0x00, 0x03,
    0x01, 0x03, 0x03, 0x00, 0x04, 0x03, 0x01, 0x04, 0x00, 0x03, 0x01, 0x03,
    0x03, 0x03, 0x04, 0x00, 0x01, 0x06, 0x01, 0x02, 0x02, 0x01, 0x0A, 0x01,
    0x02, 0x00, 0x01, 0x03, 0x01, 0x04, 0x01, 0x03, 0x02, 0x01, 0x04, 0x01,
    0x01, 0x01, 0x04, 0x02, 0x01, 0x01, 0x04, 0x01, 0x01, 0x80, 0x01, 0x04,
    0x01, 0x01, 0x82, 0x01, 0x03, 0x03, 0x05, 0x02, 0x01, 0x03, 0x03, 0x01,
    0x01, 0x03, 0x00, 0x01, 0x01, 0x03, 0x03, 0x01, 0x02, 0x03, 0x03, 0x04,
    0x00, 0x04, 0x02, 0x03, 0x03, 0x04, 0x03, 0x00, 0x00
};

/* Scene 99 - Opening animation (from IDA MCP at 0x62980) */
static const u8 scene_99_raw[] = {
    0x05, 0x06, 0x04, 0x00, 0x02, 0x01, 0x02, 0x02, 0x02, 0x03, 0x02, 0x88,
    0x01, 0x00, 0x01, 0x88, 0x01, 0x00, 0x03, 0x08, 0x01, 0x00, 0x01, 0x84,
    0x01, 0x00, 0x00
};

/* Scene 100 - Intro scene 1 (from IDA MCP at 0x6299B) */
static const u8 scene_100_raw[] = {
    0x01, 0x01, 0x04, 0x04, 0x00, 0x05, 0x00, 0x06, 0x00, 0x07, 0x00, 0x04,
    0x01, 0x04, 0x08, 0x02, 0x09, 0x02, 0x0A, 0x01, 0x0B, 0x03, 0x02, 0x04,
    0x08, 0x03, 0x09, 0x02, 0x0A, 0x02, 0x0B, 0x02, 0x02, 0x04, 0x08, 0x02,
    0x09, 0x03, 0x0A, 0x02, 0x0B, 0x02, 0x84, 0x05, 0x09, 0x02, 0x00, 0x00,
    0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x03, 0x02, 0x04, 0x0E, 0x01, 0x0F,
    0x02, 0x10, 0x02, 0x11, 0x02, 0x02, 0x04, 0x0E, 0x01, 0x0F, 0x01, 0x10,
    0x01, 0x11, 0x01, 0x02, 0x04, 0x0E, 0x02, 0x0F, 0x01, 0x10, 0x02, 0x11,
    0x01, 0x02, 0x01, 0x05, 0x12, 0x02, 0x13, 0x02, 0x14, 0x03, 0x15, 0x02,
    0x16, 0x03, 0x01, 0x01, 0x12
};

/* Scene data wrapper - defined in fd2_scene.h */

static const struct raw_scene raw_scenes[] = {
    { .scene_id = 97, .raw_data = scene_97_raw, .raw_size = sizeof(scene_97_raw) },
    { .scene_id = 99, .raw_data = scene_99_raw, .raw_size = sizeof(scene_99_raw) },
    { .scene_id = 100, .raw_data = scene_100_raw, .raw_size = sizeof(scene_100_raw) },
};

#define RAW_SCENE_COUNT (sizeof(raw_scenes) / sizeof(struct raw_scene))

/* Minimum scene display time in frames (at 60fps, 60 frames = 1 second) */
#define SCENE_MIN_DISPLAY_FRAMES 120  /* 2 seconds minimum */

/* ========================================================================
 * Scene Player Implementation (async version)
 * ======================================================================== */

int scene_player_init(scene_player_t* player) {
    if (!player) {
        return -1;
    }

    memset(player, 0, sizeof(scene_player_t));
    player->current_scene_id = -1;
    player->current_cmd_idx = 0;
    player->cmd_step = 0;
    player->anim_frame = 0;
    player->bg_layer = 0;
    player->render_mode = 0;
    player->cmd_timer = 0;
    player->frame_count = 0;
    player->scene_done_frame = 0;
    player->playing = false;
    player->paused = false;
    player->skip_requested = false;
    player->num_characters = 0;

    memset(player->characters, 0, sizeof(player->characters));

    return 0;
}

void scene_player_shutdown(scene_player_t* player) {
    if (player) {
        player->playing = false;
        player->raw_scene = NULL;
    }
}

const struct raw_scene* scene_get_raw_scene(int scene_id) {
    for (size_t i = 0; i < RAW_SCENE_COUNT; i++) {
        if (raw_scenes[i].scene_id == scene_id) {
            return &raw_scenes[i];
        }
    }
    return NULL;
}

const struct raw_scene* scene_get_all_scenes(size_t* out_count) {
    if (out_count) {
        *out_count = RAW_SCENE_COUNT;
    }
    return raw_scenes;
}

int scene_player_play(scene_player_t* player, int scene_id) {
    if (!player) {
        return -1;
    }

    const struct raw_scene* raw_scene = NULL;
    for (size_t i = 0; i < RAW_SCENE_COUNT; i++) {
        if (raw_scenes[i].scene_id == scene_id) {
            raw_scene = &raw_scenes[i];
            break;
        }
    }

    if (!raw_scene) {
        printf("[SCENE] Scene %d not found\n", scene_id);
        return -1;
    }

    printf("[SCENE] Playing scene %d (raw size=%zu)\n", scene_id, raw_scene->raw_size);

    player->raw_scene = raw_scene;
    player->current_scene_id = scene_id;
    player->scene_data_ptr = raw_scene->raw_data;
    player->current_cmd_idx = 0;
    player->cmd_step = 0;
    player->anim_frame = 0;
    player->cmd_timer = 0;
    player->frame_count = 0;
    player->scene_done_frame = 0;
    player->playing = true;
    player->paused = false;
    player->skip_requested = false;

    return 0;
}

bool scene_execute_cmd(scene_player_t* player, u8 cmd_type, u8 param_count, const u16* params) {
    if (!player) {
        return true;
    }

    int special = (cmd_type & 0x80) != 0;
    int cmd_base = cmd_type & 0x7F;

    if (!special) {
        /* Regular command: animate characters */
        player->anim_frame++;
        if (player->anim_frame < 7) {
            return false;
        }

        for (int j = 0; j < param_count; j++) {
            u8 char_idx = (u8)params[j];
            if (char_idx < 32) {
                scene_char_state_t* ch = &player->characters[char_idx];
                ch->frame = player->anim_frame;
                ch->visible = 1;
            }
        }

        player->anim_frame = 0;
        return true;
    }

    /* Special command (high bit set) */
    switch (cmd_base) {
        case 0x04:
            for (int j = 0; j < param_count; j++) {
                u8 char_idx = (u8)(params[j] & 0xFF);
                u8 action = (u8)((params[j] >> 8) & 0xFF);
                if (char_idx < 32) {
                    scene_char_state_t* ch = &player->characters[char_idx];
                    ch->action = action;
                    ch->visible = 1;
                    ch->frame = 0;
                }
            }
            printf("[SCENE] Init chars (cmd=0x%02X, count=%d)\n", cmd_type, param_count);
            break;

        case 0x05:
            player->cmd_timer = 30;
            printf("[SCENE] Wait/fade (cmd=0x%02X)\n", cmd_type);
            break;

        case 0x00:
            printf("[SCENE] Display (cmd=0x%02X, count=%d)\n", cmd_type, param_count);
            break;

        default:
            printf("[SCENE] Special cmd=0x%02X, count=%d\n", cmd_type, param_count);
            break;
    }

    return true;
}

bool scene_player_update(scene_player_t* player, u32 frame_time_ms) {
    if (!player || !player->playing) {
        return true;
    }

    if (player->paused || player->skip_requested) {
        return player->skip_requested;
    }

    player->frame_count++;

    /* If scene commands are done but minimum display time not reached, keep showing */
    if (player->scene_done_frame > 0) {
        if (player->frame_count < player->scene_done_frame) {
            return false;  /* Still displaying, don't end yet */
        }
        /* Minimum display time reached */
        player->playing = false;
        printf("[SCENE] Scene %d complete (displayed for %d frames)\n",
               player->current_scene_id, player->frame_count);
        return true;
    }

    if (player->cmd_timer > 0) {
        player->cmd_timer--;
        return false;
    }

    if (!player->scene_data_ptr) {
        player->playing = false;
        return true;
    }

    const u8* data = player->raw_scene->raw_data;
    size_t offset = (size_t)player->current_cmd_idx;

    if (offset == 0) {
        player->total_commands = data[0];
        player->current_cmd_idx = 1;
        offset = 1;
        printf("[SCENE] Scene has %d commands\n", player->total_commands);
    }

    if (player->cmd_step >= player->total_commands) {
        /* All commands executed, set minimum display time */
        player->scene_done_frame = player->frame_count + SCENE_MIN_DISPLAY_FRAMES;
        printf("[SCENE] Commands done, displaying until frame %d\n", player->scene_done_frame);
        return false;
    }

    if (offset >= player->raw_scene->raw_size) {
        player->playing = false;
        return true;
    }

    u8 cmd_type = data[offset++];
    u8 param_count = data[offset++];

    u16 params[8];
    for (int i = 0; i < param_count && i < 8; i++) {
        if (offset + 1 >= player->raw_scene->raw_size) {
            break;
        }
        params[i] = (u16)(data[offset] | (data[offset + 1] << 8));
        offset += 2;
    }

    player->current_cmd_idx = offset;

    bool cmd_done = scene_execute_cmd(player, cmd_type, param_count, params);

    if (cmd_done) {
        player->cmd_step++;
    }

    return false;
}

void scene_player_render(scene_player_t* player, u8* screen, int width, int height) {
    if (!player || !screen) {
        return;
    }

    if (!player->playing && player->scene_done_frame == 0) {
        return;
    }

    int rendered_count = 0;
    for (int i = 0; i < 32; i++) {
        scene_char_state_t* ch = &player->characters[i];
        if (ch->visible) {
            int x = (i % 10) * 30 + 10;
            int y = (i / 10) * 30 + 50;

            for (int dy = 0; dy < 16; dy++) {
                for (int dx = 0; dx < 16; dx++) {
                    int sx = x + dx;
                    int sy = y + dy;
                    if (sx >= 0 && sx < width && sy >= 0 && sy < height) {
                        screen[sy * width + sx] = (u8)(100 + i * 5 + ch->frame);
                    }
                }
            }
            rendered_count++;
        }
    }

    /* Draw battlefield map background for scene 97 */
    if (player->current_scene_id == 97) {
        /* Draw a battlefield-style background with terrain */
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                /* Sky gradient (top portion) */
                if (y < 100) {
                    int sky_color = 60 + (y * 2);
                    screen[y * width + x] = (u8)sky_color;
                }
                /* Ground terrain (bottom portion) */
                else {
                    int ground_y = y - 100;
                    /* Add some variation to ground */
                    int ground_color = 20 + (ground_y / 4);
                    /* Add horizontal terrain features */
                    if ((x / 16) % 3 == 0) {
                        ground_color += 10;
                    }
                    screen[y * width + x] = (u8)ground_color;
                }
            }
        }
        
        /* Draw grid lines for tactical map feel */
        for (int x = 0; x < width; x += 32) {
            for (int y = 100; y < height; y++) {
                screen[y * width + x] = 80;
            }
        }
        for (int y = 100; y < height; y += 32) {
            for (int x = 0; x < width; x++) {
                screen[y * width + x] = 80;
            }
        }
        
        /* Draw horizon line */
        for (int x = 0; x < width; x++) {
            screen[99 * width + x] = 120;
            screen[100 * width + x] = 120;
        }
    }
    /* If no characters visible and not scene 97, show animated background */
    else if (rendered_count == 0) {
        /* Draw a colorful checkerboard pattern */
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int color = ((x / 8) + (y / 8)) % 4;
                color = 30 + color * 40 + (player->frame_count % 60);
                screen[y * width + x] = (u8)(color % 256);
            }
        }
        
        /* Draw a pulsing center rectangle */
        int pulse = (player->frame_count * 3) % 256;
        int rect_x = 100;
        int rect_y = 60;
        int rect_w = 120;
        int rect_h = 80;
        
        for (int y = rect_y; y < rect_y + rect_h && y < height; y++) {
            for (int x = rect_x; x < rect_x + rect_w && x < width; x++) {
                screen[y * width + x] = (u8)pulse;
            }
        }
    }
}

void scene_player_skip(scene_player_t* player) {
    if (player) {
        player->skip_requested = true;
    }
}

int scene_player_get_scene_id(const scene_player_t* player) {
    if (!player) {
        return -1;
    }
    return player->current_scene_id;
}

bool scene_player_is_playing(const scene_player_t* player) {
    if (!player) {
        return false;
    }
    return player->playing || player->scene_done_frame > 0;
}
