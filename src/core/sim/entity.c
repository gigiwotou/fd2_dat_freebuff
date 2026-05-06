/**
 * Entity Manager Implementation
 * Fixed-size array ECS with bitmask for component presence.
 */

#define _GNU_SOURCE
#include "fd2/sim/entity.h"
#include <string.h>

static bool bit_test(const u32* mask, entity_id_t id) {
    if (id >= FD2_MAX_ENTITIES) return false;
    return (mask[id / 32] >> (id % 32)) & 1;
}

static void bit_set(u32* mask, entity_id_t id) {
    if (id >= FD2_MAX_ENTITIES) return;
    mask[id / 32] |= (1u << (id % 32));
}

static void bit_clear(u32* mask, entity_id_t id) {
    if (id >= FD2_MAX_ENTITIES) return;
    mask[id / 32] &= ~(1u << (id % 32));
}

static int bit_popcount(const u32* mask) {
    int count = 0;
    for (int i = 0; i < (FD2_MAX_ENTITIES + 31) / 32; i++) {
        u32 v = mask[i];
        while (v) {
            count += (v & 1);
            v >>= 1;
        }
    }
    return count;
}

void fd2_entity_mgr_init(fd2_entity_mgr_t* mgr) {
    memset(mgr, 0, sizeof(*mgr));
    mgr->next_id = 0;
    mgr->entity_count = 0;
}

entity_id_t fd2_entity_create(fd2_entity_mgr_t* mgr) {
    if (mgr->entity_count >= FD2_MAX_ENTITIES) {
        return FD2_INVALID_ENTITY;
    }

    for (entity_id_t id = 0; id < FD2_MAX_ENTITIES; id++) {
        if (!bit_test(mgr->active_mask, id)) {
            bit_set(mgr->active_mask, id);
            mgr->entity_count++;
            return id;
        }
    }

    return FD2_INVALID_ENTITY;
}

void fd2_entity_destroy(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id)) return;

    fd2_entity_remove_sprite(mgr, id);
    fd2_entity_remove_stats(mgr, id);
    fd2_entity_remove_npc(mgr, id);
    fd2_entity_remove_battle(mgr, id);
    fd2_entity_remove_tag(mgr, id);

    bit_clear(mgr->active_mask, id);
    mgr->entity_count--;
}

bool fd2_entity_is_valid(const fd2_entity_mgr_t* mgr, entity_id_t id) {
    return bit_test(mgr->active_mask, id);
}

/* ---- Sprite Component ---- */

fd2_sprite_comp_t* fd2_entity_get_sprite(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id) || !bit_test(mgr->sprite_mask, id)) return NULL;
    return &mgr->sprites[id];
}

const fd2_sprite_comp_t* fd2_entity_get_sprite_c(const fd2_entity_mgr_t* mgr, entity_id_t id) {
    return (const fd2_sprite_comp_t*)fd2_entity_get_sprite((fd2_entity_mgr_t*)mgr, id);
}

fd2_sprite_comp_t* fd2_entity_add_sprite(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id)) return NULL;
    bit_set(mgr->sprite_mask, id);
    memset(&mgr->sprites[id], 0, sizeof(fd2_sprite_comp_t));
    return &mgr->sprites[id];
}

void fd2_entity_remove_sprite(fd2_entity_mgr_t* mgr, entity_id_t id) {
    bit_clear(mgr->sprite_mask, id);
    if (bit_test(mgr->active_mask, id)) {
        memset(&mgr->sprites[id], 0, sizeof(fd2_sprite_comp_t));
    }
}

/* ---- Stats Component ---- */

fd2_stats_comp_t* fd2_entity_get_stats(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id) || !bit_test(mgr->stats_mask, id)) return NULL;
    return &mgr->stats[id];
}

const fd2_stats_comp_t* fd2_entity_get_stats_c(const fd2_entity_mgr_t* mgr, entity_id_t id) {
    return (const fd2_stats_comp_t*)fd2_entity_get_stats((fd2_entity_mgr_t*)mgr, id);
}

fd2_stats_comp_t* fd2_entity_add_stats(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id)) return NULL;
    bit_set(mgr->stats_mask, id);
    memset(&mgr->stats[id], 0, sizeof(fd2_stats_comp_t));
    return &mgr->stats[id];
}

