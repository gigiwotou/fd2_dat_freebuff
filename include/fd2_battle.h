#ifndef FD2_BATTLE_H
#define FD2_BATTLE_H

#include "fd2_game.h"
#include "fd2_map_loader.h"
#include <stdbool.h>

#define MAP_TILE_SIZE 24
#define TERRAIN_INFO_WIDTH 456
#define TERRAIN_INFO_HEIGHT 24

#ifdef __cplusplus
extern "C" {
#endif

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

    /* Resources loaded via fd2_dat_load_resource (sub_111BA) - must be freed */
    u8* fdother_resource_5;      /* FDOTHER.DAT resource index 5 */
    u32 fdother_resource_5_size;
    u8* fdother_resource_3;      /* FDOTHER.DAT resource index 3 (terrain info) */
    u32 fdother_resource_3_size;

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

    bool from_save;
    int saved_num_fighters;
    u8 saved_char_positions[64][2];

    /* Character selection state - based on IDA sub_12C0D */
    int selected_char_idx;
    int cursor_char_frame_id;

    /* Terraininfo display - based on IDA sub_126F7 */
    const u8* terrain_info_data;
    u32 terrain_info_data_size;
    u8 terrain_info_buffer[TERRAIN_INFO_WIDTH * TERRAIN_INFO_HEIGHT];

    /* Player turn state - based on IDA sub_1CFF0, sub_1D51D */
    int current_char_idx;          /* n2_3: 当前选择的角色索引 */
    int active_char_count;         /* 活跃角色数量 */
    int active_char_ids[40];       /* 活跃角色ID列表 (5行x8列=40) */
    bool char_moved[64];          /* 角色是否已移动标记 */

    /* Movement range state - based on IDA sub_14818 */
    int move_range;                /* 移动力 */
    int move_start_x;              /* 移动起始x */
    int move_start_y;              /* 移动起始y */
    u8* move_range_data;           /* 移动范围标记数据 */

    /* Menu state - based on IDA sub_18D8C, sub_177FC */
    int menu_selected;             /* 当前菜单选择 (0=攻击,1=道具,2=休息,3=魔法) */
    bool menu_visible;             /* 菜单是否可见 */
    int menu_options[4];           /* 菜单选项可用性 */

    /* Turn phase - 回合阶段 */
    int turn_phase;                /* 0=选择角色,1=显示移动范围,2=选择移动目标,3=显示菜单,4=执行功能 */
} state_battle_data_t;

/* Character query - based on IDA sub_12C0D */
int battle_find_char_at_cursor(state_battle_data_t* data);
int battle_check_char_valid(state_battle_data_t* data, int char_idx);

/* Terrain info display - based on IDA sub_126F7, sub_122DC */
int load_terrain_info_data(fd2_game_t* game, state_battle_data_t* data);
void battle_render_terrain_info(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);

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

/* Player turn logic - based on IDA analysis */
void battle_turn_init(state_battle_data_t* data);
void battle_turn_cleanup(state_battle_data_t* data);
int battle_get_active_chars(state_battle_data_t* data, int* out_ids, int max_ids);
int battle_char_selection(state_battle_data_t* data, fd2_game_t* game);
int battle_calc_move_range(state_battle_data_t* data, int start_x, int start_y, int move_power);
int battle_select_move_target(state_battle_data_t* data, fd2_game_t* game, int mode, int* out_x, int* out_y);
int battle_menu_selection(state_battle_data_t* data, fd2_game_t* game, int* menu_state);
int battle_action_menu(state_battle_data_t* data, fd2_game_t* game);
void battle_render_char_list(state_battle_data_t* data, fd2_game_t* game);
void battle_render_menu(state_battle_data_t* data, fd2_game_t* game, int* menu_state);
void battle_highlight_menu_option(state_battle_data_t* data, int option_idx);

/* Battle state */
void state_battle_enter(fd2_game_t* game);
fd2_state_t state_battle_update(fd2_game_t* game);
void state_battle_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_BATTLE_H */
