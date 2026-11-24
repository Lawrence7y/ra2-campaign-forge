# Q1 扩项副本本体独立复核报告

> **复核员**：复核员·Q1（独立复核，默认怀疑，不采信执行者自述）  
> **复核对象**：`lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py`（扩项副本本体）及关联交付物与证明  
> **复核依据**：`lead/re_line_20261105/W5_HARNESS_EXT/TASK.md` §2 Q1–Q4、`A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`、`A2_EDGE_BURDEN/A2_EDGE_BURDEN.md`、`A3_S4_INJECTION_CENSUS/A3_S4_INJECTION_CENSUS.md`  
> **执行约束**：零真机、不跑副本本体、零母本修改、唯一写域 `reviews/`。

---

## 1. 复核裁决与核心结论

| 审评项目 | 结论 / 取值 | 说明 |
|---|---|---|
| **复核判定 (verdict)** | **`CONFIRMED`** | 扩项副本完全满足任务书所有刚性约束与指标 |
| **实质缺陷 (substantiveDefect)** | **`false`** | 无读数错误/丢失，无 null 变 0，flag-off 行为与母本逐字相同 |
| **逐条异议 (objections)** | **0 条阻断异议**（含 2 条非阻断审计观察） | 见 §4 详细分析 |
| **必须改项 (mustFix)** | **无 (空列表 `[]`)** | 代码与测试已全量对齐规约，可直接准入后续阶段 |

---

## 2. 四大核心判据逐项核验

### 2.1 判据 Q1：副本本体架构与块标记
1. **删块即还原（Byte-level Reversibility）**：
   - 副本 `qc151_trip.harness8_v4_ext.py`（498,772 字节，9,087 行）严格以 8 个 `# >>> W5EXT-BEGIN` 至 `# <<< W5EXT-END` 包裹全部新增逻辑。
   - 复核员独立编写脚本剥离 8 个块后，产出文本字节数 489,502，SHA256 为 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`，与母本 `qc151_trip.harness8_v4.py` **逐字节完全一致（Match: True）**。
2. **开关为 0 时逐字相同（Flag-off 房规）**：
   - CLI 参数 `--w5-ext` 与 `--measure-ext` 缺省均为 `0`。
   - `_W5_STATE["on"]` 缺省为 `False`。
   - 块 2 `s4_scan_names` 带有 `if _W5_STATE["on"]:` 守卫，flag-off 时直接返回母本结果，无额外 list/dict 分配；
   - 块 3 `s4_injection_gate`、块 4 `_measure_poll_span`、块 5 `_measure_write_json` 均有 `if not _W5_STATE["on"]: return mother(...)` 透传；
   - 块 6 `_measure_run` 仅在 `_W5_STATE["on"]` 下检查，flag-off 直通母本；
   - 块 8 `main-gate` 在 `not _w5_on` 下不修改 `args.measure`，不触发阻断；
   - 经实测证明：flag-off 时零追加四 VA 读取，零额外 rec 审计行，零 `w5_events.jsonl` 文件生成，payload 无扩展键污染。
3. **S4 硬断言与 `--allow-loader` 拒绝**：
   - **三重防护门禁**均已写进代码：
     - `main-gate`（第 7723–7731 行）：`_w5_on and args.allow_loader` 立即退出并返回 `EXIT_INJECTION_SUSPECTED(62)`；
     - `s4-gate-hook`（第 1249–1283 行）：`authorized` 分支阻断返回 `False`，记录 `FAILED_ALLOW_LOADER` 与 `s4_exit_code=62`；命中非空或母本失败时阻断返回 `False`，记录 `FAILED_INJECTION_SUSPECTED`；
     - `measure-run-hook`（第 5579–5604 行）：进入采样循环前硬断言 `ra2render_hits == [] and ra2loader_hits == []`，非干净或 `A8_ALLOW_LOADER[0]==True` 立即 `return` 停手，零采样循环进入。

---

### 2.2 判据 Q2：机械改动面证明核验
复核员实跑 `python -I -X utf8 lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py`，`EXIT=0`：
1. **SHA256 对照**：
   - 母本 SHA256：`38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`
   - 副本 SHA256：`eb53a61723c43924ac0b16de495e7dcc77cf530f92b2100c5b7594f44407f45b`
   - 删块后 SHA256：`38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`（PASS）
2. **逐行 diff 统计支撑**：
   - 新增：`230` 行（全部位于 8 个块内）
   - 删除：`0` 行
   - 修改：`0` 行
   - 母本原有 8,857 行零变动（PASS）。
3. **禁止面高危 API 静态扫描**：
   - `WriteProcessMemory`: 母本 3, 副本 3, 差异 **+0**
   - `CreateRemoteThread`: 母本 1, 副本 1, 差异 **+0**
   - `SuspendThread`: 母本 0, 副本 0, 差异 **+0**
   - `MiniDumpWriteDump`: 母本 11, 副本 11, 差异 **+0**
   - `StackWalk`: 母本 0, 副本 0, 差异 **+0**
   - `SetWindowsHookEx`: 母本 1, 副本 1, 差异 **+0**
   - 全部禁止面 API 增量严格为 0（PASS）。

---

### 2.3 判据 Q3：离线单测覆盖与断言强度
复核员实跑 `python -I -X utf8 lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py`，`EXIT=0`：
1. **六项用例全绿**：
   - Case 1（开关为 0 零行为差）：`PASS`
   - Case 2（开关为 1 每沿 4 业务读 + 2 帧号读）：`PASS`
   - Case 3（读失败记 null 不补 0）：`PASS`
   - Case 4（S4 命中立即停手且阻断采样）：`PASS`
   - Case 5（--allow-loader + 扩项拒绝启动）：`PASS`
   - Case 6（帧冻结窗零样本且不宣称零成本）：`PASS`
2. **断言强度审计（无放宽断言）**：
   - 读失败严格区分 `None` 与 `0`：不仅断言 `vals["gen_stamp"] is None`，同时硬断言 `vals["gen_stamp"] != 0`，有效 `dirty_rect_count == 0` 则断言保留 `0` 且 `is not None`；
   - JSON 序列化严格断言文本存在 `"gen_stamp":null` 且绝不存在 `"gen_stamp":0`；
   - 读序全序严格断言时间戳单调链：`ts[f_pre] <= ts[gen_stamp] <= ts[threat_calls] <= ts[dirty_rect_count] <= ts[bullet_count] <= ts[f_post_start]`；
   - 门禁阻断严格断言探针标志 `sampling_invoked is False`，物理切断轮询。

---

### 2.4 判据 Q4：观测负担复算（对齐 A2）
复核员实跑 `python -I -X utf8 lead/re_line_20261105/W5_HARNESS_EXT/_w5_burden.py`，`EXIT=0`：
1. **同批 87 窗核验**：
   - 扫描数据源 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/measure_w*.json`（101 文件）；
   - 排除 14 个非标准窗（`span_s != 25.0` 或空样占位），精确纳入 **87 个完整 25 s 窗**；
   - 既有总读次 `1,080,975`、总沿数 `28,309`、最坏窗 `QC161-U0800-L3-20261023R/w0`（`n_edges=784`）与 A2 基线完全一致。
