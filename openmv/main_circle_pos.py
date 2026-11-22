# -*- coding: utf-8 -*-
"""OpenMV H7 白/黄乒乓球识别（圆形 + 颜色）+ 多目标上报

识别逻辑：
  1) 灰度图上做霍夫圆，得到候选球；
  2) 在圆内采样 RGB，转 HSV，判断白色/黄色，得到“颜色相似度”；
  3) 用边缘清晰度得到“形状相似度”；
  4) 多球按 颜色×0.6 + 形状×0.4 排序，最多上报 4 个；
  5) C30D 侧再按权重选“最像球”并控制底盘。

接线（不变）：
  OpenMV P4 (UART3_TX) -> C30D PC11 (UART4_RX)
  OpenMV P5 (UART3_RX) -> C30D PC10 (UART4_TX)
  GND <-> GND ; VIN <- 5V

保存：Tools → Save open script to OpenMV Cam → main.py
"""

import sensor
import image
import time
import math
from pyb import UART, LED

# ====================== 视觉识别参数（OpenMV 侧） ======================
# 调参位置：本文件顶部；改完保存到 OpenMV 即可，不需要动 C30D。
# 与 C30D 相关的“转向/速度/中心带/丢球续行”参数在 firmware/App/app_config.h。
# =====================================================================

# 图像分辨率：QQVGA = 160x120（RGB565 用于颜色，灰度副本用于圆检测）
IMG_W = 160
IMG_H = 120

# ---- 圆形检测（在灰度图上做） ----
# 霍夫圆累加器阈值：越大越严格；误检多 -> 2200~3000；漏检 -> 1600~2000
CIRCLE_THRESHOLD = 2000
# 球在画面里的半径范围（像素）：远球小、近球大
R_MIN = 4
R_MAX = 22
# 霍夫圆搜索步长：越大越快越粗；卡顿/断连 -> 6；求准 -> 2
R_STEP = 4

# ---- 颜色识别（HSV） ----
# 白色球：饱和度低、亮度高
WHITE_S_MAX = 0.28          # S 上限（0~1），越小越“纯白”
WHITE_V_MIN = 0.60          # V 下限（0~1），低于此认为太暗

# 黄色球：色相在黄区、饱和度/亮度足够
YELLOW_H_MIN = 35.0         # 色相下限（度，0~360）
YELLOW_H_MAX = 70.0         # 色相上限（度）
YELLOW_S_MIN = 0.35         # 饱和度下限（0~1）
YELLOW_V_MIN = 0.45         # 亮度下限（0~1）

# 颜色相似度低于该值就不算“球”（避免把灰/棕/杂色当球）
MIN_COLOR_SCORE = 25        # 0~100

# 多目标排序权重：颜色相似度 / 形状相似度
SORT_W_COLOR = 0.6
SORT_W_SHAPE = 0.4

# 圆内平均灰度下限：太暗的候选直接丢弃（0~255）；暗光可降到 40~50
MIN_GRAY_MEAN = 60

# ---- 边缘复核 ----
EDGE_MEAN_MIN = 8           # 圆内 Canny 平均灰度下限；漏检->4~6；误检->10~15
EDGE_CANNY = (50, 100)      # Canny 双阈值 (低, 高)

# 每帧最多上报几个球（C30D 再选“最像”）
MAX_TARGETS = 4

# ---- 位置估计 ----
BALL_DIAMETER_MM = 40.0
FOCAL_PX = 160.0            # 标定：FOCAL_PX = 2*r*D/40

# ---- 串口 / LED ----
UART_ID = 3
UART_BAUD = 115200          # 必须与固件 VISION_BAUD 一致
PRINT_EVERY = 30
BLINK_PERIOD_MS = 2000      # 蓝灯：亮 1s + 灭 1s
BLINK_ON_MS = 1000
# ---------------------------------------------------------------------


def crc8(data, crc=0):
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8C if (crc & 0x01) else (crc >> 1)
    return crc & 0xFF


def _frame(ftype, payload):
    body = bytes([ftype, len(payload)]) + payload
    return bytes([0xAA, 0x55]) + body + bytes([crc8(body)])


def pack_target(dx, dy, area, conf):
    p = bytes([
        dx & 0xFF, (dx >> 8) & 0xFF,
        dy & 0xFF, (dy >> 8) & 0xFF,
        area & 0xFF, (area >> 8) & 0xFF,
        conf & 0xFF,
    ])
    return _frame(0x01, p)


