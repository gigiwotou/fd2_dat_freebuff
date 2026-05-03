#ifndef FD2_INTRO_STATE_H
#define FD2_INTRO_STATE_H

#include "fd2_game.h"

#ifdef __cplusplus
extern "C" {
#endif

void state_intro_enter(fd2_game_t* game);
fd2_state_t state_intro_update(fd2_game_t* game);
void state_intro_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_INTRO_STATE_H */
