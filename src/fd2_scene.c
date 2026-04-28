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

/* Scene 0 - First battlefield scene (5 commands, 27 bytes) */
static const u8 scene_0_raw[] = {
    0x05, 0x06, 0x04, 0x00, 0x02, 0x01, 0x02, 0x02, 0x02, 0x03, 0x02, 0x88,
    0x01, 0x00, 0x01, 0x88, 0x01, 0x00, 0x03, 0x08, 0x01, 0x00, 0x01, 0x84,
    0x01, 0x00, 0x00
};

/* Scene 99 - Opening animation (2 commands, 9 bytes) */
static const u8 scene_99_raw[] = {
    0x02, 0x88, 0x01, 0x08, 0x02, 0x80, 0x01, 0x08, 0x02
};

/* Scene 100 - Intro scene 1 */
static const u8 scene_100_raw[] = {
    0x03, 0x84, 0x05, 0x09, 0x02, 0x00, 0x00, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00
};

/* Scene data wrapper - defined in fd2_scene.h */

static const struct raw_scene raw_scenes[] = {
    { .scene_id = 0, .raw_data = scene_0_raw, .raw_size = sizeof(scene_0_raw) },
    { .scene_id = 99, .raw_data = scene_99_raw, .raw_size = sizeof(scene_99_raw) },
    { .scene_id = 100, .raw_data = scene_100_raw, .raw_size = sizeof(scene_100_raw) },
};

#define RAW_SCENE_COUNT (sizeof(raw_scenes) / sizeof(struct raw_scene))

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

const scene_data_t* scene_get_data(int scene_id) {
    for (size_t i = 0; i < RAW_SCENE_COUNT; i++) {
        if (raw_scenes[i].scene_id == scene_id) {
            return NULL;
        }
    }
    return NULL;
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
        player->playing = false;
        printf("[SCENE] Scene %d complete\n", player->current_scene_id);
        return true;
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

    if (!player->playing) {
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

    if (rendered_count == 0) {
        for (int x = 0; x < 320; x += 2) {
            for (int y = 0; y < 200; y += 2) {
                screen[y * 320 + x] = (u8)((player->frame_count + x + y) % 256);
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
    return player->playing;
}
