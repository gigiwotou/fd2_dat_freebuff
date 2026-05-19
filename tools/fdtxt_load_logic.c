/*
 * FDTXT.DAT 加载逻辑 - 基于IDA Pro反汇编代码还原
 * 
 * 文件结构:
 *   [文件头 6字节] [偏移表(每项4字节)] [数据块0] [数据块1] ...
 *   
 *   偏移表结构:
 *   - 索引N的值 = 数据块N在文件中的起始偏移
 *   - 数据块N的大小 = 索引[N+1] - 索引[N]
 *   - 文件头固定6字节，偏移表从偏移6开始
 * 
 * 资源映射:
 *   索引0: 名字、技能、职业、法术等词组
 *   索引1-32: 游戏各关卡的文字资源
 *   索引33: 开场第一个过场动画关卡的文字资源
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* 全局变量（对应游戏内存地址） */
int dword_53A79 = 0;      /* 0x53A79: 动态加载的关卡文本资源指针 */
int dword_53A7D = 0;      /* 0x53A7D: 默认文本资源指针（游戏启动时加载） */
int dword_53BFF = 0;      /* 0x53BFF: 最后一次加载的资源大小 */
unsigned char n17 = 0;    /* 当前场景/地图索引 */

/* ============================================================
 * sub_111BA: DAT文件资源加载函数
 * 
 * 参数:
 *   filename - DAT文件名（如"FDTXT.DAT"）
 *   old_ptr  - 之前分配的内存指针（用于释放旧数据，可为NULL）
 *   index    - 数据块索引号（从0开始）
 * 
 * 返回:
 *   指向加载数据的内存指针
 * ============================================================ */
uint8_t* sub_111BA(const char* filename, int old_ptr, int index)
{
    FILE* fp;
    uint8_t* buffer;
    uint32_t offset, next_offset, size;
    uint32_t offsets[2];

    /* 1. 释放旧资源（匹配汇编: if (a6) free(a6)） */
    if (old_ptr) {
        free((void*)old_ptr);
    }

    /* 2. 打开DAT文件 */
    fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "\n\n File not found %s!!! \n\n", filename);
        exit(1);
    }

    /* 3. 定位到偏移表条目: offset = 4 * index + 6
     * 跳过6字节魔数，定位到指定索引位置
     */
    fseek(fp, 4 * index + 6, SEEK_SET);

    /* 4. 读取8字节: 当前偏移(4) + 下一个偏移(4)
     * offsets[0] = 当前数据块的起始偏移
     * offsets[1] = 下一个数据块的起始偏移
     */
    if (fread(offsets, 1, 8, fp) != 8) {
        fclose(fp);
        return NULL;
    }

    offset = offsets[0];
    next_offset = offsets[1];
    
    /* 5. 计算数据块大小 */
    size = next_offset - offset;

    /* 保存到全局变量（匹配 dword_53BFF） */
    dword_53BFF = size;

    /* 6. 分配内存 */
    buffer = (uint8_t*)malloc(size);
    if (!buffer) {
        fprintf(stderr, "Out of Memory at Load %s Number:%d!!\n", filename, index);
        fclose(fp);
        return NULL;
    }

    /* 7. 定位并读取数据块 */
    fseek(fp, offset, SEEK_SET);
    fread(buffer, 1, size, fp);

    /* 8. 关闭文件 */
    fclose(fp);

    return buffer;
}

/* ============================================================
 * sub_10010: 游戏初始化/存档加载函数中的FDTXT.DAT加载逻辑
 * 
 * 完整流程:
 *   1. 读取并解密FD2.SAV存档文件
 *   2. 校验存档完整性
 *   3. 从存档读取场景索引（偏移12485处）
 *   4. 根据场景索引加载对应的FDTXT.DAT资源
 * ============================================================ */
void sub_10010_load_fdtxt(void)
{
    FILE* fp;
    uint8_t* save_buffer;
    uint32_t checksum;

    /* 1. 分配存档缓冲区（22987字节） */
    save_buffer = (uint8_t*)malloc(22987);
    if (!save_buffer) {
        printf(" Out of Memory !!!\n");
        exit(1);
    }

    /* 2. 打开并读取存档文件 */
    fp = fopen("FD2.SAV", "rb");
    if (!fp) {
        /* 存档不存在，可能使用默认数据 */
        free(save_buffer);
        return;
    }
    fread(save_buffer, 1, 22987, fp);
    fclose(fp);

    /* 3. 解密存档数据（XOR滚动加密） */
    /* sub_4DF28(save_buffer, 22987); */

    /* 4. 校验存档完整性（求和校验） */
    /* checksum = sub_4DF09(save_buffer, 22987); */
    /* if (checksum != *(uint32_t*)(save_buffer + 22983)) {
     *     校验失败处理...
     * }
     */

    /* 5. 读取场景/地图索引（存档偏移12485处，1字节） */
    n17 = save_buffer[12485];

    /* 6. 【关键】加载FDTXT.DAT对应关卡的文本资源
     * 
     * 索引映射:
     *   索引0: 名字、技能、职业、法术等词组
     *   索引1: 第1关文本
     *   索引2: 第2关文本
     *   ...
     *   索引32: 第32关文本
     *   索引33: 开场第一个过场动画文本
     * 
     * 使用 n17 + 1 作为索引，因为:
     *   - n17 = 0 时加载索引1（第1关）
     *   - n17 = 1 时加载索引2（第2关）
     *   - ...
     *   - 索引0保留给默认词组
     */
    dword_53A79 = (int)sub_111BA("FDTXT.DAT", dword_53A79, n17 + 1);

    /* 7. 释放存档缓冲区 */
    free(save_buffer);
}

