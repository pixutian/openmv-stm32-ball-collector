/*
 * vision_uart.h
 * -----------------------------------------------------------------------------
 * OpenMV 视觉串口：UART4（PC10 = TX，PC11 = RX），115200 8N1。
 *
 * 接线（与 OpenMV H7）：
 *   C30D PC11 (UART4_RX) <- OpenMV P4 (UART3_TX)
 *   C30D PC10 (UART4_TX) -> OpenMV P5 (UART3_RX)
 *   GND <-> GND
 *   C30D 5V -> OpenMV VIN
 */

#ifndef VISION_UART_H
#define VISION_UART_H

#include "stm32f4xx.h"

void vision_uart_init(uint32_t baud);

/* 从环形缓冲区取一个字节：1=取到，0=空 */
int vision_uart_read(uint8_t *byte);

#endif /* VISION_UART_H */
