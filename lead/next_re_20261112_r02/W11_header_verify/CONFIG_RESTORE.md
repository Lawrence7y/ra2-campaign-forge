# W11 CONFIG_RESTORE —— 配置逐字节还原自证

- run_id：`NEXT_RE_20261112_R02`；日期：2026-11-13
- 还原实现：复用 `W7_load_baseline\load_baseline_probe.py::restore_configs`
  （从 `baseline_pre_launch\` 逐字节 `copyfile` 回写，前后双哈希 + 逐字节比对）。

## 还原行（meta.restore_rows）

| 文件 | pre→post | byte_identical_to_baseline | sha_match |
|---|---|---|---|
| RA2MD.INI | 游戏改写后 → `c91c6a47…dc3c27d` | True | True |
| ddraw.ini | 游戏改写后 → `c983abad…d6df9d52` | True | True |
| RA2MD.INI.benchbak | 游戏改写后 → `c91c6a47…dc3c27d` | True | True |
| gamemd.exe | verify-only | — | 未变（`73201cc0…cf67476`） |
| ddraw.dll | verify-only | — | 未变（`85e0f7d5…283b03a9`） |

- 三件可写配置 post SHA-256 与基线 TSV 完全一致（sha_match=True）。
- 两件 verify-only 二进制收尾后哈希未变。

## 目录自证

- ra2youli 清单：启动前 648 项 → 收尾后 648 项；
  `diff_inventory` = added:0 / changed:0 / removed:0（meta.written_back）。
- H1 载体 `ra2youli\[2]0LoadBench_U0800_H1.yrm`：run 前后 SHA-256 均
  `3ce133ff53b67418918e3b3f812f79610094395a979ba27e444ad6fe873be1cb`，
  untouched=True；本卡未删除、未改名、未写入。
- gamemd 残留进程：收尾后 0。
