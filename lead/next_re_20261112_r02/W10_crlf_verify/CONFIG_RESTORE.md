# W10 CONFIG_RESTORE —— 配置逐字节还原自证

- run_id：`NEXT_RE_20261112_R02`；收尾时间：2026-11-12T18:15:42Z（本地 2026-11-13 02:15 +08:00）
- 还原实现：复用 W7.restore_configs()——从 `baseline_pre_launch\` 基线副本逐字节
  `shutil.copyfile` 回 `ra2youli\`，随后读回哈希与基线 TSV 比对；gamemd.exe/ddraw.dll
  为 verify_only（只核不改）。

## 还原结果（out\meta.json restore_rows）

| 文件 | 还原前 SHA-256 | 还原后 SHA-256 | 基线（TSV） | byte_identical | sha_match |
|---|---|---|---|---|---|
| RA2MD.INI | `c91c6a47…3c27d` | `c91c6a47…3c27d` | `c91c6a47…3c27d` | true | true |
| ddraw.ini | `c983abad…f9d52` | `c983abad…f9d52` | `c983abad…f9d52` | true | true |
| RA2MD.INI.benchbak | `c91c6a47…3c27d` | `c91c6a47…3c27d` | `c91c6a47…3c27d` | true | true |
| gamemd.exe（verify_only） | — | `73201cc0…7476` | `73201cc0…7476` | — | unchanged=true |
| ddraw.dll（verify_only） | — | `85e0f7d5…03a9` | `85e0f7d5…03a9` | — | unchanged=true |

## 关键事实

- 三个还原文件的**还原前哈希已等于基线**：本卡只到地图列表、未开局，游戏对配置
  零写回；restore 为幂等字节拷贝（post == pre == baseline）。
- ra2youli 清单 before/after 均 648 项；diff_inventory added/changed/removed 全空
  （out\meta.json `written_back`）。
- H1 载体 untouched：run 前后 SHA-256 均 `afb18a33895c5ff55ab3156c9a43d2a658c5c0889137f251e2d4952622925861`，
  315,706 B，未删未改未改名。
- 实例锁恢复 owner=lead（lock_restored=true）。
- gamemd 残留：收尾后 0。
