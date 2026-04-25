/**
 * FD2 Main Entry Point
 *
 * Uses the fd2_game framework for state machine, rendering, input, etc.
 * The old standalone SDL/DAT code has been moved into the game framework.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_game.h"

int main(int argc, char** argv) {
    /* Determine data directory.
     * Default: NULL (use executable directory).
     * Can be overridden via command line argument.
     */
    const char* data_dir = NULL;
    if (argc > 1) {
        data_dir = argv[1];
    }

    fd2_game_t game;
    if (fd2_game_init(&game, data_dir) != 0) {
        fprintf(stderr, "Failed to initialize game\n");
        return 1;
    }

    printf("炎龙骑士团 2 - Starting (data: %s)\n", game.data_dir);
    printf("Controls:\n");
    printf("  Arrows: Move    Z/A: Punch(L)  X/S: Kick(L)\n");
    printf("  C/D: Punch(H)/Kick(H)  Enter/Space: Start\n");
    printf("  ESC: Back/Quit   F11: Fullscreen   Tab: Coin\n");

    int result = fd2_game_run(&game);

    fd2_game_shutdown(&game);
    return result;
}
