#include "fd2_data_loader.h"
#include "fd2_globals.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 静态路径缓冲区 */
static char s_path_buf[768];

const char* fd2_get_data_path(const char* data_dir, const char* filename) {
    if (!filename) return NULL;
    if (data_dir && data_dir[0]) {
        snprintf(s_path_buf, sizeof(s_path_buf), "%s/%s", data_dir, filename);
    } else {
        snprintf(s_path_buf, sizeof(s_path_buf), "%s", filename);
    }
    return s_path_buf;
}

/* ========================================================================
 * sub_111BA: 资源加载函数 (原游戏 0x111BA, 大小 0xEB)
 *
 * 原游戏行为 (1:1 复制):
 *   1. if (a6) free(a6);
 *   2. _rb_ = fopen(a5, "rb");
 *   3. if (!_rb_) { printf("File not found %s!!!\n"); return; }
 *   4. v8 = malloc(8);
 *   5. fseek(_rb_, 4 * a7 + 6, 0);
 *   6. fread(v8, 1, 8, _rb_);
 *   7. v9 = *v8;                           // start_offset
 *   8. dword_53BFF = v8[1] - *v8;          // size = end_offset - start_offset
 *   9. free(v8);
 *   10. v10 = malloc(dword_53BFF);
 *   11. if (!v10) { printf("Out of Memory at Load %s Number:%d!!\n"); return; }
 *   12. fseek(_rb_, v9, 0);
 *   13. fread(v10, 1, dword_53BFF, _rb_);
 *   14. fclose(_rb_);
 *   15. return v10;
 * ======================================================================== */
void* fd2_dat_load_resource(const char* filename, void* oldData, int index) {
    FILE* fp;
    int offsets[2];
    void* data;

    /* 1. 释放旧数据 */
    if (oldData) {
        free(oldData);
    }

    /* 2. 打开文件 */
    fp = fopen(filename, "rb");
    if (!fp) {
        printf("\n\n File not found %s!!! \n\n", filename);
        return NULL;
    }

    /* 3. 读取索引表 (每个索引8字节: start_offset, end_offset) */
    /* fseek(_rb_, 4 * a7 + 6, 0) - 原游戏使用 4*index+6 因为索引表前6字节是头部 */
    fseek(fp, 4 * index + 6, SEEK_SET);
    fread(offsets, 1, 8, fp);

    /* 4. 计算数据大小 */
    g_dword_53BFF = (u32)(offsets[1] - offsets[0]);

    /* 5. 分配内存并读取数据 */
    data = malloc(g_dword_53BFF);
    if (!data) {
        printf("Out of Memory at Load %s Number:%d!!\n", filename, index);
        fclose(fp);
        return NULL;
    }

    /* 6. 定位到数据并读取 */
    fseek(fp, offsets[0], SEEK_SET);
    fread(data, 1, g_dword_53BFF, fp);
    fclose(fp);

    return data;
}

/* ========================================================================
 * sub_25977: 音乐切换函数 (原游戏 0x25977, 大小 0x11F)
 *
 * 原游戏行为 (1:1 复制):
 *   1. if ((unsigned char)::n16 != n16) {
 *   2.   ::n16 = n16;
 *   3.   if (n16 == -1) {
 *   4.     sub_3B124(n16, dword_53ED0, 0, 4000);  // 停止音乐
 *   5.   } else {
 *   6.     if (n16_0) {
 *   7.       if (FDMUS_DAT) sub_3AF5B(n16_0, dword_53ED0);  // 停止旧音乐
 *   8.       FDMUS_DAT = sub_111BA(..., "FDMUS.DAT", FDMUS_DAT, n16);
 *   9.       v8 = sub_3666C(FDMUS_DAT, dword_53BFF);
 *   10.      sub_3ADF5(v8, dword_53ED0, FDMUS_DAT, 0);
 *   11.      sub_3AEEE(dword_53ED0);
 *   12.      if (n127) {
 *   13.        if (n16 == 16 || n16 == 17) n2000 = 0;
 *   14.        else { sub_3B124(..., 0, 0); n2000 = 2000; }
 *   15.        v10 = sub_3B124(..., 127, n2000);
 *   16.      } else {
 *   17.        v10 = sub_3B124(..., 0, 0);
 *   18.      }
 *   19.      sub_3B1A6(v10, dword_53ED0, arg4);
 *   20.    }
 *   21.  }
 * ======================================================================== */