def pack_multi(items):
    """items: [(dx,dy,area,conf,round), ...]
    conf = 颜色相似度（0~100），round = 形状相似度（0~100）
    载荷：count(1) + 每个目标 8 字节
    """
    payload = bytes([len(items) & 0xFF])
    for dx, dy, area, conf, rnd in items[:MAX_TARGETS]:
        payload += bytes([
            dx & 0xFF, (dx >> 8) & 0xFF,
            dy & 0xFF, (dy >> 8) & 0xFF,
            area & 0xFF, (area >> 8) & 0xFF,
            conf & 0xFF, rnd & 0xFF,
        ])
    return _frame(0x05, payload)


def pack_status(fps, mode):
    return _frame(0x02, bytes([int(fps) & 0xFF, int(mode) & 0xFF]))


sensor.reset()
sensor.set_pixformat(sensor.RGB565)      # 颜色识别需要 RGB
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=600)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

uart = UART(UART_ID, UART_BAUD, timeout_char=50)
blue = LED(3)
clock = time.clock()
frame_id = 0
rxbuf = b""

blink_last = time.ticks_ms() - BLINK_PERIOD_MS
blink_off_at = 0


def service_led(has_ball):
    """有球：亮 1s、灭 1s 循环；无球：熄灭。"""
    global blink_last, blink_off_at
    now = time.ticks_ms()

    if not has_ball:
        blue.off()
        blink_off_at = 0
        return

    if blink_off_at and time.ticks_diff(now, blink_off_at) >= 0:
        blue.off()
        blink_off_at = 0

    if time.ticks_diff(now, blink_last) >= BLINK_PERIOD_MS:
        blue.on()
        blink_last = now
        blink_off_at = now + BLINK_ON_MS


def rgb_to_hsv(r, g, b):
    """r/g/b: 0~255 -> h(0~360), s(0~1), v(0~1)"""
    rf = r / 255.0
    gf = g / 255.0
    bf = b / 255.0
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    d = mx - mn

    if d == 0:
        h = 0.0
    elif mx == rf:
        h = ((gf - bf) / d) % 6.0
    elif mx == gf:
        h = (bf - rf) / d + 2.0
    else:
        h = (rf - gf) / d + 4.0
    h *= 60.0
    s = 0.0 if mx == 0 else d / mx
    return h, s, mx


def sample_rgb(img, cx, cy, r):
    """圆内取 5 个点求平均 RGB（避开边缘）。"""
    pts = [(cx, cy)]
    d = max(1, int(r * 0.5))
    pts += [(cx + d, cy), (cx - d, cy), (cx, cy + d), (cx, cy - d)]
    rs = gs = bs = 0
    n = 0
    for x, y in pts:
        if x < 0 or y < 0 or x >= IMG_W or y >= IMG_H:
            continue
        p = img.get_pixel(x, y)
        rs += p[0]
        gs += p[1]
        bs += p[2]
        n += 1
    if n == 0:
        return 0, 0, 0
    return rs // n, gs // n, bs // n


def color_score(img, c):
    """返回 (类别, 颜色相似度 0~100)；类别 'white'/'yellow'/'unknown'"""
    r, g, b = sample_rgb(img, c.x(), c.y(), c.r())
    h, s, v = rgb_to_hsv(r, g, b)

    # 白色：低饱和、高亮度
    if s <= WHITE_S_MAX and v >= WHITE_V_MIN:
        score = 100.0 * (1.0 - s / WHITE_S_MAX) * min(1.0, v / 0.9)
        return 'white', int(max(0, min(100, score)))

    # 黄色：色相在 [YELLOW_H_MIN, YELLOW_H_MAX]
    if YELLOW_H_MIN <= h <= YELLOW_H_MAX and s >= YELLOW_S_MIN and v >= YELLOW_V_MIN:
        hc = (YELLOW_H_MIN + YELLOW_H_MAX) / 2.0
        half = (YELLOW_H_MAX - YELLOW_H_MIN) / 2.0
        dh = abs(h - hc) / half if half > 0 else 0.0
        score = 100.0 * (1.0 - 0.5 * dh) * min(1.0, s / 0.6) * min(1.0, v / 0.7)
        return 'yellow', int(max(0, min(100, score)))

    return 'unknown', 0


