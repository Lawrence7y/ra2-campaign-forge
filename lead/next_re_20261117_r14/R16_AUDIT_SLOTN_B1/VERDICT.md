# R16-AUDIT-SLOTN-B1 · 审计裁决

> 审计对象：`lead\next_re_20261117_r14\R16_SLOTN_B1\` 的 `delta.tsv` 15 行 ④ 补写成文
> 审计员：agent-8 · 日期 2026-11-20（R16 第 3 轮）· 本卡写域 `R16_AUDIT_SLOTN_B1\`（只写此目录）
> 背景裁决：**D-47(A) 已裁**（维持 D-43(A) 优先、§12.3 对「活 vtable 槽位」形态让位）。故「②④ 共用同一虚表槽」本身**不作为** FAIL 理由；本审计只审「文本与字节是否相符、格式是否合先例、是否最小改动、是否抄袭」。

---

## 0 · 总体判定

**15 行 PASS / 0 行 FAIL。**

一句话结论：15 行 ④ 追加段都是各自原第 4 列之后的**纯追加**（严格前缀成立）、6 项字节事实用我自己写的 capstone 脚本 **15×6 = 90 项逐项复算全对**、骨架与盘上 91 行先例**逐字符一致**、D-47(A) 披露句 **15/15 在位**；**必改项 0 条**，无需撤回或重做。

| 项 | 不合格行数 |
|---|---|
| §A 最小改动与原文保全 | **0 / 15** |
| §B 地址与字节事实（6 小项） | **0 / 15**（6 个小项各自 0 行不符） |
| §C 文本与事实一致 | **0 / 15** |
| §D 格式合先例 | **0 / 15** |
| §E 反抄袭 | **0 / 15**（entry 归一后 0 组重复） |

---

## 1 · 复算基线与复跑方式

| 对象 | 实测 |
|---|---|
| `ra2youli\gamemd.exe` | 4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡面一致，全程只读） |
| `R16_SLOTN_B1\delta.tsv` | 13,612 B，SHA-256 `9BADFC87867D667BAA6F67909FFE725F1D99F159D294C4283C61FDF82A8448C7`，1 表头 + 15 数据行，8 列 |
| `COVERAGE\coverage.tsv`（审计基线，22:55 执行器产出时） | SHA-256 `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2`（= 执行器 REPORT §4 自述值，我 23:00 起审时实测一致） |
| `COVERAGE\coverage.tsv`（当前盘上） | SHA-256 `2BCA384650AC31BCFC9661280A1863C2D51C6548B96F5EE372DE94EDDA8104A6` —— **审计期间被并发改写**，见 §9 |

**复跑**：`python verify.py`（只读打开上述三个文件；输出 `bytecheck.tsv`、`tables.md`、`verify_out.json` 并打印汇总）。脚本自写，未复用执行器的 `scan_fields.py` / `gen_delta.py`，也不读执行器的 `verify_summary.json` / `scan_raw.json` 作为判据。

方法要点（我自己实现，非调用执行器）：
- PE32 自解析：`ImageBase=0x400000`，按节表做 **VA → 文件偏移**映射（不假设 `IB+rva` 线性，避免 .data/.rdata 处越界错读）；
- RTTI 的 `pTD`/`pCHD` 按**绝对 VA** 读；装饰名按 **`TD+8` 内联串**读（不是解引用指针）——本批 15 行实测全部为内联串，与已入账技术条一致；
- capstone 5.0.7，`CS_ARCH_X86`/`CS_MODE_32`，detail 模式解码装表点。

---

## 2 · §A 最小改动与原文保全 — **15/15 PASS**

- **15/15 原第 4 列是 delta 第 4 列的严格前缀**（`delta_col4.startswith(cov_col4)`），追加段长度 295–423 字节，首字符一律 `；`，随后即 `④ 活表槽位见证：`。
- 第 1/2/3/5/6/7/8 列与盘上 `coverage.tsv` 同 entry 行**逐字节相同**：15 行 × 6 列 = **90 次比较，0 不同**。
- 附加独立核对（卡面未要求）：`delta.tsv` 15 行的 `entry + name` 顺序与 `PROBE_802\slotN43.tsv` **数据行 1–15 逐行一致**（15/15），`slotN43` 侧 `col_ok=match` 15/15、`install_ext=y` 15/15 —— 执行器 REPORT §1 的前置核对自述属实。
- 追加段首字符 15/15 一律为 `；`（随后即 `④ 活表槽位见证：`）。原句末字符实测两分：**9 行以 `。` 结尾**（1/2/5/6/7/8/13/14/15）、**6 行以全角 `）` 结尾**（3/4/9/10/11/12）；先例 3 条的原文末字符是 `；`。故：
  - 6 行 `）` + `；④` ⇒ `）；④`，与先例 `…）；④` **同形**；
  - 9 行 `。` + `；④` ⇒ `。；④`，即在原句全角句号后接一个 `；` 再起 ④——这是「原文一字不改」硬约束下的唯一写法（原句的 `。` 不能删），**不判偏离**（见 NIT-3）。

---

## 3 · §B 地址与字节事实（**逐项独立复算**）— **15/15 PASS，6 小项无一行不符**

**结论：15 行 × 6 项 = 90 项全部为真，没有任何一个小项在任何一行上不符。**

| 小项 | 内容 | 结果 | 实测样例（row 1 / `0045A560`） |
|---|---|---|---|
| B① | `u32(vt + slot*4) == entry` | 15/15 | `u32(007E43C8 + 2*4) = 0045A560` |
| B② | `u32(vt - 4) == COL` | 15/15 | `u32(007E43C4) = 007FC298` |
| B③ | `u32(COL + 4) == offset` | 15/15（offset 全为 0） | `u32(007FC29C) = 0` |
| B④ | `u32(COL + 12) == TD` | 15/15 | `u32(007FC2A4) = 00818D28` |
| B⑤ | `cstr(TD + 8) == mangled` | 15/15 | `cstr(00818D30) = .?AV?$DynamicVectorClass@PAVInfantryClass@@@@`（`@@@@` 尾逐字节相同） |
| B⑥ | 装表点解码需为 `mov <mem>, imm32` 且 `imm32 == vt` | 15/15 | `0043B6DB: mov dword ptr [esi + 0x66c], 0x7e43c8` |

B⑥ 的形态覆盖卡面要求的 `mov [reg+disp], imm32`：`[esi+0x66c]`（rows 1–2）、`[esp+0x20]`（rows 5–7）、`[eax]`（rows 3–4）、`[esi]`（rows 8–15）——即 disp 非零 5 行 + disp 为 0 的 10 行；我的判据是「第 0 操作数为 mem 且 base 为通用寄存器 + 第 1 操作数为 imm 且 `imm32 == vt`」，15/15 成立（disp 为 0 时 capstone 只是不打印 disp，仍是 `[reg+disp]` 形态）。

**我自己的原始字节抽样**（`gamemd.exe` 只读 dump，非执行器产物）：

```text
007E43C8 + 8   : 60 A5 45 00                    -> 0045A560   (row1 entry 落在 slot2)
007FC298       : 00 00 00 00 | 00 00 00 00 | 00 00 00 00 | 28 8D 81 00
                  sign=0        offset=0      cdOffset=0    pTD=00818D28
