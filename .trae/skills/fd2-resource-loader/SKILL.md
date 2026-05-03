---
name: "fd2-resource-loader"
description: "FD2游戏资源加载函数参考手册。包含所有图像、音频、音效、动画、精灵、地图图标的加载和解码函数。当需要查找资源加载API、了解资源文件结构、或实现新的渲染/音频功能时调用。"
---

# FD2 资源加载函数参考

## 概述

FD2游戏使用多个DAT资源文件，通过资源管理器统一管理。本文档整理了所有图像、音频、音效加载相关的函数。

---

## 1. 资源管理器 (fd2_resources)

**头文件:** `include/fd2_resources.h`  
**数据文件:** 11种DAT文件

### DAT文件类型

```c
typedef enum {
    FD2_DAT_FDOTHER = 0,   // 标题、菜单、杂项图形 + 调色板
    FD2_DAT_FDTXT,         // 文本/字体字形
    FD2_DAT_FDMUS,         // MIDI音乐数据
    FD2_DAT_FDSHAP,        // 战斗角色精灵 + 调色板
    FD2_DAT_FDFIELD,       // 舞台/背景字段数据
    FD2_DAT_BG,            // 背景图像
    FD2_DAT_FIGANI,        // 角色动画帧
    FD2_DAT_TAI,           // 角色头像
    FD2_DAT_DATO,          // 游戏逻辑常量/数据
    FD2_DAT_ANI,           // AFM动画序列
    FD2_DAT_FDICON,        // 图标数据(B24格式)
    FD2_DAT_COUNT
} fd2_dat_id_t;
```

### 生命周期函数

```c
int  fd2_resources_init(fd2_resources_t* res, const char* data_dir);
void fd2_resources_shutdown(fd2_resources_t* res);
```

### 加载函数

```c
int  fd2_resources_load_dat(fd2_resources_t* res, fd2_dat_id_t id);  // 加载单个DAT
int  fd2_resources_load_all(fd2_resources_t* res);                    // 加载所有DAT
```

### 访问函数

```c
const fd2_dat_t* fd2_resources_get_dat(const fd2_resources_t* res, fd2_dat_id_t id);
const u8*        fd2_resources_get(const fd2_resources_t* res, fd2_dat_id_t dat_id, int index, u32* out_size);
bool             fd2_resources_is_loaded(const fd2_resources_t* res, fd2_dat_id_t id);
const char*      fd2_resources_dat_path(const fd2_resources_t* res, fd2_dat_id_t id);
```

---

## 2. DAT文件系统 (fd2_decoder)

**头文件:** `include/fd2_decoder.h`  
**文件格式:** LLLLLL魔数 + 资源偏移表 + 资源数据

### 加载与解析

```c
int         fd2_dat_load(fd2_dat_t* dat, const char* path);           // 加载DAT文件
void        fd2_dat_free(fd2_dat_t* dat);                             // 释放DAT文件
const u8*   fd2_dat_get_resource(const fd2_dat_t* dat, int index, u32* out_size);  // 获取资源
int         fd2_is_dat_magic(const u8* data, u32 size);               // 检查魔数 LLLLLL
int         fd2_dat_validate_offsets(const u8* data, u32 file_size, u32 resource_count);
```

### 资源分类

```c
typedef enum {
    FD2_RES_UNKNOWN,          // 未知
    FD2_RES_RLE_IMAGE,        // RLE压缩图像 (以有效宽高开头)
    FD2_RES_PALETTE,          // 调色板 (恰好768字节)
    FD2_RES_NESTED_DAT,       // 嵌套DAT (以LLLLLL开头)
    FD2_RES_TEXT,             // 文本 (高比例可打印ASCII)
    FD2_RES_RAW,              // 其他
} fd2_resource_type_t;

typedef struct {
    fd2_resource_type_t type;
    int                 width;
    int                 height;
    int                 inner_resource_count;
} fd2_resource_info_t;

void fd2_resource_classify(const u8* data, u32 size, fd2_resource_info_t* info);
```

