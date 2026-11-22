/*
 * app_vision.c
 * -----------------------------------------------------------------------------
 * OpenMV 目标帧解析与视觉伺服。
 *
 * 帧：AA 55 | TYPE | LEN | PAYLOAD | CRC8
 *   TYPE 0x01 TARGET: dx:int16, dy:int16, area:uint16, conf:uint8（小端）
 *
 * 控制：dx 做差速对准，area 做接近/后退；conf==0 或超时则停车。
 */

#include "app_vision.h"
#include "app_config.h"
#include "app_chassis.h"
#include "vision_uart.h"
#include "motor.h"
#include "clock.h"

#include <math.h>

#define VISION_H0        0xAA
#define VISION_H1        0x55
#define VISION_TYPE_TARGET 0x01
#define VISION_PAYLOAD_MAX 64

typedef enum {
    PS_H0 = 0,
    PS_H1,
    PS_TYPE,
    PS_LEN,
    PS_PAYLOAD,
    PS_CRC
} parse_state_t;

static parse_state_t s_state = PS_H0;
static uint8_t  s_type;
static uint8_t  s_len;
static uint8_t  s_idx;
static uint8_t  s_crc;
static uint8_t  s_payload[VISION_PAYLOAD_MAX];

static uint8_t  s_enabled;
static uint8_t  s_has_target;
static int16_t  s_dx;
static int16_t  s_dy;
static uint16_t s_area;
static uint8_t  s_conf;
static uint8_t  s_round;
static uint8_t  s_count;
static float    s_score;
static float    s_speed = VISION_SPEED_BASE;
static uint32_t s_last_tick;
static float    s_last_left;
static float    s_last_right;
static uint32_t s_lost_tick;
static uint8_t  s_tracking;
static uint8_t  s_search_state;   /* 0 正常, 1 旋转, 2 暂停, 3 休息 */
static uint8_t  s_search_step;
static uint32_t s_search_tick;
static uint32_t s_no_target_since;
static uint8_t  s_search_done;

/* 反射式 CRC8：poly 0x07（0x8C 反向），与 OpenMV 端一致 */
static uint8_t crc8_update(uint8_t crc, uint8_t byte)
{
    uint8_t i;
    crc ^= byte;
    for (i = 0; i < 8; i++) {
        if (crc & 0x01) {
            crc = (uint8_t)((crc >> 1) ^ 0x8C);
        } else {
            crc >>= 1;
        }
    }
    return crc;
}

typedef struct {
    int16_t  dx;
    int16_t  dy;
    uint16_t area;
    uint8_t  conf;
    uint8_t  round;
    float    score;
} vision_target_t;

static float score_target(const vision_target_t *t, uint16_t max_area)
{
    float area_norm = (max_area > 0) ? ((float)t->area / (float)max_area) : 0.0f;
    float center = 1.0f - fabsf((float)t->dx) / VISION_CENTER_PX;
    float score;

    if (center < 0.0f) center = 0.0f;

    score = VISION_W_CONF  * (float)t->conf
          + VISION_W_ROUND * (float)t->round
          + VISION_W_AREA  * area_norm * 100.0f
          + VISION_W_CENTER * center * 100.0f;
    return score;
}

static void select_best(const vision_target_t *list, uint8_t n)
{
    uint16_t max_area = 0;
    uint8_t  i;
    uint8_t  best = 0;
    float    best_score = -1.0f;

    s_count = n;
    s_has_target = 0;
    if (n == 0) {
        return;
    }

    for (i = 0; i < n; i++) {
        if (list[i].area > max_area) max_area = list[i].area;
    }
    for (i = 0; i < n; i++) {
        float sc = score_target(&list[i], max_area);
        if (sc > best_score) {
            best_score = sc;
            best = i;
        }
    }

    s_dx    = list[best].dx;
    s_dy    = list[best].dy;
    s_area  = list[best].area;
    s_conf  = list[best].conf;
    s_round = list[best].round;
    s_score = best_score;
    s_has_target = (uint8_t)((list[best].conf > 0) && (list[best].area > 0));
    s_last_tick = tick_ms();
}

