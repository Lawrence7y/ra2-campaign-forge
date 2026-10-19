# DROPPED-611-AUDIT01 · 核实"611 个危险点被静默排除"（独立复算 · 只读审计）

- 执行：ZCode（GLM-5.3-Flash）· 日期 2026-10-05
- 写域：`lead/dropped611/**`（本件与其余交付件同目录；**主位置** = `out/re_work/work_chain/CONTINUE_20261003/lead/dropped611/`，并在仓根 `lead/dropped611/` 留有字节级镜像）
- 二进制：`ra2youli/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` / 4,825,360 B（**预检断言通过**，`raw/E01_sha256.out`）[实证]
- 工具链：python 3.12.10 + capstone 5.0.7；输入件时点钉定哈希见 `dropped611_recomputed.json → meta.inputs_pinned`
- 证据分级：`[实证]` = 字节级/命令级；`[推演]` = 由产物与字节推断；`[待实测]` = 未验

## §0 结论速览

| 命题 | 裁定 |
|---|---|
| **611 是否成立** | **成立**。从 `candidates.json` T3 全域独立重导出 2656 = 778（vtable-indirect）+ 1197（capable_fixed）+ 681（first_deref=None），与 g15 的 132 个 (族,被调方) 对**逐对全等**（132/132，sum=611，零差异）。`raw/E06_ab.json`、`raw/E17_sets.exitcode` |
| **611 ∩ 681** | **611 ⊂ 681**（∩ = 611，611\681 = ∅，681\611 = **70** 站、分布于 21 族）。不是 ∅-矛盾情形，无需紧急上报 |
| **是否静默丢弃缺陷** | **成立，且是两层**：①留痕层（A-90.6 已指出）：None 站点自 `n5_windows.tsv` 消失、无显式类别；②**正确性层（本卡新发现）**：`first_deref=None ⇒ 被调方从不解引用` 这个隐含等式**不成立**——112 中 **6 个被调方（22 站）字节级实证存在真实 this 解引用**（§3.2） |
| **对 2656 有无影响** | **分母 2656 不变**（它是 `danger_points_T3`，独立于该谓词；闭合算术不破）。但 **1975/681 的内部分割被实证错 ≥22 站**：681 应 ≤659、1975 应 ≥1997。凡以 1975 为分母的比值（如 1154/1975=58.4%）偏移约 1 个百分点内 |

## §1 A 组 · 计数复算

- **全域**：`candidates.json.families` 中 tier=T3 的 45 族的 `danger_drive` 逐条重导出，得 **2656** 条 (family,site,consumer)，(family,site) 无重复 —— 与 `candidates.json.counts.danger_points_T3=2656`（ACCEPTANCE.md:1741 引 `candidates.json:27`）一致 [实证]。
- **分桶**：consumer 为 `(vtable-indirect)` 或 None → 778；固定 consumer 且 `consumers[c].first_deref != None` → 1197；固定且 `first_deref == None` → **681**。778+1197+681 = 2656 闭合 [实证]（ACCEPTANCE.md:1741 的 `1975 = 1197 + 778` 同步成立）。
- **611/112**：g15 的 `pairs`（132 对）与我方逐对计数**全等**（`pair_diffs=[]`，sum=611）；`rows` 112 个被调方与"None 且不在 `n5_windows.tsv`/`new_windows.json`"的被调方集合**零差集**（None 被调方在两产物中的交集均为 0，见 `E06_ab.json → neverderef_in_windows / neverderef_in_new_windows`）[实证]。
- **"120"与"17 族"**：`new_windows.json` 顶层字段 `distinct_consumer_entries=120`、`families_in_scope` len=**17**、`family_consumer_pairs=125` [实证]；g15 的 132 对实际横跨 **15** 族（§6 不一致 #1）。
- **正对照（0 命中配对）**：`n5_danger_points.tsv` 中 `rc4_covered=='yes'` 共 **50** 行，50/50 落在我方 T3 全域、50/50 落在 capable 桶 —— 集合运算管道对已知命中目标全部命中 [实证]（`E06_ab.json → rc4_*`）。