/* ============================================================
 * sub_1088D: 关卡切换时的FDTXT.DAT重新加载
 * 
 * 当玩家切换到新关卡时调用此函数重新加载对应的文本资源
 * ============================================================ */
void sub_1088D_reload_fdtxt(uint8_t new_level)
{
    /* new_level 是当前关卡编号 */
    
    /* 重新加载对应关卡的文本资源 */
    dword_53A79 = (int)sub_111BA("FDTXT.DAT", dword_53A79, new_level + 1);
}

/* ============================================================
 * 文本渲染函数sub_15F84的文本读取逻辑
 * 
 * 从FDTXT.DAT加载的数据结构中读取指定索引的文本
 * 
 * 参数:
 *   fdtxt_data - FDTXT.DAT数据块指针（dword_53A79或dword_53A7D）
 *   text_index - 文本项索引号
 * ============================================================ */
int16_t* get_text_pointer(int fdtxt_data, int text_index)
{
    int16_t* base = (int16_t*)fdtxt_data;
    
    /* 关键计算公式:
     * v15 = (__int16 *)(*(__int16 *)(arg0 + 2 * arg4) + arg0);
     * 
     * 分解:
     * 1. arg0 + 2 * arg4
     *    - 定位到偏移表中第text_index项（每项2字节）
     *    - 因为FDTXT.DAT的偏移表使用16位（2字节）偏移量
     * 
     * 2. *(__int16 *)(arg0 + 2 * arg4)
     *    - 读取该索引项的值（一个16位偏移量）
     * 
     * 3. + arg0
     *    - 相对偏移 + 基地址 = 文本块的绝对地址
     */
    int16_t offset = *(int16_t*)((uint8_t*)base + 2 * text_index);
    return (int16_t*)((uint8_t*)base + offset);
}

/* ============================================================
 * 文本项结构
 * 
 * 每个文本块是一个WORD（16位）数组:
 *   [字符/控制码][字符/控制码]...[-1]
 * ============================================================ */

/* 特殊控制字符定义 */
#define TEXT_END         -1   /* 0xFFFF: 文本块结束 */
#define TEXT_NEWLINE     -2   /* 0xFFFE: 换行 */
#define TEXT_NEWLINE2    -3   /* 0xFFFD: 换行+等待输入 */
#define TEXT_RECURSE1    -4   /* 0xFFFC: 递归显示dword_53AD9的文本 */
#define TEXT_RECURSE2    -5   /* 0xFFFB: 递归显示dword_53ADD的文本 */
#define TEXT_SHOW_NUM    -6   /* 0xFFFA: 显示数字变量dword_53AE1 */
#define TEXT_CHAR_F      -19  /* 0xFFED: 从dword_53A45加载角色头像(正面) */
#define TEXT_CHAR_S      -20  /* 0xFFEC: 从dword_53A45加载角色头像(侧面) */
#define TEXT_PORTRAIT_F  -17  /* 0xFFEF: 加载DATO.DAT头像(正面) */
#define TEXT_PORTRAIT_S  -18  /* 0xFFEE: 加载DATO.DAT头像(侧面) */

/* ============================================================
 * 测试代码
 * ============================================================ */
#ifdef TEST_FDTXT

int main(int argc, char* argv[])
{
    printf("=== FDTXT.DAT 加载测试 ===\n\n");

    /* 测试sub_111BA加载函数 */
    printf("1. 测试加载FDTXT.DAT索引0（词组）...\n");
    uint8_t* set0 = sub_111BA("FDTXT.DAT", 0, 0);
    if (set0) {
        printf("   加载成功，大小: %d 字节\n\n", dword_53BFF);
    }

    printf("2. 测试加载FDTXT.DAT索引1（第1关文本）...\n");
    uint8_t* set1 = sub_111BA("FDTXT.DAT", 0, 1);
    if (set1) {
        printf("   加载成功，大小: %d 字节\n\n", dword_53BFF);
    }

    /* 模拟存档加载流程 */
    printf("3. 模拟存档加载流程...\n");
    /* sub_10010_load_fdtxt(); */
    printf("   （需要FD2.SAV文件才能测试）\n\n");

    return 0;
}

#endif
