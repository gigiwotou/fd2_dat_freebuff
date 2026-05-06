/**
 * Modern FD2 Game - Main Entry Point
 * Integrates all Phase 1-6 systems using the modern framework.
 */

#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include "fd2/types.h"
#include "fd2/game_framework.h"
#include "fd2/platform_video.h"
#include "fd2/platform_audio.h"
#include "fd2/platform_input.h"
#include "fd2/platform_file.h"
#include "fd2/platform_time.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#undef main
#endif

static void print_usage(const char* prog_name) {
    printf("Usage: %s [options]\n", prog_name);
    printf("Options:\n");
    printf("  --data-dir <path>   Path to game data directory\n");
    printf("  --mods-dir <path>   Path to mods directory\n");
    printf("  --scale <N>         Screen scale factor (default: 3)\n");
    printf("  --help              Show this help\n");
}

int main(int argc, char* argv[]) {
    const char* data_dir = "game";
    const char* mods_dir = "mods";
    int scale = 3;

    /* Parse command line */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--data-dir") == 0 && i + 1 < argc) {
            data_dir = argv[++i];
        } else if (strcmp(argv[i], "--mods-dir") == 0 && i + 1 < argc) {
            mods_dir = argv[++i];
        } else if (strcmp(argv[i], "--scale") == 0 && i + 1 < argc) {
            scale = atoi(argv[++i]);
            if (scale < 1) scale = 1;
            if (scale > 5) scale = 5;
        } else if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
    }

    printf("=== FD2 Modern Architecture ===\n");
    printf("Data dir: %s\n", data_dir);
    printf("Mods dir: %s\n", mods_dir);
    printf("Scale: %d\n", scale);

    /* Initialize SDL */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_TIMER) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }

    /* Get platform interfaces */
    const fd2_video_iface_t* video_iface = fd2_platform_get_video();
    const fd2_audio_iface_t* audio_iface = fd2_platform_get_audio();
    const fd2_input_iface_t* input_iface = fd2_platform_get_input();
    const fd2_time_iface_t* time_iface = fd2_platform_get_time();

    if (!video_iface || !audio_iface || !input_iface || !time_iface) {
        fprintf(stderr, "Failed to get platform interfaces\n");
        SDL_Quit();
        return 1;
    }

    /* Initialize platform state */
    fd2_video_t* video = NULL;
    fd2_audio_t* audio = NULL;
    fd2_input_t* input = NULL;

    if (video_iface->init(&video, FD2_SCREEN_W, FD2_SCREEN_H, scale, "FD2 Modern") < 0) {
        fprintf(stderr, "Failed to initialize video\n");
        SDL_Quit();
        return 1;
    }

    if (audio_iface->init(&audio) < 0) {
        fprintf(stderr, "Audio init failed (non-fatal)\n");
    }

    if (input_iface->init(&input) < 0) {
        fprintf(stderr, "Failed to initialize input\n");
        video_iface->shutdown(video);
        SDL_Quit();
        return 1;
    }

    /* Initialize game framework */
    fd2_game_framework_t game;
    if (fd2_game_framework_init(&game, data_dir, mods_dir) < 0) {
        fprintf(stderr, "Failed to initialize game framework\n");
        input_iface->shutdown(input);
        audio_iface->shutdown(audio);
        video_iface->shutdown(video);
        SDL_Quit();
        return 1;
    }

    /* Main loop */
    u32 last_time = time_iface->get_ticks_ms();
    u32 frame_count = 0;
    u32 fps_timer = 0;

    printf("[MAIN] Starting main loop...\n");

    while (game.running) {
        u32 current_time = time_iface->get_ticks_ms();
        u32 delta = current_time - last_time;
        last_time = current_time;

        /* Cap delta to prevent spiral of death */
        if (delta > 100) delta = 100;

        /* FPS counter */
        frame_count++;
        fps_timer += delta;
        if (fps_timer >= 1000) {
            printf("[MAIN] FPS: %u\n", frame_count);
            frame_count = 0;
            fps_timer = 0;
        }

        /* Process SDL events */
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                game.running = false;
            } else if (event.type == SDL_KEYDOWN) {
                if (event.key.keysym.sym == SDLK_F11) {
                    video_iface->toggle_fullscreen(video);
                }
            }
            input_iface->process_event(input, &event);
        }

        /* Update game */
        fd2_game_framework_update(&game,
                                  input_iface, input,
                                  video_iface, video,
                                  audio_iface, audio);

        /* Render */
        fd2_game_framework_render(&game);

        /* Upload and present */
        video_iface->upload_screen(video, game.screen);
        video_iface->set_palette(video, game.palette);
        video_iface->present(video);

        /* Frame rate limiting (target 60 FPS = 16.67ms per frame) */
        u32 frame_time = time_iface->get_ticks_ms() - current_time;
        if (frame_time < FD2_FRAME_TIME_MS) {
            time_iface->delay_ms(FD2_FRAME_TIME_MS - frame_time);
        }
    }

    printf("[MAIN] Main loop ended.\n");

    /* Shutdown */
    fd2_game_framework_shutdown(&game);
    input_iface->shutdown(input);
    audio_iface->shutdown(audio);
    video_iface->shutdown(video);
    SDL_Quit();

    printf("[MAIN] Shutdown complete.\n");
    return 0;
}
