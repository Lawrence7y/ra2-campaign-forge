# Q1 · 扩项副本本体（`qc151_trip.harness8_v4_ext.py`）设计与实现交付报告

## 1. 一句话结论

**已严格以母本 `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`（489,502 字节，SHA256 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`）为基底，采用「纯插块、零修改母本行」机制产出 `W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py`（498,772 字节，纯新增 8 个 `W5EXT` 块共 230 行代码，删改 0 行；删块即还原 SHA256 逐字节完全一致；禁止面高危 API 增量为 0）；直接复用候选件 `frame_edge_sampler.py` 状态机，落实了每沿 4 次只读 VA + 2 次帧号读、读失败记 `null` 不补 0、每记录强制携带未证双 markers、硬断言 S4 零命中且拒绝在 `--allow-loader` 下启动扩项。**

---

## 2. ★ 必须披露的安全声明（TASK.md §4）

> **「本副本在启用扩项前断言 S4 零命中；若 `ra2render` 在场，`threat_calls` 字段不可解释为入口调用总数。」**

**依据与威胁机理说明**：
- 依据 A3 普查及 W4 卡（`card_00A8EC34.md` §6.2）确证，`ra2render.dll` 会在 `Greatest_Threat` 入口 `0x6F8DF0` 安装 9 字节 Inline Hook（改写为 `E9 <rel32> 90 90 90 90`）。跳板逻辑按照 `interval`（默认 8）对索敌扫描执行节流，**被节流时整次跳过 `0x6F8E04/0x6F8E09` 的自增**。若注入在场，`0x00A8EC34` 仅记录约 1/8 的调用。
- 因此，本副本在进入扩项采样前施加硬断言门禁，强制要求 `ra2render_hits == [] and ra2loader_hits == []`，并坚决拒绝在 `--allow-loader` 授权旁路下运行扩项。

---

## 3. 扩项副本架构与 8 个 W5EXT 插入块清单

扩项副本通过 8 个严格以 `# >>> W5EXT-BEGIN <name>` 与 `# <<< W5EXT-END <name>` 包裹的最小插入块，在保证母本所有原有行零改动的前提下，完成工具链扩项：

| 块编号 | 块标识名称 | 副本所在行号 | 新增行数 | 挂载点（母本行后） | 核心功能与语义 |
|---|---|---|---|---|---|
| **块 1** | `imports` | 176 ~ 211 | 36 行 | 175 (`from pathlib import Path`) | 导入 `A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`，建立 `_W5_STATE` 容器与 `w5_set_reader` 假读取器注入钩子 |
| **块 2** | `s4-scan-hook` | 999 ~ 1009 | 11 行 | 962 (`return {"ra2render_hits": ...}`) | 包装 `s4_scan_names`，仅在 `_W5_STATE["on"]` 时提取并捕获 `ra2render_hits` 与 `ra2loader_hits` 列表 |
| **块 3** | `s4-gate-hook` | 1249 ~ 1283 | 35 行 | 1201 (`return True` in `s4_injection_gate`) | 包装 `s4_injection_gate`，硬断言 S4 零命中；若 `authorized=True` 试图旁路放行，强制拦截并记 `62` |
| **块 4** | `poll-span-hook` | 4128 ~ 4197 | 70 行 | 4045 (`return t0, samples, counters, err`) | 包装 `_measure_poll_span`，在 500 Hz 轮询中仅在检测到 `f != prev_f` 时调用 `fes.read_sample` 追加 4 读 + 2 帧读 |
| **块 5** | `json-hook` | 4978 ~ 5014 | 37 行 | 4825 (`return p` in `_measure_write_json`) | 包装 `_measure_write_json`，落盘 `measure_w{k}_w5_events.jsonl`，向 `payload` 注入 `w5_ext` 结构化字段，登记 `rec` |
| **块 6** | `measure-run-hook` | 5579 ~ 5604 | 26 行 | 5389 (`rec.add("MEASURE", "handle_closed", ...)`) | 包装 `_measure_run`，进入采样前二次硬断言 S4 干净态；非干净或 loader 在场则立即停手拒采 |
| **块 7** | `argparse` | 7711 ~ 7716 | 6 行 | 7495 (`# <<< H6-CLOSE-END argparse`) | 新增 CLI 参数 `--w5-ext` 与同义别名 `--measure-ext`，缺省均为 `0` |
| **块 8** | `main-gate` | 7723 ~ 7731 | 9 行 | 7501 (`args = parse_args(argv)`) | 顶层参数门禁：若启用扩项且携带 `--allow-loader`，直接阻断返回 `EXIT_INJECTION_SUSPECTED(62)` |

---

## 4. 八项刚性要点落实对照表

