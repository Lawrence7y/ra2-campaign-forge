# W13 · SAFETY.md（RE-N04b attempt 3）

## 授权与写域
- 用户总授权：`lead/next_re_20261112_r02/USER_AUTHORIZATION_20261112.md`（2026-11-12，「全部动作 + 自行裁决、不干预」）。
- 本卡写域：仅 `lead/next_re_20261112_r02/W13_longrun_drift/`（脚本、out/、报告）+ 实例锁 `.game_instance.lock`（开工接管 / 收尾恢复 owner=lead）+ `ra2youli` 配置还原（RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak，卡面要求）。
- 未触碰 `lead/next_re_20261112_r02/` 其它卡目录与仓库源码；未提交 git。

## 对目标进程的边界（逐条遵守）
- 只启动 `ra2youli/gamemd.exe`（WMI 分离），只处理**自己启动的 pid**（42824）。
- 只读 `ReadProcessMemory`（12 个地址 + 地图名指针）；**无** SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标内存 / 改 exe / dll / hook。
- UI 输入仅限导航/选图/开局阶段（BM_CLICK 消息 + 置前）；**采样段（首个 frame>0 起）零按键、零切窗、零干预**（GetLastInputInfo 501 次留痕 dwTime 变化 0）。
- 启动前 gamemd 残留非空 ⇒ 停手不杀（本趟为 0，未触发）。

## 进程与现场自愈（attempt2 教训落地）
- 探针以 **WMI `Win32_Process.Create`** 启动（ProbePID=4940），完全脱离代理进程树；代理死亡不影响其跑完。
- 探针 `finally` 自愈链（全部实测落地）：关游戏 → 残留核对（0）→ 配置逐字节还原+哈希自证 → 写 `meta_end` → 恢复锁 `owner=lead`（lock_restored=true）。
- 未使用 Start-Job / `&` 后台 / `Start-Process -NoNewWindow`（attempt2 失败模式）。

## 哈希守卫（启动前 5 文件 + 载体，全 match）
- RA2MD.INI `c91c6a47…c3c27d` · ddraw.ini `c983abad…f9d52` · RA2MD.INI.benchbak `c91c6a47…c3c27d`
- gamemd.exe `73201cc0…67476` · ddraw.dll `85e0f7d5…b03a9`
- 载体 `[8]试验地_Pro_ProvingGrounds.yrm` 175,361 B `3e3c8745…bfd5b19`（实算=钉定）。

## 运行后现场
- 收尾后 gamemd 残留 0；ra2youli 清单 647→647（增 0 / 删 0 / 改 0——RA2MD.INI 由游戏运行改写、已还原自证）；
- 锁 `owner=lead`（Lead 可直接开工下一卡）。
