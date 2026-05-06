/**
 * Modern Architecture Test Entry Point
 * Validates platform layer, event bus, and ECS framework.
 */

#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include "fd2/types.h"
#include "fd2/platform_video.h"
#include "fd2/platform_audio.h"
#include "fd2/platform_input.h"
#include "fd2/platform_file.h"
#include "fd2/platform_time.h"
#include "fd2/event_bus.h"
#include "fd2/sim/entity.h"
#include "fd2/sim/systems.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int test_platform_video(void) {
    printf("[TEST] Platform Video... ");
    const fd2_video_iface_t* video = fd2_platform_get_video();
    if (!video) { printf("FAIL (NULL iface)\n"); return -1; }
    if (!video->init || !video->shutdown || !video->present) {
        printf("FAIL (NULL methods)\n"); return -1;
    }

    fd2_video_t* v = NULL;
    if (video->init(&v, FD2_SCREEN_W, FD2_SCREEN_H, 3, "FD2 Modern Test") < 0) {
        printf("FAIL (init)\n"); return -1;
    }

    video->fill_screen(v, 0);
    video->present(v);
    video->shutdown(v);
    printf("PASS\n");
    return 0;
}

static int test_platform_audio(void) {
    printf("[TEST] Platform Audio... ");
    const fd2_audio_iface_t* audio = fd2_platform_get_audio();
    if (!audio) { printf("FAIL (NULL iface)\n"); return -1; }

    fd2_audio_t* a = NULL;
    if (audio->init(&a) < 0) { printf("FAIL (init)\n"); return -1; }

    audio->shutdown(a);
    printf("PASS\n");
    return 0;
}

static int test_platform_input(void) {
    printf("[TEST] Platform Input... ");
    const fd2_input_iface_t* input = fd2_platform_get_input();
    if (!input) { printf("FAIL (NULL iface)\n"); return -1; }

    fd2_input_t* i = NULL;
    if (input->init(&i) < 0) { printf("FAIL (init)\n"); return -1; }

    if (!input->is_action_held(i, FD2_ACTION_NONE)) {
        /* Expected: no action held initially */
    }

    input->shutdown(i);
    printf("PASS\n");
    return 0;
}

static int test_platform_filesys(void) {
    printf("[TEST] Platform FileSys... ");
    const fd2_filesys_iface_t* fs = fd2_platform_get_filesys();
    if (!fs) { printf("FAIL (NULL iface)\n"); return -1; }

    fd2_filesys_t* f = NULL;
    if (fs->init(&f, ".") < 0) { printf("FAIL (init)\n"); return -1; }

    const char* base = fs->get_base_dir(f);
    if (!base) { printf("FAIL (get_base_dir)\n"); fs->shutdown(f); return -1; }

    fs->shutdown(f);
    printf("PASS\n");
    return 0;
}

static int test_platform_time(void) {
    printf("[TEST] Platform Time... ");
    const fd2_time_iface_t* time = fd2_platform_get_time();
    if (!time) { printf("FAIL (NULL iface)\n"); return -1; }

    u32 ticks = time->get_ticks_ms();
    if (ticks == 0 && time->delay_ms) {
        time->delay_ms(1);
        ticks = time->get_ticks_ms();
    }

    printf("PASS (ticks=%u)\n", ticks);
    return 0;
}

/* ---- Event Bus Tests ---- */

static int g_test_event_count = 0;

static void test_event_handler(const fd2_event_t* event, void* user_data) {
    g_test_event_count++;
    printf("  [EVENT] type=%d tick=%u data[0]=%d\n",
           event->type, event->timestamp, event->data[0]);
}

static int test_event_bus(void) {
    printf("[TEST] Event Bus... ");

    fd2_event_bus_t bus;
    fd2_event_bus_init(&bus);

    int sub_id = fd2_event_bus_subscribe(&bus, EVENT_ENTITY_MOVED, test_event_handler, NULL);
    if (sub_id < 0) { printf("FAIL (subscribe)\n"); return -1; }

    int test_data = 42;
    fd2_event_bus_publish(&bus, EVENT_ENTITY_MOVED, &test_data, sizeof(test_data));
    fd2_event_bus_advance_tick(&bus);

    if (bus.pending_count != 1) { printf("FAIL (pending=%d)\n", bus.pending_count); return -1; }

    fd2_event_bus_process(&bus);
    if (g_test_event_count != 1) { printf("FAIL (events_processed=%d)\n", g_test_event_count); return -1; }

    fd2_event_bus_shutdown(&bus);
    printf("PASS\n");
    return 0;
}

