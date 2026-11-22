#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PC 侧协议模拟器：替代 OpenMV 向 C30D 发送目标帧。

用法：
    python3 protocol_sim.py /dev/ttyUSB0 --dx 0 --area 1500 --rate 20
    python3 protocol_sim.py COM5 --sweep          # 左右扫动，测试对准
    python3 protocol_sim.py --dry-run             # 只打印十六进制帧

依赖：pyserial（非 OpenMV 环境）。Windows 串口号如 COM5。
"""

import argparse
import math
import sys
import time

from protocol_common import pack_target, pack_status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port", nargs="?", help="串口，如 /dev/ttyUSB0 或 COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--dx", type=int, default=0, help="目标横向偏移（像素）")
    ap.add_argument("--dy", type=int, default=0)
    ap.add_argument("--area", type=int, default=1500)
    ap.add_argument("--conf", type=int, default=90)
    ap.add_argument("--rate", type=float, default=20.0)
    ap.add_argument("--sweep", action="store_true", help="dx 在 -120..120 之间扫动")
    ap.add_argument("--dry-run", action="store_true", help="只打印帧，不打开串口")
    args = ap.parse_args()

    if args.dry_run:
        frame = pack_target(args.dx, args.dy, args.area, args.conf)
        print(" ".join("%02X" % b for b in frame))
        return

    if not args.port:
        ap.error("需要串口名，或使用 --dry-run")

    try:
        import serial
    except ImportError:
        print("缺少 pyserial：pip install pyserial")
        sys.exit(2)

    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    period = 1.0 / max(1.0, args.rate)
    t0 = time.time()
    n = 0
    try:
        while True:
            if args.sweep:
                dx = int(120 * math.sin((time.time() - t0) * 1.2))
            else:
                dx = args.dx
            frame = pack_target(dx, args.dy, args.area, args.conf)
            ser.write(frame)
            n += 1
            if n % 25 == 0:
                ser.write(pack_status(args.rate, 1))
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    main()
