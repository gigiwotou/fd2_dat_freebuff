#ifndef FD2_MOD_API_H
#define FD2_MOD_API_H

#include "fd2/types.h"
#include "fd2/sim/entity.h"
#include "fd2/event_bus.h"
#include "fd2/data/dat_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- MOD API ----
 * This API is exposed to MODs for extending game functionality.
 * MODs can use these functions to interact with the game engine.
 */

typedef struct {
    /* ---- Version Info ---- */
    int api_version;
    const char* api_name;

    /* ---- Entity System ---- */
    entity_id_t (*create_entity)(void);
    void (*destroy_entity)(entity_id_t id);
    fd2_sprite_comp_t* (*add_sprite)(entity_id_t id);
    fd2_stats_comp_t*  (*add_stats)(entity_id_t id);
    fd2_npc_comp_t*    (*add_npc)(entity_id_t id);

    /* ---- Event System ---- */
    int  (*subscribe_event)(fd2_event_type_t type, fd2_event_handler_t handler, void* user_data);
    void (*publish_event)(fd2_event_type_t type, const void* data, size_t size);

    /* ---- Data Access ---- */
    const fd2_dat_resource_t* (*get_resource)(const char* dat_name, int index);
    int (*register_data_override)(const char* dat_name, int index, const u8* data, u32 size);

    /* ---- Logging ---- */
    void (*log_info)(const char* fmt, ...);
    void (*log_warn)(const char* fmt, ...);
    void (*log_error)(const char* fmt, ...);

    /* ---- Utility ---- */
    u32 (*get_tick_ms)(void);
    const char* (*get_version)(void);
} fd2_mod_api_v1_t;

/* Get the MOD API instance */
const fd2_mod_api_v1_t* fd2_mod_get_api(void);

/* Set internal state (called by game engine) */
void fd2_mod_set_entity_mgr(fd2_entity_mgr_t* mgr);
void fd2_mod_set_event_bus(fd2_event_bus_t* bus);

#ifdef __cplusplus
}
#endif

#endif /* FD2_MOD_API_H */