## §2 B 组 · 611 vs 681 集合级判定（★最承重）

集合键 = (family_upper, site)，两集合同域（2656 内的 never_deref 子集）：

| 集合 | 大小 | 成员文件 |
|---|---|---|
| 611 | 611 站 | `raw/sets_611.tsv` |
| 681 | 681 站 | `raw/sets_681.tsv` |
| 611 ∩ 681 | **611** | — |
| 611 \ 681 | **0** | — |
| 681 \ 611 | **70** | `raw/sets_681_minus_611.tsv`（21 族，最大 0x00A8B254=21 站） |

- **判定：611 ⊂ 681。** A-90.6 的"静默排除"是 681 分母**内部的一次细分**（按 g15 的 15 族 scope 截取），2656 与 681 的算术不受其影响。
- **但是**（承重结论）：681 的**谓词本身**（None ⇒ 被调方从不解引用）被 §3.2 的 6 例字节级反例证伪一部分 —— 集合关系成立不等于成员定性正确。

## §3 C 组 · first_deref=None 的成因（抽样 + 全量辅助）

### 3.0 仪器与正对照
- 我方检测器：capstone 线性扫描（extent=ret/尾跳+padding/已知函数边界），跟踪 this：ecx 起，`mov` 链传播、`[ebp+disp]` 槽恢复、 callee-saved 存活；`lea` 不计为访问；`E9` thunk 跟随。
- **正对照 1**：RC-4 六入口 6/6 检出 deref [实证]（`E12_sweep.json → rc4`）。
- **正对照 2**：`new_windows.json` 的 120 个 distinct consumer（census 均有 deref）：我方检出 **111/120**，9 例假阴性（`newwin_disagree`）⇒ 我方灵敏度 ~92.5%，**这是我方下界口径** [实证]。
- ** extent 互证**：0x4068E0→1 条 ret、0x750920→71 条止 0x7509DA、0x6D2790→285 条止 0x6D2B42，与 g15 rows 的 census extent **逐字一致** [实证]。

### 3.1 任务要求的三类计数
**任务口径的分层 20 例（top-10 by sites + 种子 20261005 随机 10）内部：(i)=13，(ii)=0，(iii)=7。**
**追加全量复核后（27 例人工裁决，覆盖 413/611 站）：(i)=13 callees/245 站，(ii)=6/22，(iii)=8/149；未人工裁决 85 callees/195 站。**

- 关键方法学发现：**6 例 (ii) 全部不在分层 20 里** —— 漏报集中于低站点数被调方（最大仅 11 站），按站点数分层抽不到；是"检测器对 112 全量扫描 → 10 阳性 → 逐例字节复核"才抓到（10 阳性中 4 例是我方 `lea` 型假阳性，已剔除并记入 §6）。

### 3.2 类 (ii) —— census 漏解（6 例，22 站，全部 `[实证]` 字节证据）
| 被调方 | 站数 | 字节证据（全部在 census 一致 extent 内） |
|---|---|---|
| 0x004F9A50 | 11 | `mov eax,ecx`@entry → `mov edx,[eax+0x30]`@0x4F9A66、`test [eax+0x5788],edx`@0x4F9A7E |
| 0x004F9A90 | 2 | `mov esi,ecx`@0x4F9A91 → `mov ecx,[esi+0x30]`@0x4F9AB1、`mov eax,[esi+0x5788]`@0x4F9ACA |
| 0x0054F450 | 3 | `mov ebp,ecx`@0x54F459 → **写** `[ebp+0x24/0x25/0x26]`@0x54F4A5..、`lea edx,[ebp+0x14]` 作参 |
| 0x005ADD10 | 1 | `mov edi,ecx`@0x5ADD18 → `mov ax,[edi+0x35A0]`@0x5ADDE2、`repne scasb es:[edi]`@0x5ADE05（esi=&this+0x125C） |
| 0x00694760 | 3 | `mov edi,ecx`@0x69476A（无调用阻隔）→ `repne scasb es:[edi]`@0x69483C = strlen(this+0)，中段无 edi 重载 |
| 0x007B1DE0 | 2 | `call 0x7CA650` = **`__chkstk`（push ecx…mov ecx,[eax] 恢复 ⇒ 保 ecx）[实证]** → `mov edi,ecx`@0x7B1DEC → 读 `[edi+0x3F068]`、`mov edx,[edi]`+虚调 `call [edx+0x14]`、**写** `[edi+0x3F06C]`/`[edi+4]`/`[edi+0x3F068]` |