static int current_music_n16 = -1;

void fd2_music_switch(int n16, int arg4) {
    (void)arg4;

    /* 1. 检查音乐ID是否变化 */
    if ((unsigned char)current_music_n16 != (unsigned char)n16) {
        current_music_n16 = n16;

        /* 3. 停止音乐 */
        if (n16 == -1) {
            /* 调用AIL库停止音乐 sub_3B124(..., dword_53ED0, 0, 4000) */
            /* SDL2实现: 停止当前播放的音乐 */
        }
        else {
            /* 6. 播放新音乐 (如果 n16_0 非零) */
            /* TODO: 完整的AIL音乐加载和播放逻辑
             * - 从FDMUS.DAT加载音乐索引n16
             * - sub_111BA(..., "FDMUS.DAT", FDMUS_DAT, n16)
             * - sub_3666C 检查音乐数据
             * - sub_3ADF5 设置音乐
             * - sub_3AEEE 启动音乐
             * - sub_3B124 设置音量
             * - sub_3B1A6 播放音乐
             */
        }
    }
}

void fd2_music_stop(void) {
    fd2_music_switch(-1, 0);
}

void fd2_music_play(int musicId) {
    fd2_music_switch(musicId, 0);
}

int fd2_music_get_scene_music_id(int sceneId) {
    if (sceneId < 0 || sceneId >= 30) return 0;
    return (unsigned char)g_byte_51E63[sceneId];
}

/* ========================================================================
 * funcs_1197B: 场景完成条件检查函数数组 (原游戏 0x51B19)
 *
 * 原游戏: 30个函数指针数组，检查场景是否可以完成
 * 每个函数返回 1=完成, 0=未完成
 * ======================================================================== */

static int scene_check_default_impl(fd2_state_machine_t* sm) {
    (void)sm;
    /* 默认场景完成条件: 永远不完成 */
    return 0;
}

fd2_scene_check_fn funcs_1197B[30];

void fd2_scene_check_init(void) {
    /* 所有场景使用默认检查 */
    for (int i = 0; i < 30; i++) {
        funcs_1197B[i] = scene_check_default_impl;
    }
}

int scene_check_default(void) {
    return scene_check_default_impl(NULL);
}

/* ========================================================================
 * fd2_data_load_all: 加载所有初始资源 (对应原游戏 main() 0x25BF4 中的加载序列)
 * 
 * 加载顺序 (必须1:1按原游戏顺序):
 *   1. FDOTHER.DAT 索引31 -> FDOTHER_DAT__2
 *   2. FDOTHER.DAT 索引1  -> FDOTHER_DAT__3
 *   3. FDOTHER.DAT 索引2  -> FDOTHER_DAT__4
 *   4. FDOTHER.DAT 索引3  -> FDOTHER_DAT__5
 *   5. FDOTHER.DAT 索引4  -> FDOTHER_DAT__6
 *   6. FDOTHER.DAT 索引5  -> FDOTHER_DAT__7
 *   7. FDTXT.DAT   索引0  -> FDTXT_DAT__0
 *   8. FDOTHER.DAT 索引6  -> FDOTHER_DAT__8
 *   9. malloc(32)         -> g_n8_0
 *   10. malloc(65536)     -> g_n655360_0
 *   11. malloc(2560)      -> g_n8_3
 * ======================================================================== */
