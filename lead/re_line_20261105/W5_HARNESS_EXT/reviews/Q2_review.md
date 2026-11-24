# Q2 · 改动面证明独立复核报告

> **复核员**：复核员·Q2（独立复核，默认怀疑，不采信执行者自述）  
> **复核对象**：`lead/re_line_20261105/W5_HARNESS_EXT/sections/Q2_DIFF_PROOF.md`、改动面证明机械脚本 `_w5_diff_proof.py` 及输出 `_w5_diff_proof_out.txt`  
> **基准母本**：`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`（489,502 字节，SHA256 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`）  
> **待验副本**：`lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py`（498,772 字节，SHA256 `eb53a61723c43924ac0b16de495e7dcc77cf530f92b2100c5b7594f44407f45b`）  
> **复核依据**：`lead/re_line_20261105/W5_HARNESS_EXT/TASK.md` §2 Q2、D-19/D-20 裁决书  
> **执行纪律**：零真机、不跑副本本体、零母本修改、唯一写域 `reviews/`。

---

## 0. 复核裁决与核心结论

| 审评项目 | 结论 / 取值 | 说明 |
|---|---|---|
| **复核判定 (verdict)** | **`CONFIRMED`** | 机械改动面证明三大判据全项实跑通过，删块即还原 SHA256 完全闭合 |
| **实质缺陷 (substantiveDefect)** | **`false`** | 无让读数错/丢/null 变 0 缺陷，flag-off 行为与母本逐字相同 |
| **必须改项 (mustFix)** | **无 (空列表 `[]`)** | 代码、证明脚本与输出一致闭合，直接准入总报告合成 |
| **逐条异议 (objections)** | **0 条阻断异议**（含 2 条文档流转说明） | 见下文详细分析 |

### 异议与流转审计说明 (Objections)
1. **阶段性阻断已消除**：执行者在 Phase 1 阶段初次提交自述及 `sections/Q2_DIFF_PROOF.md` 草稿时，因并发轮询前置 Q1 副本超时而记录为阻断状态（`blocking: true`）并列出三项自认未验。复核员独立核验表明，前置 Q1 副本件 `qc151_trip.harness8_v4_ext.py`（498,772 字节）已于后续时序就位并完成构建；复核员实跑机械证明脚本 `_w5_diff_proof.py`，证实三项判据（删块即还原、零改动零删除、禁止面 API 零增量）已全部真实通过（`EXIT=0`），历史阶段性阻断已彻底解除。
2. **正文草稿滞后提示**：磁盘上的检验输出 `_w5_diff_proof_out.txt` 已记录为全项 PASS，但 `sections/Q2_DIFF_PROOF.md` 文档草稿仍停留在初次等待 Q1 时的阻塞态描述。总报告 `W5_HARNESS_EXT.md` 应以复核员实跑和 `_w5_diff_proof_out.txt` 之最新 PASS 判定为准入账。

---

## 1. 三大判据逐项机械核验

### 1.1 判据 1：SHA256 对照是否实跑过（删块即还原）
- **核验方式**：复核员独立重跑 `_w5_diff_proof.py`，并编写独立 Python 探针剥离所有以 `# >>> W5EXT-BEGIN` 至 `# <<< W5EXT-END` 包裹的块，对剥离后字节流计算 SHA256 与字节一致性。
- **实测数据**：
  - 母本字节数：`489,502` 字节，LF 换行符（CRLF = 0）
  - 母本 SHA256：`38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`
  - 副本字节数：`498,772` 字节，LF 换行符（CRLF = 0）
  - 副本 SHA256：`eb53a61723c43924ac0b16de495e7dcc77cf530f92b2100c5b7594f44407f45b`
  - 剥离 8 个 `W5EXT` 插入块后字节数：`489,502` 字节
  - 剥离后 SHA256：`38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`
  - 逐字节全等判定：`restored_bytes == mother_bytes` 严格为 `True`。
- **判定结果**：**PASS**（删块即还原证明真实无误，SHA256 逐字节完全一致）。

### 1.2 判据 2：「删除 0 修改 0」是否有逐行 diff 计数支撑（改动面清单）
- **核验方式**：使用 `difflib.SequenceMatcher` 对母本文本行与副本文本行做逐行 diff 分析，严查是否存在未受控的删除、替换或修改。
- **实测数据**：
  - `added_lines`：**230 行**（分布在 8 个独立插入块中）
  - `deleted_lines`：**0 行**
  - `modified_lines`：**0 行**
