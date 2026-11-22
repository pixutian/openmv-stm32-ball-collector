# Fusion OpenCar Firmware

[简体中文](README.zh-CN.md) | **English**

Full vehicle control firmware for a four-wheel differential car, based on STM32F407VET6 and the Standard Peripheral Library. The Android app sends joystick direction and gear commands over Bluetooth (USART2 + HC-02 / JDY-33 transparent module). The board runs a 200 Hz control loop covering encoder sampling, four PI speed loops and PWM output, while driving the OLED and sending telemetry back to the app.

## Features

- Four-wheel differential chassis: left pair A/C, right pair B/D; eight-way remote control (forward / reverse / four diagonals / spin left/right)
- 7-level speed cycling; at the top or bottom, the next press returns to the middle level; boot default is the middle level
- Blade motor (auxiliary motor) also has 7 levels, 10% duty per step
- Four independent incremental PI speed loops at 200 Hz
- 9-axis attitude (ICM-20948 + AK09916), complementary filter for roll / pitch / yaw
- 128×64 OLED showing target/actual speed, gear, servo angle, battery voltage and debug values
- Battery voltage sampling and percentage conversion
- One independent auxiliary motor output (TIM8_CH1) for continuous rotation

## Directory Structure

```text
Fusion_OpenCar/
├─ App/                     Application layer
│   ├─ app_config.h         Vehicle parameters (gear ratio, gears, PI, PWM timing, battery)
│   ├─ app_chassis.c/.h     Gear management, direction commands, speed PI, motor output
│   ├─ app_link.c/.h        Bluetooth frame parsing, module-response filtering, telemetry
│   ├─ app_main.c           Init flow, main loop, 200 Hz control tick
│   └─ stm32f4xx_it.c       Cortex-M4 core exceptions
├─ Hardware/                Board support layer
│   ├─ board.h              Pin / timer / UART resource map
│   ├─ clock.c/.h           1 ms system tick and delays
│   ├─ io.c/.h              LEDs, buzzer, keys
│   ├─ motor.c/.h           Four H-bridge PWM channels, servo, auxiliary motor
│   ├─ encoder.c/.h         Four quadrature encoder counters
│   ├─ adc.c/.h             Battery voltage sampling
│   ├─ serial.c/.h          Debug UART and Bluetooth UART
│   ├─ i2c_soft.c/.h        GPIO software I²C
│   ├─ imu.c/.h             9-axis sensor access and attitude solution
│   ├─ imu_reg.h            ICM-20948 register map
│   ├─ screen.c/.h          SSD1306 driver and layout
│   └─ font.h               6×12 ASCII font
├─ Driver/                  ST official code (kept as-is; copyright STMicroelectronics)
│   ├─ CMSIS/               Core headers, startup file, system_stm32f4xx.c
│   └─ StdPeriph/           Standard Peripheral Library (inc / src)
├─ Objects/                 Keil build output (hex / axf / logs)
└─ Fusion_OpenCar.uvprojx   Keil MDK project
```

## Hardware Resources

| Function | Pin / peripheral |
| --- | --- |
| A-wheel PWM | TIM10_CH1 (PB8) / TIM11_CH1 (PB9) |
| B-wheel PWM | TIM9_CH1 (PE5) / TIM9_CH2 (PE6) |
| C-wheel PWM | TIM1_CH2 / TIM1_CH1 (PE9 / PE11) |
| D-wheel PWM | TIM1_CH4 / TIM1_CH3 (PE13 / PE14) |
| Servo | TIM12_CH2 (PB14 / PB15), center 90° |
| Blade motor | TIM8_CH1 (PC6), 7-level duty |
| Encoders A/B/C/D | TIM2 (PA15/PB3), TIM3 (PB4/PB5), TIM4 (PB6/PB7), TIM5 (PA0/PA1) |
| Bluetooth | USART2 (PD5/PD6), 9600 |
| Debug UART | USART1 (PA9/PA10), 115200 |
| OLED | GPIOD 11=D/C, 12=RST, 13=SDA, 14=SCL |
| 9-axis IMU | Software I²C, GPIOB 10=SCL, 11=SDA, address 0x68 |
| Battery sense | ADC1_IN8 (PB0), divider ratio 11 |
| LED / buzzer | PE8 / PA8 |

## Control Logic

