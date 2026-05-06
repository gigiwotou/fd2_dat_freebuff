#ifndef FD2_SIM_SYSTEMS_H
#define FD2_SIM_SYSTEMS_H

#include "fd2/types.h"
#include "fd2/sim/entity.h"
#include "fd2/event_bus.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- System Update Functions ----
 * Each system operates on entities that have specific components.
 * Systems are called in order from the simulation update loop.
 */

/* Sprite System: Updates animation frames and movement interpolation */
void sprite_system_update(fd2_entity_mgr_t* mgr, u32 tick);

/* NPC System: Processes NPC scripts, triggers, patrol behaviors */
void npc_system_update(fd2_entity_mgr_t* mgr, u32 tick, fd2_event_bus_t* bus);

/* Battle System: Processes battle turns, actions, AI, damage */
void battle_system_update(fd2_entity_mgr_t* mgr, u32 tick, fd2_event_bus_t* bus);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SIM_SYSTEMS_H */