### RLE解压缩

```c
int fd2_rle_decompress(const u8* src, u32 src_size, u8* dst, int width, int height);
int fd2_rle_decompress_from_resource(const u8* res_data, u32 res_size, u8** out_pixels, int* out_w, int* out_h);
int fd2_rle_decompress_to_buffer(const u8* res_data, u32 res_size, u8* dst_buf, int dst_y, int stride);
```

### 图像处理

```c
int fd2_image_get_dimensions(const u8* data, u32 data_size, int* out_w, int* out_h);
```

### 调色板操作

```c
void fd2_palette_6bit_to_8bit(const u8* palette_6bit, u8* palette_8bit);  // 6位转8位
void fd2_palette_set_brightness(u8* palette_8bit, int brightness);         // 设置亮度 0-63
void fd2_palette_fade(const u8* src, const u8* dst, u8* out, int steps, int current);  // 淡入淡出
void fd2_palette_add_6bit(u8* palette_8bit, int add_6bit);                 // 增加亮度值
```

---

## 3. 渲染系统 (fd2_render)

**头文件:** `include/fd2_render.h`  
**屏幕规格:** 320x200 8位索引颜色

### 生命周期

```c
int  fd2_render_init(fd2_render_t* render, int scale);
void fd2_render_shutdown(fd2_render_t* render);
```

### 屏幕操作

```c
void fd2_render_fill_screen(fd2_render_t* render, u8 color);
void fd2_render_plot(fd2_render_t* render, int x, int y, u8 color);
void fd2_render_present(fd2_render_t* render);  // 渲染并显示
```

### 图像Blit

```c
void fd2_render_blit(fd2_render_t* render, const u8* pixels, int w, int h, int dx, int dy);
void fd2_render_blit_trans(fd2_render_t* render, const u8* pixels, int w, int h, int dx, int dy, u8 transparent);
int  fd2_render_blit_rle(fd2_render_t* render, const u8* res_data, u32 res_size, int dx, int dy);
void fd2_render_blit_afm(fd2_render_t* render, const u8* afm_frame, int transparent);
```

### 调色板操作

```c
void fd2_render_set_palette_6bit(fd2_render_t* render, const u8* pal_6bit);
void fd2_render_set_palette_8bit(fd2_render_t* render, const u8* pal_8bit);
void fd2_render_set_brightness(fd2_render_t* render, int brightness);
void fd2_render_fade_palette(fd2_render_t* render, const u8* src, const u8* dst, int steps, int current);
void fd2_render_fade_to_black(fd2_render_t* render, int steps, int step_ms);
void fd2_render_fade_from_black(fd2_render_t* render, int steps, int step_ms);
void fd2_render_fade_to_color(fd2_render_t* render, int steps, int step_ms, int base_r6, int base_g6, int base_b6);
void fd2_render_fade_from_color(fd2_render_t* render, int steps, int step_ms, int base_r6, int base_g6, int base_b6);
void fd2_render_palette_add_6bit(fd2_render_t* render, int add_6bit);
```

### 全屏

```c
void fd2_render_toggle_fullscreen(fd2_render_t* render);
```

---

## 4. AFM动画系统 (fd2_afm)

**头文件:** `include/fd2_afm.h`  
**存储文件:** ANI.DAT  
**格式:** 173字节头 + 帧数据 (每帧8字节头 + 变长数据)

### 生命周期

```c
void fd2_afm_init(fd2_afm_t* afm);
int  fd2_afm_open(fd2_afm_t* afm, const u8* resource_data, u32 resource_size);
void fd2_afm_rewind(fd2_afm_t* afm);
```

### 帧解码

```c
int  fd2_afm_decode_next_frame(fd2_afm_t* afm);
bool fd2_afm_is_done(const fd2_afm_t* afm);
```