- 这 6 个被调方的**全部 39 条跨族 census 记录一律 `first_deref=None`**（`raw/E15_crossfam.out`）⇒ 漏报是仪器级、跨族一致的。
- 机制归属 `[推演]`（未读其源码，见 §7）：census/g15 自扫描可能跨调用杀死易失寄存器跟踪（0x7B1DE0 的 this 复制发生在 `__chkstk` 调用之后——而 chkstk 恰好保 ecx）；A-90.6 自称 "MY scan 0/112" 说明**其自扫描与 census 同盲**。

### 3.3 类 (i)/(iii) 代表例（完整 27 例表见 `dropped611_recomputed.json → C_adjudication.manual_27`）
- (i) 真无解引用（13 callees/245 站）：0x00750920（95 站——`cmp ecx,[0xB1D388]`+`mov ecx,[eax+ecx*4]`：**ecx 是 ID/索引，非对象指针**）；0x007C5F00（57 站，FPU 舍入助手，ecx 未用）；0x004068E0（16 站，空日志桩）；0x0068BCE0/0x0068BD00（把 `&this->field(arg)` 作栈参转发给 0x5657A0）；0x0048A4F0/0x0045E970（this 存入 edi 后仅传参/未用）等。
- (iii) this 不在寄存器（8 callees/149 站）：0x006D2790（56 站，入口第 2 条 `mov ecx,[0xB0CE88]`）、0x006D8700/0x0053A140（`mov ecx,0x87F7E8`）、0x0054F5C0（ecx=arg）、0x004A60E0/0x006D2070/0x006D2360（ecx=&local）、0x006DA740（尾部 `xor ecx,ecx` 后尾跳）。

## §4 三个点名例的字节复核（全部 `[实证]` VERIFIED）

1. **0x00750920**（95 站）："拿 ecx 当索引（非对象）" —— **成立**。`85c9  test ecx,ecx`@0x750939 → `3b0d 88d3b100  cmp ecx,[0xB1D388]`（边界检查）→ `a1 7cd3b100 / 8b0c88  mov eax,[0xB1D37C]; mov ecx,[eax+ecx*4]`（表索引）→ `8b19 mov ebx,[ecx]`（解引用的是**解析出的对象**，非全局值）。ecx 在体内从未作对象基址（deref=0）。
2. **0x006D2790**（56 站）："入口即覆写 ecx" —— **成立**。`83ec58 sub esp,0x58`@0x6D2790 → `8b0d 88ceb000 mov ecx,[0xB0CE88]`@0x6D2793（第 2 条）。入口 this 值此后再未使用。
3. **0x004068E0**（16 站）："空 stub C3+15×90" —— **成立**。字节 `c3909090909090909090909090909090`（`raw/E07_pe.json → bytes_4068E0`）。语义为被掏空的日志桩：0x5ADD10/0x694760/0x7B1DE0 等体内 `call 0x4068e0` 时 push 的全是 0x84xxxx 格式串指针，caller-cdecl 清栈。

## §5 D 组 · 裁定

1. **是否"普查侧静默丢弃"缺陷：成立。** 两层：
   - **留痕层**（A-90.6 已指出，本卡确认）：None 站点从 `n5_windows.tsv` 消失且无任何显式类别/告警 —— "找不到 ⇒ 排除，无留痕"。
   - **正确性层（本卡新发现，更重）**：`first_deref=None` 在下游被当作"被调方从不解引用"的充分判据进入 681，但 6 callees/22 站存在字节级 deref ⇒ **681 名实不符**。
