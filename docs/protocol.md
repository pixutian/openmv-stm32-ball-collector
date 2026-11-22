# 通信协议：OpenMV → C30D

## 1. 帧格式

```
AA 55 | TYPE | LEN | PAYLOAD ... | CRC8
```

- 多字节字段为**小端**
- `CRC8`：多项式 `0x07`（反射实现 `0x8C`），初值 0，覆盖 `TYPE`、`LEN`、`PAYLOAD`
- 单帧最大载荷 16 字节

| TYPE | 名称 | 载荷 | 说明 |
|---|---|---|---|
| `0x01` | TARGET | `dx:int16, dy:int16, area:uint16, conf:uint8` | 目标相对画面中心的偏移、像素面积、置信度 0–100 |
| `0x02` | STATUS | `fps:uint8, mode:uint8` | 帧率与模式，调试用 |
| `0x03` | CMD | `cmd:uint8` | 预留：C30D → OpenMV（0x01 开始追踪 / 0x02 停止） |
| `0x05` | MULTI | `count:uint8, [dx:int16, dy:int16, area:uint16, conf:uint8, round:uint8] × count` | 多目标（最多 4 个），C30D 选“最像球” |
| `0x04` | POSITION | `dx:int16, dy:int16, dist_mm:uint16, angle_deg10:int16, conf:uint8` | 预留：位置帧，`angle_deg10` 为角度×10 |

`conf == 0` 或 `area == 0` 表示**当前没有目标**；C30D 收到后停车。

## 2. 示例

目标在中心右侧 10 px、面积 1500 px、置信度 90：

```
AA 55 01 07 0A 00 00 00 DC 05 5A 07
```

| 字段 | 值 |
|---|---|
| dx | `0x000A` = 10 |
| dy | `0x0000` = 0 |
| area | `0x05DC` = 1500 |
| conf | `0x5A` = 90 |
| CRC | `0x07` |

## 3. 时序

- OpenMV 以 20–25 Hz 发送 TARGET；无目标时也持续发送空目标（conf=0）
- C30D 侧 `VISION_TIMEOUT_MS = 300`：超过 300 ms 没有有效帧 → 四轮目标清零
- 每 25 帧发一次 STATUS，便于确认链路

## 4. 与蓝牙协议的关系

蓝牙（USART2）继续负责手动遥控与档位；视觉走 UART4，两者互不占用。

- 蓝牙发 `V`：进入/退出视觉自动模式
- 自动模式下方向键不生效（视觉接管底盘），按 `V` 退出后恢复手动
- `X/Y`、`T/U` 档位键仍有效，视觉伺服用当前档位速度


## 5. 多目标选择（C30D 侧）

收到 `0x05 MULTI` 后，固件对每个目标评分：

```
score = 0.45×conf + 0.30×round + 0.15×(area/最大面积)×100 + 0.10×居中程度×100
```

- `conf`：OpenMV 给的置信度（0–100）
- `round`：边缘清晰度换算的“圆度”（0–100）
- 面积越大越近，居中程度越高越优先
- 取 `score` 最大的目标作为当前球；`TARGET(0x01)` 仍兼容单目标固件

控制上采用“转向优先”：转向分量超过 `VISION_TURN_FIRST`（默认 0.6）时先原地转正，
再向前接近；进入 `NEAR_AREA` 后原地对准并开叶片。
