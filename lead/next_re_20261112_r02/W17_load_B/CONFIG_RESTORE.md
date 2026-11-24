# CONFIG_RESTORE · W17 RE-N04f

配置基线：`lead\next_re_20261112_r02\baseline_pre_launch\`（与 W12–W15 同源，开工前逐字节核对）。

## 启动前核对（两趟 attempt 各执行一次，探针 S0 阶段）
| 文件 | sha256 | 与基线一致 |
|---|---|---|
| RA2MD.INI | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | ✓ |
| ddraw.ini | c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52 | ✓ |
| RA2MD.INI.benchbak | c91c6a47…（同 RA2MD.INI） | ✓ |
| gamemd.exe | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 | ✓（verify-only） |
| ddraw.dll | 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9 | ✓（verify-only） |
| B 载体 [8]音速公路_SonicHighways.yrm | 0805e637d3ac14bd8c68ab2acac92b157514f8472c819bbbfecee9c00da712f3 / 252,270 B | ✓（钉定值） |

## 收尾还原（两趟 attempt，探针 finally 实算自证）
- `restore_configs()` 逐字节拷贝基线 → 游戏目录，实测 sha256 与字节比较：
  - attempt1（05:07:14+08）：RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak 三件 `byte_identical_to_baseline=True`，gamemd.exe/ddraw.dll verify-only 一致。
  - attempt2（05:09:50+08）：同上全部一致（见 `out\meta.json` → restore_rows）。
- 文件清单 diff：`inventory 647 → 647`，`added/removed/changed` 全空（两趟）⇒ 游戏运行未改动任何 ra2youli 文件（含未写任何地图缓存）。
- 实例锁：两趟均恢复 `owner=lead`（`lock_restored=True`）。
- `timeBeginPeriod(1)`：未调用（未到采样段）；无遗留计时器请求。

## 结论
配置域 **净变更 = 0**；全部还原证据实算落盘于 `out\meta.json`（restore_rows / written_back / residual_after / lock_restored）。
