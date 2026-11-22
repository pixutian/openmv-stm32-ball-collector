# -*- coding: utf-8 -*-
"""OpenMV 视觉参数（按现场光照调整）"""

# 图像
IMG_W = 320
IMG_H = 240
FPS_TARGET = 25

# 乒乓球：白色高亮 + 圆形度过滤
# 灰度阈值下限太低会把地板/反光也算进来；先 200，再按现场调。
GRAY_THRESHOLD = (200, 255)
PIXELS_THRESHOLD = 120      # 最小像素面积
AREA_THRESHOLD = 120        # 最小外接矩形面积
MERGE = True

# 只处理画面下方区域（球在地面），可按安装角度调整
ROI = (0, 40, IMG_W, IMG_H - 40)

# 圆形度：4πA/P²，1.0 为完美圆；过滤长条反光
MIN_ROUNDNESS = 0.55

# 串口：OpenMV UART3，P4=TX、P5=RX，接 C30D UART4
UART_ID = 3
UART_BAUD = 115200

# 心跳
STATUS_EVERY_N = 25         # 每 25 帧发一次状态
