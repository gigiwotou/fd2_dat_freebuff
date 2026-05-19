/*
 * FDTXT.DAT 文本渲染测试 - 修正版
 * 
 * 使用原游戏逻辑将FDTXT.DAT的文本渲染到屏幕上
 * 基于sub_15F84和sub_4ED7A函数的还原代码
 * 
 * FDTXT.DAT 完整结构:
 *   [文件头6字节 "LLLLLL"]
 *   [资源集偏移表: 每项4字节，共34项]
 *   
 *   资源集N:
 *     [子资源数量: 2字节WORD]
 *     [子偏移表: 每项2字节WORD，共count项]
 *     [子资源0: WORD数组，以-1结束]
 *     [子资源1: WORD数组，以-1结束]
 *     ...
 * 
 * 编译: build.bat fdtxttest
 * 运行: bin\fd2_fdtxt_test.exe
 */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

/* 游戏常量 */
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 200
#define SCALE_FACTOR 3  /* 放大3倍 = 960x600 */
#define CHAR_WIDTH 16
#define CHAR_HEIGHT 16

/* 字体编码表最大字符数 */
#define FONT_MAX_CHARS 1824

/* 控制码定义 */
#define TEXT_END        -1   /* 文本结束 */
#define TEXT_NEWLINE    -2   /* 换行 */
#define TEXT_NEWLINE2   -3   /* 换行+等待输入 */
#define TEXT_RECURSE1   -4   /* 递归显示dword_53AD9的文本 */
#define TEXT_RECURSE2   -5   /* 递归显示dword_53ADD的文本 */
#define TEXT_SHOW_NUM   -6   /* 显示数字变量dword_53AE1 */
#define TEXT_PORTRAIT_F -17  /* 加载DATO.DAT头像(正面) */
#define TEXT_PORTRAIT_S -18  /* 加载DATO.DAT头像(侧面) */
#define TEXT_CHAR_F     -19  /* 从角色数据加载头像(正面) */
#define TEXT_CHAR_S     -20  /* 从角色数据加载头像(侧面) */

/* 文件路径 */
#define FONT_DAT_PATH "game/FDOTHER.DAT"
#define FDTXT_DAT_PATH "game/FDTXT.DAT"

/* 全局变量 */
static uint8_t* font_data = NULL;      /* FDOTHER.DAT索引3的字体数据 */
static uint8_t* fdtxt_data = NULL;     /* FDTXT.DAT整个文件数据 */
static size_t fdtxt_file_size = 0;     /* FDTXT.DAT文件大小 */
static int fdtxt_count = 0;            /* FDTXT.DAT资源集数量 */
static uint32_t fdtxt_offsets[146];    /* FDTXT.DAT资源集偏移表 */

/* SDL相关 */
static SDL_Window* window = NULL;
static SDL_Renderer* renderer = NULL;
static SDL_Texture* texture = NULL;
static uint32_t* screen_buffer = NULL;

/* 颜色定义 */
#define COLOR_TEXT 0xFFFFFFFF  /* 白色文本 */

/* ============================================================
 * 加载整个文件到内存
 * ============================================================ */
static uint8_t* load_file(const char* filename, size_t* out_size)
{
    FILE* fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "无法打开: %s\n", filename);
        return NULL;
    }
    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    uint8_t* data = (uint8_t*)malloc(size);
    if (data) fread(data, 1, size, fp);
    fclose(fp);
    if (out_size) *out_size = size;
    return data;
}

/* ============================================================
 * 从DAT文件加载指定索引的资源
 * ============================================================ */
static uint8_t* load_dat_resource(uint8_t* dat_data, size_t dat_size,
                                   int index, int* out_size)
{
    if (dat_size < 10) return NULL;
    uint32_t count;
    memcpy(&count, dat_data + 6, 4);
    if (index < 0 || (uint32_t)index >= count - 1) return NULL;

    uint32_t off_start, off_end;
    memcpy(&off_start, dat_data + 10 + index * 4, 4);
    memcpy(&off_end, dat_data + 10 + (index + 1) * 4, 4);
    if (off_start >= dat_size || off_end > dat_size) return NULL;

    size_t size = off_end - off_start;
    uint8_t* buf = (uint8_t*)malloc(size);
    if (buf) memcpy(buf, dat_data + off_start, size);
    if (out_size) *out_size = (int)size;
    return buf;
}

/* ============================================================
 * 字体渲染（还原sub_4ED7A）
 * ============================================================ */
