#ifndef FD2_CUTSCENE_H
#define FD2_CUTSCENE_H

#include "fd2_game.h"

#ifdef __cplusplus
extern "C" {
#endif

void state_cutscene_enter(fd2_game_t* game);
fd2_state_t state_cutscene_update(fd2_game_t* game);
void state_cutscene_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_CUTSCENE_H */
