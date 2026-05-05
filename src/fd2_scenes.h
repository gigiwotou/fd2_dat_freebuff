#ifndef FD2_SCENES_H
#define FD2_SCENES_H

/*
 * FD2 场景生命周期函数
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[]
 * 
 * 场景0-29对应原游戏的30个场景
 */

#include "fd2_state_machine.h"

/* 前置声明 */
struct fd2_state_machine;

/* 场景0: 主菜单/标题场景 (对应原游戏 sub_3231B) */
void scene_0_init(struct fd2_state_machine* sm);
void scene_0_exit(struct fd2_state_machine* sm);
int scene_0_check(struct fd2_state_machine* sm);

/* 场景1: 默认处理 (对应原游戏 sub_22EF6) */
void scene_1_init(struct fd2_state_machine* sm);
void scene_1_exit(struct fd2_state_machine* sm);

/* 场景2-29: 默认处理 (对应原游戏 sub_21206) */
void scene_default_init(struct fd2_state_machine* sm);
void scene_default_exit(struct fd2_state_machine* sm);

/* 注册所有场景到状态机 */
void fd2_register_all_scenes(fd2_state_machine_t* sm);

/* sub_4E809: 场景元数据读取 */
void* fd2_scene_get_metadata(int scene_id);

/* sub_4E838: 图标元数据读取 */
void* fd2_icon_get_metadata(int icon_id);

/* sub_4E821: 图标属性读取 */
void* fd2_icon_get_props(int icon_id);

/* sub_112A5: 图标加载函数 */
int fd2_icon_load(int icon_id);

/* sub_4ED7A: 字符渲染函数 */
void fd2_render_char(void* fdother_dat, int char_index, void* screen_buf,
                     int screen_offset, int row_width, u8 color1, u8 color2, int do_clear);

/* sub_15F84 简化版: 文本渲染函数 */
void fd2_render_text(void* fdother_dat, void* screen_buf,
                     int x, int y, const char* text,
                     u8 color1, u8 color2, int do_clear);

/* sub_1366A 简化版: 场景动画/资源加载 */
int fd2_scene_load_resources(int resource_id);

/* sub_4EBFF: 屏幕区域复制函数 */
void fd2_copy_screen_region(u8* dst, s16* src, int row_width);

/* sub_11EB0: 屏幕区域更新函数 */
void fd2_screen_region_update(void* dst, int dst_stride,
                               const void* src, int src_stride,
                               int copy_size, int num_lines);

/* sub_4E22A: 光标图像复制函数 */
void fd2_copy_cursor_image(u8* dst, const u8* src, int row_width);

#endif /* FD2_SCENES_H */