static void render_char(int char_index, int x, int y, uint32_t color)
{
    if (!font_data || char_index < 0 || char_index >= FONT_MAX_CHARS) return;

    uint8_t* char_data = font_data + char_index * 32;

    for (int row = 0; row < 16; row++) {
        uint16_t bits;
        memcpy(&bits, char_data + row * 2, 2);
        bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);  /* 字节交换 */

        for (int col = 0; col < 16; col++) {
            int px = x + col, py = y + row;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            if (bits & (1 << (15 - col))) {
                screen_buffer[py * SCREEN_WIDTH + px] = color;
            }
        }
    }
}

/* ============================================================
 * 渲染单个文本项（还原sub_15F84的核心循环）
 * 
 * text_ptr: 指向文本项的WORD数组（以-1结束）
 * start_x, start_y: 起始坐标
 * 返回: 最后的光标Y坐标
 * ============================================================ */
static int render_text_item(int16_t* text_ptr, int start_x, int start_y)
{
    if (!text_ptr) return start_y;

    int16_t* ptr = text_ptr;
    int x = start_x;
    int y = start_y;

    while (1) {
        int16_t word = *ptr++;

        if (word == TEXT_END) break;

        if (word == TEXT_NEWLINE || word == TEXT_NEWLINE2) {
            x = start_x;
            y += CHAR_HEIGHT;
            if (word == TEXT_NEWLINE2) SDL_Delay(300);
            continue;
        }

        if (word < 0) {
            /* 控制码处理 */
            switch (word) {
                case TEXT_PORTRAIT_F:
                case TEXT_PORTRAIT_S:
                case TEXT_CHAR_F:
                case TEXT_CHAR_S:
                    ptr++;  /* 跳过头像/角色ID */
                    break;
                case TEXT_SHOW_NUM:
                    /* 简化: 显示数字0 */
                    render_char(0, x, y, COLOR_TEXT);
                    x += CHAR_WIDTH;
                    break;
            }
            continue;
        }

        /* 正值 = 字符索引 */
        if (word < FONT_MAX_CHARS) {
            render_char(word, x, y, COLOR_TEXT);
            x += CHAR_WIDTH;
            if (x + CHAR_WIDTH > SCREEN_WIDTH) {
                x = start_x;
                y += CHAR_HEIGHT;
            }
        }
    }
    return y;
}

/* ============================================================
 * 获取资源集N的子文本项M的指针
 * 
 * 资源集结构:
 *   [子数量: 2字节] [子偏移表: 每项2字节] [子资源0] [子资源1] ...
 * ============================================================ */
static int16_t* get_sub_text(int resource_idx, int sub_idx)
{
    uint32_t res_start = fdtxt_offsets[resource_idx];
    uint32_t res_end = (resource_idx + 1 < fdtxt_count && fdtxt_offsets[resource_idx + 1] < fdtxt_file_size)
                       ? fdtxt_offsets[resource_idx + 1] : fdtxt_file_size;

    if (res_start >= fdtxt_file_size) return NULL;

    uint8_t* res_data = fdtxt_data + res_start;
    size_t res_size = res_end - res_start;

    /* 读取子资源数量 */
    if (res_size < 2) return NULL;
    int16_t sub_count;
    memcpy(&sub_count, res_data, 2);

    if (sub_idx < 0 || sub_idx >= sub_count) return NULL;

    /* 读取子偏移表 */
    int16_t* sub_offsets = (int16_t*)(res_data + 2);

    /* 子偏移是相对于资源集数据开始的位置 */
    return (int16_t*)(res_data + sub_offsets[sub_idx]);
}

/* 获取资源集的子资源数量 */
static int get_sub_count(int resource_idx)
{
    uint32_t res_start = fdtxt_offsets[resource_idx];
    if (res_start >= fdtxt_file_size) return 0;
    int16_t count;
    memcpy(&count, fdtxt_data + res_start, 2);
    return (count > 0) ? count : 0;
}

/* ============================================================
 * SDL初始化
 * ============================================================ */
static int sdl_init(void)
{
    if (SDL_Init(SDL_INIT_VIDEO) < 0) { fprintf(stderr, "SDL失败: %s\n", SDL_GetError()); return -1; }
    window = SDL_CreateWindow("FDTXT.DAT 文本渲染测试", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              SCREEN_WIDTH * SCALE_FACTOR, SCREEN_HEIGHT * SCALE_FACTOR, SDL_WINDOW_SHOWN);
    if (!window) { fprintf(stderr, "窗口失败: %s\n", SDL_GetError()); return -1; }
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) { fprintf(stderr, "渲染器失败: %s\n", SDL_GetError()); return -1; }
    texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING,
                                SCREEN_WIDTH, SCREEN_HEIGHT);
    if (!texture) { fprintf(stderr, "纹理失败: %s\n", SDL_GetError()); return -1; }
    screen_buffer = (uint32_t*)malloc(SCREEN_WIDTH * SCREEN_HEIGHT * 4);
    return screen_buffer ? 0 : -1;
}

