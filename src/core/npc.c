/**
 * NPC System Implementation
 * Based on IDA sub_13185 - NPC/character initialization.
 */

#define _GNU_SOURCE
#include "fd2/npc.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int fd2_npc_system_init(fd2_npc_system_t* sys) {
    if (!sys) return -1;

    memset(sys, 0, sizeof(*sys));
    sys->npc_count = 0;
    sys->active_npc = -1;

    return 0;
}

void fd2_npc_system_shutdown(fd2_npc_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(*sys));
}

int fd2_npc_create(fd2_npc_system_t* sys,
                   s16 map_x, s16 map_y,
                   u8 sprite_id, u8 dialog_id, u8 behavior) {
    if (!sys || sys->npc_count >= FD2_NPC_MAX) return -1;

    fd2_npc_t* npc = &sys->npcs[sys->npc_count];
    memset(npc, 0, sizeof(*npc));

    npc->map_x = map_x;
    npc->map_y = map_y;
    npc->sprite_id = sprite_id;
    npc->dialog_id = dialog_id;
    npc->behavior = behavior;
    npc->visible = true;
    npc->activated = false;

    int index = sys->npc_count;
    sys->npc_count++;

    return index;
}

fd2_npc_t* fd2_npc_get(fd2_npc_system_t* sys, int index) {
    if (!sys || index < 0 || index >= sys->npc_count) return NULL;
    return &sys->npcs[index];
}

const fd2_npc_t* fd2_npc_get_c(const fd2_npc_system_t* sys, int index) {
    return (const fd2_npc_t*)fd2_npc_get((fd2_npc_system_t*)sys, index);
}

int fd2_npc_find_at(const fd2_npc_system_t* sys, s16 map_x, s16 map_y) {
    if (!sys) return -1;

    for (int i = 0; i < sys->npc_count; i++) {
        if (sys->npcs[i].visible &&
            sys->npcs[i].map_x == map_x &&
            sys->npcs[i].map_y == map_y) {
            return i;
        }
    }

    return -1;
}

void fd2_npc_system_update(fd2_npc_system_t* sys, u32 tick) {
    if (!sys) return;

    for (int i = 0; i < sys->npc_count; i++) {
        fd2_npc_t* npc = &sys->npcs[i];
        if (!npc->visible) continue;

        if (npc->behavior == 1 && npc->patrol_count > 0) {
            /* Patrol behavior: move between patrol points */
            if (tick % 60 == 0) {  /* Move every 60 ticks (1 second at 60fps) */
                npc->patrol_index = (npc->patrol_index + 1) % npc->patrol_count;
                u8 point = npc->patrol_route[npc->patrol_index];
                npc->map_x = (point & 0x0F) * 2;
                npc->map_y = (point >> 4) * 2;
            }
        }
    }
}

void fd2_npc_system_render(const fd2_npc_system_t* sys,
                           u8* screen, int screen_w, int screen_h,
                           s16 scroll_x, s16 scroll_y) {
    if (!sys || !screen) return;

    for (int i = 0; i < sys->npc_count; i++) {
        const fd2_npc_t* npc = &sys->npcs[i];
        if (!npc->visible) continue;

        /* Convert map position to screen position */
        int screen_x = npc->map_x * 16 - scroll_x;
        int screen_y = npc->map_y * 16 - scroll_y;

        /* Simple NPC sprite rendering (placeholder) */
        int sprite_w = 16;
        int sprite_h = 24;

        for (int dy = 0; dy < sprite_h; dy++) {
            for (int dx = 0; dx < sprite_w; dx++) {
                int sx = screen_x + dx;
                int sy = screen_y + dy;
                if (sx >= 0 && sx < screen_w && sy >= 0 && sy < screen_h) {
                    /* Render sprite as colored rectangle */
                    u8 color = 100 + (i * 7) % 100;
                    if (dx == 0 || dx == sprite_w - 1 || dy == 0 || dy == sprite_h - 1) {
                        color += 50;
                    }
                    screen[sy * screen_w + sx] = color;
                }
            }
        }

        /* Draw NPC index number below sprite */
        if (screen_y + sprite_h + 8 < screen_h && screen_x + 8 < screen_w) {
            screen[(screen_y + sprite_h + 4) * screen_w + screen_x + 6] = 255;
        }
    }
}

/* NPC initialization data for opening scene (sub_13185) */
typedef struct {
    s16 map_x;
    s16 map_y;
    u8  sprite_id;
    u8  dialog_id;
    u8  behavior;
} npc_init_data_t;

/* Opening scene NPC configuration (map 32) */
static const npc_init_data_t opening_scene_npcs[] = {
    { .map_x = 8,  .map_y = 6, .sprite_id = 0, .dialog_id = 0, .behavior = 0 },
    { .map_x = 9,  .map_y = 6, .sprite_id = 1, .dialog_id = 1, .behavior = 0 },
    { .map_x = 10, .map_y = 6, .sprite_id = 2, .dialog_id = 2, .behavior = 0 },
    { .map_x = 11, .map_y = 6, .sprite_id = 3, .dialog_id = 3, .behavior = 0 },
    { .map_x = 12, .map_y = 6, .sprite_id = 4, .dialog_id = 4, .behavior = 0 },
};

#define OPENING_NPC_COUNT (sizeof(opening_scene_npcs) / sizeof(npc_init_data_t))

int fd2_npc_init_from_script(fd2_npc_system_t* sys, int script_id) {
    if (!sys) return -1;

    /* Clear existing NPCs */
    sys->npc_count = 0;

    /* Load NPCs based on script ID */
    if (script_id == 32 || script_id == 99) {
        /* Opening scene - load default NPCs */
        for (size_t i = 0; i < OPENING_NPC_COUNT; i++) {
            const npc_init_data_t* data = &opening_scene_npcs[i];
            fd2_npc_create(sys, data->map_x, data->map_y,
                          data->sprite_id, data->dialog_id, data->behavior);
        }
        printf("[NPC] Loaded %d NPCs for opening scene (script %d)\n",
               sys->npc_count, script_id);
        return sys->npc_count;
    }

    printf("[NPC] Unknown script ID: %d\n", script_id);
    return 0;
}