1. **Tick**: TIM7 interrupts every 5 ms (200 Hz): IMU sampling and attitude update, LED toggle, battery-sample flag, refresh the four wheel targets from the current direction command, run the speed loops and output PWM. The main loop (~100 Hz) handles battery conversion, display refresh and app telemetry.
2. **Gears**: gear index 0–6; target speed = `GEAR_BASE_RPM + (gear - GEAR_CENTER) * GEAR_STEP_RPM`; defaults 100/200/300/400/500/600/700 rpm. Only the index is stored, so holding a key cannot keep increasing speed; at the limits it wraps back to the middle gear.
3. **Blade gears**: 0–6 map to 40/50/60/70/80/90/100% duty; gear 3 (70%) is the middle. At the top or bottom, the next press returns to the middle. Only the index is stored; a press rewrites `TIM8->CCR1` immediately, with no accumulation. Boot default is gear 6 (100%).
4. **Speed loop**: incremental PI (`Kp=5.0`, `Ki=1.6`), output limited to ±16700; the right-side B/D encoder readings are negated so all four speeds use the same positive direction.
5. **Communications**: frame format `{...}$`. Direction keys are single bytes (0x41–0x48 for 1–8); `X`/`Y` raise/lower chassis gear; `T`/`U` raise/lower blade gear (both with 200 ms debounce, one step per press); `I`/`J`/`K` switch app pages. Telemetry: `{A:a:b:c:d}$` (two wheel speeds, battery, heading), `{B:p:r:y}$` (attitude), `{C:p1:p2}$` (debug values).

## Build

1. Open `Fusion_OpenCar.uvprojx` with Keil MDK (ARMCC V5.06).
2. Build; output goes to `Objects/` and produces `Fusion_OpenCar.hex`.
3. Device: STM32F407VETx; defines: `STM32F40_41xxx,USE_STDPERIPH_DRIVER`.

## Common Parameters

All in `App/app_config.h`; the two most frequently changed are marked with `★`:

| Parameter | Meaning |
| --- | --- |
| `GEAR_BASE_RPM` | **Initial car speed** (boot speed = middle gear target) |
| `GEAR_STEP_RPM` | Speed difference between gears |
| `AUX_GEAR_STEP` | **Blade motor step per gear** (default 10% duty) |
| `AUX_GEAR_TOP_DUTY` | Blade motor top duty (default 100%) |
| `AUX_GEAR_BOOT` | Blade boot gear (default 6 = 100%; set 3 for 70%) |
| `GEAR_COUNT` / `GEAR_CENTER` | Number of gears and middle index |
| `TURN_RATE_SCALE` | Target-speed multiplier while turning |
| `SPEED_PI_KP` / `SPEED_PI_KI` | Speed-loop PI gains |
| `MOTOR_GEAR_RATIO` / `ENCODER_PULSE_PER_REV` | Gear ratio and encoder counts for speed conversion |
| `SERVO_TRAVEL_DEG` | 180° or 270° servo |

### Code Locations for the Two Common Changes

**Initial speed**

1. `App/app_config.h` → `GEAR_BASE_RPM` (single source of truth; 400 means 400 rpm at the middle gear)
2. `App/app_chassis.c` → `chassis_init()` resets gears; `chassis_gear_change()` computes
   `GEAR_BASE_RPM + (gear - 3) * GEAR_STEP_RPM`

**Blade motor speed**

1. `App/app_config.h` → `AUX_GEAR_STEP` (10% per step), `AUX_GEAR_TOP_DUTY` (100% top), `AUX_GEAR_BOOT` (boot gear, default 6 = 100%)
2. `App/app_chassis.c` → `aux_gear_to_duty()` converts gear to duty; `aux_gear_change()` raises/lowers and wraps; `chassis_init()` applies the boot gear
3. `App/app_link.c` → `T`/`U` 200 ms debounce (`s_aux_key_tick`)
4. `Hardware/motor.c` → `s_aux_duty` (current duty), `aux_motor_init()` (writes TIM8->CCR1 at boot), `aux_motor_set_duty()` (rewrites compare value)
5. Compare value: `CCR1 = duty * (AUX_PWM_ARR + 1) / 100`; 100% → 10000 (full duty)

## License

- `App/` and `Hardware/` are original project code and follow the repository `LICENSE`.
- `Driver/CMSIS/` and `Driver/StdPeriph/` come from STMicroelectronics' STM32F4 Standard Peripheral Library and CMSIS; copyright remains with STMicroelectronics. They are kept as-is and used only to build this project.
