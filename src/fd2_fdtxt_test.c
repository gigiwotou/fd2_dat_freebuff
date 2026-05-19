/*
 * FDTXT.DAT 文本渲染测试
 * 
 * 使用原游戏逻辑将FDTXT.DAT的文本渲染到屏幕上
 * 基于sub_15F84和sub_4ED7A函数的还原代码
 * 
 * 编译: build.bat test
 * 运行: bin/fd2_fdtxt_test.exe
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

/* 字体文件路径 */
#define FONT_DAT_PATH "game/FDOTHER.DAT"
#define FDTXT_DAT_PATH "game/FDTXT.DAT"
#define ENCODING_PATH "tools/font/encoding_cn.json"

/* 全局变量 */
static uint8_t* font_data = NULL;      /* FDOTHER.DAT索引3的字体数据 */
static uint8_t* fdtxt_data = NULL;     /* FDTXT.DAT数据块 */
static int fdtxt_size = 0;             /* FDTXT.DAT数据块大小 */
static int fdtxt_count = 0;            /* FDTXT.DAT资源数量 */
static uint32_t fdtxt_offsets[146];    /* FDTXT.DAT偏移表 */

/* SDL相关 */
static SDL_Window* window = NULL;
static SDL_Renderer* renderer = NULL;
static SDL_Texture* texture = NULL;
static uint32_t* screen_buffer = NULL; /* 32位屏幕缓冲区 */

/* 字体颜色 */
#define COLOR_BG       0x00000000  /* 黑色背景 */
#define COLOR_TEXT     0xFFFFFFFF  /* 白色文本 */
#define COLOR_BORDER   0x000000FF  /* 红色边框 */

/* ============================================================
 * DAT文件加载函数（还原sub_111BA）
 * ============================================================ */

/* 加载整个DAT文件到内存 */
static uint8_t* load_entire_dat(const char* filename, size_t* out_size)
{
    FILE* fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "无法打开文件: %s\n", filename);
        return NULL;
    }

    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    uint8_t* data = (uint8_t*)malloc(size);
    if (!data) {
        fclose(fp);
        return NULL;
    }

    fread(data, 1, size, fp);
    fclose(fp);

    if (out_size) *out_size = size;
    return data;
}

/* 从DAT文件加载指定索引的资源（还原sub_111BA） */
static uint8_t* load_dat_resource(uint8_t* dat_data, size_t dat_size, 
                                   int index, int* out_size)
{
    /* 解析头部：前6字节是魔数 */
    if (dat_size < 10) return NULL;

    /* 读取资源数量 */
    uint32_t count;
    memcpy(&count, dat_data + 6, 4);

    if (index < 0 || index >= count - 1) return NULL;

    /* 读取偏移表（从偏移10开始，每项4字节） */
    uint32_t offset_start, offset_end;
    memcpy(&offset_start, dat_data + 10 + index * 4, 4);
    memcpy(&offset_end, dat_data + 10 + (index + 1) * 4, 4);

    if (offset_start >= dat_size || offset_end > dat_size) return NULL;

    size_t size = offset_end - offset_start;
    uint8_t* buffer = (uint8_t*)malloc(size);
    if (!buffer) return NULL;

    memcpy(buffer, dat_data + offset_start, size);

    if (out_size) *out_size = (int)size;
    return buffer;
}

/* ============================================================
 * 字体渲染函数（还原sub_4ED7A）
 * 
 * 参数:
 *   font_data - 字体数据指针（FDOTHER.DAT索引3）
 *   char_index - 字符索引（0-1823）
 *   x, y - 屏幕坐标
 *   color - 前景色（32位RGBA）
 */
static void render_char_16x16(int char_index, int x, int y, uint32_t color)
{
    if (!font_data || char_index < 0 || char_index >= FONT_MAX_CHARS) {
        return;
    }

    /* 定位到字体数据：每个字符32字节（16行 × 2字节/行） */
    uint8_t* char_data = font_data + char_index * 32;

    /* 渲染16×16位图 */
    for (int row = 0; row < 16; row++) {
        /* 每行2字节（16位），需要交换字节序（匹配原游戏4ED7A的逻辑）
         * 原游戏代码:
         *   v19 = v17;
         *   LOBYTE(v18) = HIBYTE(v17);  // v18的低字节 = v17的高字节
         *   HIBYTE(v18) = v19;           // v18的高字节 = v17的低字节
         *
         * 数据格式: char_data[row*2]是低字节, char_data[row*2+1]是高字节
         * 所以: bits = (低字节 << 8) | 高字节 是错误的
         * 应该: bits = (高字节 << 8) | 低字节 也是错的
         *
         * 实际上原游戏读取的是小端序的uint16，然后交换字节
         * 即: bits = *(uint16*)(char_data + row*2)
         *     bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF)
         */
        uint16_t bits;
        memcpy(&bits, char_data + row * 2, 2);
        bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);

        for (int col = 0; col < 16; col++) {
            int px = x + col;
            int py = y + row;

            /* 检查边界 */
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) {
                continue;
            }

            /* 检查当前位是否为1 */
            if (bits & (1 << (15 - col))) {
                screen_buffer[py * SCREEN_WIDTH + px] = color;
            }
        }
    }
}

