# Communication Protocol: OpenMV → C30D

[简体中文](../protocol.md) | **English**

## 1. Frame format

```text
AA 55 | TYPE | LEN | PAYLOAD ... | CRC8
```

- Multi-byte fields are **little-endian**.
- `CRC8`: polynomial `0x07` (reflected `0x8C`), initial value 0, covering `TYPE`, `LEN` and `PAYLOAD`.
- Maximum payload per frame: 16 bytes.

| TYPE | Name | Payload | Description |
|---|---|---|---|
| `0x01` | TARGET | `dx:int16, dy:int16, area:uint16, conf:uint8` | Offset from frame center, pixel area, confidence 0–100 |
| `0x02` | STATUS | `fps:uint8, mode:uint8` | Frame rate and mode, for debugging |
| `0x03` | CMD | `cmd:uint8` | Reserved: C30D → OpenMV (0x01 start tracking / 0x02 stop) |
| `0x05` | MULTI | `count:uint8, [dx:int16, dy:int16, area:uint16, conf:uint8, round:uint8] × count` | Multiple targets (up to 4); C30D chooses the most ball-like |
| `0x04` | POSITION | `dx:int16, dy:int16, dist_mm:uint16, angle_deg10:int16, conf:uint8` | Reserved: position frame; `angle_deg10` is angle × 10 |

`conf == 0` or `area == 0` means **no target**; C30D stops when it receives such a frame.

## 2. Example

Target 10 px right of center, area 1500 px, confidence 90:

```text
AA 55 01 07 0A 00 00 00 DC 05 5A 07
```

| Field | Value |
|---|---|
| dx | `0x000A` = 10 |
| dy | `0x0000` = 0 |
| area | `0x05DC` = 1500 |
| conf | `0x5A` = 90 |
| CRC | `0x07` |

## 3. Timing

- OpenMV sends TARGET at 20–25 Hz; when there is no target it keeps sending empty targets (`conf=0`).
- C30D `VISION_TIMEOUT_MS = 300`: if no valid frame arrives for 300 ms, all four wheel targets are cleared.
- STATUS is sent every 25 frames to help verify the link.

## 4. Relationship to the Bluetooth protocol

Bluetooth (USART2) remains responsible for manual driving and gear changes; vision uses UART4. They do not share a port.

- Send `V` over Bluetooth to enter/leave visual auto mode.
- In auto mode the direction keys are ignored (vision controls the chassis); send `V` again to return to manual.
- `X/Y` and `T/U` gear keys remain active; visual servo uses the current gear speed.

## 5. Multi-target selection (C30D side)

After receiving `0x05 MULTI`, the firmware scores each target:

```text
score = 0.45×conf + 0.30×round + 0.15×(area/max_area)×100 + 0.10×centering×100
```

- `conf`: confidence from OpenMV (0–100)
- `round`: circularity derived from edge sharpness (0–100)
- Larger area means closer; better centering is preferred
- The target with the highest `score` becomes the current ball; `TARGET(0x01)` remains compatible with single-target firmware

Control is turn-first: when the turn component exceeds `VISION_TURN_FIRST` (default 0.6), the car turns in place before approaching; after entering `NEAR_AREA`, it aligns in place and starts the blade.