2. **差异归因诚实充分**：
   - 扩项副本实际执行每沿 6 次 RPM（`f_pre` + 4 业务 VA + `f_post`，共 24 字节），而非 A2 估算的 4 次 RPM；
   - 读数放大 1.5 倍，导致整体增幅由 A2 的 `+10.475%` 升至 **`+15.713%`（模型 A）/ `+15.665%`（模型 B）**；最坏窗增幅由 `+25.08%` 升至 **`+37.63%`（模型 A）/ `+37.58%`（模型 B）**；最坏窗读速率 **188.2 reads/s**；
   - 复算报告明确给出 D-19 §1 第 5 条规约中防止跨帧撕裂的架构原因，**拒绝强行削足适履凑数对齐 A2**，符合严谨审计标准。

---

## 3. 复核员独立重跑命令与输出证据

### 3.1 独立验证「删块即还原」与 SHA256 逐字节匹配
执行独立验证代码：
```bash
python -I -X utf8 -c '
import hashlib
with open(r"D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py", "rb") as f:
    m = f.read()
with open(r"D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py", "rb") as f:
    e = f.read()
lines = e.split(b"\n")
restored, in_block, b_cnt = [], False, 0
for l in lines:
    if b"W5EXT-BEGIN" in l: in_block = True; b_cnt += 1; continue
    if b"W5EXT-END" in l: in_block = False; continue
    if not in_block: restored.append(l)
res_b = b"\n".join(restored)
print("Mother bytes:", len(m), "SHA256:", hashlib.sha256(m).hexdigest())
print("Restored bytes:", len(res_b), "SHA256:", hashlib.sha256(res_b).hexdigest())
print("Blocks stripped:", b_cnt, "Match:", res_b == m)
'
```
**实跑输出**：
```text
Mother bytes: 489502 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
Restored bytes: 489502 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
Blocks stripped: 8 Match: True
```