### 访问器

```c
const u8* fd2_afm_get_frame(const fd2_afm_t* afm);   // 获取当前帧缓冲 (320x200索引)
const u8* fd2_afm_get_palette(const fd2_afm_t* afm); // 获取当前调色板 (768字节)
```

### AFM专用RLE

```c
int fd2_afm_rle_decode(const u8* src, u32 src_size, u8* dst, u32 dst_size);
```

---

## 5. 精灵系统 (fd2_sprite)

**头文件:** `include/fd2_sprite.h`  
**存储文件:** FIGANI.DAT  
**格式:** RLE压缩，多帧多方向

### 初始化

```c
int fd2_sprite_decoder_init(fd2_sprite_decoder_t* decoder, const uint8_t* data, int data_size);
void fd2_sprite_decoder_free(fd2_sprite_decoder_t* decoder);
```

### 帧解码

```c
int fd2_sprite_decode_frame(fd2_sprite_decoder_t* decoder, int sprite_index, int frame_index, fd2_sprite_frame_t* frame);
int fd2_sprite_decode_frame_with_palette(fd2_sprite_decoder_t* decoder, int sprite_index, int frame_index, int palette_offset, fd2_sprite_frame_t* frame);
void fd2_sprite_frame_free(fd2_sprite_frame_t* frame);
```

### 渲染

```c
int fd2_sprite_render(const fd2_sprite_frame_t* frame, uint8_t* dest, int dest_width, int x, int y);
```

---

## 6. 图标系统 (fd2_icon_b24)

**头文件:** `include/fd2_icon_b24.h`  
**存储文件:** FDICON.B24  
**格式:** B24格式，每个图标12个段（方向/动画帧）

### 生命周期

```c
int  fd2_icon_init(const char* fdicon_path);
void fd2_icon_shutdown(void);
```

### 图标加载

```c
int  fd2_icon_get(int icon_id);                              // 加载图标到缓存，返回缓存索引
int  fd2_icon_get_count(void);                               // 获取总图标数
int  fd2_icon_get_cached_count(void);                        // 获取已缓存数
int  fd2_icon_get_cached_id(int cache_index);                // 获取缓存的图标ID
```

### 图标数据访问

```c
unsigned char* fd2_icon_get_segment(int cache_index, int segment);  // 获取段数据
unsigned char* fd2_icon_get_buffer(void);                           // 获取主缓冲指针
int            fd2_icon_get_buffer_size(void);                      // 获取缓冲使用量
```

### 解码

```c
int fd2_icon_decode_segment(int cache_index, int segment, int width, int height, unsigned char* pixels);
```

---

## 7. 地图系统 (fd2_map_loader)

**头文件:** `include/fd2_map_loader.h`  
**数据文件:** FDFIELD.DAT (地图数据) + FDSHAP.DAT (瓦片集) + FDOTHER.DAT (全局调色板)

### 加载

```c
int  fd2_map_init(fd2_map_t* map);
int  fd2_map_load_from_dat(fd2_map_t* map, int map_id, const char* fdfield_path, const char* fdshap_path, const char* fdother_path);
void fd2_map_free(fd2_map_t* map);
```

### 渲染

```c
void fd2_map_render(const fd2_map_t* map, u8* screen, int screen_w, int screen_h, int offset_x, int offset_y);
void fd2_map_render_centered(const fd2_map_t* map, u8* screen, int screen_w, int screen_h);
```

---

## 8. 音频系统 (fd2_audio)

**头文件:** `include/fd2_audio.h`  
**音乐文件:** FDMUS.DAT (MIDI格式)

### 生命周期

```c
int  fd2_audio_init(fd2_audio_t* audio);
void fd2_audio_shutdown(fd2_audio_t* audio);
void fd2_audio_set_fdmus_path(fd2_audio_t* audio, const char* path);
```

### 音乐播放

