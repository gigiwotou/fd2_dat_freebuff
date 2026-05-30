/*
 * FDOTHER.DAT 资源分析器
 * 
 * 从索引0开始逐个解析所有子资源，记录每个资源的详细资料并输出报告。
 * 
 * 编译: build.bat analyzer
 * 运行: bin\fd2_resource_analyzer.exe [game/FDOTHER.DAT]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef _WIN32
#include <direct.h>
#define mkdir(p, m) _mkdir(p)
#endif

#include "fd2_fdother_resources.h"

/* 资源类型名称 */
static const char* type_names[] = {
    "PALETTE",
    "TILE",
    "LMI1",
    "NESTED_DAT",
    "RAW"
};

/* 获取类型名称 */
static const char* get_type_name(fdother_res_type_t type) {
    if (type >= 0 && type <= 4) {
        return type_names[type];
    }
    return "UNKNOWN";
}

/* 获取资源描述 */
static const char* get_resource_desc(int index, fdother_res_type_t type) {
    switch (index) {
        case 0: return "主调色板";
        case 1: return "图标 24x24";
        case 2: return "原始数据 (字体?)";
        case 3: return "LMI1 Tile集 (23 tiles)";
        case 4: return "原始数据 (字符位图?)";
        case 5: return "LMI1 Tile集 (138 tiles)";
        case 6: return "LMI1 Tile集 (230 tiles)";
        case 7: return "嵌套DAT (38子资源)";
        case 8: return "调色板副本";
        case 9: return "LMI1 Tile集 (12 tiles)";
        case 10: return "图标 62x26";
        case 11: return "全屏图像 320x200 A";
        case 12: return "嵌套DAT (122子资源)";
        case 13: return "LMI1 Tile集 (28 tiles)";
        case 14: return "LMI1 Tile集 (32 tiles)";
        case 15: return "全屏图像 320x200 B";
        case 18: return "字符位图 16x16 A";
        case 19: return "字符位图 30x30 A";
        case 20: return "字符位图 16x16 B";
        case 21: return "字符位图 30x30 B";
        case 26: return "图标 18x18 (大数据)";
        case 29: return "LMI1 Tile集 (24 tiles)";
        case 31: return "音效DAT (62音效)";
        case 34: return "大图标 101x101";
        case 42: return "大图像 312x192";
        case 55: return "全屏图像 320x200 C";
        case 56: return "全屏图像 320x200 D";
        case 57: return "调色板副本";
        case 61: return "全屏图像 320x200 G";
        case 62: return "全屏图像 320x200 H";
        case 63: return "嵌套DAT (130子资源)";
        case 64: return "嵌套DAT (34子资源)";
        case 69: case 70: case 71: case 72: case 73: return "菜单图像 320x147";
        case 74: return "标题文字 320x200";
        case 75: return "全屏图像 320x200 I";
        case 76: return "标题画面调色板";
        case 77: return "嵌套DAT (26子资源)";
        case 78: return "嵌套DAT (14子资源)";
        case 80: return "嵌套DAT (74子资源)";
        case 96: return "图标 24x24 B";
        case 97: return "全屏图像 320x200 J";
        case 98: return "条形图像 155x30";
        case 99: return "调色板副本";
        case 100: return "全屏图像 320x200 K";
        case 101: return "调色板副本";
        case 102: return "调色板副本";
        default: return "";
    }
}

