# 视觉伺服与控制策略

[English](en/control.md) | **简体中文**

## 1. 模式

- 上电默认**手动模式**：蓝牙方向键/摇杆控制，视觉只接收不使用。
- 切换方式（每按一次依次切换，互相同步同一状态）：
  - 蓝牙发送 `V`；
  - 或按一下 **C30D 板上的 USER 按键**（PE0），蜂鸣器短鸣一声提示。
- 自动模式下方向键被视觉接管（不生效），档位键 `X/Y`、叶片键 `T/U` 仍有效。

## 2. 控制量

OpenMV 每帧给出：

- `dx`：目标中心相对画面中心的横向像素偏差（右为正）
- `area`：目标像素面积，近似反映距离（越大越近）
- `conf`：置信度，0 表示无目标

C30D 侧（`app_vision.c`）：

```c
turn = speed * VISION_TURN_KP * (dx / VISION_CENTER_PX);
base = 0;
if (area < VISION_NEAR_AREA)      base =  speed * VISION_APPROACH_RATIO;  /* 接近 */
else if (area > VISION_STOP_AREA) base = -speed * VISION_BACKOFF_RATIO;   /* 太近后退 */
left  = base + turn;
right = base - turn;
```

- `dx > 0`（目标在右）→ 左轮加速、右轮减速，车向右转
- 进入 `[NEAR_AREA, STOP_AREA]` 后 `base = 0`，只做原地对准
- `area ≥ NEAR_AREA` 时叶片开到 100%，离开则停

## 3. 参数

| 参数 | 默认 | 位置 | 说明 |
|---|---|---|---|
| `VISION_TIMEOUT_MS` | 300 | `app_config.h` | 无帧超时停车 |
| `VISION_CENTER_PX` | 160 | `app_config.h` | QVGA 320 宽的中心 |
| `VISION_TURN_KP` | 0.9 | `app_config.h` | 转向增益，越大越灵敏 |
| `VISION_APPROACH_RATIO` | 0.6 | `app_config.h` | 接近速度占档位比例 |
| `VISION_BACKOFF_RATIO` | 0.4 | `app_config.h` | 后退比例 |
| `VISION_NEAR_AREA` | 1500 | `app_config.h` | 进入收集区面积 |
| `VISION_STOP_AREA` | 4000 | `app_config.h` | 过大后退面积 |

## 4. 调试顺序

1. **架空车轮**，手动模式确认八方向与停止正常。
2. 接 OpenMV，确认 `{A...}` 之外能看到视觉帧（在 `app_vision.c` 的 `handle_frame` 打断点或临时点灯）。
3. 蓝牙发 `V`，把球放在正前方 50 cm，观察车是否转向对准、缓慢接近。
4. 调 `VISION_TURN_KP`：左右摆动就减小，反应迟钝就增大。
5. 调 `VISION_NEAR_AREA / STOP_AREA`：用实际球在 30/50/80 cm 处的 `area` 值确定。
6. 落地低速测试；先确认“看不到球会停”，再试连续收球。

## 5. 安全

- 超时 300 ms 自动停车；蓝牙断开不影响该逻辑。
- 叶片在进入收集区才开，退出即停；但仍建议调试时先断开叶片电源。
- 自动模式没有避障/防跌落，必须在平整、封闭场地测试。
- 任何时候可发 `V` 退出自动，或直接断电。

## 6. 无球搜索（自动模式）

- 超过 `VISION_SEARCH_AFTER_MS`（默认 5000ms）没有有效球 → 进入搜索；
- 原地慢速旋转，每段约 60°（按 `VISION_SEARCH_60_MS` 计时），每段后停 3s；
- 共 6 段 ≈ 360°；转完仍无球 → **原地休息**（不运动），直到再次识别到球；
- 搜索/暂停/休息途中一旦识别到球 → 立即退出搜索，恢复正常收集。

参数（`firmware/App/app_config.h`）：

| 参数 | 默认 | 说明 |
|---|---|---|
| `VISION_SEARCH_AFTER_MS` | 5000 | 无球多久开始搜索 |
| `VISION_SEARCH_SPEED` | 120 | 原地旋转速度 r/min |
| `VISION_SEARCH_60_MS` | 333 | 转 60° 的时间，需按实车标定 |
| `VISION_SEARCH_PAUSE_MS` | 3000 | 每段 60° 后停 3s |
| `VISION_SEARCH_STEPS` | 6 | 6×60°≈360° |
