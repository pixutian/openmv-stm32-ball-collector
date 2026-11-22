# Publishing Guide (GitHub / Gitee / AtomGit)

[简体中文](../publishing.md) | **English**

This guide covers publishing the repository to three platforms. Platform rules change; check the current limits on each site.

## 1. Pre-flight checks

```bash
du -sh .
find . -type f -size +50M -printf "%s\t%p\n" | sort -rn
git status --ignored
```

Checklist:

- [ ] `README.md`, `LICENSE` and `THIRD_PARTY_NOTICES.md` exist and links work.
- [ ] `hardware/mechanical/` contains only original parts, STL, drawings and previews.
- [ ] No vendor BSP, serial secrets, Wi-Fi/Bluetooth passwords.
- [ ] APK and hex download correctly; release notes include version and checksums.
- [ ] Relative links resolve on the default branch (wrap Chinese filenames in `<>`).

The repository is about 22 MB; the largest file is `hardware/mechanical/solidworks/parts/车前端.SLDPRT` (~1.8 MB). **Git LFS is not required.**

## 2. Initialize and push

```bash
cd openmv-stm32-ball-collector
git init -b main
git add .
git commit -m "chore: initial open-source release"
```

## 3. GitHub

1. Open <https://github.com/new>, name the repository `openmv-stm32-ball-collector`.
2. Select **Public**.
3. Do **not** add a README, .gitignore or license; the repository already has them.
4. Push:

```bash
git remote add github https://github.com/<username>/openmv-stm32-ball-collector.git
git push -u github main
git push github --tags
```

5. Add a description and topics (for example `stm32f407`, `openmv`, `ping-pong`, `robotics`, `solidworks`, `keil`, `bluetooth`).
6. GitHub rejects files over 100 MB; this repository has none.

## 4. Gitee

1. Open <https://gitee.com/projects/new>, name it `openmv-stm32-ball-collector`.
2. Select **Public**; do not initialize a README/license.
3. Push:

```bash
git remote add gitee https://gitee.com/<username>/openmv-stm32-ball-collector.git
git push -u gitee main
git push gitee --tags
```

4. Set the license to MIT and fill in the description/topics in **Management → Basic Information**.

## 5. AtomGit

1. Open <https://atomgit.com>, create a public project named `openmv-stm32-ball-collector`.
2. Use the SSH/HTTPS URL shown on the project page:

```bash
git remote add atomgit https://atomgit.com/<username>/openmv-stm32-ball-collector.git
git push -u atomgit main
git push atomgit --tags
```

3. Fill in the description, topics and license in project settings.

## 6. Releases

Create a `v1.0.0` release on each platform and attach:

- `releases/Fusion_OpenCar.hex` (prebuilt firmware, for reference)
- `app/收集车控制台V3.3.apk`
- Release notes: changes, known issues and test conditions

## 7. Keeping mirrors in sync

Use one platform as the primary remote and the others as mirrors:

```bash
git push github main
git push gitee main
git push atomgit main

git push github --tags
git push gitee --tags
git push atomgit --tags
```

Notes:

- Use relative links in README so all mirrors render correctly.
- Check image rendering and Chinese filenames on each platform.
- If large assemblies return later (>100 MB), enable Git LFS and confirm platform support first.

## 8. License and compliance

- Original code/docs/CAD: MIT, see `LICENSE`.
- STM32 StdPeriph/CMSIS: ST license; not covered by MIT.
- WHEELTEC chassis, C30D, OpenMV, Android SDK: follow their respective licenses.

## 9. After publishing

- Add repository links to the README if desired.
- Enable Issues/Discussions and collect reproduction reports.
- Tag the first release:

```bash
git tag -a v1.0.0 -m "first open-source release"
git push origin v1.0.0
```

- Record test conditions (venue, lighting, ball count, floor material) so others can reproduce parameter sets.
