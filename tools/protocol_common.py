# -*- coding: utf-8 -*-
"""PC 侧协议实现（与 openmv/protocol.py 保持一致）

帧格式（小端）：
    AA 55 | TYPE | LEN | PAYLOAD... | CRC8

TYPE:
    0x01 TARGET    dx:int16, dy:int16, area:uint16, conf:uint8
    0x02 STATUS    fps:uint8, mode:uint8
    0x03 CMD       cmd:uint8      （C30D → OpenMV，可选）

CRC8: poly=0x07, init=0x00，覆盖 TYPE、LEN、PAYLOAD。
"""

import struct

HEAD0 = 0xAA
HEAD1 = 0x55

TYPE_TARGET = 0x01
TYPE_STATUS = 0x02
TYPE_CMD = 0x03


def crc8(data, init=0x00):
    crc = init
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc & 0xFF


def pack_frame(ftype, payload):
    body = bytes([ftype, len(payload)]) + bytes(payload)
    return bytes([HEAD0, HEAD1]) + body + bytes([crc8(body)])


def pack_target(dx, dy, area, conf):
    """dx/dy 为目标相对画面中心的像素偏移，area 为像素面积，conf 0~100。"""
    payload = struct.pack("<hhHB", int(dx), int(dy), int(area), int(conf))
    return pack_frame(TYPE_TARGET, payload)


def pack_status(fps, mode):
    return pack_frame(TYPE_STATUS, struct.pack("<BB", int(fps) & 0xFF, int(mode) & 0xFF))


def parse_frame(buf):
    """从字节串中找一帧，返回 (type, payload, rest) 或 (None, None, buf)。"""
    i = 0
    n = len(buf)
    while i + 5 <= n:
        if buf[i] != HEAD0 or buf[i + 1] != HEAD1:
            i += 1
            continue
        ftype = buf[i + 2]
        length = buf[i + 3]
        end = i + 4 + length
        if end + 1 > n:
            break
        body = buf[i + 2:end]
        if crc8(body) != buf[end]:
            i += 1
            continue
        return ftype, buf[i + 4:end], buf[end + 1:]
    return None, None, buf[i:]