int fd2_data_load_all(fd2_state_machine_t* sm, const char* data_dir) {
    const char* path;

    (void)sm;

    /* 1. 加载FDOTHER.DAT索引31 */
    path = fd2_get_data_path(data_dir, "FDOTHER.DAT");
    g_FDOTHER_DAT__2 = fd2_dat_load_resource(path, NULL, 31);
    if (!g_FDOTHER_DAT__2) return -1;

    /* 2. 加载FDOTHER.DAT索引1 */
    g_FDOTHER_DAT__3 = fd2_dat_load_resource(path, NULL, 1);
    if (!g_FDOTHER_DAT__3) return -1;

    /* 3. 加载FDOTHER.DAT索引2 */
    g_FDOTHER_DAT__4 = fd2_dat_load_resource(path, NULL, 2);
    if (!g_FDOTHER_DAT__4) return -1;

    /* 4. 加载FDOTHER.DAT索引3 */
    g_FDOTHER_DAT__5 = fd2_dat_load_resource(path, NULL, 3);
    if (!g_FDOTHER_DAT__5) return -1;

    /* 5. 加载FDOTHER.DAT索引4 */
    g_FDOTHER_DAT__6 = fd2_dat_load_resource(path, NULL, 4);
    if (!g_FDOTHER_DAT__6) return -1;

    /* 6. 加载FDOTHER.DAT索引5 */
    g_FDOTHER_DAT__7 = fd2_dat_load_resource(path, NULL, 5);
    if (!g_FDOTHER_DAT__7) return -1;

    /* 7. 加载FDTXT.DAT索引0 */
    path = fd2_get_data_path(data_dir, "FDTXT.DAT");
    g_FDTXT_DAT__0 = fd2_dat_load_resource(path, NULL, 0);
    if (!g_FDTXT_DAT__0) return -1;

    /* 8. 加载FDOTHER.DAT索引6 */
    path = fd2_get_data_path(data_dir, "FDOTHER.DAT");
    g_FDOTHER_DAT__8 = fd2_dat_load_resource(path, NULL, 6);
    if (!g_FDOTHER_DAT__8) return -1;

    /* 9. 分配缓冲区 */
    g_n8_0 = malloc(32);
    if (!g_n8_0) return -1;

    /* 10. 分配后备缓冲区 (64KB) */
    g_n655360_0 = malloc(65536);
    if (!g_n655360_0) return -1;

    /* 11. 分配场景数据缓冲区 (2560字节) */
    g_n8_3 = malloc(2560);
    if (!g_n8_3) return -1;

    return 0;
}

/* ========================================================================
 * 数据初始化和清理
 * ======================================================================== */

int fd2_data_init(void) {
    /* 初始化场景检查数组 */
    fd2_scene_check_init();
    return 0;
}

void fd2_data_shutdown(void) {
    /* 释放资源指针 */
    if (g_FDOTHER_DAT__2) { free(g_FDOTHER_DAT__2); g_FDOTHER_DAT__2 = NULL; }
    if (g_FDOTHER_DAT__3) { free(g_FDOTHER_DAT__3); g_FDOTHER_DAT__3 = NULL; }
    if (g_FDOTHER_DAT__4) { free(g_FDOTHER_DAT__4); g_FDOTHER_DAT__4 = NULL; }
    if (g_FDOTHER_DAT__5) { free(g_FDOTHER_DAT__5); g_FDOTHER_DAT__5 = NULL; }
    if (g_FDOTHER_DAT__6) { free(g_FDOTHER_DAT__6); g_FDOTHER_DAT__6 = NULL; }
    if (g_FDOTHER_DAT__7) { free(g_FDOTHER_DAT__7); g_FDOTHER_DAT__7 = NULL; }
    if (g_FDOTHER_DAT__8) { free(g_FDOTHER_DAT__8); g_FDOTHER_DAT__8 = NULL; }
    if (g_FDOTHER_DAT__12) { free(g_FDOTHER_DAT__12); g_FDOTHER_DAT__12 = NULL; }
    if (g_FDOTHER_DAT__13) { free(g_FDOTHER_DAT__13); g_FDOTHER_DAT__13 = NULL; }

    if (g_FDTXT_DAT__0) { free(g_FDTXT_DAT__0); g_FDTXT_DAT__0 = NULL; }
    if (g_FDSHAP_DAT) { free(g_FDSHAP_DAT); g_FDSHAP_DAT = NULL; }
    if (g_FDFIELD_DAT__1) { free(g_FDFIELD_DAT__1); g_FDFIELD_DAT__1 = NULL; }
    if (g_FDICON_DAT) { free(g_FDICON_DAT); g_FDICON_DAT = NULL; }
}
