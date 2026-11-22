# 第三方组件与许可说明

本项目包含或使用以下第三方组件，版权与许可归各自权利人所有。根目录 [LICENSE](LICENSE) 的 MIT 许可只覆盖项目团队原创部分。

## 1. STM32F4 标准外设库 / CMSIS

位置：

```text
firmware/Driver/CMSIS/
firmware/Driver/StdPeriph/
```

这些文件来自 STMicroelectronics 的 STM32F4 Standard Peripheral Library 与 ARM CMSIS，遵循其原有许可条款。它们不属于本项目原创代码，MIT 许可不覆盖这些文件。

## 2. 轮趣科技（WHEELTEC）硬件

项目使用轮趣 R1 四轮差速底盘、C30D 主控板和配套电机。底盘、主控板及其 BSP、示例工程、三维模型的权利归轮趣科技所有，相关硬件与资料遵循厂家许可，本项目不转授权。

## 3. OpenMV / MicroPython

`openmv/` 下是运行在 OpenMV H7 上的 MicroPython 脚本；OpenMV 固件与 IDE 遵循其各自许可。

## 4. Android

`app/` 下提供编译后的 APK，使用 Android SDK 构建。Android 相关组件遵循其原有许可。

## 5. 机械模型与图片

- `hardware/mechanical/` 下的自研零件、工程图、装配参考图和 `media/tech/` 下的 CAD 截图、样机照片由项目团队制作，随本项目按 MIT 许可发布。
- 实拍照片中出现的第三方产品、场地和人物，其权利归各自权利人所有，仅用于项目说明。
- 采购件（轮趣底盘、C30D、电机等）的照片和图纸权利归厂家所有，仅用于项目说明。
