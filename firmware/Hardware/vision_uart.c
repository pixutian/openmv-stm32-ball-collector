/*
 * vision_uart.c
 * -----------------------------------------------------------------------------
 * UART4 驱动：PC10/PC11 复用为 AF8，115200 8N1，接收中断写入环形缓冲区。
 */

#include "vision_uart.h"
#include "board.h"

#define VISION_RX_SIZE  256

static volatile uint8_t  s_rx_buf[VISION_RX_SIZE];
static volatile uint16_t s_rx_head = 0;
static volatile uint16_t s_rx_tail = 0;

void vision_uart_init(uint32_t baud)
{
    GPIO_InitTypeDef gpio;
    USART_InitTypeDef usart;
    NVIC_InitTypeDef nvic;

    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_UART4, ENABLE);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource10, GPIO_AF_UART4);
    GPIO_PinAFConfig(GPIOC, GPIO_PinSource11, GPIO_AF_UART4);

    gpio.GPIO_Pin   = GPIO_Pin_10 | GPIO_Pin_11;
    gpio.GPIO_Mode  = GPIO_Mode_AF;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_PuPd  = GPIO_PuPd_UP;
    GPIO_Init(GPIOC, &gpio);

    USART_StructInit(&usart);
    usart.USART_BaudRate            = baud;
    usart.USART_WordLength          = USART_WordLength_8b;
    usart.USART_StopBits            = USART_StopBits_1;
    usart.USART_Parity              = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode                = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(UART4, &usart);

    USART_ITConfig(UART4, USART_IT_RXNE, ENABLE);

    nvic.NVIC_IRQChannel                   = UART4_IRQn;
    nvic.NVIC_IRQChannelPreemptionPriority = 5;
    nvic.NVIC_IRQChannelSubPriority        = 0;
    nvic.NVIC_IRQChannelCmd                = ENABLE;
    NVIC_Init(&nvic);

    USART_Cmd(UART4, ENABLE);
}

void UART4_IRQHandler(void)
{
    if (USART_GetITStatus(UART4, USART_IT_RXNE) != RESET) {
        uint8_t byte = (uint8_t)USART_ReceiveData(UART4);
        uint16_t next = (uint16_t)((s_rx_head + 1) % VISION_RX_SIZE);
        if (next != s_rx_tail) {          /* 满了就丢新字节 */
            s_rx_buf[s_rx_head] = byte;
            s_rx_head = next;
        }
        USART_ClearITPendingBit(UART4, USART_IT_RXNE);
    }
}

int vision_uart_read(uint8_t *byte)
{
    if (s_rx_tail == s_rx_head) {
        return 0;
    }
    *byte = s_rx_buf[s_rx_tail];
    s_rx_tail = (uint16_t)((s_rx_tail + 1) % VISION_RX_SIZE);
    return 1;
}
