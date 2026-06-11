/**
 * FD2 DAT文件加载 - 向后兼容层
 *
 * 所有DAT文件加载接口已统一到 fd2_dat_loader.h
 * 本头文件保留旧API作为别名(将被弃用)
 *
 * 新代码请使用 #include "fd2_dat_loader.h"
 */

#ifndef FD2_DAT_H
#define FD2_DAT_H

#include "fd2_dat_loader.h"

#ifdef __cplusplus
extern "C" {
#endif

/* 旧API别名 - @deprecated 使用 fd2_dat_loader.h 中的对应函数 */
#define fd2_load_dat_resource    fd2_dat_loader_load_resource
#define fd_load_palette          fd2_dat_loader_load_palette
#define fd_get_image_dimensions  fd2_dat_loader_get_dimensions

#ifdef __cplusplus
}
#endif

#endif /* FD2_DAT_H */
