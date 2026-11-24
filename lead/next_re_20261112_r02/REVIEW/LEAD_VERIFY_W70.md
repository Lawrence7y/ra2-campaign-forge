# LEAD_VERIFY_W70 · C 线加固：三关链**三趟一致** + 卸载后官方战役**功能级**可用

> 记录人：Lead｜时间：2026-11-14 00:46｜卡：W70（Hy4，真机，一趟一锁）
> 我核过的：`out\TRIP_trip2.json` / `out\TRIP_trip3.json`（逐字段打印）、`REPEATABILITY.md`

## 1 · 两条结论（分开签发）

### T1 · 重复性：成立（3 趟一致）
| 趟 | outcome | ok | M1 | M2 | M3 |
|---|---|---|---|---|---|
| trip1（W63） | `FULL_CHAIN_M1_M2_M3` | true | enter/victory/**advance** | enter/victory/**advance** | enter/victory/**不推进 + EOG=1** |
| trip2（W70） | `FULL_CHAIN_M1_M2_M3` | true | 同 | 同 | 同 |
| trip3（W70） | `FULL_CHAIN_M1_M2_M3` | true | 同 | 同 | 同 |

`[签发]` **同一构建的三关链在 3 趟中逐项一致通过**（W70 自己只计 2 趟，把 W63 那趟标 `[转引]` —— 这个口径是对的，我按 3 趟记账但注明 trip1 来自 W63）。
`[边界]` **不是**"三方战役包通用可通关"；是"**同一个包、3 关、3 趟、1 台机、1 个镜像**"。

### T2 · 卸载后官方战役：**功能级可用**（这是产品诚实性的关键）
`[签发]` 装包(inplace) → 卸载 → 逐字节还原 → **重启游戏** → 走官方苏联战役：
- `Scen+0x125C = SOV01UMD.MAP`（**官方图名**，不是 `RA2F_M1.MAP`）
- `frame=32` 进局内；`scen_next=GDI2A.map`（官方关的 NextScenario，**独立旁证**）
- 全程 **0 次** `MSG:UnableMapSelect`；截图为官方海岸大图（非我方 40×40 小图）
- `BATTLEMD.INI` 还原 2,733 B / SHA `7e40691a…` == 清单 `original_sha256` == 官方 == 真目录 PRE/POST；沙箱配置 21 项 = 20 项 `byte_identical=True` + 1 项 `.seal` 为 `absent_baseline`；沙箱 `identical_tree=True`

⇒ **「能卸载」≠「卸载后正常」这条被真正验了**。这是 W63 没做的一步。

## 2 · 纪律（我核过）
- 包复用：`W63\work\pkg` → 本卡，**11/11 文件 SHA 一致、0 mismatch**（包内容一字节未改，保证与 trip1 同构）
- 工具：复制并改输出路径，`py_compile` 通过，未 import 他卡脚本（符合我立的规矩）
- 锁：3 次启动 3 次独立取放（`w70`→`lead`），未跨趟长期持锁（这正是我批评 W65 的点，W70 做对了）
- 只关自己 pid（6256/13952/16488），`residual_own_pid=0`，全局 `gamemd` 残留 0
- 真目录 `IDENTICAL_TREE=True`（647 文件 / 1,989,215,270 B）

## 3 · 仍未覆盖（照登）
- 未跑 `SkipMapSelect=yes` 分支
- 未做"两个包同时装"的共存测试
- 官方全战役通关未验（只验第一关可进）
