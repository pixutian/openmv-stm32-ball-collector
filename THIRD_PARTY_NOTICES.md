# Third-Party Components and Licenses

[简体中文](THIRD_PARTY_NOTICES.zh-CN.md) | **English**

This project includes or uses the following third-party components. Copyright and licenses remain with their respective owners. The MIT license in [LICENSE](LICENSE) covers only original project work.

## 1. STM32F4 Standard Peripheral Library / CMSIS

Location:

```text
firmware/Driver/CMSIS/
firmware/Driver/StdPeriph/
```

These files come from STMicroelectronics' STM32F4 Standard Peripheral Library and ARM CMSIS and remain under their original license terms. They are not original project code and are not covered by the MIT license.

## 2. WHEELTEC Hardware

The project uses a WHEELTEC R1 four-wheel differential chassis, a C30D controller and matching motors. Rights to the chassis, controller, BSP, examples and 3D models belong to WHEELTEC; they are used under the vendor's terms and are not relicensed by this project.

## 3. OpenMV / MicroPython

`openmv/` contains MicroPython scripts that run on the OpenMV H7; OpenMV firmware and the IDE remain under their own licenses.

## 4. Android

`app/` contains an APK built with the Android SDK. Android components remain under their original licenses.

## 5. Mechanical Models and Images

- Original parts, drawings, assembly references and CAD/field photos under `hardware/mechanical/` and `media/tech/` were created by the project team and are released under the MIT license.
- Third-party products, venues and people appearing in field photos remain the rights of their respective owners and are used for project documentation only.
- Photos and drawings of purchased parts (WHEELTEC chassis, C30D, motors) remain the rights of the vendor and are used for project documentation only.
