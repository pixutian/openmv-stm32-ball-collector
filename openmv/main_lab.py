# -*- coding: utf-8 -*-
"""OpenMV H7：白/黄乒乓球识别（圆形 + LAB 颜色）+ 多目标上报

这是 `main_circle_pos.py` 的 LAB 阈值版本：
  - 颜色判断不再用 RGB→HSV，而是把圆内平均 RGB 转成 LAB；
  - 白色：L 高、a/b 接近 0；黄色：b 明显为正、L 中高；
  - 其余逻辑（圆检测、边缘复核、多目标、位置、蓝灯、协议）保持一致。

LAB 说明（OpenMV）：
  L：0（黑）~ 100（白）
  a：绿(-) ~ 红(+)
  b：蓝(-) ~ 黄(+)

保存：Tools → Save open script to OpenMV Cam → main.py（或先存 main_lab.py 测试）
"""

import sensor
import image
import time
import math
from pyb import UART, LED

# ====================== 视觉识别参数（LAB 版） ======================
# 调参位置：本文件顶部；改完保存到 OpenMV 即可。
# 与 C30D 相关的转向/速度/中心带/搜索参数在 firmware/App/app_config.h。
# ===================================================================

IMG_W = 160                 # QQVGA
IMG_H = 120

# ---- 圆形检测（灰度副本上做） ----
CIRCLE_THRESHOLD = 2000     # 越大越严格；误检多 -> 2200~3000；漏检 -> 1600~2000
R_MIN = 4                   # 球的像素半径范围（远球小、近球大）
R_MAX = 22
R_STEP = 4                  # 越大越快越粗；卡顿 -> 6；求准 -> 2

# ---- LAB 颜色阈值 ----
# 白色球：L 高、a/b 都接近 0
# 光照偏黄时 b 可能偏大；反光强时 L 会更高
WHITE_L_MIN = 70.0          # 亮度下限（0~100）；认不到白球 -> 降到 60~65
WHITE_A_MAX = 10.0          # |a| 上限；色偏大 -> 放宽到 12~15
WHITE_B_MAX = 15.0          # |b| 上限；灯光偏黄 -> 放宽到 18~22

# 黄色球：b 明显为正（黄），L 中高，a 在红绿之间
YELLOW_L_MIN = 50.0         # 亮度下限；暗光 -> 降到 40~45
YELLOW_B_MIN = 20.0         # 黄色程度下限；认不到 -> 降到 15~18
YELLOW_A_MIN = -10.0        # a 下限（太绿会小于它）
YELLOW_A_MAX = 20.0         # a 上限（太红会大于它）

MIN_COLOR_SCORE = 25        # 颜色相似度低于此值不算球（0~100）

# 多目标排序权重
SORT_W_COLOR = 0.6
SORT_W_SHAPE = 0.4

# 圆内平均灰度下限：太暗的候选直接丢弃（0~255）；暗光可降到 40~50
MIN_GRAY_MEAN = 60

# ---- 边缘复核 ----
EDGE_MEAN_MIN = 8           # 漏检 -> 4~6；误检 -> 10~15
EDGE_CANNY = (50, 100)

MAX_TARGETS = 4             # 每帧最多上报几个球

# ---- 位置估计 ----
BALL_DIAMETER_MM = 40.0
FOCAL_PX = 160.0            # 标定：FOCAL_PX = 2*r*D/40

# ---- 串口 / LED ----
UART_ID = 3
UART_BAUD = 115200          # 与固件 VISION_BAUD 一致
PRINT_EVERY = 30
BLINK_PERIOD_MS = 2000      # 蓝灯：亮 1s + 灭 1s
BLINK_ON_MS = 1000
# -------------------------------------------------------------------


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
    conf = LAB 颜色相似度，round = 形状相似度
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
sensor.set_pixformat(sensor.RGB565)      # LAB 需要 RGB
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


def sample_rgb(img, cx, cy, r):
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


def color_score_lab(img, c):
    """返回 (类别, LAB 颜色相似度 0~100)。"""
    r, g, b = sample_rgb(img, c.x(), c.y(), c.r())
    l, a, bb = image.rgb_to_lab((r, g, b))

    # 白色：L 高、a/b 都接近 0
    if l >= WHITE_L_MIN and abs(a) <= WHITE_A_MAX and abs(bb) <= WHITE_B_MAX:
        s_l = (l - WHITE_L_MIN) / max(1.0, (100.0 - WHITE_L_MIN))
        s_a = 1.0 - abs(a) / WHITE_A_MAX
        s_b = 1.0 - abs(bb) / WHITE_B_MAX
        score = 100.0 * (0.5 * s_l + 0.25 * s_a + 0.25 * s_b)
        return 'white', int(max(0, min(100, score)))

    # 黄色：b 明显为正、L 中高、a 在范围内
    if (l >= YELLOW_L_MIN and bb >= YELLOW_B_MIN and
            YELLOW_A_MIN <= a <= YELLOW_A_MAX):
        s_l = min(1.0, l / 90.0)
        s_b = min(1.0, bb / 40.0)
        s_a = 1.0 - abs(a - 5.0) / 20.0
        if s_a < 0:
            s_a = 0
        score = 100.0 * (0.4 * s_b + 0.3 * s_l + 0.3 * s_a)
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

        kind, cscore = color_score_lab(img, c)
        if cscore < MIN_COLOR_SCORE:
            continue

        shape_score = min(100, int(edge_mean * 2.5))
        r_px = c.r()
        dx = (c.x() - IMG_W // 2) * 2
        dy = (c.y() - IMG_H // 2) * 2
        area = int(math.pi * r_px * r_px * 4)
        balls.append((dx, dy, area, cscore, shape_score, kind, c))

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
