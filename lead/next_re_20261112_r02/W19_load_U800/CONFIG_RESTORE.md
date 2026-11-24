# W19 / RE-N04h 配置还原记录（LoadBench U800 单趟）

run_id = NEXT_RE_20261112_R02 · 收尾时刻 = 2026-11-12T21:59:56 UTC（05:59:56+08:00）

## 还原链（探针 finally 自动执行）
| 文件 | 基线副本 sha256（=baseline_pre_launch/PRE_LAUNCH_BASELINE.tsv） | 还原后 sha256 | 逐字节一致 | TSV 一致 |
|---|---|---|---|---|
| RA2MD.INI | c91c6a47…3c27d | c91c6a47…3c27d | ✔ True | ✔ True |
| ddraw.ini | c983abad…df9d52 | c983abad…df9d52 | ✔ True | ✔ True |
| RA2MD.INI.benchbak | c91c6a47…3c27d | c91c6a47…3c27d | ✔ True | ✔ True |

只验证不还原（不得变动的二进制）：
| 文件 | TSV sha256 | 还原后实测 | unchanged |
|---|---|---|---|
| gamemd.exe | 73201cc0…f67476 | 73201cc0…f67476 | ✔ True |
| ddraw.dll | 85e0f7d5…47283a? 见下方全值 | 85e0f7d5…47283b03a9 | ✔ True |

（全值：gamemd.exe=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476；
ddraw.dll=85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9）

## 运行期差异与还原
- `inventory` 差异：added=0 / removed=0 / **changed=1 → RA2MD.INI**（游戏运行期/退出期自行写回，属预期行为）。
- 收尾以 baseline_pre_launch/ 逐字节 `copyfile` 覆盖还原，`byte_identical_to_baseline=True` 实算自证。
- 收尾后 gamemd 残留 = **0**；观察者以 `reason=stop_file` 正常退出（433 行，thread 校验 216/216 OK）。
- 实例锁恢复 `owner=lead`（lock_restored=True）。