static void handle_frame(uint8_t type, const uint8_t *p, uint8_t len)
{
    vision_target_t list[VISION_MAX_TARGETS];
    uint8_t n = 0;
    uint8_t i;

    if (type == VISION_TYPE_TARGET) {
        if (len < 7) return;
        list[0].dx    = (int16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
        list[0].dy    = (int16_t)((uint16_t)p[2] | ((uint16_t)p[3] << 8));
        list[0].area  = (uint16_t)((uint16_t)p[4] | ((uint16_t)p[5] << 8));
        list[0].conf  = p[6];
        list[0].round = p[6];          /* 单目标没有圆度字段，用 conf 代替 */
        select_best(list, 1);
        return;
    }

    if (type == 0x05 && len >= 1) {
        n = p[0];
        if (n > VISION_MAX_TARGETS) n = VISION_MAX_TARGETS;
        if ((uint8_t)(1 + n * 8) > len) {
            /* 载荷不够就按实际长度截断 */
            n = (uint8_t)((len - 1) / 8);
        }
        for (i = 0; i < n; i++) {
            const uint8_t *q = &p[1 + i * 8];
            list[i].dx    = (int16_t)((uint16_t)q[0] | ((uint16_t)q[1] << 8));
            list[i].dy    = (int16_t)((uint16_t)q[2] | ((uint16_t)q[3] << 8));
            list[i].area  = (uint16_t)((uint16_t)q[4] | ((uint16_t)q[5] << 8));
            list[i].conf  = q[6];
            list[i].round = q[7];
        }
        select_best(list, n);
    }
}

static void parse_byte(uint8_t b)
{
    switch (s_state) {
        case PS_H0:
            if (b == VISION_H0) s_state = PS_H1;
            break;
        case PS_H1:
            if (b == VISION_H1) {
                s_state = PS_TYPE;
            } else if (b != VISION_H0) {
                s_state = PS_H0;
            }
            break;
        case PS_TYPE:
            s_type = b;
            s_crc = crc8_update(0, b);
            s_state = PS_LEN;
            break;
        case PS_LEN:
            s_len = b;
            s_crc = crc8_update(s_crc, b);
            s_idx = 0;
            if (s_len > VISION_PAYLOAD_MAX) {
                s_state = PS_H0;
            } else {
                s_state = (s_len == 0) ? PS_CRC : PS_PAYLOAD;
            }
            break;
        case PS_PAYLOAD:
            s_payload[s_idx++] = b;
            s_crc = crc8_update(s_crc, b);
            if (s_idx >= s_len) s_state = PS_CRC;
            break;
        case PS_CRC:
            if (b == s_crc) {
                handle_frame(s_type, s_payload, s_len);
            }
            s_state = PS_H0;
            break;
        default:
            s_state = PS_H0;
            break;
    }
}

void vision_init(void)
{
    vision_uart_init(VISION_BAUD);
    s_enabled = 0;
    s_has_target = 0;
    s_state = PS_H0;
}

void vision_set_enabled(uint8_t on)
{
    if (on == s_enabled) {
        return;
    }
    s_enabled = on;

    if (on) {
        s_has_target = 0;
        s_last_tick = tick_ms();
        s_speed = VISION_SPEED_BASE;
        s_tracking = 0;
        s_lost_tick = 0;
        s_search_state = 0;
        s_search_step = 0;
        s_search_done = 0;
        s_no_target_since = tick_ms();
    } else {
        s_tracking = 0;
        s_lost_tick = 0;
        s_search_state = 0;
        s_search_step = 0;
        s_search_done = 0;
        s_no_target_since = 0;
        chassis_clear_external();
    }
}

void vision_toggle(void)
{
    vision_set_enabled((uint8_t)!s_enabled);
}

uint8_t vision_is_enabled(void)
{
    return s_enabled;
}

uint8_t vision_target_visible(void)
{
    return s_has_target;
}

uint8_t vision_target_count(void)
{
    return s_count;
}

uint16_t vision_target_area(void)
{
    return s_area;
}

static float clampf(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

void vision_update(void)
{
    uint8_t b;
    uint32_t now;
    uint8_t has_target;

    while (vision_uart_read(&b)) {
        parse_byte(b);
    }

    if (!s_enabled) {
        return;
    }

    now = tick_ms();
    has_target = (uint8_t)(s_has_target &&
                           ((uint32_t)(now - s_last_tick) <= VISION_TIMEOUT_MS));

    /* ================= 有球：正常收集 ================= */
    if (has_target) {
        float step = VISION_SPEED_RAMP * 0.005f;
        float turn;
        float left;
        float right;

        s_search_state = 0;
        s_search_step = 0;
        s_search_done = 0;
        s_no_target_since = 0;

        if (s_speed < VISION_SPEED_TRACK) {
            s_speed += step;
            if (s_speed > VISION_SPEED_TRACK) s_speed = VISION_SPEED_TRACK;
        }

        turn = s_speed * VISION_TURN_RATE;

        if (s_area > VISION_STOP_AREA) {
            left = right = -s_speed * VISION_BACKOFF_RATIO;
        } else if (s_dx < -VISION_BAND_PX) {
            left = -turn;
            right = turn;
        } else if (s_dx > VISION_BAND_PX) {
            left = turn;
            right = -turn;
        } else {
            left = right = s_speed;
        }

        chassis_set_external(left, right);

        s_last_left = left;
        s_last_right = right;
        s_tracking = 1;
        s_lost_tick = 0;
        return;
    }

    /* ================= 没有球 ================= */
    if (s_search_state == 0) {
        /* 1) 丢球续行：保持最后一次目标 */
        if (s_tracking && (VISION_LOST_HOLD_MS > 0)) {
            if (s_lost_tick == 0) {
                s_lost_tick = now;
            }
            if ((uint32_t)(now - s_lost_tick) < VISION_LOST_HOLD_MS) {
                chassis_set_external(s_last_left, s_last_right);
                return;
            }
        }

        s_tracking = 0;
        s_lost_tick = 0;
        chassis_set_external(0.0f, 0.0f);
        s_speed = VISION_SPEED_BASE;

        /* 2) 长时间没球 -> 进入搜索 */
        if (s_no_target_since == 0) {
            s_no_target_since = now;
        }
        if ((!s_search_done) &&
            ((uint32_t)(now - s_no_target_since) >= VISION_SEARCH_AFTER_MS)) {
            s_search_state = 1;
            s_search_step = 0;
            s_search_tick = now;
        }
        return;
    }

    /* 状态 1：原地慢速旋转（左轮后退、右轮前进 = 左转） */
    if (s_search_state == 1) {
        if ((uint32_t)(now - s_search_tick) >= VISION_SEARCH_60_MS) {
            s_search_state = 2;
            s_search_tick = now;
            chassis_set_external(0.0f, 0.0f);
        } else {
            chassis_set_external(-VISION_SEARCH_SPEED, VISION_SEARCH_SPEED);
        }
        return;
    }

    /* 状态 2：停 3s，然后进入下一段 60° */
    if (s_search_state == 2) {
        chassis_set_external(0.0f, 0.0f);
        if ((uint32_t)(now - s_search_tick) >= VISION_SEARCH_PAUSE_MS) {
            s_search_step++;
            if (s_search_step >= VISION_SEARCH_STEPS) {
                s_search_state = 3;      /* 360° 转完，休息 */
                s_search_done = 1;
                s_search_tick = now;
            } else {
                s_search_state = 1;
                s_search_tick = now;
            }
        }
        return;
    }

    /* 状态 3：转完仍无球 -> 原地休息（正常工作，不运动） */
    chassis_set_external(0.0f, 0.0f);
}