/* ============================================================
 * 渲染文本块（还原sub_15F84）
 * 
 * 参数:
 *   text_data - 文本数据块指针（整个资源集就是一个文本块）
 *   start_x, start_y - 起始坐标
 * 
 * 注意: FDTXT.DAT每个资源集的第一个WORD是字符数量，不是文本！
 *       需要跳过这个头部信息。
 */
static void render_text_block(int16_t* text_data, int start_x, int start_y)
{
    if (!text_data) return;

    /* 跳过第一个WORD（字符数量头） */
    int16_t* ptr = text_data + 1;
    int x = start_x;
    int y = start_y;

    while (1) {
        int16_t word = *ptr;
        ptr++;

        if (word == TEXT_END) {
            break;  /* 文本结束 */
        }

        if (word == TEXT_NEWLINE || word == TEXT_NEWLINE2) {
            /* 换行 */
            x = start_x;
            y += CHAR_HEIGHT;

            if (word == TEXT_NEWLINE2) {
                /* 等待输入（这里简化为自动继续） */
                SDL_Delay(500);
            }
            continue;
        }

        if (word < 0) {
            /* 其他控制码（简化处理） */
            switch (word) {
                case TEXT_PORTRAIT_F:
                case TEXT_PORTRAIT_S:
                case TEXT_CHAR_F:
                case TEXT_CHAR_S:
                    /* 跳过头像ID（下一个WORD） */
                    ptr++;
                    break;

                case TEXT_SHOW_NUM:
                    /* 简化：显示数字0 */
                    render_char_16x16(0, x, y, COLOR_TEXT);
                    x += CHAR_WIDTH;
                    break;

                default:
                    break;
            }
            continue;
        }

        /* 正值 = 字符索引 */
        if (word < FONT_MAX_CHARS) {
            render_char_16x16(word, x, y, COLOR_TEXT);
            x += CHAR_WIDTH;

            /* 自动换行 */
            if (x + CHAR_WIDTH > SCREEN_WIDTH) {
                x = start_x;
                y += CHAR_HEIGHT;
            }
        }
    }
}

/* ============================================================
 * SDL初始化
 * ============================================================ */
static int sdl_init(void)
{
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL初始化失败: %s\n", SDL_GetError());
        return -1;
    }

    window = SDL_CreateWindow("FDTXT.DAT 文本渲染测试",
                              SDL_WINDOWPOS_CENTERED,
                              SDL_WINDOWPOS_CENTERED,
                              SCREEN_WIDTH * SCALE_FACTOR,
                              SCREEN_HEIGHT * SCALE_FACTOR,
                              SDL_WINDOW_SHOWN);
    if (!window) {
        fprintf(stderr, "创建窗口失败: %s\n", SDL_GetError());
        return -1;
    }

    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) {
        fprintf(stderr, "创建渲染器失败: %s\n", SDL_GetError());
        return -1;
    }

    texture = SDL_CreateTexture(renderer,
                                SDL_PIXELFORMAT_ARGB8888,
                                SDL_TEXTUREACCESS_STREAMING,
                                SCREEN_WIDTH, SCREEN_HEIGHT);
    if (!texture) {
        fprintf(stderr, "创建纹理失败: %s\n", SDL_GetError());
        return -1;
    }

    /* 分配屏幕缓冲区 */
    screen_buffer = (uint32_t*)malloc(SCREEN_WIDTH * SCREEN_HEIGHT * 4);
    if (!screen_buffer) {
        fprintf(stderr, "分配屏幕缓冲区失败\n");
        return -1;
    }

    return 0;
}

/* ============================================================
 * 渲染屏幕缓冲区到纹理
 * ============================================================ */
static void render_frame(void)
{
    SDL_UpdateTexture(texture, NULL, screen_buffer, SCREEN_WIDTH * 4);
    SDL_RenderClear(renderer);

    /* 放大渲染 */
    SDL_Rect dst_rect = {0, 0, SCREEN_WIDTH * SCALE_FACTOR, SCREEN_HEIGHT * SCALE_FACTOR};
    SDL_RenderCopy(renderer, texture, NULL, &dst_rect);

    SDL_RenderPresent(renderer);
}

/* ============================================================
 * 清屏
 * ============================================================ */
static void clear_screen(void)
{
    memset(screen_buffer, 0, SCREEN_WIDTH * SCREEN_HEIGHT * 4);
}

/* ============================================================
 * 清理资源
 * ============================================================ */
