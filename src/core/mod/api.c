/**
 * MOD API Implementation
 * Provides game engine access to MODs.
 */

#define _GNU_SOURCE
#include "fd2/mod/api.h"
#include <stdio.h>
#include <stdarg.h>

/* Internal state - set by the game engine */
static fd2_entity_mgr_t* g_mod_entity_mgr = NULL;
static fd2_event_bus_t*  g_mod_event_bus = NULL;

void fd2_mod_set_entity_mgr(fd2_entity_mgr_t* mgr) {
    g_mod_entity_mgr = mgr;
}

void fd2_mod_set_event_bus(fd2_event_bus_t* bus) {
    g_mod_event_bus = bus;
}

static entity_id_t mod_create_entity(void) {
    if (!g_mod_entity_mgr) return FD2_INVALID_ENTITY;
    return fd2_entity_create(g_mod_entity_mgr);
}

static void mod_destroy_entity(entity_id_t id) {
    if (!g_mod_entity_mgr) return;
    fd2_entity_destroy(g_mod_entity_mgr, id);
}

static fd2_sprite_comp_t* mod_add_sprite(entity_id_t id) {
    if (!g_mod_entity_mgr) return NULL;
    return fd2_entity_add_sprite(g_mod_entity_mgr, id);
}

static fd2_stats_comp_t* mod_add_stats(entity_id_t id) {
    if (!g_mod_entity_mgr) return NULL;
    return fd2_entity_add_stats(g_mod_entity_mgr, id);
}

static fd2_npc_comp_t* mod_add_npc(entity_id_t id) {
    if (!g_mod_entity_mgr) return NULL;
    return fd2_entity_add_npc(g_mod_entity_mgr, id);
}

static int mod_subscribe_event(fd2_event_type_t type, fd2_event_handler_t handler, void* user_data) {
    if (!g_mod_event_bus) return -1;
    return fd2_event_bus_subscribe(g_mod_event_bus, type, handler, user_data);
}

static void mod_publish_event(fd2_event_type_t type, const void* data, size_t size) {
    if (!g_mod_event_bus) return;
    fd2_event_bus_publish(g_mod_event_bus, type, data, size);
}

static const fd2_dat_resource_t* mod_get_resource(const char* dat_name, int index) {
    (void)dat_name;
    (void)index;
    return NULL;
}

static int mod_register_data_override(const char* dat_name, int index, const u8* data, u32 size) {
    (void)dat_name;
    (void)index;
    (void)data;
    (void)size;
    return -1;
}

static void mod_log_info(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "[MOD INFO] ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
}

static void mod_log_warn(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "[MOD WARN] ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
}

static void mod_log_error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "[MOD ERROR] ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
}

static u32 mod_get_tick_ms(void) {
    return 0;
}

static const char* mod_get_version(void) {
    return "FD2 MOD API v1.0";
}

static fd2_mod_api_v1_t g_mod_api = {
    .api_version = 1,
    .api_name = "FD2 MOD API",

    .create_entity = mod_create_entity,
    .destroy_entity = mod_destroy_entity,
    .add_sprite = mod_add_sprite,
    .add_stats = mod_add_stats,
    .add_npc = mod_add_npc,

    .subscribe_event = mod_subscribe_event,
    .publish_event = mod_publish_event,

    .get_resource = mod_get_resource,
    .register_data_override = mod_register_data_override,

    .log_info = mod_log_info,
    .log_warn = mod_log_warn,
    .log_error = mod_log_error,

    .get_tick_ms = mod_get_tick_ms,
    .get_version = mod_get_version,
};

const fd2_mod_api_v1_t* fd2_mod_get_api(void) {
    return &g_mod_api;
}
