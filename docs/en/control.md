# Visual Servo and Control Strategy

[简体中文](../control.md) | **English**

## 1. Modes

- Power-on default is **manual mode**: Bluetooth direction keys/joystick control the car; vision receives but does not act.
- Switching (each action toggles the same state):
  - Send `V` over Bluetooth;
  - Or press the **C30D USER button** (PE0); the buzzer beeps once.
- In auto mode the direction keys are ignored (vision takes over the chassis); gear keys `X/Y` and blade keys `T/U` remain active.

## 2. Control variables

OpenMV reports every frame:

- `dx`: horizontal pixel offset of the target center from frame center (positive = right)
- `area`: target pixel area, a rough distance proxy (larger = closer)
- `conf`: confidence; 0 means no target

C30D side (`app_vision.c`):

```c
turn = speed * VISION_TURN_KP * (dx / VISION_CENTER_PX);
base = 0;
if (area < VISION_NEAR_AREA)      base =  speed * VISION_APPROACH_RATIO;  /* approach */
else if (area > VISION_STOP_AREA) base = -speed * VISION_BACKOFF_RATIO;   /* too close, back off */
left  = base + turn;
right = base - turn;
```

- `dx > 0` (target on the right) → left wheel speeds up, right wheel slows down; the car turns right
- Inside `[NEAR_AREA, STOP_AREA]`, `base = 0`; the car aligns in place
- When `area ≥ NEAR_AREA`, the blade runs at 100%; otherwise it stops

## 3. Parameters

| Parameter | Default | Location | Description |
|---|---|---|---|
| `VISION_TIMEOUT_MS` | 300 | `app_config.h` | Stop after no frame |
| `VISION_CENTER_PX` | 160 | `app_config.h` | QVGA 320-wide center |
| `VISION_TURN_KP` | 0.9 | `app_config.h` | Turn gain; higher = more sensitive |
| `VISION_APPROACH_RATIO` | 0.6 | `app_config.h` | Approach speed as a fraction of gear speed |
| `VISION_BACKOFF_RATIO` | 0.4 | `app_config.h` | Back-off fraction |
| `VISION_NEAR_AREA` | 1500 | `app_config.h` | Area at which collection starts |
| `VISION_STOP_AREA` | 4000 | `app_config.h` | Area at which the car backs off |

## 4. Debug order

1. **Raise the wheels**, verify eight directions and stop in manual mode.
2. Connect OpenMV and verify vision frames arrive (breakpoint in `handle_frame` in `app_vision.c`, or toggle an LED temporarily).
3. Send `V`, place a ball 50 cm ahead, and check that the car turns toward it and approaches slowly.
4. Tune `VISION_TURN_KP`: reduce it if the car oscillates, increase it if response is sluggish.
5. Tune `VISION_NEAR_AREA / STOP_AREA` using measured `area` values at 30/50/80 cm.
6. Test at low speed on the floor; first confirm “no ball → stop”, then try continuous collection.

## 5. Safety

- A 300 ms timeout stops the car automatically; Bluetooth loss does not bypass this logic.
- The blade starts only in the collection zone and stops on exit; still disconnect blade power during debugging.
- Auto mode has no obstacle avoidance or cliff detection; test only on flat, enclosed surfaces.
- At any time, send `V` to exit auto mode or cut power.

## 6. Search without a ball (auto mode)

- After `VISION_SEARCH_AFTER_MS` (default 5000 ms) without a valid ball, enter search;
- Rotate slowly in place in ~60° segments (timed by `VISION_SEARCH_60_MS`), pausing 3 s between segments;
- Six segments ≈ 360°; if no ball is found, **rest in place** (no motion) until a ball appears;
- If a ball is detected during search/pause/rest, exit search immediately and resume collection.

Parameters (`firmware/App/app_config.h`):

| Parameter | Default | Description |
|---|---|---|
| `VISION_SEARCH_AFTER_MS` | 5000 | No-ball time before search |
| `VISION_SEARCH_SPEED` | 120 | In-place rotation speed, r/min |
| `VISION_SEARCH_60_MS` | 333 | Time per 60°; calibrate on the car |
| `VISION_SEARCH_PAUSE_MS` | 3000 | Pause after each 60° segment |
| `VISION_SEARCH_STEPS` | 6 | 6 × 60° ≈ 360° |