```c
int  fd2_audio_play_music(fd2_audio_t* audio, int track_id, int loops);  // track_id: FDMUS.DAT中的资源索引, loops: -1=无限, 0=播放1次
void fd2_audio_stop_music(fd2_audio_t* audio);
void fd2_audio_set_music_volume(fd2_audio_t* audio, int volume);         // 0-128
void fd2_audio_fade_music(fd2_audio_t* audio, int ms);
bool fd2_audio_music_playing(const fd2_audio_t* audio);
```

### 音效

```c
int  fd2_audio_play_sfx(fd2_audio_t* audio, int sfx_id);
void fd2_audio_set_sfx_volume(fd2_audio_t* audio, int volume);  // 0-128
```

### 控制

```c
void fd2_audio_toggle_mute(fd2_audio_t* audio);
```

---

## 9. 专用解码器

### BG.DAT 背景

```c
int fd2_bg_decode(const u8* res_data, u32 res_size, u8** out_pixels, int* out_w, int* out_h);
```

### FDSHAP.DAT 精灵调色板

```c
int fd2_shap_extract_palette(const u8* res_data, u32 res_size, fd2_shap_palette_t* out);
```

### FIGANI.DAT 动画帧

```c
int  fd2_ani_decode_frame(const u8* res_data, u32 res_size, fd2_ani_frame_t* frame);
int  fd2_ani_read_timing(const u8* res_data, u32 res_size);
```

### FDTXT.DAT 文本/字体

```c
int fd2_text_decode_glyph(const u8* res_data, u32 res_size, fd2_text_glyph_t* glyph);
```

### TAI.DAT 头像

```c
int fd2_tai_decode_portrait(const u8* res_data, u32 res_size, u8** out_pixels, int* out_w, int* out_h);
```

---

## 典型使用流程

```c
// 1. 初始化
fd2_resources_t res;
fd2_resources_init(&res, "./game");

fd2_render_t render;
fd2_render_init(&render, FD2_RENDER_SCALE);

fd2_audio_t audio;
fd2_audio_init(&audio);

// 2. 加载资源
fd2_resources_load_dat(&res, FD2_DAT_FDOTHER);
fd2_resources_load_dat(&res, FD2_DAT_ANI);
fd2_resources_load_dat(&res, FD2_DAT_FDMUS);

// 3. 设置音乐路径
const char* fdmus_path = fd2_resources_dat_path(&res, FD2_DAT_FDMUS);
fd2_audio_set_fdmus_path(&audio, fdmus_path);

// 4. 获取资源
u32 pal_size;
const u8* pal_res = fd2_resources_get(&res, FD2_DAT_FDOTHER, 75, &pal_size);
fd2_render_set_palette_6bit(&render, pal_res);

// 5. 播放音乐
fd2_audio_play_music(&audio, 11, -1);  // 播放轨道11，无限循环

// 6. 渲染RLE图像
u32 img_size;
const u8* img_res = fd2_resources_get(&res, FD2_DAT_FDOTHER, 73, &img_size);
fd2_render_blit_rle(&render, img_res, img_size, 0, 0);
fd2_render_present(&render);

// 7. AFM动画播放
fd2_afm_t afm;
fd2_afm_init(&afm);
const u8* ani_data = fd2_resources_get(&res, FD2_DAT_ANI, 3, NULL);
fd2_afm_open(&afm, ani_data, size);
while (!fd2_afm_is_done(&afm)) {
    fd2_afm_decode_next_frame(&afm);
    fd2_render_set_palette_6bit(&render, fd2_afm_get_palette(&afm));
    fd2_render_blit_afm(&render, fd2_afm_get_frame(&afm), -1);
    fd2_render_present(&render);
    SDL_Delay(90);
}

// 8. 清理
fd2_audio_shutdown(&audio);
fd2_render_shutdown(&render);
fd2_resources_shutdown(&res);
```
