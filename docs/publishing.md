# 开源发布指南（GitHub / Gitee / AtomGit）

[English](en/publishing.md) | **简体中文**

本文记录把本仓库发布到三个平台的步骤和发布前检查。平台规则会变，具体数值以各平台当前页面为准。

## 1. 发布前检查

```bash
# 仓库体积与最大文件
du -sh .
find . -type f -size +50M -printf "%s\t%p\n" | sort -rn

# 确认没有误提交厂家模型、密钥
git status --ignored
```

检查清单：

- [ ] 根目录 `README.md`、`LICENSE`、`THIRD_PARTY_NOTICES.md` 存在且链接可点。
- [ ] `hardware/mechanical/` 下只有自研零件、STL、工程图和预览图。
- [ ] 没有厂家 BSP、串口密钥、Wi-Fi/蓝牙密码。
- [ ] APK 与 hex 能正常下载；Release 说明写清版本和校验值。
- [ ] README 中的相对链接在默认分支下可访问（中文文件名用 `<>` 包裹）。

当前仓库约 22 MB，最大文件是 `hardware/mechanical/solidworks/parts/车前端.SLDPRT`（约 1.8 MB），**不需要 Git LFS**，三个平台都可以直接推送或网页上传。

## 2. 初始化并推送

```bash
cd pingpong-collector
git init -b main
git add .
git commit -m "chore: initial open-source release"
```

## 3. GitHub

1. 打开 <https://github.com/new>，Repository name 填 `pingpong-collector`。
2. **不要**勾选 “Add a README file”“Add .gitignore”“Choose a license”，仓库里已有。
3. 创建后按页面提示推送：

```bash
git remote add origin git@github.com:<你的用户名>/pingpong-collector.git
git push -u origin main
```

4. 在仓库 **Settings → General** 填写 Description，Topics 建议：

```text
stm32f407 openmv ping-pong robotics solidworks keil bluetooth differential-drive
```

5. GitHub 对单文件 >100 MB 直接拒绝，>50 MB 警告；本仓库当前没有超限文件。

## 4. Gitee

1. 打开 <https://gitee.com/projects/new>，新建公开仓库，名称 `pingpong-collector`。
2. 不要初始化 README/许可证；创建后添加远程：

```bash
git remote add gitee git@gitee.com:<你的用户名>/pingpong-collector.git
git push gitee main
```

3. 在 **管理 → 基本信息** 填写简介、开源许可证（MIT）和主题标签。

## 5. AtomGit

1. 打开 <https://atomgit.com>，新建公开项目，名称 `pingpong-collector`。
2. 按项目页显示的 SSH/HTTPS 地址推送（以页面为准）：

```bash
git remote add atomgit git@atomgit.com:<你的用户名>/pingpong-collector.git
git push atomgit main
```

3. 填写项目简介、标签，并检查 README 图片是否正常渲染。

## 6. Release 建议

Release 建议附上：

- `releases/Fusion_OpenCar.hex`（预编译固件，仅供参考）
- `app/收集车控制台V3.3.apk`
- 版本说明：修复项、已知问题、测试条件

## 7. 三平台同步

推荐以 GitHub 为主仓库，Gitee/AtomGit 作为镜像：

```bash
git remote -v
git push origin main
git push gitee main
git push atomgit main
```

注意：

- 不要在 README 里写死某一个平台的绝对链接；使用相对路径，镜像才能通用。
- 发布前分别检查三个平台的图片渲染和中文文件名链接。

## 8. 许可证与合规

- 原创代码/文档/CAD：MIT，见根目录 `LICENSE`。
- STM32 标准外设库/CMSIS：ST 原许可，MIT 不覆盖。
- 轮趣底盘、C30D、OpenMV、Android SDK 等第三方组件遵循各自许可。

## 9. 发布后

- 在 README 顶部补充三个平台的仓库地址（可选）。
- 打开 Issue 模板/讨论区，收集复现问题。
- 给首个版本打 tag：

```bash
git tag -a v1.0.0 -m "first open-source release"
git push origin v1.0.0
```

- 记录测试条件（场地、光照、球数、地面材质），方便别人复现参数。
