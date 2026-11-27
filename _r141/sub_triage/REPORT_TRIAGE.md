# R141-TRIAGE-RECOMPUTE · 独立复算报告

**角色**：执行员（hy4 / exec）  
**边界**：只读台账，不改 R14_COMMON/LEAD_LOCK/LEDGER/STATUS_BOARD/BOARD_ARCHIVE；未读取 `_ext/f_partial_triage/`（被复核方）。  
**输入**：`lead/next_re_20261117_r14/R17_R110_FACTINDEX_V538/FACT_INDEX.tsv`（54 行，sha256 `97eeef849a13a675e16d90f8984f3e9e4bca9d6250be3f675f4644cf8a265b04`）。  
**输出**：本报告 + `_r141/sub_triage/triage_recompute.tsv`（34 行 = 表头 + 33 条）。

---

## 1. 路径解析与部分失联集合

- 解析规则：`evidence_paths` 按 `;` 拆分；反斜杠转斜杠；`(…)` 后缀按卡文视为定位提示、剥离后取文件本体；判据 `os.path.exists(文件)`。
- 全体 54 条分布：**全部存活 20 条 / 全部失联 1 条（F23）/ 部分失联 33 条**。
- **部分失联集合实测为 33 条，不是卡面预期的 32 条**。我用的判据是卡文原话「至少一条路径失、且至少一条路径在盘」，按此得到：

```
F04 F06 F07 F08 F09 F10 F11 F12 F13 F14 F15 F16 F18 F19 F22 F24
F25 F27 F28 F29 F34 F35 F36 F39 F43 F44 F45 F46 F47 F48 F49 F51 F52
```

差异说明（如实报）：卡预期 32，实测 33；多出的候选项是 **F13**（alive=2 失联=2）或某条边界项，取决于外部报告如何定义「旁证」。我的判据完全按卡文，未做裁剪；三档统计基于实测 33 条。

---

## 2. 三档统计（严格照卡文判据）

| 分档 | 条数 | fid 列表 |
|---|---:|---|
| 仍可核验 | **28** | F04 F06 F07 F08 F10 F11 F12 F13 F14 F16 F18 F19 F24 F27 F28 F29 F34 F36 F39 F43 F44 F45 F46 F47 F48 F49 F51 F52 |
| 需重建 | **2** | F09 F15 |
| 不可核验 | **3** | F22 F25 F35 |
| **合计** | **33** | — |

判据使用说明：

- **仍可核验**：失联路径均为旁证（SECTION / VERDICT / HANDOFF / PANEL 细目在别处有等价存活，或核心数字/结论在存活 evidence_path 里逐字可读）。报告在下方逐条点名存活文件与数字。
- **需重建**：承载细目的一手文本（SECTION）已失，存活只剩看板量值提示或二手转述，一手细目不可查。
- **不可核验**：核心裁定所依赖的两份一手来源同时失（F22/F25），或一手 PANEL 文本失导致核心数值无法机械重数（F35），现盘无可替代复核路径。

---

## 3. 逐条一句话依据

### 仍可核验（28 条）

