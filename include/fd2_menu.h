#ifndef FD2_MENU_H
#define FD2_MENU_H

#include "fd2_game.h"

#ifdef __cplusplus
extern "C" {
#endif

void state_menu_enter(fd2_game_t* game);
fd2_state_t state_menu_update(fd2_game_t* game);
void state_menu_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_MENU_H */