00818D30       : ".?AV?$DynamicVectorClass@PAVInfantryClass@@@@"   (TD+8 内联串)
007E8C94 + 139*4 = 007E8CA0 : 00 42 4D 00       -> 004D4200   (row13)
00800948       : 00 00 00 00 | 00 00 00 00 | 00 00 00 00 | 78 7B 81 00   (row13 的 COL: pTD=00817B78)
007E22A4 + 133*4 = 007E22B8 : 20 4B 4D 00 | B0 4C 4D 00   (row15 entry=004D4B20，紧邻 slot134=004D4CB0)
```

**辅助项（非卡面 6 项，我加做，全部成立）**：④ 文本「装表点 X 位于 Y 体内，entry 体外」——从 `Y` 线性解码到 `X` 之后第一条 `ret`/`jmp` 定界 body 区间，**15/15** 满足 `site ∈ [Y,end)` 且 `entry ∉ [Y,end)`。其中 rows 9–12 定界出 `body=[004D0860, 004D08AE)`，与执行器 REPORT 脚注「`004D08AB` = `C2 04 00`(ret 4)、`004D08B0` = 下一函数」自洽，即 `C2 04 00` 长 3 字节、body 末 = `004D08AE`。

---

## 4 · §C 文本与事实一致 — **15/15 PASS**

1. **地址逐项一致**：④ 里的 `vt=`、`COL=`、`offset=`、`RTTI=`、`装表点` 与我 §B 实测值 15/15 一致（不是「大致对」，是逐字段相等）。
2. **槽号自洽**：name 的 `::slotN`、文本「槽 N 值」的 N、「该槽即其 vt=… 表 slotN」三处 15/15 同一个数；文本「槽 N 值=」写的 15/15 就是本行 entry。
3. **`<Class>` 一致**：15/15 等于行 name 前缀；与 `TD+8` 装饰名解出的类的比对按 `PROBE_802\probe.py:col_name_match` 的既有归一化口径（非模板 = 类名须为装饰名子串；`T_` 模板伪名 = 去 `T_`、去尾 `_`、按 `_` 切分后各段均须出现在装饰名中）——**15/15 match**。rows 1–4 是模板伪名，该写法的先例空缺见 **NIT-1**。
4. **D-47 披露句：15/15 在位**，措辞为
   `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）`
   - 提到 `D-47(A)` 且写了 `§12.3 … 让位` ✔
   - 同时指向 `R14_COMMON §12.4` 与 `PANEL` ✔（与 `R14_COMMON.md` §12.4 的「引用纪律：必须同时引用本条与 PANEL 的对应披露」逐条相符）
   - **不含**禁止表述「已过 §12.3」✔
   - 落点真实：`R14_COMMON.md` L1557 起为「§12.4【COMMON-R16 追加】D-47 裁决」；`COVERAGE\PANEL.md` L161–170 为 M74 冲突披露 + M84 裁决落定。指针不是空指（编号歧义见 **NIT-2**）。

---

## 5 · §D 格式合先例 — **15/15 PASS**

方法：把 3 条先例（`00464AC0` / `004DE630` / `004F42F0`，盘上第 4 列搜 `④ 活表槽位见证`）的 ④ 段与 15 行追加段都做「可变字段 → 占位符」归一后**逐字符**比对骨架。因为归一保留了全部标点（`，`、`；`、`：`、全角 `（）`、半角空格），骨架相等即**分隔符体例完全相同**。

先例骨架（3 条先例归一后是同一条）：

```text
④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> offset=<N>，RTTI=<H>→<MAN>；装表点 <H> 位于 <H> 体内，entry 体外） ④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；该槽即其 vt=<H> 表 slot<N>，无归属歧义）
```

- **15 行归一后的 core 与该骨架逐字符相等（15/15）**。
- 每行额外只多一段尾部括注 `（D-47(A) 裁决：…）`，紧随「无归属歧义）」之后——属卡面 §D 明确允许的「本批新增 D-47 披露括注」，不算体例偏离。
- 顺序：见证 → ④升级句，与先例一致；字段：`vt` / `槽 N 值` / `COL` / `offset` / `RTTI→装饰名` / `装表点` / `位于…体内，entry 体外`，齐全；两段之间是单个半角空格，与先例一致。
- `delta.tsv` 用 tab 分隔 8 列：与 `R4_FILL_91_R2\fill_delta.tsv`、`R4_FILL_91_R3\fill_delta.tsv` 的 tab 表头同体例（盘上 `coverage.tsv` 表头自身是**逗号**分隔，那是既有缺陷，不属本批；delta 未被它带偏）。

---

## 6 · §E 反抄袭 — **15/15 PASS**（0 组「除 entry 外完全相同」）

**按卡面判据**：把每行 ④ 段的 8 位十六进制（含 entry 与各地址）替换为占位符后取集合 → **15 条互不相同**，故不存在「除 entry 外完全相同」的两行，**不构成 FAIL**。

**我加做的收紧比对**（连 slot 号一起归一）：出现 5 个同组 —— `1–2`、`3–4`、`5–7`、`9–12`、`13–14`。我的判读是**事实相同，不是文本复制**，判据写清如下：

- **判据**：若两行的差异**全部**落在「可被独立字节复核的事实字段」（entry / vt / slot / COL / offset / TD / 装表点）上，且这些字段经我 §B 实测各自成立 ⇒ 事实相同；若差异落在事实字段**之外**（措辞、语序、增删从句、锚点描述），就是文本复制。
- 本批 5 个同组内：同为**同一张活表的不同槽**，槽号是唯一事实差异，而槽号恰恰是 ④ 要见证的对象；组内 ④ 段除 slot 号与 entry 外无任何字节级事实不同 ⇒ 事实相同。
- **先例侧同样是这个形态**：盘上 91 条已补 ④ 的行按 class 分组后做 entry+slot 归一，`WWMouseClass` 16 行塌成 1 条、`MapSeedClass` 8 行塌成 1 条、`MPGameModeClass` 36 行塌成 7 条、`LocomotionClass` 9 行塌成 4 条。即「④ 见证句是机械陈述 ⇒ 同表同类的行骨架必然相同」是 91 行既有先例的**固有形态**，本批没有引入新的复制形态。
- 反向验证：不同类的行组之间（如 `CCFileClass` 与 `FootClass`）骨架相同但 class/slot/vt/COL/TD/site 的**实测值全不同**，这正是同一模板下的不同事实，不是复制。

---

## 7 · 必改项清单

**0 条。** 15 行 ④ 文本全部可用：无需改写、无需撤回、无需重做。判定与 grade（第 5 列）未被本批触碰（§A 已逐字节证明）。

---

## 8 · NIT（不阻断判定，建议 lead 侧裁量/记档；不是必改项）

| 编号 | 涉及行 | 现象 | 我的判断与建议 |
|---|---|---|---|
| NIT-1 | rows 1–4（`T_…` 模板伪名） | `④ 表属类与行名类一致，均为 <Class>` 里的 `<Class>` 写成了**伪名** `T_DynamicVectorClass_PAVInfantryClass__`；先例 91 行**全部**是非模板真实类名（`BuildingTypeClass` 等），无一条可参照。该形态解模板后的真实类是 `DynamicVectorClass<InfantryClass*>`。 | 符合卡面 §C 的「必须与行 name 的前缀一致」，且与 `probe.py:col_name_match` 的归一化口径一致（15/15 match），**判 PASS**。但「伪名与解模板类名等价」目前只靠该归一化函数承载、COMMON 未成文；建议下一轮在 COMMON 里把模板行的 `<Class>` 口径写死（写伪名 or 写解模板名），免得后人按字符串等价读成不一致。 |
| NIT-2 | 全部 15 行（披露句） | 披露句写 `见 R14_COMMON §12.4`，而 `R14_COMMON.md` 现有**两个 §12.4**：L1216（旧）「三条推进通道的上限量化」、L1557（新，COMMON-R16 追加）「D-47 裁决」。 | 字面指针正确、落点真实（新 §12.4 正是 D-47 裁决条），**判 PASS**。建议后续披露句写成 `§12.4（COMMON-R16 追加 / D-47 裁决条）`，消掉编号歧义——否则读者照编号会先落到旧 §12.4。 |
| NIT-3 | rows 1/2/5/6/7/8/13/14/15（**9 行**） | 这 9 行原句以全角 `。` 结尾，追加段以 `；` 起头 ⇒ 连接处呈 `。；④`（另 6 行 3/4/9/10/11/12 原句以 `）` 结尾，连接处呈 `）；④`，与先例同形）。 | 先例的原文本身以 `；` 结尾，因此没有 `。；` 这一连接形态可供对照。但在「原文必须是严格前缀、一字不改」的硬约束下，`。` 不能删、又不能把它移到追加段之后，`。；④` 是唯一可行写法；**不判偏离**，仅记录以便后人比对时不再重复追问。 |

---

## 9 · 环境观察（**与执行器、与本卡产物均无关**，但会影响他人复跑，必须留痕）

审计期间 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md` 于 **2026-11-20 23:02:33** 被并发改写（coverage.tsv 4,016,071 → 4,018,942 B，+2,871 B；数据行数仍 18,498）。