| # | 任务书 / 提示词要求 | 判据与设计规格 | 落实情况与源码位置 |
|---|---|---|---|
| **1** | **母本逐字节复制** | 副本基于 `qc151_trip.harness8_v4.py`（489,502 B, SHA256 `38244d29...`），只增不改 | **已落实**：`_w5_diff_proof.py` 证实删除 0 行、修改 0 行 |
| **2** | **改动面块标记** | 所有新增内容必须包裹在 `# >>> W5EXT-BEGIN` 与 `# <<< W5EXT-END` 中 | **已落实**：共 8 块，机械删块后还原 SHA256 完全一致 |
| **3** | **CLI 开关默认关闭** | 缺省值必须为 `0`；为 0 时严格遵守 flag-off 房规 | **已落实**：`--w5-ext` 缺省 0；`_W5_STATE["on"]=False` 时所有 hook 直通母本锚逻辑，零额外采样行，零额外落盘 |
| **4** | **直接复用候选件** | 直接 `import frame_edge_sampler`，**不重写**帧沿状态机 | **已落实**：`sys.path` 动态引入 `A1_SAMPLER_CANDIDATE`，直接实例化 `FrameEdgeTracker` 并调用 `read_sample` |
| **5** | **只读安全性** | 零 `WriteProcessMemory`、零远程注入、零挂线程、零 dump | **已落实**：高危 API 静态扫描次数与母本严格相同（增量均为 +0） |
| **6** | **读失败记 null** | RPM 读取失败记 `null`，严禁补 0 | **已落实**：复用候选件 `read_one` 契约，失败返回 `None`，JSON 序列化为 `null` |
| **7** | **未证双标记** | 每条记录携带两个 marker | **已落实**：每条 event 及每份 stats 均携带 `["alpha_uncalibrated", "sampling_sufficiency_unproven"]` |
| **8** | **硬断言 S4 且禁 loader** | 强制 `ra2render_hits == [] and ra2loader_hits == []`，拒绝 `--allow-loader` | **已落实**：在 `main-gate`、`s4-gate-hook` 及 `measure-run-hook` 三重前置硬拦截 |

---

## 5. 机械改动面验证（Q2 对照）

实跑命令：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```
实跑退出码：`EXIT=0`。关键输出数据：
- **母本规格**：8,857 行，489,502 字节，SHA256: `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`
- **副本规格**：9,087 行，498,772 字节，SHA256: `eb53a61723c43924ac0b16de495e7dcc77cf530f92b2100c5b7594f44407f45b`
- **检验 1（删块即还原）**：机械删除 8 个 `W5EXT` 块后，剩余字节数 489,502，SHA256 恢复为 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`，**判定 PASS**。
- **检验 2（改动面清单）**：新增 230 行，删除 0 行，修改 0 行，母本原有行零受损，**判定 PASS**。
- **检验 3（禁止面扫描）**：
  - `WriteProcessMemory`: 母本 3, 副本 3, 差异 +0
  - `CreateRemoteThread`: 母本 1, 副本 1, 差异 +0
  - `SuspendThread`: 母本 0, 副本 0, 差异 +0
  - `MiniDumpWriteDump`: 母本 11, 副本 11, 差异 +0
  - `StackWalk`: 母本 0, 副本 0, 差异 +0
  - `SetWindowsHookEx`: 母本 1, 副本 1, 差异 +0
  - **判定 PASS**（所有受限 API 增量均为 0）。

---

## 6. 离线单测覆盖结果（Q3 对照）

实跑命令：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"
```
实跑退出码：`EXIT=0`。六大测试用例执行摘要：
1. **用例 1（开关为 0 零行为差）**：`_W5_STATE["on"]=False` 运行时，零四 VA 读取（调用计数为 0），`payload` 无 `w5_ext` 键，不产出 `.jsonl` 文件，结构与母本行为完全一致。`[PASS]`
2. **用例 2（开关为 1 精确读次）**：模拟 2 个有效单帧沿（100→101, 101→102），四 VA 各读取 2 次，`f_pre` 与 `f_post` 各读取 2 次，每沿恰好追加 4 次业务 VA 读 + 2 次帧号读，产出 2 条有效事件且均含双 markers。`[PASS]`
3. **用例 3（读失败记 null 不补 0）**：模拟读失败与抛异常，`values` 中 `gen_stamp` 与 `threat_calls` 准确置为 `None`，JSONL 序列化为 `null`，有效数值 0 保持 0，未出现补 0 现象。`[PASS]`
4. **用例 4（S4 命中立即停手）**：注入模块命中 `ra2render.dll` 时，`s4_injection_gate` 返回 `False`（即使强制传 `authorized=True` 依然拦截）；`_measure_run` 检测到命中直接中止返回，未调用任何采样。`[PASS]`
5. **用例 5（--allow-loader + 扩项拒绝启动）**：CLI 传入 `--allow-loader` 与 `--w5-ext 1`（或 `--measure-ext 1`）时，`main()` 前置拦截，直接返回退出码 `62`，绝不启动任何进程。`[PASS]`
6. **用例 6（帧冻结窗零样本）**：模拟逻辑帧恒定为 300 不动的冻结窗，事件数为 0（零样本），四 VA 读取数为 0；`stats` 记录 `frame_clock_freeze_max_s` 并带有明确声明注记：「`frame_clock_freeze_max_s` 只说明【CurrentFrame 帧号】连续未变的最长时段；不得据此宣称业务字段冻结」。`[PASS]`

---

## 7. 诚实账与未验项说明

1. **零真机声明**：本任务所有代码编写、静态差分与单测验证均在本地离线环境下完成，**零真机发射**，未启动 `gamemd.exe` / `ra2loader.exe` / `YURI.exe`，未读取真实活进程内存。
2. **母本零修改声明**：`lead/goal1_harness8_20261031/` 目录下全部文件保持只读，未做任何修改。
3. **自认未验项**：
   - **未验真机 RPM 延迟对 500 Hz 定拍周期的具体挤占量**：虽然静态测算追加的 6 次 RPM（约 60–120 µs）占 2 ms 拍周期的 3%–6% 不致引起崩溃，但尚未在活进程上实测具体抖动。
   - **未验真实游戏多线程环境下的四 VA 撕裂率**：因四 VA 地址不连续，非原子快照，虽然设计了前后帧号校验（`cross_frame` 标记），但真实高并发下的跨帧率尚待后续 3 趟真机验证。
