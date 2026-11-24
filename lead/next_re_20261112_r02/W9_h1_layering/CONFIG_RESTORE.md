# CONFIG_RESTORE.md —— W9 配置还原自证

run_id：`NEXT_RE_20261112_R02`　日期：2026-11-13

基线目录：`lead\next_re_20261112_r02\baseline_pre_launch\`（与 `PRE_LAUNCH_BASELINE.tsv` 一致）。两趟收尾均执行 `restore_configs()`（逐字节 copyfile）+ SHA-256 复算 + 逐字节比对自证。

## 第一趟（--run，2026-11-13 01:49–01:50）

| 文件 | 还原后 SHA-256 | 与基线 TSV 一致 | 逐字节一致 |
|---|---|---|---|
| RA2MD.INI | `c91c6a47…c3c27d` | True | True |
| ddraw.ini | `c983abad…6df9d52` | True | True |
| RA2MD.INI.benchbak | `c91c6a47…c3c27d` | True | True |
| gamemd.exe（verify-only） | `73201cc0…f67476` | True（未变） | — |
| ddraw.dll（verify-only） | `85e0f7d5…f83a9` | True（未变） | — |

写回 diff（游戏运行期）：added=0 / removed=0 / **changed=0**（第一趟只到主菜单即收尾）。

## 第二趟（--run2，2026-11-13 01:56–01:58）

| 文件 | 还原后 SHA-256 | 与基线 TSV 一致 | 逐字节一致 |
|---|---|---|---|
| RA2MD.INI | `c91c6a47…c3c27d` | True | True |
| ddraw.ini | `c983abad…6df9d52` | True | True |
| RA2MD.INI.benchbak | `c91c6a47…c3c27d` | True | True |
| gamemd.exe（verify-only） | `73201cc0…f67476` | True（未变） | — |
| ddraw.dll（verify-only） | `85e0f7d5…f83a9` | True（未变） | — |

写回 diff（游戏运行期）：added=0 / removed=0 / **changed=1 → `RA2MD.INI`**。
说明：第二趟真实打完一局（进图→结算屏），游戏退出时按其正常行为写回 `RA2MD.INI`（遭遇战设置/最近地图类字段）。该写回发生在收尾还原**之前**的 inventory 采集，随后已被逐字节还原为基线（上表 byte_identical=True 即还原后实算证据）。当前 `ra2youli\RA2MD.INI` 与 `baseline_pre_launch\RA2MD.INI` 逐字节相同。

## H1 载体（Lead 责任域，本卡未动）

| 时点 | 存在 | SHA-256 |
|---|---|---|
| 第一趟收尾后 | 是 | `e3acc130…d9e39`（一致） |
| 第二趟收尾后 | 是 | `e3acc130…d9e39`（一致） |

本卡**未**删除/改名/覆盖任何 `ra2youli` 文件；装入件的还原（移除）由 Lead 负责。