- 我 23:00 起审时盘上还是 `325158B5…`（= 执行器 REPORT §4 自述的改前/改后同值，**执行器的自述在它产出时点是诚实且准确的**）；
- 现在的 `2BCA3846…` **既不是执行器写的，也不是我写的**（本卡全程只读该文件，只写 `R16_AUDIT_SLOTN_B1\`）。

**对本判决无影响，已逐项确认三点**：
1. 本批 15 个 entry 在**现盘** `coverage.tsv` 里的第 4 列**仍不含** `④ 活表槽位见证`，且仍是 `delta.tsv` 第 4 列的严格前缀，追加段依旧恰好以 `；④ 活表槽位见证` 起头；
2. 15 行的第 1/2/3/5/6/7/8 列在现盘上**仍与 delta 逐字节相同**；
3. §D 用的 3 条先例行（`00464AC0`/`004DE630`/`004F42F0`）的 ④ 段与我 23:00 首次抓取的内容**一致，无差异**。

⇒ 结论：这次并发合并改的是**别的行**，本批 15 行未被触及；§A 与 §D 的判定在**改前、改后两个快照上都成立**。建议 lead 侧核一下 23:02:33 那次写盘出自哪张卡（同时间 PANEL.md 一并被改），确认它是在走「一次性整批」的合规路径。

---

## 附录 · 逐行证据表（由 verify.py 机械生成，见 tables.md）

### §A–§E 逐行结果（15 行全做，无抽样）

| # | entry | name | slot | A 最小改动 | B 字节 6 项 | C 文本一致 | D 合先例 | E 反抄袭 | 行判 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | `T_DynamicVectorClass_PAVInfantryClass__::slot2` | 2 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 2 | 0045A610 | `T_DynamicVectorClass_PAVInfantryClass__::slot4` | 4 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 3 | 0045A680 | `T_DynamicVectorClass_PAVFoggedObjectClass__::slot2` | 2 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 4 | 0045A730 | `T_DynamicVectorClass_PAVFoggedObjectClass__::slot4` | 4 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 5 | 00473BA0 | `CCFileClass::slot10` | 10 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 6 | 00473C50 | `CCFileClass::slot5` | 5 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 7 | 00473D10 | `CCFileClass::slot7` | 7 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 8 | 004A9890 | `DisplayClass::slot36` | 36 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 9 | 004D24A0 | `FoggedObjectClass::slot6` | 6 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 10 | 004D2510 | `FoggedObjectClass::slot5` | 5 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 11 | 004D27D0 | `FoggedObjectClass::slot3` | 3 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 12 | 004D2810 | `FoggedObjectClass::slot13` | 13 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 13 | 004D4200 | `FootClass::slot139` | 139 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 14 | 004D4280 | `FootClass::slot151` | 151 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 15 | 004D4B20 | `AircraftClass::slot133` | 133 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |

### §A 最小改动证据（原第 4 列是否为严格前缀 + 其余 6 列逐字节比较）

| # | entry | coverage 行号 | 原第4列字节长 | 原句末字符 | 追加段字节长 | 追加段首字符 | 连接处 | 第1/2/3/5/6/7/8 列 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | 1388 | 188 | `。` | 407 | `；` | `。；` | 逐字节相同 |
| 2 | 0045A610 | 1389 | 171 | `。` | 407 | `；` | `。；` | 逐字节相同 |
| 3 | 0045A680 | 1391 | 199 | `）` | 423 | `；` | `）；` | 逐字节相同 |
| 4 | 0045A730 | 1392 | 171 | `）` | 423 | `；` | `）；` | 逐字节相同 |
| 5 | 00473BA0 | 1633 | 214 | `。` | 299 | `；` | `。；` | 逐字节相同 |
| 6 | 00473C50 | 1635 | 194 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 7 | 00473D10 | 1638 | 126 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 8 | 004A9890 | 2638 | 122 | `。` | 303 | `；` | `。；` | 逐字节相同 |
| 9 | 004D24A0 | 3109 | 153 | `）` | 319 | `；` | `）；` | 逐字节相同 |
| 10 | 004D2510 | 3110 | 133 | `）` | 319 | `；` | `）；` | 逐字节相同 |
| 11 | 004D27D0 | 3114 | 192 | `）` | 319 | `；` | `）；` | 逐字节相同 |
| 12 | 004D2810 | 3115 | 163 | `）` | 323 | `；` | `）；` | 逐字节相同 |
| 13 | 004D4200 | 3141 | 185 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 14 | 004D4280 | 3142 | 169 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 15 | 004D4B20 | 3143 | 174 | `。` | 311 | `；` | `。；` | 逐字节相同 |

### §B 六项实测值（本脚本从 `ra2youli\gamemd.exe` 字节独立复算）

| # | entry | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=off | ④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 |
|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | `0045A560` | `007FC298` | `0` | `00818D28` | `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@` | `mov dword ptr [esi + 0x66c], 0x7e43c8` |
| 2 | 0045A610 | `0045A610` | `007FC298` | `0` | `00818D28` | `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@` | `mov dword ptr [esi + 0x66c], 0x7e43c8` |
| 3 | 0045A680 | `0045A680` | `007FC528` | `0` | `00819230` | `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@` | `mov dword ptr [eax], 0x7e44f4` |
| 4 | 0045A730 | `0045A730` | `007FC528` | `0` | `00819230` | `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@` | `mov dword ptr [eax], 0x7e44f4` |
| 5 | 00473BA0 | `00473BA0` | `007FA590` | `0` | `00815E58` | `.?AVCCFileClass@@` | `mov dword ptr [esp + 0x20], 0x7e16b0` |
| 6 | 00473C50 | `00473C50` | `007FA590` | `0` | `00815E58` | `.?AVCCFileClass@@` | `mov dword ptr [esp + 0x20], 0x7e16b0` |
| 7 | 00473D10 | `00473D10` | `007FA590` | `0` | `00815E58` | `.?AVCCFileClass@@` | `mov dword ptr [esp + 0x20], 0x7e16b0` |
| 8 | 004A9890 | `004A9890` | `007FFCB8` | `0` | `00816BD8` | `.?AVDisplayClass@@` | `mov dword ptr [esi], 0x7e6114` |
| 9 | 004D24A0 | `004D24A0` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 10 | 004D2510 | `004D2510` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 11 | 004D27D0 | `004D27D0` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 12 | 004D2810 | `004D2810` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 13 | 004D4200 | `004D4200` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` |
| 14 | 004D4280 | `004D4280` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` |
| 15 | 004D4B20 | `004D4B20` | `007FB4C0` | `0` | `00817B90` | `.?AVAircraftClass@@` | `mov dword ptr [esi], 0x7e22a4` |

### §C 文本与事实一致（各项均以实测值比对）

| # | entry | name 的 slot | 文本「槽 N 值」 | 槽内值==entry | COL/offset/RTTI/装表点 与实测 | <Class>==name 前缀 | <Class>↔TD+8 装饰名 | D-47 披露句 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | 2 | `0045A560` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVInfantryClass__`） | PASS | PASS 在位 |
| 2 | 0045A610 | 4 | `0045A610` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVInfantryClass__`） | PASS | PASS 在位 |
| 3 | 0045A680 | 2 | `0045A680` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVFoggedObjectClass__`） | PASS | PASS 在位 |
| 4 | 0045A730 | 4 | `0045A730` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVFoggedObjectClass__`） | PASS | PASS 在位 |
| 5 | 00473BA0 | 10 | `00473BA0` | PASS | PASS | PASS（`CCFileClass`） | PASS | PASS 在位 |
| 6 | 00473C50 | 5 | `00473C50` | PASS | PASS | PASS（`CCFileClass`） | PASS | PASS 在位 |
| 7 | 00473D10 | 7 | `00473D10` | PASS | PASS | PASS（`CCFileClass`） | PASS | PASS 在位 |
| 8 | 004A9890 | 36 | `004A9890` | PASS | PASS | PASS（`DisplayClass`） | PASS | PASS 在位 |
| 9 | 004D24A0 | 6 | `004D24A0` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 10 | 004D2510 | 5 | `004D2510` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 11 | 004D27D0 | 3 | `004D27D0` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 12 | 004D2810 | 13 | `004D2810` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 13 | 004D4200 | 139 | `004D4200` | PASS | PASS | PASS（`FootClass`） | PASS | PASS 在位 |
| 14 | 004D4280 | 151 | `004D4280` | PASS | PASS | PASS（`FootClass`） | PASS | PASS 在位 |
| 15 | 004D4B20 | 133 | `004D4B20` | PASS | PASS | PASS（`AircraftClass`） | PASS | PASS 在位 |

### §D 骨架与先例逐字符比对（先例 3 条归一后为同一骨架）

先例骨架（`00464AC0/004DE630/004F42F0`）：

```text
④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> offset=<N>，RTTI=<H>→<MAN>；装表点 <H> 位于 <H> 体内，entry 体外） ④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；该槽即其 vt=<H> 表 slot<N>，无归属歧义）
```

| # | entry | core 与先例逐字符相等 | 尾部额外括注 |
|---|---|---|---|
| 1 | 0045A560 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 2 | 0045A610 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 3 | 0045A680 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 4 | 0045A730 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 5 | 00473BA0 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 6 | 00473C50 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 7 | 00473D10 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 8 | 004A9890 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 9 | 004D24A0 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 10 | 004D2510 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 11 | 004D27D0 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 12 | 004D2810 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 13 | 004D4200 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 14 | 004D4280 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 15 | 004D4B20 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |

### §E 归一化分组（同组=同 vt 同 class 的行，属「事实相同」）

- 0045A560, 0045A610
- 0045A680, 0045A730
- 00473BA0, 00473C50, 00473D10
- 004D24A0, 004D2510, 004D27D0, 004D2810
- 004D4200, 004D4280

（entry 归一化后重复组：无）

---

## 产物清单

| 文件 | 内容 |
|---|---|
| `VERDICT.md` | 本裁决书 |
| `verify.py` | 可复跑的独立复核脚本：§A 前缀/列比 + §B 6 项字节检查（含 capstone 解码 + 装表点体内/体外辅助项）+ §C 文本一致 + §D 骨架比对 + §E 归一化查重；只读打开 `coverage.tsv`/`delta.tsv`/`gamemd.exe`，输出 `bytecheck.tsv`/`tables.md`/`verify_out.json` |
| `bytecheck.tsv` | 15 行 × 6 项实测值对照（列：`entry` `slot_no` `check1..check6` `verdict` `note`，check 单元格为 `判定:实测值`） |
| `tables.md` / `verify_out.json` / `rerun.log` | 机械生成的中间证据（审计附录所用） |
