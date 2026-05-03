#ifndef FD2_CONTINUE_H
#define FD2_CONTINUE_H

#include "fd2_game.h"

#ifdef __cplusplus
extern "C" {
#endif

void state_continue_enter(fd2_game_t* game);
fd2_state_t state_continue_update(fd2_game_t* game);
void state_continue_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_CONTINUE_H */
