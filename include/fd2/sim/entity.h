#ifndef FD2_SIM_ENTITY_H
#define FD2_SIM_ENTITY_H

#include "fd2/types.h"
#include "fd2/sim/components.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Entity Manager ----
 * Simplified ECS: fixed-size arrays per component type,
 * bitmask for active entities and component presence.
 */

typedef struct {
    entity_id_t          next_id;
    u32                  active_mask[(FD2_MAX_ENTITIES + 31) / 32];
    u32                  sprite_mask[(FD2_MAX_ENTITIES + 31) / 32];
    u32                  stats_mask[(FD2_MAX_ENTITIES + 31) / 32];
    u32                  npc_mask[(FD2_MAX_ENTITIES + 31) / 32];
    u32                  battle_mask[(FD2_MAX_ENTITIES + 31) / 32];
    u32                  tag_mask[(FD2_MAX_ENTITIES + 31) / 32];

    fd2_sprite_comp_t    sprites[FD2_MAX_ENTITIES];
    fd2_stats_comp_t     stats[FD2_MAX_ENTITIES];
    fd2_npc_comp_t       npcs[FD2_MAX_ENTITIES];
    fd2_battle_comp_t    battles[FD2_MAX_ENTITIES];
    fd2_tag_comp_t       tags[FD2_MAX_ENTITIES];

    int                  entity_count;
} fd2_entity_mgr_t;

/* Initialize the entity manager */
void fd2_entity_mgr_init(fd2_entity_mgr_t* mgr);

/* Create a new entity, returns ID or FD2_INVALID_ENTITY */
entity_id_t fd2_entity_create(fd2_entity_mgr_t* mgr);

/* Destroy an entity and all its components */
void fd2_entity_destroy(fd2_entity_mgr_t* mgr, entity_id_t id);

/* Check if entity exists and is active */
bool fd2_entity_is_valid(const fd2_entity_mgr_t* mgr, entity_id_t id);

/* ---- Component Accessors ----
 * Returns pointer to component, or NULL if not present.
 */

fd2_sprite_comp_t* fd2_entity_get_sprite(fd2_entity_mgr_t* mgr, entity_id_t id);
const fd2_sprite_comp_t* fd2_entity_get_sprite_c(const fd2_entity_mgr_t* mgr, entity_id_t id);

fd2_stats_comp_t* fd2_entity_get_stats(fd2_entity_mgr_t* mgr, entity_id_t id);
const fd2_stats_comp_t* fd2_entity_get_stats_c(const fd2_entity_mgr_t* mgr, entity_id_t id);

fd2_npc_comp_t* fd2_entity_get_npc(fd2_entity_mgr_t* mgr, entity_id_t id);
const fd2_npc_comp_t* fd2_entity_get_npc_c(const fd2_entity_mgr_t* mgr, entity_id_t id);

fd2_battle_comp_t* fd2_entity_get_battle(fd2_entity_mgr_t* mgr, entity_id_t id);
const fd2_battle_comp_t* fd2_entity_get_battle_c(const fd2_entity_mgr_t* mgr, entity_id_t id);

fd2_tag_comp_t* fd2_entity_get_tag(fd2_entity_mgr_t* mgr, entity_id_t id);
const fd2_tag_comp_t* fd2_entity_get_tag_c(const fd2_entity_mgr_t* mgr, entity_id_t id);

/* ---- Component Add/Remove ---- */

fd2_sprite_comp_t* fd2_entity_add_sprite(fd2_entity_mgr_t* mgr, entity_id_t id);
fd2_stats_comp_t*  fd2_entity_add_stats(fd2_entity_mgr_t* mgr, entity_id_t id);
fd2_npc_comp_t*    fd2_entity_add_npc(fd2_entity_mgr_t* mgr, entity_id_t id);
fd2_battle_comp_t* fd2_entity_add_battle(fd2_entity_mgr_t* mgr, entity_id_t id);
fd2_tag_comp_t*    fd2_entity_add_tag(fd2_entity_mgr_t* mgr, entity_id_t id);

void fd2_entity_remove_sprite(fd2_entity_mgr_t* mgr, entity_id_t id);
void fd2_entity_remove_stats(fd2_entity_mgr_t* mgr, entity_id_t id);
void fd2_entity_remove_npc(fd2_entity_mgr_t* mgr, entity_id_t id);
void fd2_entity_remove_battle(fd2_entity_mgr_t* mgr, entity_id_t id);
void fd2_entity_remove_tag(fd2_entity_mgr_t* mgr, entity_id_t id);

/* ---- Tag Lookup ---- */
entity_id_t fd2_entity_find_by_tag(const fd2_entity_mgr_t* mgr, const char* name);

/* ---- Iteration ---- */
#define FD2_FOR_EACH_ENTITY(mgr, id_var) \
    for (entity_id_t id_var = 0; id_var < FD2_MAX_ENTITIES; id_var++) \
        if (fd2_entity_is_valid((mgr), id_var))

/* ---- Stats ---- */
int fd2_entity_get_count(const fd2_entity_mgr_t* mgr);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SIM_ENTITY_H */