static void cleanup(void)
{
    if (screen_buffer) free(screen_buffer);
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
    printf("=== FDTXT.DAT 文本渲染测试 ===\n\n");

    /* 1. 加载字体数据（FDOTHER.DAT索引3） */
    printf("1. 加载字体数据...\n");
    size_t other_size;
    uint8_t* other_data = load_entire_dat(FONT_DAT_PATH, &other_size);
    if (!other_data) {
        fprintf(stderr, "无法加载 %s\n", FONT_DAT_PATH);
        return 1;
    }

    int font_size;
    font_data = load_dat_resource(other_data, other_size, 3, &font_size);
    if (!font_data) {
        fprintf(stderr, "无法加载字体数据（索引3）\n");
        free(other_data);
        return 1;
    }
    printf("   字体数据加载成功: %d 字节 (%d 字符)\n\n", font_size, font_size / 32);

    /* 2. 加载FDTXT.DAT（加载整个文件） */
    printf("2. 加载FDTXT.DAT...\n");
    size_t fdtxt_file_size;
    uint8_t* fdtxt_file = load_entire_dat(FDTXT_DAT_PATH, &fdtxt_file_size);
    if (!fdtxt_file) {
        fprintf(stderr, "无法加载 %s\n", FDTXT_DAT_PATH);
        free(other_data);
        free(font_data);
        return 1;
    }

    /* 解析FDTXT.DAT头部 */
    memcpy(&fdtxt_count, fdtxt_file + 6, 4);
    printf("   FDTXT.DAT 资源数量: %d\n", fdtxt_count);

    /* 读取偏移表 */
    for (int i = 0; i < fdtxt_count && i < 146; i++) {
        memcpy(&fdtxt_offsets[i], fdtxt_file + 10 + i * 4, 4);
    }

    /* 加载第一个资源集（索引0）作为测试 */
    if (fdtxt_count > 0 && fdtxt_offsets[0] < fdtxt_file_size) {
        uint32_t start = fdtxt_offsets[0];
        uint32_t end = (fdtxt_offsets[1] < fdtxt_file_size) ? fdtxt_offsets[1] : fdtxt_file_size;
        fdtxt_size = end - start;
        fdtxt_data = (uint8_t*)malloc(fdtxt_size);
        if (fdtxt_data) {
            memcpy(fdtxt_data, fdtxt_file + start, fdtxt_size);
            printf("   资源集0加载成功: %d 字节\n", fdtxt_size);
        }
    }

    free(fdtxt_file);
    free(other_data);

    /* 3. 初始化SDL */
    printf("3. 初始化SDL渲染器...\n");
    if (sdl_init() < 0) {
        free(font_data);
        free(fdtxt_data);
        return 1;
    }
    printf("   SDL初始化成功\n\n");

    /* 4. 主循环 */
    int current_resource = 0;
    bool need_render = true;

    printf("控制说明:\n");
    printf("  上/下箭头: 切换资源集（0-%d）\n", fdtxt_count - 1);
    printf("  ESC: 退出\n");
    printf("  当前资源集: %d\n\n", current_resource);

    /* 事件循环 */
    bool running = true;
    while (running) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
                case SDL_QUIT:
                    running = false;
                    break;

                case SDL_KEYDOWN:
                    switch (event.key.keysym.sym) {
                        case SDLK_ESCAPE:
                            running = false;
                            break;

                        case SDLK_UP:
                            if (current_resource < fdtxt_count - 1) {
                                current_resource++;
                                need_render = true;
                            }
                            break;

                        case SDLK_DOWN:
                            if (current_resource > 0) {
                                current_resource--;
                                need_render = true;
                            }
                            break;

                        default:
                            break;
                    }
                    break;

                default:
                    break;
            }
        }

        /* 需要渲染时更新画面 */
        if (need_render) {
            /* 清屏 */
            clear_screen();

            /* 加载新的资源集 */
            if (fdtxt_data) {
                free(fdtxt_data);
                fdtxt_data = NULL;
            }

            if (current_resource < fdtxt_count && fdtxt_offsets[current_resource] < fdtxt_file_size) {
                uint32_t start = fdtxt_offsets[current_resource];
                uint32_t end = (current_resource + 1 < fdtxt_count && fdtxt_offsets[current_resource + 1] < fdtxt_file_size) 
                              ? fdtxt_offsets[current_resource + 1] : fdtxt_file_size;
                fdtxt_size = end - start;

                /* 重新加载FDTXT.DAT */
                uint8_t* fdtxt_file = load_entire_dat(FDTXT_DAT_PATH, &fdtxt_file_size);
                if (fdtxt_file) {
                    fdtxt_data = (uint8_t*)malloc(fdtxt_size);
                    if (fdtxt_data) {
                        memcpy(fdtxt_data, fdtxt_file + start, fdtxt_size);
                        printf("\r加载资源集 %d: %d 字节", current_resource, fdtxt_size);
                    }
                    free(fdtxt_file);
                }
            }

            /* 渲染文本块 */
            if (fdtxt_data) {
                render_text_block((int16_t*)fdtxt_data, 10, 10);
            }

            /* 更新屏幕 */
            render_frame();
            need_render = false;
        }

        /* 限制帧率 */
        SDL_Delay(16);
    }

    /* 5. 清理 */
    cleanup();
    free(font_data);
    free(fdtxt_data);

    printf("\n\n测试完成\n");
    return 0;
}
