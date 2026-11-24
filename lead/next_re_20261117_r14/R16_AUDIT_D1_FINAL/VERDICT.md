# R16-AUDIT-D1-FINAL 审计裁决

> 审计员：`work/cn:deepseek-v4.1-flash`（异族）· 2026-11-21 · 被审：`R16_D1_FINAL\`
> 只读性：`ra2youli\gamemd.exe` 仅 `pefile` 只读打开；`COVERAGE\coverage.tsv` 只读（sha 见 §7）；
> **只写本目录**（`VERDICT.md` / `verify.py` / `check.tsv` / `verify_summary.json`）。产物未改、卡目录未改。
> 复跑：`python verify.py`（202 项检查；capstone 5.0.7 `skipdata=True`，自解 PE、自算 RTTI 链、自解码装表指令）

---

## 0 · 总体判定：**FAIL（口径层不成立；事实层可用）**

| 维度 | 结果 |
|---|---|
| 5 行 delta 的**字节事实 / 文本保全 / 体外 / 装配形态 / 披露指针 / 行行不同** | **5/5 全 PASS**（§A1–A4、A6、E） |
| 5 行 delta 的 **D-51 ②**（用户口径：有独立审计链） | **实质 5/5 PASS**；卡面字面（必须落在 `NAMED_PUSH_AUDIT*/verdict.tsv`）**1/5** ⇒ 4 行须改引用（§A5，必改 1） |
| **12 行 SKIP 正当性** | **12/12 正当**（盘上确已有 ④，且逐字节等于 `R16_F1_OTHER14\delta.tsv` 第 4 列、并由 `R16_MERGE_OTHER14` 于 `09:11:18` 并表） |
| `0070B570` 表改选 | **成立**（§C，4 项全 PASS） |
| 派生 317 / 12-5-1-299 | **可复现**（逐值一致） |
| 派生「**17 行**」是否 D-51 的筛果 | **否** ⇒ **判 FAIL**（§D3）：字面应 1 行；宽读应 ≥83 行；17 = `D47 classify` 的 **F1+F2 语义带**，与审计链无关。**「做完 17 行静态 ④ 线整线收口」不成立** |

**一句话**：5 行产物本身可以并表（事实层干净、可见字节全对），但本批的**派生口径与「收官」结论是错的**，
且 4/5 行的审计记录栏写成了产出方 EVIDENCE 而非审计裁决。按卡面口径判 **FAIL**，必改 4 条 + 待裁 1 条。

---

## A · 那 5 行 delta 逐项

### A1 原文保全 —— **5/5 PASS**（11 项检查全 PASS）
- 第 4 列以**盘上现第 4 列为严格前缀**：5/5 `prefix=True`。
- 第 1/2/3/5/6/7/8 列逐字节相同、grade 未变：5/5 **0 处不同**（对照 `COVERAGE\coverage.tsv` 同行）。
- 追加段 = `；④ 活表槽位见证：…`（见 §A2 的文本↔字节比对）。

### A2 字节事实 6 项 —— **5/5 × 6 全 PASS（30/30）**
自算（非复用 `generate.py`）：`vt-4→COL`、`COL+4→offset`、`COL+12→TD`、`TD+8→mangled`、`u32(vt+slot*4)→slot 值`、`capstone` 解码装表点。

| entry | vt | slot | slot值==entry | COL | off | TD | mangled | 装表指令（site） | imm32==vt |
|---|---|---|---|---|---|---|---|---|---|
| 0051B1F0 | 007EB058 | 242 | ✅ | 008033B8 | 0 | 00825508 | `.?AVInfantryClass@@` | `00517ACC: mov [esi], 0x7eb058` | ✅ |
| 0051DAF0 | 007EB058 | 320 | ✅ | 008033B8 | 0 | 00825508 | `.?AVInfantryClass@@` | `00517ACC: mov [esi], 0x7eb058` | ✅ |
| 00522340 | 007EB058 | 335 | ✅ | 008033B8 | 0 | 00825508 | `.?AVInfantryClass@@` | `00517ACC: mov [esi], 0x7eb058` | ✅ |
| 0070B570 | 007F4960 | 263 | ✅ | 0080C058 | 0 | 00817B58 | `.?AVTechnoClass@@` | `006F3130: mov [esi], 0x7f4960` | ✅ |
| 00748190 | 007F6218 | 8 | ✅ | 0080CD28 | 0 | 00845980 | `.?AVUnitTypeClass@@` | `007471BF: mov [esi], 0x7f6218` | ✅ |

另加一项独立检查：**④ 正文里的 vt/slot/COL/offset/RTTI/装表点 全部等于字节复算值** —— 5/5 PASS（无手改数字）。

### A3 体外 —— **5/5 PASS**
装表点均**在 entry 起址之前**（`site < entry`），且宿主函数 ≠ entry：
`00517A50`(size 617, atlas) ≠ 0051B1F0/0051DAF0/00522340；`006F2B40`(1833) ≠ 0070B570；`007470D0`(487) ≠ 00748190。

### A4 装配方式标注 —— **5/5 PASS（`ctor_body` 属实，不是 `mov_abs`）**
三行 Infantry 共用**同一个**装表点 `00517ACC`（同一张 `007EB058` 表的三个不同槽：242/320/335）——这是**正确**的，
不是重复计数：一个 `mov [esi], vt` 把整张表装进 `this`，三个槽各自持有一个 entry。
- 指令形态：`mov dword ptr [esi], imm32`（reg-form，非绝对地址）⇒ 不是 `mov_abs`。
- 宿主头部独立核：`00517A50: mov esi, ecx`（= `this`），紧随 `00517AD2/00517AD8/00517ADF` 连写 `[eax]/[esi+8]/[esi+0xc]`
  三张基类子对象表 ⇒ 典型多继承构造器 vptr 初始化；`006F2B40: 006F2B44 mov esi,ecx`；`007470D0: 007470DB mov esi,ecx`。
- 结论：**`ctor_body` 标注属实**，D-50 的 `mov [abs], vt` 绑定条件对这 5 行**不适用**（无一行是 `mov_abs`）。

### A5 D-51 ② 独立审计链 —— **实质 5/5 PASS；卡面字面 1/5（4 行须改引用）**
D-51 原文（`lead\PENDING_DECISIONS.md:63`）：「只收 ② 有独立审计链的 —— 即 entry 能在 `NAMED_PUSH_AUDIT*/verdict.tsv`
里找到、且类身份判定有审计记录；不接受仅靠 YRpp 知识库代理的 ②」。

**两个读法的实测：**

| entry | ① `NAMED_PUSH_AUDIT*/verdict.tsv` 命中（20 目录 / 163 条） | ② 独立审计裁决（异族 `_audit`，已逐行核过） |
|---|---|---|
| 0051B1F0 | ❌ 未命中 | ✅ `S10_K12/_audit/VERDICT.md:31`（裁决 PASS：「0051D6F0 / 0051DAF0 / 0051B1F0 / 00522340 四行 [已证] 可并入」）+ `:7`（独立复算 `vt=0x7EB058`→`[vt-4]=008033B8`→`TD+8=?AVInfantryClass@@`；并指出 `vt-8=0x410230` 是函数指针非 COL） |
| 0051DAF0 | ❌ | ✅ 同上 `:31` + `:15`（环④外部化逐行：`call [reg+0x500]`，0x500/4=**320**） |
| 00522340 | ❌ | ✅ 同上 `:31` + `:17`（`call [reg+0x53c]`，0x53C/4=**335**） |
| 0070B570 | ❌ | ✅ `S10_K16/_audit/VERDICT.md:17`（「**0070B570 应升 [已证]**」，环② 独立复算钳制/推进）+ `:21`（类归属：952 条 COL 中仅 6 张表槽数≥259，「三槽六表同址」⇒ **TechnoClass 级正确**） |
| 00748190 | ✅ `NAMED_PUSH_AUDIT3/verdict.tsv:2`（PASS；`ring2_at` 已写 `TD=00845980 … .?AVUnitTypeClass@@`） | ✅ 同左 |

**判定**：按用户 D-51 的**实质**（不接受仅靠 YRpp 代理的 ②），这 5 行 **5/5 有独立审计链**，不是 YRpp 代理 ⇒ **不判 FAIL**。
但按卡面 §A.5 的**字面路线**（必须给 `NAMED_PUSH_AUDIT*/verdict.tsv` 的 `文件:行号`）只有 **1/5**；
且 `fields.tsv` 的 `audit_record(文件:行号)` 列 4/5 写的是**产出方 EVIDENCE**（`S10_K12/EVIDENCE/ROW_PROOFS.txt:67/52/109`、
`S10_K16/EVIDENCE/PROOF_0070B570.txt:9`），**不是审计裁决** —— 列名与内容错配，必须改（必改 1）。
该分歧属口径解释，须 Lead 明文裁「`_audit/VERDICT.md` 是否等值于 `NAMED_PUSH_AUDIT*/verdict.tsv`」（待裁 1）。

### A6 披露指针 —— **5/5 PASS**
5 行第 4 列均含 `D-47(A) 裁决`、指向 `R14_COMMON §12.6`、**无 `§12.4`**（`§12.3 让位` 的表述是 D-47(A) 要求的原样披露，不算错指）。

---

## B · 那 12 行 SKIP 的正当性 —— **12/12 正当**

### B1 盘上确已有 ④ —— **12/12 含 `④ 活表槽位见证`**（逐行见下表）

### B2 确由 `R16_F1_OTHER14` 写入 —— **12/12 有硬证据（三重）**
1. **文本逐字节相等**：12 行 live 第 4 列 **完全等于** `R16_F1_OTHER14\delta.tsv` 的第 4 列（`exact_equal=True`，长度逐行相同）。
2. **并表日志**：`R16_MERGE_OTHER14\after_state.json` → `changed_rows` 恰 14 行，coverage mtime `2026-11-21T09:11:18`、
   sha `6353351E…`→`E4F111B6…`；本批 12 行 **全在这 14 行内**。
3. **集合关系**：`R16_F1_OTHER14\fields.tsv` / `delta.tsv` 共 14 entry；与本批 12 行交集 **12**，
   差集恰为 `004AF540`、`004B5AB0` —— 这两个 entry **不在** D1 317 行内（故不属本批派生范围），
   说明本卡没有「多算」也没有「少算」这 12 行。

| entry | 行名（截断） | 盘上 ④（类::slot / vt / 装表点） | ④ 文本 == F1-OTHER14 delta |
|---|---|---|---|
| `0040BC10` | DynamicVectorClass<BombClass*>::scalar_deletin | `DynamicVectorClass<BombClass*>::slot0` / `007E17CC` / slot 0 / site `0040B563` | ✅ 逐字节相等 |
| `0040F8F0` | DynamicVectorClass<WarheadTypeClass*>::scalar_ | `DynamicVectorClass<WarheadTypeClass*>::slot0` / `007E1E84` / slot 0 / site `0040F4AD` | ✅ 逐字节相等 |
| `0040FEC0` | DynamicVectorClass<WeaponTypeClass*>::scalar_d | `DynamicVectorClass<WeaponTypeClass*>::slot0` / `007E1ED4` / slot 0 / site `0040FB4D` | ✅ 逐字节相等 |
| `00422CA0` | AnimClass::Draw | `AnimClass::slot69` / `007E3354` / slot 69 / site `0042201C` | ✅ 逐字节相等 |
| `0046B910` | DynamicVectorClass<BulletClass*>::scalar_delet | `DynamicVectorClass<BulletClass*>::slot0` / `007E4678` / slot 0 / site `004662FD` | ✅ 逐字节相等 |
| `0048AFD0` | VectorClass<DamageGroup*>::scalar_deleting_dto | `VectorClass<DamageGroup*>::slot0` / `007E5144` / slot 0 / site `00489B1E` | ✅ 逐字节相等 |
| `0048B020` | DynamicVectorClass<DamageGroup*>::scalar_delet | `DynamicVectorClass<DamageGroup*>::slot0` / `007E5170` / slot 0 / site `004892AA` | ✅ 逐字节相等 |
| `0054EBA0` | DynamicVectorClass<KamikazeControl*>::scalar_d | `DynamicVectorClass<KamikazeControl*>::slot0` / `007ECE7C` / slot 0 / site `0054E298` | ✅ 逐字节相等 |
| `0062B380` | DynamicVectorClass<ParasiteClass*>::scalar_del | `DynamicVectorClass<ParasiteClass*>::slot0` / `007EF824` / slot 0 / site `006291AD` | ✅ 逐字节相等 |
| `0065BED0` | RadSiteClass::scalar_deleting_dtor | `RadSiteClass::slot8` / `007F0810` / slot 8 / site `0065B228` | ✅ 逐字节相等 |
| `0065C200` | DynamicVectorClass<RadSiteClass*>::scalar_dele | `DynamicVectorClass<RadSiteClass*>::slot0` / `007F07A4` / slot 0 / site `0065B17D` | ✅ 逐字节相等 |
| `0075E510` | WarheadTypeClass::scalar_deleting_dtor | `WarheadTypeClass::slot8` / `007F6B30` / slot 8 / site `0075D0BA` | ✅ 逐字节相等 |

### B3 有没有「假 SKIP」（盘上其实没 ④）—— **0/12**，SKIP 全部有正当理由

### B4 这 12 行是否满足 D-51 —— **实质 12/12 有审计链；字面 0/12**
- 11 行：`S13_K8RECHK/_audit/VERDICT.md:37`「**应并入 11 行**（均为 `[静态推断]`→`[已证]` 升格）：0075E510 / 0065BED0 / 0040BC10 / 0040F8F0 / 0040FEC0 / 0046B910 / 0048AFD0 / 0048B020 / 0054EBA0 / 0062B380 / 0065C200」——
  该审计是**异族**独立审计（自解 PE、自走 RTTI、`RTTI fail-closed 18/18`、`vt[slot]==entry 18/18`），② 类身份有独立判据。
- `00422CA0`：`S20-K1/_audit/VERDICT.md:33`（「槽 11/12/65/69 … 4 个 Draw 零直接调用（我实测 0）」）+ 审计器自己的原始输出
  `S20-K1/_audit/out_a6.txt:482`（`-- Anim v[69] Draw 0x422CA0 --`）、`out_a12_fields.txt:15`（`Draw Anim 0x00422CA0 直接 call/jmp = 0`）。
  ⚠️ 注意：`VERDICT.md` 只写「槽 69」，**不点 entry 地址**，引用时须两者并引（NIT）。
- 字面 `NAMED_PUSH_AUDIT*/verdict.tsv` 命中 **0/12**（与 `R16-F1-OTHER14` 卡自述「14 行在 20 个 verdict.tsv 里命中 0 次」一致）。
  ⇒ 这 12 行**只能靠实质口径留在 17 行里**；若 Lead 采窄读，本批 17 行应塌成 1 行（见 §D3）。

---

## C · `0070B570` 表改选 —— **成立**

| 项 | 实测 |
|---|---|
| C1 `vt=007E22A4` 的 RTTI | `COL=007FB4C0(off=0) → TD=00817B90 → .?AVAircraftClass@@` ⇒ **确为 AircraftClass**，与行名类 `TechnoClass::…` **不符** |
| C2 `vt=007F4960` 的 RTTI | `COL=0080C058(off=0) → TD=00817B58 → .?AVTechnoClass@@`，`u32(007F4960+263*4)=0070B570` ⇒ **entry 确在 slot263** |
| C2' 全镜像出现处 | `0x0070B570` 恰 **6 次**：`007E26C0 / 007E42D8 / 007E90B0 / 007EB474 / 007F4D7C / 007F608C` = Aircraft/Building/Foot/Infantry/Techno/Unit 六表 **同为 slot263**（与 `S10_K16/_audit/VERDICT.md:21`「三槽六表同址」吻合，行语义「shared by six classes, no subclass override」亦吻合） |
| C3 6 项字节事实 | 全成立（见 §A2 表）；装表点 `006F3130: mov [esi],0x7f4960` 在 host `006F2B40` 内、entry `0070B570` **体外** |
| C4 结论 | **成立**。改选不是挑表凑数：六表同址、选「与行名类一致」的 TechnoClass 表是唯一自洽解 |

---

## D · 派生口径核

### D1 `has_ring4==D1` —— **317 行，317 distinct，可复现 PASS**
### D2 来源类别 join —— **F1=12 / F2=5 / F3=1 / F4=299，逐值可复现 PASS**
细分也一致：`F1={'sem_virtual_witness_only':12}`、`F2={'sem_call_mem_anchor':4,'audit_ring4_dispatch':1}`；
`F3=004D7330(sem_direct_only)`。`F1∪F2` 与 `fields.tsv` 的 17 entry **完全相等**。

### D3 「17 行」是否 D-51 的筛果 —— **FAIL（不多不少都不成立）**

**根因（可直接验）**：`generate.py:135-137` 只做
```python
f1 = [r for r in d1 if src[...]["form"] == "F1"]
f2 = [r for r in d1 if src[...]["form"] == "F2"]
sel = f1 + f2
```
**没有任何审计链判定**。而 `D47_SURFACE.classify()` 的 F1–F4 是**④ 证据形态**轴（F1=slot-install 形态、F2=可见派发形态、
F3=direct-only、F4=其它），**不是 ② 审计链轴**。`derive.txt:10` 的「阶段 3 口径二筛（② 有独立审计链）：保留 F1+F2」
是把两个无关轴当成同一个 —— 该结论从探针 `R16_PROBE_4FINAL\REPORT.md:196` 的一句断言直接继承而来，本身无证据。

**三读实测（同一 317 行）**：

| 读法 | 应得行数 | 与本批 17 的关系 |
|---|---:|---|
| 窄读 = 卡面字面（entry ∈ `NAMED_PUSH_AUDIT*/verdict.tsv`） | **1**（仅 `00748190`） | 17 **多了 16**（含本批 4 行 delta） |
| 本批实际用的轴（`classify` 的 F1+F2） | **17** | 就是它自己 —— 与 D-51 无关 |
| 宽读 = 实质「任一异族 `_audit` 裁决背书该 entry 的类身份」 | **≥83**（我机械扫描：D1 内 83 行；其中 **67 行不在 17 内**） | 17 **少了 ≥67** |

**漏收是实的（8 行已逐条抽验，含唯一的 F3 行）**：

| entry | 本批 form / reason | 盘上 ④ | ② 审计背书（已核到行） |
|---|---|---|---|
| `004D7330` | **F3 / sem_direct_only** | 无 | `S10_K13/_audit/VERDICT.md:12`（`vt 0x007E8C94, RTTI=.?AVFootClass@@, slot 0x16C`）、`:39`（「**保留：[已证] 004D7330 —— 四环成立**」） |
| `00413F80` | F4 / no_ring4_described | 无 | `S05_KPROVED2/_audit/VERDICT.md:21`（逐行表：`007E22A4[9] AircraftClass … PASS`）、`:39`（「PASS（有条件）：8 行并入 [已证]」） |
| `0040B880` | F4 / no_ring4_described | 无 | `S13_K9/_audit/VERDICT.md:21`（`✓DynVec<BombClass*>`…PASS）、`:58`（「**可并入白名单（11 行，grade=[已证]）**」） |
| `0040B930` | F4 | 无 | 同上 `:22` / `:58` |
| `0040F7C0` | F4 | 无 | 同上 `:23` / `:58` |
| `0040FD90` | F4 | 无 | 同上 `:24` / `:58` |
| `0040FE40` | F4 | 无 | 同上 `:25` / `:58` |
| `0040F870` | F4 | 无 | `S13_K10/_audit/VERDICT.md:35`（「PASS 22（可直接并入）」）、`S13_K12/_audit/VERDICT.md:19`（逐行 `PASS`） |

另 59 行为同一机械扫描命中、未逐条抽验（列表见 `verify_summary.json:d51_broad_outside_17`），**不入判决**，仅供 Lead 复核。

**⇒ 结论**：`17` 既不是窄读的 1，也不是宽读的 ≥83；它只是「④ 形态为 F1/F2」的那一带。
因此 `REPORT.md:20-21`「派生数完全等于 17，无差异」与「**本批是静态 ④ 线收官批**」**不成立**：
按窄读，本批 16 行不该收；按宽读，至少还欠 8 行（实测）～60+ 行（待核）。

---

## E · 反抄袭 / 行行不同 —— **PASS**

| 检查 | 结果 |
|---|---|
| 5 行 delta 的 ④ 两两不同 | 5/5 |
| 5 行 delta 的 ④ 归一（8 位十六进制→`ENTRY`）后不同 | 5/5 |
| 17 行 ④ 两两不同（5 行取 delta 正文、12 行取盘上正文） | 17/17 |
| 17 行 ④ 归一后不同 | 17/17 |

（12 行里 3 行 Infantry 共用 vt/COL/TD，只靠 slot 242/320/335 区分 —— slot 是十进制小数字，归一化不会抹掉，故仍 17/17 不同。）

---

## F · 必改清单（4 条）+ 待裁（1 条）

1. **【必改】`fields.tsv` 的 `audit_record(文件:行号)` 列 4/5 写错对象**：现写产出方证据
   （`S10_K12/EVIDENCE/ROW_PROOFS.txt:67/52/109`、`S10_K16/EVIDENCE/PROOF_0070B570.txt:9`），
   应改为审计裁决：`S10_K12/_audit/VERDICT.md:31`（+ `:7`）、`S10_K16/_audit/VERDICT.md:17`（+ `:21`）。
   否则下一手会按「无审计记录」把 4 行判掉（`S10_K12/_audit`、`S10_K16/_audit` 均在盘）。
2. **【必改】`derive.txt` 阶段 3 与 `REPORT.md` §1/§0 的「口径二筛」表述失实**：`generate.py:135-137` 无审计链判定；
   `derive.txt:11-15` 自陈「严格 verdict.tsv 仅 1 行」却仍报「17 一致」。须改为如实：17 = `classify` 的 F1+F2（④ 形态轴），
   并说明「审计链」是另一根轴、结果见本裁决 §D3。
3. **【必改】`REPORT.md` §7 样例 ④ 与盘面不符**：`0040BC10` 的样例文本含「装表指令为 mov [abs], vt」，
   **盘上该句不存在**（live 第 4 列为 `…；装表点 0040B563 位于 0040B540 体内，entry 体外）`）。报告不得把未落盘的生成版当盘上原文。
4. **【必改·写域在 F1-OTHER14 线】12 行里 7 行 `mov_abs` 的盘上 ④ 未按 D-50 写清装配方式**：
   `0040BC10 / 0040F8F0 / 0040FEC0 / 0046B910 / 0054EBA0 / 0062B380 / 0065C200` 的 ④ 只写「装表点 X 位于 Y 体内」，
   未写「装表指令为 `mov [abs], vt`」⇒ 违反 D-50 绑定条件「必须写清装配方式」。本卡 5 行 delta 全是 `ctor_body`、不受此条影响。
5. **【待裁】D-51 的「独立审计链」是否认 `*_audit/VERDICT.md` 等值于 `NAMED_PUSH_AUDIT*/verdict.tsv`**：
   - 认 ⇒ 本批 5 行 + 12 行 SKIP 的 ② 均合规（5/5、12/12），但**「17 行收口」仍不成立**（宽读还欠 ≥8 行，见 §D3）。
   - 不认 ⇒ 本批只剩 `00748190` 一行合规，**4 行 delta 须撤、12 行 SKIP 不再算 17 行之内**，且须另开卡按窄读重筛。
   两种结果都需要 Lead 落一个字，否则「收官」无法结账。

## G · NIT（不影响本批判定，供下一手）

1. `generate.py` 的「6 项字节复核」第 6 项**只判操作数是否以 `0x` 开头、未比对 `imm32==vt`**；第 5 项在 entry 不在 atlas 时
   （`atlas.get(entry)` 返回 0）退化为恒真；`chk[5]` 有一段死代码。本批 5 行经我独立复算全过，**结论不变**，但自检实现不可沿用。
2. `generate.py` 的 `install_form` 判定 = 「内存操作数非绝对地址 ⇒ `ctor_body`」，**不验证宿主是构造器**；
   若遇到 atexit/普通函数内的 `mov [reg],vt` 会误标。本批 5 行宿主经独立核（`mov esi,ecx` + 多基类 vptr 连写）确为构造器。
3. `host_capstone()` 用「site 前最后一个 `ret` 后的首条指令」当宿主起址，**可给出错误宿主**；本批 5 行未走该分支（宿主均在 atlas）。
4. `00422CA0` 的审计链在 `S20-K1/_audit/VERDICT.md` 里只写「槽 11/12/65/69」不点地址，点名在 `out_a6.txt:482` / `out_a12_fields.txt:15` ⇒ 引用须并引。
5. `delta.tsv` 第 6 列 `evidence_path` 保留盘上原值（含 `M82 指针修复：…` 备注段）—— 与盘上逐字节一致是对的，但引用者易误读为两条来源。

---

## H · 只读与复跑证明

| 项 | 值 |
|---|---|
| `COVERAGE\coverage.tsv` sha256 | `E4F111B6643661D01C66DB1889172437A06A563233F0A252AD0DB4A54FD51C8A`（= `R16_MERGE_OTHER14` 并表后态，mtime `2026-11-21T09:11:18`；**本卡未改**） |
| `ra2youli\gamemd.exe` sha256 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（只读） |
| `R16_PROBE_4FINAL\_pin_coverage.tsv` sha256 | `2F498B18E64E7EF568A0EB7888CE9F8D710CABC91038E52A8167F8826B53B36E` |
| 检查项 | **202**（PASS 162 / FAIL 29 / NIT 7 / INFO 4；明细 `check.tsv`） |
| 复跑 | `python verify.py`（实测 ≈2 s；capstone 5.0.7 + pefile，自解 PE / 自算 RTTI / 自解码装表指令） |
