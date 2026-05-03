#ifndef FD2_BATTLE_H
#define FD2_BATTLE_H

#include "fd2_game.h"
#include "fd2_map_loader.h"
#include <stdbool.h>

#define MAP_TILE_SIZE 24

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    BATTLE_STATE_IDLE,
    BATTLE_STATE_CHAR_SELECTED,
    BATTLE_STATE_MENU,
    BATTLE_STATE_SUBMENU,
    BATTLE_STATE_TARGET_SELECT,
    BATTLE_STATE_ANIMATING,
} battle_interaction_state_t;

typedef struct {
    char text[32];
    int action_id;
} menu_item_t;

typedef struct {
    int tile_x;
    int tile_y;
    int icon_id;
    int cache_idx;
    int direction;
    int anim_frame;
    int anim_timer;
    u8* pixels;
    int width;
    int height;
    bool loaded;
} map_sprite_t;

typedef struct {
    fd2_map_t map;
    int camera_x;
    int camera_y;

    int cursor_x;
    int cursor_y;
    int scroll_x;
    int scroll_y;
    int move_counter_x;
    int move_counter_y;
    int cursor_blink;
    int cursor_frame_id;

    bool debug_grid_enabled;

    const u8* fdother_data;
    u32 fdother_data_size;
    const u8* cursor_image_data;
    u32 cursor_image_width;
    u32 cursor_image_height;

    map_sprite_t* sprites;
    int sprite_count;
    int max_sprites;

    int character_icon_id;
    int character_icon_cache_idx;
    int character_segment;
    int character_direction;
    int character_frame;
    fd2_sprite_frame_t character_icon_frame;
    bool character_icon_loaded;
    int character_tile_x;
    int character_tile_y;

    battle_interaction_state_t interaction_state;
    int selected_char_idx;
    int menu_selected_idx;
    int menu_item_count;
    menu_item_t menu_items[16];
    int submenu_selected_idx;
    int submenu_item_count;
    menu_item_t submenu_items[16];
    int target_tile_x;
    int target_tile_y;

    bool from_save;
    int saved_num_fighters;
    u8 saved_char_positions[64][2];
} state_battle_data_t;

/* Sprite system */
void battle_render_sprites(map_sprite_t* sprites, int sprite_count,
                           int camera_x, int camera_y,
                           u8* screen, int screen_w, int screen_h);
void battle_free_sprites(map_sprite_t* sprites, int sprite_count);
int battle_load_sprites(fd2_game_t* game, map_sprite_t** out_sprites,
                        int num_sprites, bool from_save,
                        u8 char_positions[64][2], u8 char_icons[64],
                        fd2_map_t* map_data);
void battle_update_sprite_animations(map_sprite_t* sprites, int sprite_count);

/* Cursor system */
void cursor_move_up(state_battle_data_t* data, int map_height);
void cursor_move_down(state_battle_data_t* data, int map_height);
void cursor_move_left(state_battle_data_t* data, int map_width);
void cursor_move_right(state_battle_data_t* data, int map_width);
void update_camera_from_cursor(state_battle_data_t* data);
int decode_rle_image(const u8* src, u8* dst, int dst_stride, int width, int height);
int load_cursor_image(fd2_game_t* game, state_battle_data_t* data);
void battle_render_cursor(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);
void battle_render_debug_grid(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);

/* Menu system */
void battle_init_main_menu(state_battle_data_t* data, int char_idx);
void battle_render_menu(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);
void battle_menu_move_up(state_battle_data_t* data);
void battle_menu_move_down(state_battle_data_t* data);
void battle_render_text_box(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);

/* Battle state */
void state_battle_enter(fd2_game_t* game);
fd2_state_t state_battle_update(fd2_game_t* game);
void state_battle_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_BATTLE_H */