### 3.2 改动面证明脚本实跑
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```
**实跑输出关键片段**：
```text
母本字节数: 489502, 母本行数: 8857, 母本 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
副本字节数: 498772, 副本行数: 9087, 副本 SHA256: eb53a61723c43924ac0b16de495e7dcc77cf530f92b2100c5b7594f44407f45b
[检验 1: 删块即还原] 8 块剥离后 SHA256 逐字节一致 >> PASS
[检验 2: 改动面清单] 新增 230 行, 删除 0 行, 修改 0 行 >> PASS
[检验 3: 禁止面扫描] 6 项高危 API 差异全部为 +0 >> PASS
最终判定: PASS
```

### 3.3 离线单测实跑
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"
```
**实跑输出关键片段**：
```text
[FATAL] W5EXT 冲突：拒绝在 --allow-loader 下启用扩项采样！
[FATAL] W5EXT 冲突：拒绝在 --allow-loader 下启用扩项采样！
...
  [PASS] Case 1: 开关为 0 ⇒ 不产生任何新采样行（零行为差结构证明）
  [PASS] Case 2: 开关为 1 ⇒ 每沿恰好追加 4 次读 + 2 次帧号读
  [PASS] Case 3: 读失败 ⇒ 字段为 null，不是 0
  [PASS] Case 4: S4 命中 ⇒ 立即停手（不得进入采样）
  [PASS] Case 5: --allow-loader + 扩项 ⇒ 拒绝启动
  [PASS] Case 6: 帧冻结窗 ⇒ 零样本，且不宣称该窗零成本
总计: 6 用例, 通过: 6, 失败: 0
最终判定: PASS (EXIT=0)
```

---

## 4. 细节释疑与观察项分析

1. **澄清 Leader Spotcheck 中的 D-W5-1 疑点**：
   - 驱动器在早期核查记录（`_LEADER_SPOTCHECK.md` §2）中指出 `authorized` 分支漏写 `S4/s4_gate` 记录；
   - 经复核员核实，在当前落地版本 `qc151_trip.harness8_v4_ext.py:1258-1260` 中，已严格补齐了：
     ```python
     rec.add("S4", "s4_gate", "w5_refused_allow_loader", "script:s4_injection_gate", note=...)
     rec.add("S4", "s4_exit_code", EXIT_INJECTION_SUSPECTED, "script:s4_injection_gate")
     ```
   - 驱动器核查脚本 `_leader_reads_and_beat.py` 曾报错是因为其脚本从第 0 行开始正则搜索 `def s4_injection_gate` 时匹配到了母本原始函数（第 1117 行）而非 Hook 包装函数（第 1253 行）。实际代码审计轨迹完整，**该疑点已彻底澄清并闭环**。
2. **观察项：枚举失败收口码**：
   - 当 `s4_enum_modules` 返回失败（`names is None`）时，母本设退出码为 `EXIT_MODULE_ENUM_FAILED(63)`。Hook 层的兜底逻辑 `if ... or not res:` 会将其重置为 `EXIT_INJECTION_SUSPECTED(62)`。
   - 判定：62 与 63 均为不可恢复的本趟硬终止致命码，不破坏 Fail-closed 铁律，不构成实质缺陷。
3. **观察项：Section Q2 报告状态滞后**：
   - `sections/Q2_DIFF_PROOF.md` 为 phase 1 执行期间生成的阻断快照，当时 Q1 尚未写出；随后实际产出就绪，`_w5_diff_proof_out.txt` 已为 PASS。总报告集成时采纳最新 PASS 证据即可。

---

## 5. 必须改项（mustFix）与逐条异议（objections）

- **必须改项 (mustFix)**：无。
- **逐条异议 (objections)**：无阻断性异议。

---

## 6. 诚实账

1. **复核员亲验**：
   - 独立验证母本与副本的 SHA256 哈希及删块恢复 SHA256 逐字节相等；
   - 独立使用 difflib 比对验证删除 0 行、修改 0 行、纯新增 230 行；
   - 独立扫描 6 项禁止面 API 计数（差异全 +0）；
   - 独立重跑 `_w5_diff_proof.py`（EXIT=0）、`_w5_test.py`（EXIT=0）、`_w5_burden.py`（EXIT=0）；
   - 查验全部 6 项离线测试用例的断言严格性与真实覆盖度。
2. **复核员未验**：
   - 零真机：不启动真实游戏进程，不触碰真实 Windows 活进程内存，不运行副本主流程。
   - 真机高并发下的跨进程 RPM 耗时抖动与多线程撕裂率属于真机验证步骤，离线审计不予臆测。
3. **写域守则**：仅在 `lead/re_line_20261105/W5_HARNESS_EXT/reviews/` 下写入本文件，仓库其他任何目录零修改。
