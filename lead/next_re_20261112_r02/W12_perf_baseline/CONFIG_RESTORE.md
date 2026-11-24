# CONFIG_RESTORE.md —— RE-N04 W12 逐趟配置还原与实算自证

- 基线副本：`lead\next_re_20261112_r02\baseline_pre_launch\`（与 `PRE_LAUNCH_BASELINE.tsv` 一致）
- 还原实现：探针每趟 P1 `restore_configs()` —— 逐字节 `copyfile` 后**实算 SHA-256 自证**
  （`byte_identical_to_baseline` + `sha_match` 双判据），并复验两个只读文件未变。
- 四趟 meta `restore_rows` 全部满足：`sha_match=True` 且 `byte_identical_to_baseline=True`；
  `gamemd.exe`/`ddraw.dll` verify-only `unchanged=True`；`written_back`（ra2youli 全目录
  inventory 对比）四趟 added/removed/changed 均空。

## 基线哈希（预期值）

| 文件 | SHA-256 |
|:--|:--|
| RA2MD.INI | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` |
| ddraw.ini | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` |
| RA2MD.INI.benchbak | `c91c6a47…（同 RA2MD.INI）` |
| gamemd.exe（只验不改） | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` |
| ddraw.dll（只验不改） | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` |

## 逐趟收尾实算（post-restore SHA-256 = 基线值 ⇒ 还原成立）

| 趟 | RA2MD.INI | ddraw.ini | RA2MD.INI.benchbak | gamemd.exe | ddraw.dll | inventory 对比 | 收尾后残留 |
|:--|:--|:--|:--|:--|:--|:--|:--|
| R1 (pid 6120) | =基线 ✓ | =基线 ✓ | =基线 ✓ | unchanged ✓ | unchanged ✓ | 0 增 0 删 0 改（647 项） | 0 |
| R2 (pid 38360) | =基线 ✓ | =基线 ✓ | =基线 ✓ | unchanged ✓ | unchanged ✓ | 0 增 0 删 0 改（647 项） | 0 |
| R3 (pid 36888) | =基线 ✓ | =基线 ✓ | =基线 ✓ | unchanged ✓ | unchanged ✓ | 0 增 0 删 0 改（647 项） | 0 |
| R4 (pid 38312) | =基线 ✓ | =基线 ✓ | =基线 ✓ | unchanged ✓ | unchanged ✓ | 0 增 0 删 0 改（647 项） | 0 |
| R1 首趟中断 (pid 26832) | =基线 ✓ | =基线 ✓ | =基线 ✓ | unchanged ✓ | unchanged ✓ | 0 增 0 删 0 改（647 项） | 0 |

说明：R1 首趟在主菜单前因探针绑定缺陷中断（见 RUNLOG），收尾链照常执行且自证通过；
其 meta/ndjson 存档为 `out\R1_meta.aborted_try1.json` / `out\R1.ndjson.aborted_try1`。

## 全部趟次结束后的终态核对

- `gamemd` 残留进程：0（R4 收尾后复查）。
- 实例锁：恢复 `owner=lead`（由本代理在 R4 收尾后写回）。
- 本卡写域外零写入；`ra2youli` 文件清单与开工前逐项一致（哈希级）。