| fid | 一句话依据 |
|---|---|
| F04 | 失 `R17_LEDGER_1062/SECTION(事项1)` 是旁证；存活 `BOARD_ARCHIVE.md`(R17 第14/15轮段) 逐字含 0x5A6510、fn_end 0x5A691C、0x43F180 与 `[0x7E3EBC+0x124]` 全链。 |
| F06 | 失 `R14_COMMON.md(§2.10(a′))` 与 SECTION 为旁证；`BOARD_ARCHIVE.md`(第16轮段) 逐字含入口 0x449440、尾界 0x4494B5、117 字节、3 条 call 的全部数字。 |
| F07 | 失 §2.10(a′)/SECTION 为旁证；`BOARD_ARCHIVE.md`(第16轮段) 逐字含 A/B 两路径地址与收尾四指令 `F6 D8`/`1B C0`/`24 F9`/`83 C0 07`。 |
| F08 | 失 SECTION 为旁证；存活 `R14_COMMON.md`(§2.9一/§2.10一/二) 逐字含 ②-b `[静态推断]` 收口、书面限制 a–e 与 D-53(A)。 |
| F10 | 失两份 SECTION(1065/1064) 为旁证；`BOARD_ARCHIVE.md`(第16轮段) 逐字含 0x5A5020 零到达、1439 直接 call、0x43F180 体内 8 处调用点。 |
| F11 | 失 SECTION(1062事项3) 为旁证；`BOARD_ARCHIVE.md`(第15轮段) 逐字含双口径 S=397/32/383、C=403/26/377、复合名 660。 |
| F12 | 失 SECTION(1062事项4) 为旁证；`BOARD_ARCHIVE.md`(第14/15轮段) 逐字含 1654/1094/433/141 与敏感度 1085/397/168/91。 |
| F13 | 失两份 SECTION(1063/1064) 为旁证；`BOARD_ARCHIVE.md`(第16轮段) + `R14_COMMON.md`(§2.8规则A/§2.10三) 逐字含 C3/C2 反例与规则二。 |
| F14 | 失 SECTION(1062事项5) 为旁证；7 份存活（看板第13/15轮段、GOAL §1060/61/62、`reconcile.tsv` 等）逐字含 220→32/26、17→15。 |
| F16 | 失两份 SECTION(1063/1062) 为旁证；看板第15/16轮段 + `R14_COMMON.md`(§2.9三) 逐字含 0x6F4A70 字节事实、0x5A6510、三装表 host 及未取得清单。 |
| F18 | 失 `GATE_BEHAV/PROGRESS.md`(第二/三步) 为旁证；存活 `CASES.tsv` 逐字含 4/6、5/5、5/5 与 `R14_COMMON.md`(§2.6四) 含唯一写点 0x6F322F。 |
| F19 | 失 `AUDIT_R9/VERDICT(B1)` 为旁证；`R14_COMMON.md`(§2.9二) + 6 份 REPORT/VERDICT 逐字含 #73/#107 零命中、E8 正控 10、jmp 387 全 switch。 |
| F24 | 失 `DELIVERY_SUMMARY.md(§3)` 为旁证；28 份存活含 `R14_COMMON.md`(§16.1)、GOAL(§1054)、`files_tier_A_snap2.tsv`、`tier_final*.tsv`，逐字含 24,723/863/791/4,417 全数。 |
| F27 | 失 `HANDOFF_R16` 为旁证；`LEAD_LOCK`(99-104轮段)、`BOARD_ARCHIVE`、GOAL(N9)、`lead_byte_checks.tsv` 逐字含 68/误命中/7C978A。 |
| F28 | 失 `NAMED_PUSH_AUDIT10/VERDICT` 与 PANEL(M72) 两份一手为旁证；`R14_COMMON.md`(§8.1错源㉓/§13.5) 与 `LEAD_LOCK`(86-92轮段) 逐字含 `test al,1`/成对行必一假/㉓ 全规则。 |
| F29 | 失 PANEL(M71) 为旁证；`R14_COMMON.md`(§13.3)、`LEAD_LOCK`(70-78轮段) 与 `_r139/r139e/f/a` 三脚本逐字含 63/77、64/77、74/77、96.10%。 |
| F34 | 失 PANEL(M98/M102) 为旁证；`LEAD_LOCK`(方法论硬约束/R16遗留段) 逐字含 G1–G5、`host<=site<fn_end` 与「缺位置断言不算校验」。 |
| F36 | 失 PANEL(M103) 为旁证；`R14_COMMON.md`(§2.6来源段/§2.7) 逐字含 GATE_MAP 用途与 0x43F504「循环增量+回边」的字节更正。 |
| F39 | 失 `HANDOFF_R14_R3(五)` 为旁证；`R14_COMMON.md`(§8.3) 与 `BOARD_ARCHIVE`(R14-R17) 逐字含「同源不得双计/只计一环」。 |
| F43 | 失 `S13_K10/_audit/VERDICT(§4)` 为旁证；`R14_COMMON.md`(§8.1) 逐字含「族内随机」规则与 1.53–2.02% vs 93.3% 实证。 |
| F44 | 失 `S13_K10/_audit/VERDICT(§4)` 为旁证；`R14_COMMON.md`(§8.1) 逐字含「合取判据自洽可能是循环论证/恒等式不是核对」。 |
| F45 | 失 `S13_K10/_audit/VERDICT(§3)` 为旁证；`R14_COMMON.md`(§8.1) 逐字含「PAU/PAV 前缀不是类名一部分」禁例。 |
| F46 | 失两份 VERDICT(S10_KPROVED/S13_K12) 为旁证；`R14_COMMON.md`(§8.1) 逐字含「随机基线恒为 0，必须差分检验」及实证。 |
| F47 | 失 `S13_K12/_audit/VERDICT(§3)` 为旁证；`R14_COMMON.md`(§8.1) 逐字含「P=R=100%/恰命中 N 可能是判据自证」。 |
| F48 | 失 `S10_KPROVED/_audit/VERDICT(§1/§2)` 为旁证；`R14_COMMON.md`(§8.1错源㉖) 逐字含「自报扫描规模/11.13%/须给 .text 覆盖百分比」。 |
| F49 | 失 `HANDOFF_R14_R3(九)` 为旁证；`R14_COMMON.md`(§8.3新增坑) 与 `R17_R52_ADJ_D4/VERDICT` 逐字含 `B8 imm32 C2 04 00` vs `C3` 形态与 D-4 裁决。 |
| F51 | 失 `AUDIT_FI_V5/VERDICT(A5/N2)` 为旁证；`GOAL_THREE_TARGETS_20261018.md`(N9段) 逐字含 336/68/1439 三数且 Lead 已独立复算为双源。 |
| F52 | 失 `NAMED_PUSH_AUDIT10/VERDICT(§2)` 为旁证；`R14_COMMON.md`(§13.3/§13.5) 逐字含 `vt+0x20`/`7C8B3D`/`push 1` 三件齐判据。 |