/* ---- ECS Tests ---- */

static int test_entity_manager(void) {
    printf("[TEST] Entity Manager... ");

    fd2_entity_mgr_t mgr;
    fd2_entity_mgr_init(&mgr);

    if (fd2_entity_get_count(&mgr) != 0) { printf("FAIL (initial count)\n"); return -1; }

    entity_id_t e1 = fd2_entity_create(&mgr);
    if (e1 == FD2_INVALID_ENTITY) { printf("FAIL (create e1)\n"); return -1; }

    entity_id_t e2 = fd2_entity_create(&mgr);
    if (e2 == FD2_INVALID_ENTITY) { printf("FAIL (create e2)\n"); return -1; }

    fd2_sprite_comp_t* s1 = fd2_entity_add_sprite(&mgr, e1);
    if (!s1) { printf("FAIL (add sprite)\n"); return -1; }

    s1->tile_x = 10;
    s1->tile_y = 15;
    s1->icon_id = 5;

    fd2_stats_comp_t* st1 = fd2_entity_add_stats(&mgr, e1);
    if (!st1) { printf("FAIL (add stats)\n"); return -1; }

    st1->hp = 100;
    st1->max_hp = 100;
    st1->level = 1;

    if (fd2_entity_get_count(&mgr) != 2) { printf("FAIL (count=%d)\n", fd2_entity_get_count(&mgr)); return -1; }

    const fd2_sprite_comp_t* cs1 = fd2_entity_get_sprite_c(&mgr, e1);
    if (!cs1 || cs1->tile_x != 10 || cs1->icon_id != 5) {
        printf("FAIL (sprite data)\n"); return -1;
    }

    fd2_entity_destroy(&mgr, e1);
    if (fd2_entity_is_valid(&mgr, e1)) { printf("FAIL (destroyed entity still valid)\n"); return -1; }
    if (fd2_entity_get_count(&mgr) != 1) { printf("FAIL (count after destroy)\n"); return -1; }

    entity_id_t e3 = fd2_entity_create(&mgr);
    if (e3 != e1) { printf("FAIL (reuse ID, got %d expected %d)\n", e3, e1); return -1; }

    fd2_entity_destroy(&mgr, e3);
    memset(&mgr, 0, sizeof(mgr));
    printf("PASS\n");
    return 0;
}

static int test_systems(void) {
    printf("[TEST] Systems... ");

    fd2_entity_mgr_t mgr;
    fd2_entity_mgr_init(&mgr);

    fd2_event_bus_t bus;
    fd2_event_bus_init(&bus);

    entity_id_t e1 = fd2_entity_create(&mgr);
    fd2_sprite_comp_t* s = fd2_entity_add_sprite(&mgr, e1);
    s->tile_x = 5;
    s->tile_y = 5;

    sprite_system_update(&mgr, 0);
    if (s->anim_frame != 0 && s->anim_timer != 1) {
        printf("FAIL (sprite update)\n");
        memset(&mgr, 0, sizeof(mgr));
        fd2_event_bus_shutdown(&bus);
        return -1;
    }

    memset(&mgr, 0, sizeof(mgr));
    fd2_event_bus_shutdown(&bus);
    printf("PASS\n");
    return 0;
}

/* ---- Main ---- */

#ifdef _WIN32
#undef main
#endif

int main(int argc, char* argv[]) {
    (void)argc; (void)argv;

    printf("=== FD2 Modern Architecture Test ===\n\n");

    int failures = 0;

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_TIMER) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }

    failures += test_platform_video();
    failures += test_platform_audio();
    failures += test_platform_input();
    failures += test_platform_filesys();
    failures += test_platform_time();
    failures += test_event_bus();
    failures += test_entity_manager();
    failures += test_systems();

    SDL_Quit();

    printf("\n=== Results: %d failures ===\n", failures);
    return failures > 0 ? 1 : 0;
}