- **8 个插入块精确行区间核实**：
  1. `[INSERT]` 副本第 176 ~ 211 行（母本第 175 行后插入 36 行，块名 `imports`）
  2. `[INSERT]` 副本第 999 ~ 1009 行（母本第 962 行后插入 11 行，块名 `s4-scan-hook`）
  3. `[INSERT]` 副本第 1249 ~ 1283 行（母本第 1201 行后插入 35 行，块名 `s4-gate-hook`）
  4. `[INSERT]` 副本第 4128 ~ 4197 行（母本第 4045 行后插入 70 行，块名 `poll-span-hook`）
  5. `[INSERT]` 副本第 4978 ~ 5014 行（母本第 4825 行后插入 37 行，块名 `json-hook`）
  6. `[INSERT]` 副本第 5579 ~ 5604 行（母本第 5389 行后插入 26 行，块名 `measure-run-hook`）
  7. `[INSERT]` 副本第 7711 ~ 7716 行（母本第 7495 行后插入 6 行，块名 `argparse`）
  8. `[INSERT]` 副本第 7723 ~ 7731 行（母本第 7501 行后插入 9 行，块名 `main-gate`）
- **判定结果**：**PASS**（母本原有 8,857 行完全未变，纯新增 230 行全部处于块标记内）。

### 1.3 判据 3：禁止面扫描是否与母本同数
- **核验方式**：对 TASK.md §2 Q2 规定的 6 项 Windows API 在母本与副本全文进行大小写敏感字符串计数对比。
- **实测比对表**：

| 受限 API 名称 | 母本出现次数 | 副本出现次数 | 增量 (副本 - 母本) | 合规判定 |
|---|---|---|---|---|
| `WriteProcessMemory` | 3 | 3 | **+0** | **PASS** |
| `CreateRemoteThread` | 1 | 1 | **+0** | **PASS** |
| `SuspendThread` | 0 | 0 | **+0** | **PASS** |
| `MiniDumpWriteDump` | 11 | 11 | **+0** | **PASS** |
| `StackWalk` | 0 | 0 | **+0** | **PASS** |
| `SetWindowsHookEx` | 1 | 1 | **+0** | **PASS** |

- **判定结果**：**PASS**（所有受限高危 API 出现次数均未增加，增量全部严格为 0）。

---

## 2. 复核员独立实跑记录与证据

复核员在独立 shell 环境中执行机械验证命令：

```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```

**执行退出码**：`EXIT=0`

**实跑完整输出原文**：
```text
================================================================================
W5 改动面证明 (Q2) 机械验证
================================================================================
母本路径: D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py
副本路径: D:\Project\ra2-campaign-forge\lead\re_line_20261105\W5_HARNESS_EXT\qc151_trip.harness8_v4_ext.py
--------------------------------------------------------------------------------
母本字节数: 489502
母本行数:   8857
母本 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
母本禁止面 API 出现基线:
  - WriteProcessMemory: 3
  - CreateRemoteThread: 1
  - SuspendThread: 0
  - MiniDumpWriteDump: 11
  - StackWalk: 0
  - SetWindowsHookEx: 1
--------------------------------------------------------------------------------
副本字节数: 498772
副本行数:   9087
副本 SHA256: eb53a61723c43924ac0b16de495e7dcc77cf530f92b2100c5b7594f44407f45b
--------------------------------------------------------------------------------
[检验 1: 删块即还原]
识别到 W5EXT 插入块数量: 8
  块 #1: 行 176 ~ 211 (共 36 行)
  块 #2: 行 999 ~ 1009 (共 11 行)
  块 #3: 行 1249 ~ 1283 (共 35 行)
  块 #4: 行 4128 ~ 4197 (共 70 行)
  块 #5: 行 4978 ~ 5014 (共 37 行)
  块 #6: 行 5579 ~ 5604 (共 26 行)
  块 #7: 行 7711 ~ 7716 (共 6 行)
  块 #8: 行 7723 ~ 7731 (共 9 行)
删块后字节数: 489502 (母本: 489502)
删块后 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
母本   SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
>> 检验 1 判定: PASS (删块后内容与母本逐字节完全一致)
--------------------------------------------------------------------------------
[检验 2: 改动面清单]
  [INSERT] 副本第 176~211 行 (母本第 175 行后插入 36 行)
  [INSERT] 副本第 999~1009 行 (母本第 962 行后插入 11 行)
  [INSERT] 副本第 1249~1283 行 (母本第 1201 行后插入 35 行)
  [INSERT] 副本第 4128~4197 行 (母本第 4045 行后插入 70 行)
  [INSERT] 副本第 4978~5014 行 (母本第 4825 行后插入 37 行)
  [INSERT] 副本第 5579~5604 行 (母本第 5389 行后插入 26 行)
  [INSERT] 副本第 7711~7716 行 (母本第 7495 行后插入 6 行)
  [INSERT] 副本第 7723~7731 行 (母本第 7501 行后插入 9 行)
改动统计: 新增 230 行, 删除 0 行, 修改 0 行
>> 检验 2 判定: PASS (母本原有行零改动，纯新增 230 行)
--------------------------------------------------------------------------------
[检验 3: 禁止面扫描]
  - WriteProcessMemory    : 母本= 3, 副本= 3, 差异=+0 [OK]
  - CreateRemoteThread    : 母本= 1, 副本= 1, 差异=+0 [OK]
  - SuspendThread         : 母本= 0, 副本= 0, 差异=+0 [OK]
  - MiniDumpWriteDump     : 母本=11, 副本=11, 差异=+0 [OK]
  - StackWalk             : 母本= 0, 副本= 0, 差异=+0 [OK]
  - SetWindowsHookEx      : 母本= 1, 副本= 1, 差异=+0 [OK]
>> 检验 3 判定: PASS (所有禁止面 API 出现次数均未增加)
================================================================================
最终判定: PASS
================================================================================
```

