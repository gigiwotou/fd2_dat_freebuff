/**
 * System Implementations
 * Simulation systems that process entities with specific component sets.
 */

#define _GNU_SOURCE
#include "fd2/sim/systems.h"

void sprite_system_update(fd2_entity_mgr_t* mgr, u32 tick) {
    if (!mgr) return;

    FD2_FOR_EACH_ENTITY(mgr, id) {
        fd2_sprite_comp_t* sprite = fd2_entity_get_sprite(mgr, id);
        if (!sprite) continue;

        if (sprite->moving) {
            sprite->move_progress++;
            if (sprite->move_progress >= 8) {
                sprite->move_progress = 0;
                sprite->moving = false;
                sprite->prev_tile_x = sprite->tile_x;
                sprite->prev_tile_y = sprite->tile_y;
            }
        }

        sprite->anim_timer++;
        if (sprite->anim_timer >= 4) {
            sprite->anim_timer = 0;
            sprite->anim_frame = (sprite->anim_frame + 1) % 4;
        }
    }
}

void npc_system_update(fd2_entity_mgr_t* mgr, u32 tick, fd2_event_bus_t* bus) {
    if (!mgr) return;

    FD2_FOR_EACH_ENTITY(mgr, id) {
        fd2_npc_comp_t* npc = fd2_entity_get_npc(mgr, id);
        if (!npc) continue;

        if (!npc->activated) continue;

        if (npc->behavior == 0) {
            continue;
        }

        if (npc->behavior == 1 && npc->patrol_count > 0) {
            fd2_sprite_comp_t* sprite = fd2_entity_get_sprite(mgr, id);
            if (sprite && !sprite->moving) {
                npc->current_patrol = (npc->current_patrol + 1) % npc->patrol_count;
                u8 target_point = npc->patrol_points[npc->current_patrol];
                sprite->tile_x = (target_point & 0x0F) * 16;
                sprite->tile_y = (target_point >> 4) * 16;
                sprite->prev_tile_x = sprite->tile_x;
                sprite->prev_tile_y = sprite->tile_y;
                sprite->moving = true;
                sprite->move_progress = 0;
            }
        }
    }
}

void battle_system_update(fd2_entity_mgr_t* mgr, u32 tick, fd2_event_bus_t* bus) {
    if (!mgr) return;

    FD2_FOR_EACH_ENTITY(mgr, id) {
        fd2_battle_comp_t* battle = fd2_entity_get_battle(mgr, id);
        if (!battle) continue;

        if (battle->damage_shake > 0) {
            battle->damage_shake--;
        }

        if (battle->anim_playing) {
            battle->anim_frame++;
            if (battle->anim_frame >= 8) {
                battle->anim_playing = 0;
                battle->anim_frame = 0;
                battle->in_action = false;
            }
        }
    }
}