void fd2_entity_remove_stats(fd2_entity_mgr_t* mgr, entity_id_t id) {
    bit_clear(mgr->stats_mask, id);
    if (bit_test(mgr->active_mask, id)) {
        memset(&mgr->stats[id], 0, sizeof(fd2_stats_comp_t));
    }
}

/* ---- NPC Component ---- */

fd2_npc_comp_t* fd2_entity_get_npc(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id) || !bit_test(mgr->npc_mask, id)) return NULL;
    return &mgr->npcs[id];
}

const fd2_npc_comp_t* fd2_entity_get_npc_c(const fd2_entity_mgr_t* mgr, entity_id_t id) {
    return (const fd2_npc_comp_t*)fd2_entity_get_npc((fd2_entity_mgr_t*)mgr, id);
}

fd2_npc_comp_t* fd2_entity_add_npc(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id)) return NULL;
    bit_set(mgr->npc_mask, id);
    memset(&mgr->npcs[id], 0, sizeof(fd2_npc_comp_t));
    return &mgr->npcs[id];
}

void fd2_entity_remove_npc(fd2_entity_mgr_t* mgr, entity_id_t id) {
    bit_clear(mgr->npc_mask, id);
    if (bit_test(mgr->active_mask, id)) {
        memset(&mgr->npcs[id], 0, sizeof(fd2_npc_comp_t));
    }
}

/* ---- Battle Component ---- */

fd2_battle_comp_t* fd2_entity_get_battle(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id) || !bit_test(mgr->battle_mask, id)) return NULL;
    return &mgr->battles[id];
}

const fd2_battle_comp_t* fd2_entity_get_battle_c(const fd2_entity_mgr_t* mgr, entity_id_t id) {
    return (const fd2_battle_comp_t*)fd2_entity_get_battle((fd2_entity_mgr_t*)mgr, id);
}

fd2_battle_comp_t* fd2_entity_add_battle(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id)) return NULL;
    bit_set(mgr->battle_mask, id);
    memset(&mgr->battles[id], 0, sizeof(fd2_battle_comp_t));
    return &mgr->battles[id];
}

void fd2_entity_remove_battle(fd2_entity_mgr_t* mgr, entity_id_t id) {
    bit_clear(mgr->battle_mask, id);
    if (bit_test(mgr->active_mask, id)) {
        memset(&mgr->battles[id], 0, sizeof(fd2_battle_comp_t));
    }
}

/* ---- Tag Component ---- */

fd2_tag_comp_t* fd2_entity_get_tag(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id) || !bit_test(mgr->tag_mask, id)) return NULL;
    return &mgr->tags[id];
}

const fd2_tag_comp_t* fd2_entity_get_tag_c(const fd2_entity_mgr_t* mgr, entity_id_t id) {
    return (const fd2_tag_comp_t*)fd2_entity_get_tag((fd2_entity_mgr_t*)mgr, id);
}

fd2_tag_comp_t* fd2_entity_add_tag(fd2_entity_mgr_t* mgr, entity_id_t id) {
    if (!fd2_entity_is_valid(mgr, id)) return NULL;
    bit_set(mgr->tag_mask, id);
    memset(&mgr->tags[id], 0, sizeof(fd2_tag_comp_t));
    return &mgr->tags[id];
}

void fd2_entity_remove_tag(fd2_entity_mgr_t* mgr, entity_id_t id) {
    bit_clear(mgr->tag_mask, id);
    if (bit_test(mgr->active_mask, id)) {
        memset(&mgr->tags[id], 0, sizeof(fd2_tag_comp_t));
    }
}

/* ---- Tag Lookup ---- */
entity_id_t fd2_entity_find_by_tag(const fd2_entity_mgr_t* mgr, const char* name) {
    if (!mgr || !name) return FD2_INVALID_ENTITY;

    FD2_FOR_EACH_ENTITY(mgr, id) {
        if (bit_test(mgr->tag_mask, id)) {
            if (strcmp(mgr->tags[id].name, name) == 0) {
                return id;
            }
        }
    }

    return FD2_INVALID_ENTITY;
}

int fd2_entity_get_count(const fd2_entity_mgr_t* mgr) {
    return mgr ? mgr->entity_count : 0;
}
