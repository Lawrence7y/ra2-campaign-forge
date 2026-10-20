# RECEIPT_BUILD —— P2 离线阶段 0–3

- 日期：2026-10-20 08:14
- 执行者：GOAL-3T 驱动器（opencode deepseek-v4.1-flash）
- 范围：仅离线阶段 0–3；**未运行 `ra2render\build.bat`**（未触发 `copy ..\ra2youli\`）、**未写 ra2youli**、**未启动游戏**
- 依据：`lead/goal3_configsplit_20261019/RECEIPT.md`（R1 重交）+ `QC_P2_VERIFY_R2.md`（CONFIRMED）

## 0. 阶段 0：备份（07:28 已存在，本轮复核）

`D:\Project\ra2-campaign-forge\lead\goal3_configsplit_20261019\master_backup_20261020\`

| 文件 | SHA-256(16) | 判定 |
|:--|:--|:--|
| `ra2render.ini` | `fd9ebb32dcb6cda7` | 与母本一致 |
| `blitter_hooks.cpp` | `b461ed21aa92bd5f` | 与母本一致 |
| `ra2render.h` | `b70cbf8d620e340e` | 与母本一致 |

另存旧 DLL：`pre_p2/ra2render.dll` = `626f98b6d6327b10`（163,328 B）；旧 ini 同备份。

## 1. 阶段 1–2：覆盖与目标哈希

- Mimosa 钩子拦截 Bash 直接写 `.cpp/.h`（要求 Write/Edit）。改用 Edit 按 `cpp.diff`（282 行）/ `h.diff`（54 行）逐段施加；`ra2render.ini` 用 cp 覆盖。
- 覆盖后实测：
  - `ra2render.ini` = `27c9a60c55a8a1b4` ✓
  - `blitter_hooks.cpp` = `656e6b4e48cdd251` ✓（与补丁副本 `diff -q` 为空）
  - `ra2render.h` = `10410c98642dc51a` ✓（`diff -q` 为空）

## 2. 阶段 3a：编译（只编译，不部署）

- 脚本：`p2_build.cmd`（`vcvarsall.bat x86` → `cl.exe /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /LD dllmain.cpp blitter_hooks.cpp /Fe:ra2render.dll /link /MACHINE:X86 /SUBSYSTEM:WINDOWS kernel32.lib user32.lib winmm.lib`）
- `EXIT=0`；`build.log` 无 error/warning（仅 vcvarsall 横幅 + 编译文件名 + 正在生成代码）
- 产物：`ra2render\ra2render.dll` = `39cbd66550141610`，165,376 B（旧 163,328 B）

## 3. 阶段 3b：verify_hooks.py（只读）

- 命令：`python tools/verify_hooks.py --json ...\verify_hooks.json`
- `EXIT=1`
- 对称/配对全部 OK：虚表 13/13、inline 备份 9/9、Install/Remove 7/7、ini 键 10/10
- **[5] v1.6.0 四键检查报 `ini=False loadconfig=False`**：四键已按 P2 设计迁入 `[Gameplay]`（出厂全注释）且读取改走 `GetGameplayIntEx`；旧检查器按 `[FogOfWar]` 直读口径判定，属**预期口径差异**，不是 Install/Remove 配对回归
- [6] 27 个头部 `ADDR_*` 死宏/待接线提示（信息项）
- 执行者**未修改** `tools/verify_hooks.py`；[5] 是否需更新检查器口径，交独立核验员裁定

## 4. 阶段 3c：部署包（已备好，未部署）

`deploy/`：

| 文件 | SHA-256(16) | 说明 |
|:--|:--|:--|
| `ra2render.dll` | `39cbd66550141610` | 新编译产物 |
| `ra2render.ini` | `27c9a60c55a8a1b4` | P2 出厂配置 |
| `deploy.cmd` | — | 哈希自检→备份目标→复制；不启动游戏 |
| `rollback.cmd` | — | 从 `backup_*` 恢复 |
| `rollback/ra2render.dll.pre_p2` | `626f98b6d6327b10` | 回滚 DLL |
| `rollback/ra2render.ini.pre_p2` | `fd9ebb32dcb6cda7` | 回滚 ini |
| `DEPLOY.md` | — | 部署步骤 + T1 冒烟六条判据 |

**deploy.cmd / rollback.cmd 未执行；ra2youli 目录零写入。**

## 5. 证据文件

- `build.log`（编译输出）
- `cpp.diff` / `h.diff`（母本→补丁副本差异，已全部施加）
- `verify_hooks.json`（静态自证机器可读报告）
- `p2_build.cmd`（编译命令，可复跑）
- `pre_p2/`（旧 DLL/ini）

## 6. 回退

1. 包内 `deploy/rollback/` 覆盖回 `ra2render\` 并重跑编译；或
2. 用根 `lead/goal3_configsplit_20261019/master_backup_20261020/` 三母本覆盖回 `ra2render\`，再按 `p2_build.cmd` 重编（不要跑 build.bat）。

## 7. 待独立核验（执行者≠核验者）

核验员需确认：三目标哈希、旧备份哈希、编译 exit 0 与 DLL 哈希、verify_hooks 的 [1][2][3][4] 通过及 [5] 预期差异裁定、部署包清单与脚本不启动游戏/不提前写 ra2youli、改动面仅三件（无第四文件改写）。