2. **正确处置形态**：None 的站点应**显式登记为独立类别**（如 `first_deref=None(UNVERIFIED)` 并附 body extent 与复审位）随产物落盘，而不是从 `n5_windows.tsv` 静默消失；且 **None ≠ 从不解引用**，不得直接并入 681。
3. **对 2656 的影响：分母不变；1975/681 分割需修正 ≥22 站**（681：681→≤659；1975：1975→≥1997）。以 1975 为分母的比值（如 1154/1975=58.43%）相应偏移 ~1pp 内。**不需要**改 2656，也**不需要**改 611 的计数本身。

## §6 不一致清单（并列值，不凑数）

1. **17 vs 15 族**：g15_dropped.txt 称 "the 17 families"；其 `pairs` 实际横跨 **15** 族。`new_windows.json.families_in_scope` len=17 —— 差 2 个 in-scope 族无 dropped callees，属散文口径未对齐产物，非计数错误。
2. **0x004068E0 的 census extent 失真**：g15 row 记 `census_body=37 / extent_end=0x40691A`；真身 1 条 ret（extent 0x4068E1，§4）。其 extent 扫过 padding 与下邻函数 —— 不影响 `n_derefs=0` 的结论，但 "body" 记录不可直接引用。
3. **我方仪器勘误两件**：① extent 在 `ret` 后无 padding 时会过冲（0x007C5F00：我 162 vs census 20，census 对）；② 检测器把 `lea [base∈this]` 误计 deref（0x68BCE0/0x68BD00/0x6D2070/0x6D2360 四例假阳性，人工剔除）。10 例 (ii) 候选的最终 6 例均在**与 census 一致的 extent 内**复核，未受影响。
4. **我方灵敏度**：120 对照 9 例假阴性（§3.0）⇒ "我方未检出" 只是 92.5% 灵敏度下的下界口径。
5. **内存口传偏移勘误**：`file_off = VA−0x401000` 对本二进制**不成立**；`.text` PointerToRawData=0x1000 ⇒ `file_off = VA−0x400000`（census insn 0x7241A7 逐字互证 + 两处 extent 互证）。我方 E09 调试曾因此产出一批错位反汇编（已废弃，`raw/E09_debug.out` 仅作过程留痕）。
6. **A-90.6 的 "0/112" 与本卡 "6/112"**：两值并列，归因 = 双仪器共盲（§3.2 机制[推演]），非同一仪器的重复计算。

## §7 未发现项与枚举口径

- **132/132 对零差异** —— 在"从 `candidates.json` T3 danger_drive + consumers.first_deref 重导出"口径下，未发现任何 (family,callee) 计数不一致。
- 除 27 例人工裁决（413/611 站）外，其余 **85 个 dropped callees（195 站）仅有我方检测器的 deref=0 结论** —— "在了我方检测器+一致 extent 的枚举口径下未发现"，**不等于不存在**；灵敏度上界受 §6.4 约束。
- **未读** `nullthis_sweep/scripts/*.py`（避免触碰在飞卡的 mtime 门禁）⇒ census 漏报的确切代码机制只能是 [推演]。
- 未逐条复算 ACCEPTANCE.md 全文；仅引用了 grep 命中的 1741/1745/1746/2071 等行。

## §8 未读未验部分

`n3_families_raw.json`（12.8MB）、`n01_*` 三件、`families45.json` 的逐族明细（仅用了 counts）、`g01–g14` 几何件、`perf_alloc*/` 与 `new_windows_geometry/` 的其余产物（他卡写域，仅读了任务点名的 `g15_dropped.json/txt`）、ACCEPTANCE.md 非命中行。

## §9 是否需第四通道

**需要，但范围收窄为三件事**（不必全量重扫 2656）：
1. 用"跨调用保活至 callee-saved 寄存器"判据对 **112 个 None-callees** 复扫一遍（本卡的检测器 + 6 例字节样板可直接复用；`raw/dis_00*.txt` 27 份清单在案）；
2. 对已实证的 **6 callees/22 站**做 681→1975 重挂，并在重挂后重算 1154/1975 类比值；
3. 在 n5 产物链为 `first_deref=None` 类别建立**显式登记**（§5.2 形态），并对 0x004068E0（16 站）这类"空日志桩"单独标注（其危险点实为对桩的调用约定残留，非 nullthis 危险）。

—— 完 ——
