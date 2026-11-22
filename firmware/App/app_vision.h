/*
 * app_vision.h
 * -----------------------------------------------------------------------------
 * 视觉自动收集：解析 OpenMV 目标帧，生成底盘差速目标与叶片开关。
 *
 * 模式切换：蓝牙收到 'V' 进入/退出自动模式（手动方向键仍然有效，退出后恢复）。
 * 安全：超过 VISION_TIMEOUT_MS 没有有效目标帧，四轮目标清零。
 */

#ifndef APP_VISION_H
#define APP_VISION_H

#include "stm32f4xx.h"

void vision_init(void);

/* 5 ms 控制节拍里调用：收帧 + 更新底盘目标 */
void vision_update(void);

void vision_toggle(void);
void vision_set_enabled(uint8_t on);
uint8_t vision_is_enabled(void);

/* 调试/显示用：最近一帧是否有效、目标面积 */
uint8_t vision_target_visible(void);
uint16_t vision_target_area(void);
uint8_t vision_target_count(void);

#endif /* APP_VISION_H */