/* 分析单个资源 */
static void analyze_resource(int index, const byte* data, dword size, FILE* report_fp) {
    fdother_res_type_t type = fdother_get_resource_type(data, size);
    const char* desc = get_resource_desc(index, type);
    
    printf("Index %3d | Type: %-12s | Size: %6u bytes | %s\n", 
           index, get_type_name(type), size, desc);
    
    fprintf(report_fp, "Index %3d | Type: %-12s | Size: %6u bytes | %s\n", 
            index, get_type_name(type), size, desc);
    
    switch (type) {
        case FDOTHER_RES_TYPE_PALETTE: {
            fdother_palette_t pal;
            if (fdother_parse_palette(data, size, &pal) == 0) {
                printf("         -> 调色板: 256颜色, 前3色: (%d,%d,%d) (%d,%d,%d) (%d,%d,%d)\n",
                       pal.colors[0], pal.colors[1], pal.colors[2],
                       pal.colors[3], pal.colors[4], pal.colors[5],
                       pal.colors[6], pal.colors[7], pal.colors[8]);
                fprintf(report_fp, "         -> 调色板: 256颜色, 前3色: (%d,%d,%d) (%d,%d,%d) (%d,%d,%d)\n",
                        pal.colors[0], pal.colors[1], pal.colors[2],
                        pal.colors[3], pal.colors[4], pal.colors[5],
                        pal.colors[6], pal.colors[7], pal.colors[8]);
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_TILE: {
            fdother_tile_t tile;
            if (fdother_parse_tile(data, size, &tile) == 0) {
                printf("         -> Tile: %dx%d, 调色板窗口=%d, RLE数据=%u字节\n",
                       tile.width, tile.height, tile.palette_window, tile.rle_size);
                fprintf(report_fp, "         -> Tile: %dx%d, 调色板窗口=%d, RLE数据=%u字节\n",
                        tile.width, tile.height, tile.palette_window, tile.rle_size);
                
                byte* pixels = (byte*)malloc((size_t)tile.width * tile.height);
                if (pixels) {
                    int ret = fdother_decode_tile(&tile, pixels);
                    printf("         -> RLE解码: %s\n", ret == 0 ? "成功" : "失败");
                    fprintf(report_fp, "         -> RLE解码: %s\n", ret == 0 ? "成功" : "失败");
                    free(pixels);
                }
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_LMI1: {
            fdother_lmi1_t lmi1;
            if (fdother_parse_lmi1(data, size, &lmi1) == 0) {
                printf("         -> LMI1: %d tiles, 总大小=%u字节\n",
                       lmi1.tile_count, lmi1.size);
                fprintf(report_fp, "         -> LMI1: %d tiles, 总大小=%u字节\n",
                        lmi1.tile_count, lmi1.size);
                
                if (lmi1.tile_count > 0) {
                    word w, h;
                    const byte* rle_data;
                    dword rle_size;
                    if (fdother_lmi1_get_tile(&lmi1, 0, &w, &h, &rle_data, &rle_size) == 0) {
                        printf("         -> 第一个Tile: %dx%d, RLE=%u字节\n", w, h, rle_size);
                        fprintf(report_fp, "         -> 第一个Tile: %dx%d, RLE=%u字节\n", w, h, rle_size);
                    }
                }
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_NESTED_DAT: {
            fdother_nested_dat_t nested;
            if (fdother_parse_nested_dat(data, size, &nested) == 0) {
                printf("         -> 嵌套DAT: %d 子资源, 总大小=%u字节\n",
                       nested.resource_count, nested.size);
                fprintf(report_fp, "         -> 嵌套DAT: %d 子资源, 总大小=%u字节\n",
                        nested.resource_count, nested.size);
                
                int max_show = (int)nested.resource_count;
                if (max_show > 5) max_show = 5;
                for (int i = 0; i < max_show; i++) {
                    dword sub_size;
                    const byte* sub_data = fdother_nested_get_resource(&nested, i, &sub_size);
                    if (sub_data && sub_size < size) {
                        fdother_res_type_t sub_type = fdother_get_resource_type(sub_data, sub_size);
                        printf("         -> 子资源[%d]: 类型=%s, 大小=%u字节\n", 
                               i, get_type_name(sub_type), sub_size);
                        fprintf(report_fp, "         -> 子资源[%d]: 类型=%s, 大小=%u字节\n", 
                                i, get_type_name(sub_type), sub_size);
                    } else if (sub_data) {
                        printf("         -> 子资源[%d]: 大小异常 (%u字节)，标记为RAW\n", i, sub_size);
                        fprintf(report_fp, "         -> 子资源[%d]: 大小异常 (%u字节)，标记为RAW\n", i, sub_size);
                    }
                }
                if (nested.resource_count > 5) {
                    printf("         -> ... 还有 %d 个子资源\n", nested.resource_count - 5);
                    fprintf(report_fp, "         -> ... 还有 %d 个子资源\n", nested.resource_count - 5);
                }
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_RAW:
            printf("         -> RAW数据: %u字节\n", size);
            fprintf(report_fp, "         -> RAW数据: %u字节\n", size);
            break;
            
        default:
            break;
    }
    
    printf("\n");
    fprintf(report_fp, "\n");
}

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    
    if (argc > 1) {
        filepath = argv[1];
    }
    
    printf("===========================================\n");
    printf("  FDOTHER.DAT 资源分析器\n");
    printf("===========================================\n\n");
    printf("文件: %s\n\n", filepath);
    
    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("错误: 无法加载 FDOTHER.DAT\n");
        return 1;
    }
    
    FILE* report_fp = fopen("output/fdother_resource_report.txt", "w");
    if (!report_fp) {
        mkdir("output", 0755);
        report_fp = fopen("output/fdother_resource_report.txt", "w");
    }
    
    if (report_fp) {
        fprintf(report_fp, "===========================================\n");
        fprintf(report_fp, "  FDOTHER.DAT 资源分析报告\n");
        fprintf(report_fp, "===========================================\n\n");
        fprintf(report_fp, "文件: %s\n\n", filepath);
    }
    
    const byte* res0 = fdother_get_resource(0, NULL);
    if (!res0) {
        printf("错误: 无法获取资源0\n");
        return 1;
    }
    
    printf("开始分析所有资源...\n\n");
    
    for (int i = 0; i < 103; i++) {
        dword size;
        const byte* data = fdother_get_resource(i, &size);
        if (data && size > 0) {
            analyze_resource(i, data, size, report_fp);
        } else {
            printf("Index %3d | 无数据\n\n", i);
            if (report_fp) {
                fprintf(report_fp, "Index %3d | 无数据\n\n", i);
            }
        }
    }
    
    printf("===========================================\n");
    printf("  分析完成\n");
    printf("===========================================\n");
    
    if (report_fp) {
        fprintf(report_fp, "===========================================\n");
        fprintf(report_fp, "  分析完成\n");
        fprintf(report_fp, "===========================================\n");
        fclose(report_fp);
        printf("\n报告已保存: output/fdother_resource_report.txt\n");
    }
    
    fdother_unload();
    return 0;
}
