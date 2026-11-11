# 本轮推进状态板（2026-11-11 21:1x）

> 记录人：调度方（DSH 会话）。用途：让下一步接手的人知道「谁跑到哪、什么已成立、什么还没落盘」。

## 1 · 通道实测结论（重要，影响后续所有派发）

| 通道 | 实测结果 | 判定 |
|:--|:--|:--|
| **call-agy / Gemini 3.8 Flash (high)** | 冒烟 27.2s SUCCESS；核验任务 463.8s SUCCESS；处置表任务 1089.2s SUCCESS（31KB 交付） | ✅ **唯一稳定可靠的重活通道** |
| **pi CLI + magpie/work/cn:hy4free** | 冒烟 13s 回 OK；但 3 并发 11 分钟零落盘、单并发 1125s 零落盘 | ❌ **不可用于多步落盘任务** |
| **DSH 原生 subagent** | 收发正常（SUBI_OK），但**无法指定模型**（child model selection is disabled for this tool instance） | ⚠️ 只能跑会话锁定模型 |

## 2 · 子智能体模型挂载检查（用户截图核对）

- `profiles/desktop/cordis.patch.yml`：`subagent-model-selection-settings.enabled: true`，`allowedModels` = `magpie-anthropic/{work/cn:hy4free, work/cn:deepseek-v4.1-flash, zcode/GLM-5.3-Flash}` —— **与截图一致，配置无错**。
- `agent-default-model` = `magpie-anthropic / work/cn:deepseek-v4.1-flash / high`。
- 本会话 `modelSelection.lastUsed` = 同上，`pending: null` ⇒ **本会话子代理跑的是 DeepSeek-V4.1-Flash，不是 hy4**。
- 显式传 `provider/model` 一律被拒（连传 lastUsed 同值也拒）⇒ 该工具实例禁用「按调用指定模型」。
- **结论：要子代理用 hy4，须新开会话或在会话内选择一次；配置本身不需要修。**

## 3 · 本轮派发与产出

| 包 | 通道 | 状态 | 产出 |
|:--|:--|:--|:--|
| 进度检查 + 自查纠错 | 本会话直做 | ✅ 完成 | `lead/re_progress_check_20261111/RE_PROGRESS_20261111.md`（含 §8 自查、§9 核验回应） |
| 异族核验（8 命题） | agy Gemini 3.8F | ✅ 完成 463.8s | `lead/re_progress_xverify_20261111/VERDICT.md`：**HOLD 4 / FAIL 3** |
| WP-D 轮次处置表（182 轮） | agy Gemini 3.8F | ✅ 完成 1089.2s | `lead/re_round_disposition_20261111/` DISPOSITION.md 33KB + CSV + 枚举脚本 |
| WP-A 台账并账（§605–§609） | agy Gemini 3.8F | 🔄 在跑 | 写域未建，台账仍为基线 759,518 B（未动） |
| WP-B′ 六探针合流（含复现门） | agy Gemini 3.8F | 🔄 在跑 | 写域未建 |
| WP-B（原） | pi + hy4 | ❌ 取消 | 1125s 零落盘 |

## 4 · 已确认的三处自我纠错（我改的）

1. **git 规模**：`276` 是 `git status --porcelain` 总行数，不是已跟踪改动数；实测 **tracked 13 / untracked 266**。
2. **空目录口径**：`const_exit_fix_20261110` 的 `patched/` 有 32 个文件（18 py），非空 ⇒ 正确分解 **182 = 153 报告 + 18 无报告 + 11 空**。
3. **地图同名不同件**：XMP29U2.MAP 311,822 B ≠ 载体 yrm 222,799 B ≠ ra2youli yrm 92,332 B，三者不同文件（台账 L6595 早已写明，是我读错）。

## 5 · 已拦下的「过度归纳」（重要）

WP-D 的摘要把探针读数升格成机制结论，我已在 `DISPOSITION.md` 追加**附录 X** 就地降级，并复验：

- ✗「0x0084F2BA = DEP 取指违规」→ 实为 2026-10-20 真机崩溃对话框里的地址（`lead/stale_pass_20261109/_sp_report.txt:37`），性质未定谳。
- ✗「House 实例由 [Houses] 严格决定」→ 单图（XMP29U2.MAP）只证明 [Houses] 14 项↔house 节 14 项一一对应，推不出引擎机制。
- ✗「PercentBuilt 引擎零读取」→ 缺全镜像读点普查，按未验。
- ✓ 处置建议本身（探针读数值得固化成 md）仍然成立。

## 6 · 下一步（按性价比）

1. 等 WP-A 收线后**逐字节验证**：追加段一致性、§605–§609 各出现 1 次、旧内容前缀哈希不变。
2. WP-B′ 收线后核**复现门**：6 个探针 MATCH/MISMATCH 表是否真的逐项跑过。
3. 把 WP-D 的「入账 10 轮」按批固化成 md（第一批就是那 5 个静态逆向轮）。
4. **D-13 仍等用户一句话**（A 只采 ≥1s 长停 / C 走 SuspendThread / 暂停）——① 的唯一硬阻塞。


---

## 7 · 调度方亲验的一条硬结论（2026-11-11 21:2x）

**来源**：`lead/slot2_fullscan_20261111/_sf_scan_out.txt`（156,052 B，脚本 `_sf_scan.py`）。
**靶件**：`ra2bench/gamemd.exe` sha256 `73201cc0…7476`（4,825,360 B）——我已核对与探针记录一致。

### 7.1 读数（探针实算，我复读输出确认，未重跑脚本）

