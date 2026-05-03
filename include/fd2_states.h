#ifndef FD2_STATES_H
#define FD2_STATES_H

#include "fd2_game.h"

#ifdef __cplusplus
extern "C" {
#endif

void state_init_enter(fd2_game_t* game);
fd2_state_t state_init_update(fd2_game_t* game);
void state_init_exit(fd2_game_t* game);

void state_demo_enter(fd2_game_t* game);
fd2_state_t state_demo_update(fd2_game_t* game);
void state_demo_exit(fd2_game_t* game);

void state_char_select_enter(fd2_game_t* game);
fd2_state_t state_char_select_update(fd2_game_t* game);
void state_char_select_exit(fd2_game_t* game);

void state_victory_enter(fd2_game_t* game);
fd2_state_t state_victory_update(fd2_game_t* game);
void state_victory_exit(fd2_game_t* game);

void state_game_over_enter(fd2_game_t* game);
fd2_state_t state_game_over_update(fd2_game_t* game);
void state_game_over_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_STATES_H */
