# Camera Mounting and Calibration

[简体中文](../calibration.md) | **English**

## 1. Mounting position

- Mount the OpenMV H7 **above the front of the car**, with the lens tilted down about 30°–45°.
- Aim the lower edge of the frame at the floor 20–60 cm ahead; balls should appear in the lower half of the image.
- Keep the lens clear of the shell and blades; avoid direct sunlight and highly reflective floors.

## 2. Pixels and distance

OpenMV outputs pixel coordinates; C30D only needs “align + approach”, not precise ranging. Calibrate thresholds against the actual image:

1. Place a ball at **30 / 50 / 80 cm** ahead and record `blob.pixels()` in OpenMV IDE.
2. Use the value near 50 cm as `VISION_NEAR_AREA`, and the value near 30 cm as `VISION_STOP_AREA`.
3. If the ball appears left/right of center, verify that `dx = cx - 160` has the correct sign for the steering direction.

## 2.5 Focal-length calibration (optional position estimate)

1. Place a ball at a **known distance D** (for example 300 mm).
2. Read the ball radius `r` in pixels from that frame in OpenMV IDE.
3. Compute `FOCAL_PX = 2 * r * D / 40` (ball diameter is 40 mm).
4. Average 2–3 distances and write the result to `FOCAL_PX` in `openmv/main_circle_pos.py`.

> Distance estimates are very sensitive to radius, so far/near errors can be large. Auto-collection only needs “approach/arrived”; prefer `area` thresholds and use `dist_mm` as a reference only.

## 3. Threshold calibration (OpenMV IDE)

1. Connect OpenMV and run `openmv/main.py`.
2. Open the **frame buffer** and inspect the grayscale histogram; ping-pong balls are usually in the bright region (>200).
3. Adjust `openmv/config.py`:
   - `GRAY_THRESHOLD`: start with `(200, 255)`; raise the lower bound if the floor is reflective
   - `PIXELS_THRESHOLD`: too small detects reflections; too large misses distant balls
   - `MIN_ROUNDNESS`: filters elongated reflections; 0.5–0.7 is a good range
4. Test with different colors and worn balls (white, yellow, dirty); adjust LAB thresholds if needed.

## 4. UART verification

- The OpenMV IDE serial terminal should show frame output (temporary `print` statements are fine).
- Alternatively, connect a PC USB-TTL adapter to C30D UART4 (3.3 V) and run
  `python3 tools/protocol_sim.py COM5 --sweep` to simulate a target and check that the car follows.
- Without hardware, check the frame format with:

```text
python3 tools/protocol_sim.py --dry-run
```

## 5. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Car does not move | `V` not sent; `conf=0`; UART not connected |
| Steering reversed | `dx` sign or left/right wheel definition reversed; verify manually first |
| Surge/stop oscillation | Timeout too short / frame rate too low; check baud rate and wire length |
| Only white balls detected | Thresholds cover only bright white; adjust for ball color |
| Ball lost at close range | Ball falls below the frame; adjust camera tilt or increase `STOP_AREA` |
