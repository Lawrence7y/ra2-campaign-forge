# S01-V1 · PROGRESS（卡号 S01-V1，主循环每帧调用顺序真机验证）

基线：LIVE_LOCK=S01-V1 ✓；启动前无残留 gamemd ✓；gamemd SHA256 73201CC0…F67476（ImageBase 0x400000）；只读目标。

## 结论表（三级分级，证据路径）

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | WinMainCRTStartup=`0x7CD80F`；游戏入口(WinMain 等价)=`0x6BB9A0`；主循环=`0x48CCC0`(780B) | [静态推断] | `EVIDENCE/static_entry_disasm.txt`、`static_mainloop_disasm.txt`；台账 §881 |
| 2 | 主循环内层回边 `0x48CEA8→0x48CE8A`；4 个 per-frame call site 顺序 `0x48CE8A<0x48CE93<0x48CE9C<0x48CEA1` | [静态推断] | `EVIDENCE/static_mainloop_disasm.txt`；`LIVE.md` §0 |
| 3 | 帧计数 `0xA8ED84` 的 inc 在 `0x55DE7E`/写回 `0x55DE81`，在 `0x55D360` 内 | [静态推断] | `EVIDENCE/static_framecounter.txt`；台账 §881-1 |
| 4 | 预期每帧 callee 5 个不同目标中 **出现 3**（`0x55D360`/`0x55CFD0`/`0x48C8B0`）、**未出现 2**（`0x69BAB0`/`0x7241A0`）；容器 `0x48CCC0` 由栈间接证执行 | [已证]/[未证] | `EVIDENCE/stack_dense.ndjson`、`live45.log`、`LIVE.md` §1 |
| 5 | 栈证 3 条调用边：`0x48CE8F⇒0x55D360`(94739)、`0x48CEA1⇒0x48C8B0`(3)、`0x48CEA6⇒0x55CFD0`(2) | [已证] | `EVIDENCE/stack_dense.ndjson`、`.log` |
| 6 | 实测帧率 3 窗 31.2503 / 31.2380 / 31.2268 fps（≈32 ms/帧地板） | [已证] | `EVIDENCE/live45.ndjson`、`analysis_summary.txt` |
| 7 | EIP 99.72% 落在 ntdll.dll Sleep/等待；game .text 仅 0.18% ⇒ EIP 权重≠调用频率，单靠 EIP 不能定序 | [已证] | `EVIDENCE/eip_raw_hist.tsv`、`module_list2.txt`、`LIVE.md` §3 |
| 8 | 单帧内严格时序 + “每帧每对象调用一次” | [未证] | 需单步/写上下文或调用计数，卡面禁止；`UNKNOWNS.md` U2/U4 |

## 核心数字与复算

- **实测帧率**：W1=**31.2503** fps（`Δframe=375/Δt=12.000s`）、W2=**31.2380**（`373/11.941s`）、W3=**31.2268**（`378/12.105s`）；整段 **31.2472** fps（`1404/44.932s`=32.003 ms/帧）。复算 `work/analyze_s01.py` → `EVIDENCE/analysis_summary.txt`。
- **EIP 分桶**：桶总数 **917** 个不同 EIP / **1,352,400** 样本；top-10 桶合计 **99.7948%**（ntdll 4 桶 **99.7152%**：`0x7712890C`=39.1274%、`0x7712837C`=34.7763%、`0x7712869C`=17.1192%、`0x7712A1CC`=8.6923%）。复算 `work/s01_live_probe.py` → `EVIDENCE/eip_raw_hist.tsv`（全量不截断）。
- **出现/未出现**：5 个预期 callee 中 3 出现 / 2 未出现（详见 `LIVE.md` §1）。
- **except.txt**：长度与 mtime 前后**一致**（26272 B / `2026-11-12T22:29:17.2046290Z`）。
- 采样纪律：CPU 未用单样本（GetProcessTimes 15.625 ms 量化），帧率只用 ≥10s 窗聚合；capstone `skipdata=True`；站点归属用函数区间包含；未改任何 ra2youli 文件/台账、未注入/Hook/写内存/联网。

## 真机收尾

**真机收尾：进程已关闭 / except.txt 未变（长度与 mtime 前后一致 26272 B / 2026-11-12T22:29:17.2046290Z）。**
关闭我启动的 pid=20344（`ra2youli\gamemd.exe`），确认无残留 gamemd（count=0）。gamemd.exe/ddraw.dll SHA256 前后一致（73201CC0…F67476 / 85E0F7D5…83B03A9）。LIVE_LOCK 末尾改为 `RELEASED by S01-V1`。