---

## 3. 实质缺陷核查与代码审计

依据任务书定义，实质缺陷指「会让读数错/丢/null 变 0，或让 flag-off 行为不再逐字相同」。复核员对改动面代码进行逐项审查：

1. **读失败处理（null 不补 0）**：
   - 查证 `A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:98-109`：`read_one` 针对异常、非 int 类型、bool 子类及越界数值均显式返回 `None`；
   - 查证 `qc151_trip.harness8_v4_ext.py:4164`：沿触发追加读取通过 `frame_edge_sampler.read_sample` 执行，读失败字段在字典中严格保存为 `None`，序列化到 `measure_w{k}_w5_events.jsonl` 中呈现为标准 JSON `null`；真实值 0 保持 0，绝无补 0 逻辑。
2. **Flag-off 行为逐字相同（零计算与语义差）**：
   - CLI 参数 `--w5-ext` 缺省 0，`_W5_STATE["on"]` 缺省 `False`；
   - 块 2 `s4_scan_names`：`if _W5_STATE["on"]:` 守卫拦截，flag-off 时直接返回原母本 scan 字典；
   - 块 3 `s4_injection_gate`：`if not _W5_STATE["on"]: return res` 直接早退；
   - 块 4 `_measure_poll_span`：`if not _W5_STATE["on"]: return _measure_poll_span_mother(...)` 直接透传；
   - 块 5 `_measure_write_json`：`if not _W5_STATE["on"]: return _measure_write_json_mother(...)` 直接透传，不生成额外 jsonl，不注入 `w5_ext` 键；
   - 块 6 `_measure_run`：`if _W5_STATE["on"]:` 守卫，flag-off 零追加检查；
   - 块 8 `main-gate`：`_w5_on` 为 False 时不拦截 `--allow-loader`，不修改 `args.measure`；
   - 因此，flag-off 行为与母本逐字相同，零行为差。
3. **结论**：**`substantiveDefect = false`**。

---

## 4. 诚实账与核验边界

1. **复核员实跑**：
   - `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"`（`EXIT=0`，全项 PASS）
   - 独立 Python 校验探针（SHA256 逐字节全等验证、逐行 diff opcodes 统计、禁止面 API 穷举扫描）
2. **复核员未运行**：
   - 严守铁律：未启动任何游戏进程（零真机、不发 `gamemd.exe` / `ra2loader.exe` / `YURI.exe`）；
   - 未运行副本本体 `qc151_trip.harness8_v4_ext.py`（只做纯静态差分审计与离线单测）；
   - 零母本修改（母本文件保持完全只读）。
3. **未验项说明**：
   - 未在活进程上测量真机环境下的单次跨进程 RPM 微秒耗时；
   - 未在真实高并发物理机上实测非原子四 VA 读取的跨帧撕裂率。