static void render_frame(void)
{
    SDL_UpdateTexture(texture, NULL, screen_buffer, SCREEN_WIDTH * 4);
    SDL_RenderClear(renderer);
    SDL_Rect dst = {0, 0, SCREEN_WIDTH * SCALE_FACTOR, SCREEN_HEIGHT * SCALE_FACTOR};
    SDL_RenderCopy(renderer, texture, NULL, &dst);
    SDL_RenderPresent(renderer);
}

static void clear_screen(void) { memset(screen_buffer, 0, SCREEN_WIDTH * SCREEN_HEIGHT * 4); }

static void cleanup(void)
{
    free(screen_buffer);
    if (texture) SDL_DestroyTexture(texture);
    if (renderer) SDL_DestroyRenderer(renderer);
    if (window) SDL_DestroyWindow(window);
    SDL_Quit();
}

/* ============================================================
 * 主函数
 * ============================================================ */
int main(int argc, char* argv[])
{
    (void)argc; (void)argv;

    printf("=== FDTXT.DAT 文本渲染测试 ===\n\n");

    /* 1. 加载字体 */
    printf("1. 加载字体数据...\n");
    size_t other_size;
    uint8_t* other_data = load_file(FONT_DAT_PATH, &other_size);
    if (!other_data) return 1;

    int font_size;
    font_data = load_dat_resource(other_data, other_size, 3, &font_size);
    free(other_data);
    if (!font_data) { fprintf(stderr, "字体加载失败\n"); return 1; }
    printf("   字体: %d 字节 (%d 字符)\n\n", font_size, font_size / 32);

    /* 2. 加载FDTXT.DAT整个文件 */
    printf("2. 加载FDTXT.DAT...\n");
    fdtxt_data = load_file(FDTXT_DAT_PATH, &fdtxt_file_size);
    if (!fdtxt_data) { free(font_data); return 1; }

    /* 解析头部 */
    memcpy(&fdtxt_count, fdtxt_data + 6, 4);
    for (int i = 0; i < fdtxt_count && i < 146; i++)
        memcpy(&fdtxt_offsets[i], fdtxt_data + 10 + i * 4, 4);

    printf("   资源集数量: %d\n\n", fdtxt_count);

    /* 3. SDL初始化 */
    if (sdl_init() < 0) { free(font_data); free(fdtxt_data); return 1; }

    /* 4. 主循环 */
    int current_resource = 0;
    int current_sub = 0;
    bool need_render = true;

    printf("控制:\n");
    printf("  上/下: 切换资源集 (0-%d)\n", fdtxt_count - 1);
    printf("  左/右: 切换子文本项\n");
    printf("  ESC: 退出\n\n");

    bool running = true;
    while (running) {
        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            if (ev.type == SDL_QUIT) { running = false; break; }
            if (ev.type == SDL_KEYDOWN) {
                switch (ev.key.keysym.sym) {
                    case SDLK_ESCAPE: running = false; break;
                    case SDLK_UP:
                        if (current_resource > 0) {
                            current_resource--; current_sub = 0; need_render = true;
                        }
                        break;
                    case SDLK_DOWN:
                        if (current_resource < fdtxt_count - 1) {
                            current_resource++; current_sub = 0; need_render = true;
                        }
                        break;
                    case SDLK_LEFT:
                        if (current_sub > 0) { current_sub--; need_render = true; }
                        break;
                    case SDLK_RIGHT:
                        {
                            int sc = get_sub_count(current_resource);
                            if (current_sub < sc - 1) { current_sub++; need_render = true; }
                        }
                        break;
                }
            }
        }

        if (need_render) {
            clear_screen();
            int16_t* text = get_sub_text(current_resource, current_sub);
            int sub_count = get_sub_count(current_resource);
            if (text) {
                render_text_item(text, 10, 10);
            }
            render_frame();
            printf("\r资源集: %d/%d  子项: %d/%d  ",
                   current_resource, fdtxt_count - 1,
                   current_sub, sub_count > 0 ? sub_count - 1 : 0);
            fflush(stdout);
            need_render = false;
        }
        SDL_Delay(16);
    }

    cleanup();
    free(font_data);
    free(fdtxt_data);
    printf("\n\n完成\n");
    return 0;
}