### 需重建（2 条）

| fid | 一句话依据 |
|---|---|
| F09 | 两份一手 SECTION（`R17_LEDGER_1065` 86 个 `[reg+0x1AC]` 派发点重审、`R17_LEDGER_1063` 事项1/5）已失；存活 `BOARD_ARCHIVE`(第16轮段) 仅给量值、`R14_COMMON`(§2.9二) 为二手边界说明，R33 逐点分类一手不可查。 |
| F15 | 权威一手 SECTION（`R17_LEDGER_1063R` 事项4）已失；存活看板第16轮段只给 129/125/5/19 量值，`R17_LEDGER_1063/SUPERSEDED.md` 明标 108/82/4/33 不得引用，细目一手不可查。 |

### 不可核验（3 条）

| fid | 一句话依据 |
|---|---|
| F22 | 两份一手来源 `R17_DELIVERY/DELIVERY_SUMMARY.md(§1)` 与 `COVERAGE/PANEL.md(M69/M102)` 同时失；仅 `R14_COMMON.md`(§12.6/§16.1) 二手转述 1,654/791/458/291/65，无原件可机械复核。 |
| F25 | 两份一手 `DELIVERY_SUMMARY.md(§1)` 与 `PANEL.md(M58界向更正)` 同时失；唯一存活 `strict_panel.py` 只有判据与输出格式，无结果数字，且输入 `coverage.tsv`/`function_atlas.tsv` 及其目录均不在盘，无法重数 1,331/3/22/1/22。 |
| F35 | 一手 `COVERAGE/PANEL.md(M47/M52/严格口径双列表)` 已失；4 份存活脚本虽逐字含 `proved_strict` 判据（`strict_panel.py:78` 带方括号字面）与 ceil 式，但该定义的权威散文文本与具体数值在现盘只剩二手转述，n 的取法/数值不可从盘重数。 |

---

## 4. 我判不准的条目

**F35**（归入「不可核验」，但存在争议）。  
判不准的原因：卡文要求「核心裁定或两份一手来源同时失 → 不可核验」。F35 的 `PANEL.md` 一手文本确实失联（M52/严格口径双列表），但 limitations 中 R139 更正指出 `proved_strict` 的判据在现盘有**代码级一手实现**（`strict_panel.py:78` + `LEAD_LOCK` 错误 #14 段逐字认定为权威定义），且另有 3 份脚本含同一判据。按「有可替代机械复核路径」的宽松读法它可由「需重建」上调到「仍可核验」（判据可复核）；按「一手文本失 + 具体数值不可重数」的严格读法则为不可核验。我采用的是后者。  
**缺什么才能判**：`COVERAGE/PANEL.md` 原件（或 `coverage.tsv` + `function_atlas.tsv` 两个输入）在盘，即可确定「n 的取法」与具体数值是否有权威一手，从而定档。

**F13**（集合 33 vs 预期 32 的差异项）。  
按卡文判据我把它列入部分失联（alive=2/dead=2）并判「仍可核验」，但无法确认外部 32 条口径是否因把它视作「非部分失联」而排除。**缺什么才能判**：外部报告对 F13 的存活/失联路径逐条判定，或「部分失联」的 32 条 fid 白名单。

---

## 5. 可复跑命令

在 `/home/t628/projects/ra2-campaign-forge` 根目录执行（只读台账、只写本卡产物）：

```bash
cd /home/t628/projects/ra2-campaign-forge
python3 - <<'PY'
import os,csv,hashlib
IDX='lead/next_re_20261117_r14/R17_R110_FACTINDEX_V538/FACT_INDEX.tsv'
raw=open(IDX,'rb').read()
rows=list(csv.DictReader(raw.decode('utf-8').splitlines(),delimiter='\t'))
def sp(s):
    o=[]
    for t in s.split(';'):
        t=t.strip()
        if not t: continue
        b=t[:t.rfind('(')].rstrip() if t.endswith(')') else t
        o.append(b.replace('\\','/'))
    return o
part=[]
for r in rows:
    ps=sp(r['evidence_paths']); a=sum(os.path.exists(b) for b in ps); d=len(ps)-a
    if a>0 and d>0: part.append((r['fact_id'],a,d))
assert len(rows)==54
assert len(part)==33
print('sha256',hashlib.sha256(raw).hexdigest())
print('partial',len(part),[x[0] for x in part])
PY
```

完整分档（含 12 断言与逐条依据）见本卡执行脚本逻辑；产物 TSV 为 `_r141/sub_triage/triage_recompute.tsv`。