def circle_rect(c):
    try:
        return c.roi()
    except Exception:
        return (c.x() - c.r(), c.y() - c.r(), 2 * c.r(), 2 * c.r())


def detect_balls(img, gray):
    edge_img = gray.copy()
    try:
        edge_img.find_edges(image.EDGE_CANNY, threshold=EDGE_CANNY)
    except Exception:
        edge_img = None

    circles = gray.find_circles(
        threshold=CIRCLE_THRESHOLD,
        x_margin=8,
        y_margin=8,
        r_margin=10,
        r_min=R_MIN,
        r_max=R_MAX,
        r_step=R_STEP,
    )

    balls = []
    for c in circles:
        if c.y() < 15:
            continue
        rect = circle_rect(c)
        try:
            if gray.get_statistics(roi=rect).mean() < MIN_GRAY_MEAN:
                continue
            edge_mean = 0.0
            if edge_img is not None:
                edge_mean = edge_img.get_statistics(roi=rect).mean()
        except Exception:
            continue
        if edge_img is not None and edge_mean < EDGE_MEAN_MIN:
            continue

        kind, cscore = color_score(img, c)
        if cscore < MIN_COLOR_SCORE:
            continue

        shape_score = min(100, int(edge_mean * 2.5))
        r_px = c.r()
        dx = (c.x() - IMG_W // 2) * 2
        dy = (c.y() - IMG_H // 2) * 2
        area = int(math.pi * r_px * r_px * 4)
        balls.append((dx, dy, area, cscore, shape_score, kind, c))

    # 按“颜色×0.6 + 形状×0.4”排序，保留最像的 MAX_TARGETS 个
    balls.sort(key=lambda b: b[3] * SORT_W_COLOR + b[4] * SORT_W_SHAPE, reverse=True)
    return balls


def handle_command(cmd):
    """C30D -> OpenMV（预留）：0x01 开始追踪 / 0x02 停止。"""
    pass


def poll_uart():
    global rxbuf
    n = uart.any()
    if not n:
        return
    rxbuf += uart.read(n)
    while True:
        i = rxbuf.find(b"\xAA\x55")
        if i < 0:
            rxbuf = rxbuf[-1:]
            return
        rxbuf = rxbuf[i:]
        if len(rxbuf) < 5:
            return
        ftype = rxbuf[2]
        length = rxbuf[3]
        if len(rxbuf) < 5 + length:
            return
        body = rxbuf[2:4 + length]
        if crc8(body) != rxbuf[4 + length]:
            rxbuf = rxbuf[1:]
            continue
        payload = rxbuf[4:4 + length]
        if ftype == 0x03 and len(payload) >= 1:
            handle_command(payload[0])
        rxbuf = rxbuf[5 + length:]


while True:
    clock.tick()
    img = sensor.snapshot()
    gray = img.to_grayscale(copy=True)
    frame_id += 1

    poll_uart()

    balls = detect_balls(img, gray)
    service_led(len(balls) > 0)

    if balls:
        # 先发单目标（兼容旧固件），再发多目标（C30D 选“最像”）
        b = balls[0]
        uart.write(pack_target(b[0], b[1], b[2], b[3]))
        uart.write(pack_multi([(b[0], b[1], b[2], b[3], b[4]) for b in balls]))

        for dx, dy, area, cscore, sscore, kind, c in balls:
            img.draw_circle(c.x(), c.y(), c.r(), color=(255, 255, 255), thickness=2)
            img.draw_string(c.x() - 3, c.y() - 4,
                            "W" if kind == 'white' else ("Y" if kind == 'yellow' else "?"),
                            color=(255, 255, 255))

        c = balls[0][6]
        r_px = c.r()
        dist_mm = int(BALL_DIAMETER_MM * FOCAL_PX / (2.0 * r_px))
        img.draw_cross(c.x(), c.y(), color=(255, 255, 255))
        img.draw_string(2, 2, "N:%d D:%d" % (len(balls), dist_mm), color=(255, 255, 255))
    else:
        uart.write(pack_multi([]))
        uart.write(pack_target(0, 0, 0, 0))

    if frame_id % PRINT_EVERY == 0:
        print("fps=%.1f n=%d" % (clock.fps(), len(balls)))

    time.sleep_ms(5)
