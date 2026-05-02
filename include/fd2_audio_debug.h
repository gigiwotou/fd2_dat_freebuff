/*
 * FD2 Audio Debug Patch
 * 在关键音频函数中添加调试输出，打印实际使用的参数
 */

#ifndef FD2_AUDIO_DEBUG_H
#define FD2_AUDIO_DEBUG_H

#include <stdio.h>
#include <stdint.h>

/* 在 Miles Sound System 包装函数中添加调试输出 */

/* 修改 AIL_init_sample (sub_414E0) 附近的代码 */
#define DEBUG_AUDIO_INIT 1
#define DEBUG_AUDIO_SET_RATE 1
#define DEBUG_AUDIO_SET_ADDR 1

/* 采样率设置调试输出 */
static inline void debug_set_sample_rate(void *hsample, int rate) {
    printf("[AUDIO DEBUG] AIL_set_sample_playback_rate: sample=%p, rate=%d Hz\n", 
           hsample, rate);
    fflush(stdout);
}

/* 样本地址设置调试输出 */
static inline void debug_set_sample_address(void *hsample, void *data, uint32_t size) {
    printf("[AUDIO DEBUG] AIL_set_sample_address: sample=%p, data=%p, size=%u\n", 
           hsample, data, size);
    printf("[AUDIO DEBUG]   Data header (first 16 bytes): ");
    if (data) {
        uint8_t *p = (uint8_t *)data;
        for (int i = 0; i < 16 && i < (int)size; i++) {
            printf("%02x ", p[i]);
        }
    }
    printf("\n");
    fflush(stdout);
}

/* 样本播放调试输出 */
static inline void debug_start_sample(void *hsample) {
    printf("[AUDIO DEBUG] AIL_start_sample: sample=%p\n", hsample);
    fflush(stdout);
}

/* 闪电音效播放调试 */
static inline void debug_lightning_sfx(void *fdother_data, int sample_index) {
    printf("[AUDIO DEBUG] Lightning SFX (sub_25A96): fdother=%p, index=%d\n", 
           fdother_data, sample_index);
    if (fdother_data) {
        uint32_t *header = (uint32_t *)fdother_data;
        printf("[AUDIO DEBUG]   res78[0]=0x%08x, [4]=0x%08x, [8]=0x%08x, [12]=0x%08x\n",
               header[0], header[1], header[2], header[3]);
    }
    fflush(stdout);
}

#endif /* FD2_AUDIO_DEBUG_H */
