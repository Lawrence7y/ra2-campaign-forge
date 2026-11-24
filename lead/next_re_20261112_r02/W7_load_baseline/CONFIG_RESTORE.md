# CONFIG_RESTORE.md —— 配置逐字节还原与残留进程核对（三趟独立收尾）

- run_id: `NEXT_RE_20261112_R02`；生成时刻：2026-11-13（本地）
- 基线：`lead\next_re_20261112_r02\baseline_pre_launch\`（RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak 字节副本
  + `PRE_LAUNCH_BASELINE.tsv` 5 条目）；gamemd.exe / ddraw.dll 无字节副本，按 TSV 仅校验

## 1. 每趟开工前哈希守卫（实算 = 期望）

| 文件 | run1 | run2 | run3 |
|:--|:--|:--|:--|
| RA2MD.INI (`c91c6a47…`) | match | match | match |
| ddraw.ini (`c983abad…`) | match | match | match |
| RA2MD.INI.benchbak (`c91c6a47…`) | match | match | match |
| gamemd.exe (`73201cc0…`) | match | match | match |
| ddraw.dll (`85e0f7d5…`) | match | match | match |
| 启动前 gamemd 残留 | 0 | 0 | 0 |

（另：被误杀的首趟存档运行开工前守卫同样全 match。）

## 2. 游戏写回清单（收尾 vs 启动前，ra2youli 647 项清单比对）

| 趟 | 新增 | 删除 | 变化 | 变化明细 |
|:--|:--|:--|:--|:--|
| run1 | 0 | 0 | 1 | `RA2MD.INI` |
| run2 | 0 | 0 | 1 | `RA2MD.INI` |
| run3 | 0 | 0 | 1 | `RA2MD.INI` |

> 与历史一致：游戏退出时写回 `RA2MD.INI`（ScenIndex 等）；`ddraw.ini` 未被动过。

## 3. 逐字节还原自证（每趟收尾执行，还原发生在写回比对之后）

| 趟 | 文件 | 还原前 SHA（被游戏改写后） | 基线副本 SHA | 还原后 SHA | 字节一致 | 与 TSV 一致 |
|:--|:--|:--|:--|:--|:--|:--|
| run1 | RA2MD.INI | （改写后值，见 meta） | `c91c6a47…` | `c91c6a47…` | True | True |
| run1 | ddraw.ini | `c983abad…`（未变） | `c983abad…` | `c983abad…` | True | True |
| run1 | RA2MD.INI.benchbak | `c91c6a47…` | `c91c6a47…` | `c91c6a47…` | True | True |
| run2 | RA2MD.INI | （改写后值） | `c91c6a47…` | `c91c6a47…` | True | True |
| run2 | ddraw.ini | `c983abad…` | `c983abad…` | `c983abad…` | True | True |
| run2 | RA2MD.INI.benchbak | `c91c6a47…` | `c91c6a47…` | `c91c6a47…` | True | True |
| run3 | RA2MD.INI | （改写后值） | `c91c6a47…` | `c91c6a47…` | True | True |
| run3 | ddraw.ini | `c983abad…` | `c983abad…` | `c983abad…` | True | True |
| run3 | RA2MD.INI.benchbak | `c91c6a47…` | `c91c6a47…` | `c91c6a47…` | True | True |

verify-only（未改证实）：三趟 `gamemd.exe` = `73201cc0…`、`ddraw.dll` = `85e0f7d5…`，均 unchanged=True。

## 4. 残留进程核对（三趟独立）

| 趟 | 关闭步骤摘要 | 收尾后残留 |
|:--|:--|:--|
| run1 | WM_CLOSE → taskkill(无/F) → taskkill(/F)，最终存活=False | **0** |
| run2 | 同上 | **0** |
| run3 | 同上 | **0** |

全仓最终核对：三趟收尾 + 全部文档产出后，`gamemd` 残留 = 0（本卡收尾时再次实查，见 RUNLOG §4）。