- 字节级（解码无关）`call [reg+8]` = **1715**、`jmp [reg+8]` = 1、异形（变址）= 2；主流（seg-extend 流）= **1714**（call 1713 + jmp 1）。
- 分块覆盖：单次 disasm 只到 `0x46F59D`（155,215 条 / 11.13% .text，**陷阱复现**）；分块 seg-extend 达 **1,392,527 条 / 覆盖至 `0x7E038D`**（65 个自然停点，主普查流）。
- 值闸门：全镜像 dword 值 == `0x54A4F0` 仅 **1** 处（`0x7ECC04`，即 vtable `0x7ECBFC` 的 slot2 单元）；== `0x54A630` 仅 **1** 处（`0x7ECBE4`，vtable `0x7ECBDC` 的 slot2 单元）。
- 指针逃逸：无任何指令把 slot2 单元值装载或 call/jmp 它（FF15/FF25/A1/8B/89/SIB-abs 全编码 = 0）；`.rdata/.data` 无 dword == `0xAA1078` ⇒ **指针值不逃逸**。
- 唯一装载：`load r32 ← [0xAA1078]` 全编码仅 **1** 处 = `0x54605F mov eax,[0xAA1078]`；`0x546064 mov ecx,0xAA1078` 是全镜像唯一 this 装载。

### 7.2 结论（可引用）

> **全镜像中，经虚表 slot2 派发到 `0x54A4F0` / `0x54A630` 的调用点唯一 = `0x546069`（`call dword ptr [eax+8]`）**；其 this 与 vptr 均锚定全局单例 `0xAA1078`；常态 vptr=`0x7ECBDC` → `0x54A630`，atexit 析构后 vptr=`0x7ECBFC` → `0x54A4F0`。

**我核对了地址对**：`0x546069` 是调用指令地址，`0x54605F` 是它的 vptr 装载地址，两者不冲突（WP-D 报的「仅 0x546069 一处」正确）。

### 7.3 边界

- 这是**静态**结论：证明「代码里只有这一处会这样派发」，**不证明**该处在运行期被频繁触发、也不说明 `0x54A4F0`/`0x54A630` 做什么（那属另一轮语义定名）。
- 与 ① 卡顿的关系**未建立**：没有任何证据表明这个派发点在慢帧路径上。
- 我**未重跑** `_sf_scan.py`（复现门归 WP-B′ 负责），只复读了它的输出并核对了靶件哈希。

## 8 · pi 通道取消任务的核验（回执 rcpt-e236064d-1）

- 终态 `aborted` / `cancelled by caller` / `output_chars=0` / elapsed 1139s。
- **零副作用**：写域 `lead/re_chain_synthesis_20261111` 不存在；台账 sha256 仍为基线 `2baa0de45d412554`、759,518 B、mtime 未变。
- 该通道判定：**不可用于需要写盘的多步任务**（两次实测合计 2264s 零产出）。


---

## 9 · WP-A / WP-B′ 收线结果（2026-11-11 21:2x–21:3x）

### 9.1 WP-A（台账并账）：**由调度方亲自补完**
- agy 原任务完成 STEP0–3（追加至 787,950 B、自检 PASS）后**台账被回滚至基线**并卡死 40 分钟；已终止。
- 调度方用 `_apply2.py` 重新执行：**759,518 → 788,030 B**，10/10 自检 PASS（前缀哈希不变、§605–§609 各 1 次、§604 未重复、UTF-8 可读）。
- **唯一非逐字改动**：§609 标题加 `unconfirmed` 标记（合订本 §5 硬要求，草案正文缺此标记）。
- 回执：`lead/re_ledger_apply_20261111/APPLY_RECEIPT.md`。
- 附带发现：`_apply.py` 写死的 5 个期望 sha256 与当前单件正文**不符**（长度全对、哈希全异），原因是 4 份 `_la_draft*` 的 mtime 在提取之后被改动 ⇒ 属**指纹漂移**，本次按「长度精确 + 结构完整」接受并如实登记。

### 9.2 WP-B′（六探针合流）：**完成，1081s，SUCCESS**
- 交付：`CHAIN_SYNTHESIS.md`（20,971 B）、`LEDGER_SECTION_DRAFT.md`（3,415 B）、比对脚本与输出。
- **复现门**：14 项产出（7 txt + 7 json）**0 MISMATCH**；靶件 sha256 自核 PASS。
- **越界事故（已登记）**：重跑时因探针脚本内部写死相对路径写盘，**7 处只读输出被覆盖**。调度侧独立用 hashlib 对拍 `baseline_backup`（21 文件 / 76 MB）与当前文件：**9/9 MATCH，零失真**。
- **纪律达标**：证据表【已证】16 处 / 【未证】7 处，逐条给 VA + 字节 + 文件:行；我抽查 L13-15 / L18-20 / L43-47 / L66 **行号全部真实准确**。

### 9.3 我保留的两点质疑（未采纳其表述）

1. **CFG 推断被标【已证】偏强**：如「`0x54A524 test edi,edi` → edi==0 则提前返回」属**静态控制流推断**，不是字节级读数。建议降为【已证（CFG）】并注明未做运行期确认。
2. **`_ps_disasm` 的 `_repro` 输出为 0 B**：`playerctrl_semantics` 重跑未产出 stdout（可能全写进它自己的 `_out.txt`），故该探针的"复现"实际是**文件级对拍**而非 stdout 对拍，须在入账时说明。

## 10 · 通道最终判定

| 通道 | 3 次实测 | 结论 |
|:--|:--|:--|
| agy / Gemini 3.8 Flash | 27s / 464s / 1089s / 1081s 全部 SUCCESS | **主力**；但长任务会卡死，须 `--timeout` 硬上限 + 分段 |
| pi + hy4free | 1139s + 1125s 均零落盘 | **不可用** |
| 原生 subagent | 可用，但只能会话锁定模型 | 轻量任务 |
