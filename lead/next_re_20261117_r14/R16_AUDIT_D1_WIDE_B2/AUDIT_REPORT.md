# R16-AUDIT-D1-WIDE-B2 审计报告

> 角色：审计员 · 被审：`lead\next_re_20261117_r14\R16_D1_WIDE_B2\`（delta.tsv 18 行 / fields.tsv / REPORT.md）
> 写域：`lead\next_re_20261117_r14\R16_AUDIT_D1_WIDE_B2\`（仅此目录）；`gamemd.exe` 与 `coverage.tsv` 全程只读。
> 日期：2026-11-21

## 0. 结论

**17 PASS / 1 FAIL。** 唯一不合格行 `00473B10`（`CCFileClass::slot9`），C、D 两项同时不过 —— 与 B1 翻车的第 ① 条同一形态：**栈临时对象被标成 `ctor_body`**。

- 六项字节复核 **18/18 全真**（本审计独立复算，未采用执行器报告值）。
- 原文保全 A **18/18**，反抄袭 E **18/18**，清单一致性 F **18/18**，披露指针 **18/18 指向 §12.6**、0 处误写 §12.4。
- 5 行 CLASS_FIX **全部成立**（5/5）。
- 装配形态标注 **17/18 正确**。**1 处栈目标被标成 ctor_body**；**0 处析构宿主被标成 ctor_body**。
- **必改 2 条**（其中 1 条阻塞）。

## 1. 独立复算方法（与执行器的差别）

执行器的 `verify.py:14` `import final as F` 并复用 `F.load_atlas()` 与 `F.Image`：**第 ⑤ 项「装表点在 entry 体外」由 `atlas.get(ei, 0)` 决定**，entry 不在 atlas 时 `sz=0` 恒真；其余字节读取也走同一 `Image`。故其「独立复核」与原推导同源。本审计另立实现：

| 项 | 本审计做法 |
|---|---|
| PE 解析 | 自写 PE32 头/SectionTable 解析，按 `VirtualSize`（非 file size）铺满虚拟镜像 |
| .data 判定 | 用 `VirtualSize`：`.data va=00812000 vs=367BE4` ⇒ `0x812000..0xB79BE4`（`0xABC604` 在域内，仅凭文件大小 4.8MB 会误判出界） |
| RTTI | 自写 `u32(vt-4)`→COL→`sig==0`/`offset==0`/`u32(COL+12)`→`TD+8` 装饰名 |
| 装表点枚举 | 自写 `.text` 单遍线性反汇编建 `mov [mem], imm32` 索引（imm∈镜像） |
| 函数边界 | 首选 atlas 尺寸；非 atlas 宿主用「前邻 ≥2 填充字节 + 解码必须恰好落在装表点」验证起点 |
| `this` 归属 | 从宿主起点对齐反汇编，回溯装表基址寄存器的最近定义，判 `mov R, ecx`（thiscall this）/ `lea` / `[esp+K]` |
| 宿主身份 | 在**宿主函数真实值域内**（atlas 尺寸）检测 `test byte ptr [esp+X],1` + `call 0x7c8b3d` + `ret N` 三元组 |

> 注：本审计第一版用固定 0x1200 字节窗口做身份检测，会把相邻函数算进来而误报；已改为按函数真实值域判定。同理，首版线性窗口在 `0040D1B1` 处失步（把 `push esi` 拆成 `push edi` 前的错位），已用原始字节校验纠正 —— 详见 §6。

## 2. A–F 逐项不合格行数

| 项 | 内容 | 不合格行数 | 结论 |
|---|---|---:|---|
| **A** | 原文保全（严格前缀 + 其余列逐字节 + grade 未变） | **0** | 18/18 通过 |
| **B** | 字节事实（6 项独立复算 + 装表点所在函数≠entry） | **0** | 18/18 × 6 全真 |
| **C** | 装配方式标注是否正确（含宿主身份） | **1** | `00473B10` |
| **D** | 文本与事实一致（含 §12.6 指针、§12.4 判 FAIL） | **1** | `00473B10` |
| **E** | 反抄袭 | **0** | 18/18 |
| **F** | 清单一致性 | **0** | 18/18 |

### A 原文保全
- 8 列齐备；第 1/2/3/5/6/7/8 列与盘上 `coverage.tsv` **逐字节相同**（0 处差异）。
- 第 4 列 **严格前缀**成立（`new.startswith(old)` 且 `len(new) > len(old)`），18/18。
- `grade` 全部保持 `[已证]` 未动。
- 盘上原第 4 列 **无一行含 `④`** ⇒ 无重复追加、无 `SKIP-ALREADY` 漏判。

### B 字节事实
逐行独立复算 6 项，**18/18 行 × 6 项全 True**：

| 项 | 判据 | 结果 |
|---|---|---|
| ① | `u32(vt+slot*4) == entry` | 18/18 |
| ② | `u32(COL) == 0`（sig） | 18/18 |
| ③ | `u32(COL+4) == 0`（offset） | 18/18 |
| ④ | `TD=u32(COL+12)`；`cstr(TD+8)` 以 `.?A` 开头 | 18/18 |
| ⑤ | 装表点在 entry 体外 | 18/18 |
| ⑥ | vt 取得 | 18/18 |

⑤ 用**双重口径**：entry 自身函数值域（本审计线性解码）**与** atlas 尺寸都不含装表点。本批 18 行的装表点地址**全部低于** entry 起点，且宿主函数值域不含 entry 起点 ⇒ 「装表点所在函数≠entry」成立。

### E 反抄袭
- 完整 ④ 正文 18 条 **两两不同**（18 distinct）。
- 8 位十六进制归一为 `ENTRY` 后仍 18 distinct；再把 `slotN` 归一后仍 18 distinct。
- 与盘上已有 ④ 段比对：**0 条**与既有行重复。
- 同 vt/同装表点的成组行（4×TabClass、2×MouseClass、2×FootClass、2×InfantryClass、2×DynamicVectorClass）差异落在 `label/slot/槽值` 上，且这些差异可逐条字节验证为真 —— 属事实同源而非抄袭。

### F 清单一致性
`sieve_all.tsv` 81 行 → `has_ring4_on_disk==否` **65** 行 → 按 entry 升序取 `[18:36]`，与本批 18 个 entry **顺序完全一致**（非仅集合相等）。与 B1 前 18 行、B3 后 18 行交集均为 0。

## 3. 特别加严 ①：装配方式标注（宿主身份）

### 3.1 判据
- 标 `ctor_body`：装表点目标必须是 **`this`**（不得为 `[esp+..]` 栈临时对象）；宿主必须是真构造器/工厂，**不得**是 scalar deleting destructor（尾段 `test byte ptr [esp+X],1` + `call 0x7c8b3d` + `ret N` 同构）。
- 标 `mov_abs`：必须是 `mov [绝对地址], vt` 且该地址在 `.data`。

### 3.2 结果

| 类别 | 行数 | 核验 |
|---|---:|---|
| `mov_abs` 且 abs 落 `.data` | 4 | **4/4 正确**（`0x87F7E8`、`0xABC604` 均在 `.data`） |
| `ctor_body` 且目标 = `this`（`mov R, ecx`）、宿主非析构 | 13 | **13/13 正确** |
| `ctor_body` 但目标为栈槽 | 1 | **`00473B10` 错** |
| 析构宿主被标 `ctor_body` | 0 | **无** |

- **析构宿主检查**：14 个有 atlas 尺寸的 `ctor_body` 宿主逐个在其真实值域内检测三元组，**0 个命中**。（注意 `0046C890` 这一**行本身**确是 scalar deleting destructor，但其**宿主** `0046BBC0` 是真构造器 —— 执行器此处没有混淆。）
- **栈目标检查**：唯一命中 `00473B10`。

### 3.3 `00473B10` 错在哪（阻塞项）

```
装表点 004014AC，宿主 004011C0（1729 条指令的非构造器函数）
004014AC: mov dword ptr [esp + 0x20], 0x7e16b0     ← 写入栈槽，不是 this
004014B4: mov dword ptr [esp + 0x84], ebx
004014C0: lea ecx, [esp + 0x20]                    ← 取该栈临时对象的地址作 thiscall 实参
004014C4: mov dword ptr [esp + 0x20], 0x7e1668     ← 紧接着覆盖成另一个 vptr
004014CC: call 0x431b80
```

该处是在**宿主函数体内构造一个栈上临时 CCFileClass（及其派生）对象**，再把 `ecx` 指向它去调用。`esp` 不是 `this`。

**这不是取址失败，而是取址启发式选错。** 同一 vt `007E16B0` 共有 **185** 个装表点，其中 **5 个是真 `this` 目标**：

| 装表点 | 宿主 | 目标寄存器来源 | 宿主性质 |
|---|---|---|---|
| `004019A6` | `00401980` | `mov esi, ecx` | 虚调用转发，非构造器 |
| `00473A12` | `004739F0` | `mov esi, ecx` | 真 ctor（atlas 58 B） |
| `00473A4F` | `00473A30` | `mov esi, ecx` | 真 ctor（atlas 70 B） |
| **`00473A9B`** | **`00473A80`** | **`mov esi, ecx`** | **真 ctor（atlas 44 B，最干净）** |
| `00535A76` | `00535A70` | `mov esi, ecx` | 单指令宿主 |

`00473A80` 原始字节与解码（可作改取目标）：

```
00473A80  56            push esi
00473A81  8b f1         mov esi, ecx          ← this
00473A83  e8 a8 6f 00 00   call 0x47aa30      ← 基类 ctor
00473A8C  8d 4e 58      lea ecx, [esi + 0x58]
00473A8F  e8 6c 72 fc ff   call 0x43ad00
00473A94  c7 46 64 00 00 00 00   mov dword ptr [esi + 0x64], 0
00473A9B  c7 06 b0 16 7e 00      mov dword ptr [esi], 0x7e16b0
00473AA1  c7 46 68 00 00 00 00   mov dword ptr [esi + 0x68], 0
00473AA8  8b c6         mov eax, esi
00473AAA  5e            pop esi
00473AAB  c3            ret
```

## 4. 特别加严 ②：5 行 CLASS_FIX 逐行核

判据（卡面 §3 第 4 条，执行器记作「§3.4」）：行名类与该表 RTTI 类不符时，按「类一致优先」另取行名类自己的活表，并在 `fields.tsv` 标 `CLASS_FIX` 逐字披露理由。

| entry | 行名类 | 原决定性表 | 原表类 | 不符? | 改取表 | 改取类 | 类符? | 槽持有? | 成立 |
|---|---|---|---|---|---|---|---|---|:--:|
| `004A8960` | TabClass | `007E1964`/slot42 | `.?AVMouseClass@@` | 是 | `007EDFB4`/slot42 | `.?AVTabClass@@` | 是 | 是 | **✓** |
| `004A9840` | TabClass | `007E1964`/slot41 | `.?AVMouseClass@@` | 是 | `007EDFB4`/slot41 | `.?AVTabClass@@` | 是 | 是 | **✓** |
| `004AAD30` | TabClass | `007E6114`/slot49 | `.?AVDisplayClass@@` | 是 | `007EDFB4`/slot49 | `.?AVTabClass@@` | 是 | 是 | **✓** |
| `004AAE90` | TabClass | `007E1964`/slot46 | `.?AVMouseClass@@` | 是 | `007EDFB4`/slot46 | `.?AVTabClass@@` | 是 | 是 | **✓** |
| `004AB9B0` | DisplayClass | `007E1964`/slot48 | `.?AVMouseClass@@` | 是 | `007E6114`/slot48 | `.?AVDisplayClass@@` | 是 | 是 | **✓** |

**5/5 成立。** 逐项已核：

1. **改选表 RTTI 类 == 行名类**：均是严格 `.?AV<行名类>@@`（非 token 近似）。
2. **entry 确在改选表该槽**：`u32(vt+slot*4)==entry` 全部成立。
3. **原选表为何类不符**：原表 RTTI 类确与行名类不同（如上表）；且原表**确实**持有该 entry 于该槽 —— 不是「原表根本不含此 entry」的取址错误。
4. **改选表是唯一解**：4 个 TabClass 行各只有 **1** 张严格 TabClass 表持有该 entry（`007EDFB4`）；`004AB9B0` 只有 **1** 张严格 DisplayClass 表（`007E6114`）。不存在「另一张同样合规的表被跳过」。
5. **改选表是活表**：`007EDFB4` 有体外装表点 `005BE9C7`/`006CFE86`；`007E6114` 有 `004A8830`/`006AC861`；所选均为其中最低地址者且**均为 `this` 目标**。

**机制背景（供后续批次参照）**：这些 entry 是**继承未覆盖**的虚函数，故同时出现在整条派生链的每一张表里 —— `004A8960` 同时被 **7** 张表在同一槽持有（MouseClass/DisplayClass/TabClass/PowerClass/RadarClass/ScrollClass/SidebarClass），`004AAD30` 为 5 张。因此「取哪张表」必须由行名类决定，执行器依卡面「类一致优先」改取是对的。

### 4.1 未标 CLASS_FIX 的模板伪名两行
`0054E890` / `0054EA70`：行名 `T_DynamicVectorClass_PAUKamikazeControl__`，RTTI `.?AV?$DynamicVectorClass@PAUKamikazeControl@@@@`。严格串不等，但标识符逐 token 命中。**与 B1 `0040F870` 同口径**（`R16_D1_WIDE_B1\fields.tsv` 该行同样按「缩写/token 命中，非类不符，无需 CLASS_FIX」处置并披露）。本批亦在 `fields.tsv` note 逐字披露。**判同类、不标 CLASS_FIX，成立。**

## 5. 披露指针核验

- **18/18 行**含 `见 R14_COMMON §12.6 与 PANEL 对应披露`。
- **0 行**出现 `§12.4`。（§12.4 是「三条推进通道的上限量化」，与 ④ 无关，误引即 FAIL。）
- 18/18 行含 `§12.3 对该形态让位` 让步子句 —— 合 §12.6「引用纪律」：须同时引用本条与 PANEL 披露，且**不得**表述为「已过 §12.3」。本批表述正确。
- 18/18 行含 `D-47(A) 裁决：槽位占用即 ④`。

## 6. 「最低地址命中」类脆弱启发式（B1 根因）—— 仍然存在

执行器本批两处采用同一脆弱取法，本批已因此产生 1 行错判：

| 位置 | 代码 | 形态 | 本批后果 |
|---|---|---|---|
| `R16_D1_WIDE_B2\derive_raw.py:160` | `site = es[0]` | `ext_sites()` 按 `.text` 线性顺序返回，`es[0]` = **最低地址命中** | **`00473B10` 取到 `004014AC`（栈临时对象），丢弃了 5 个 `this` 目标点** |
| `derive_raw.py:139-144` | `cands.sort(); cands[0]` | 类一致候选按 `(vt,k,site)` 排序后取**最低 vt** | 本批未致错（每行严格类匹配表唯一） |
| `derive_raw.py:81-94` | `host_capstone()` | 「site 前最后一个 ret → 其后第一条非 nop/int3」 | 本批未致错（2 个非 atlas 宿主 `0040D1B0`/`0054E260` 经本审计填充带法复核**均正确**） |

叠加根因在分类器本身 —— `R16_D1_WIDE_B2\generate.py:87-92`：

```python
if op.lower().startswith("0x"):
    form = "mov_abs"
elif op:
    form = "ctor_body"        # ← 任何寄存器/栈目标一律判 ctor_body，不校验是否 this
```

`op` 仅由 `re.search(r"\[([^\]]+)\]", ins)` 取操作数形态，**没有宿主身份校验**，故 `[esp + 0x20]` 也被归为 `ctor_body`。B1 翻车即此，本批原样复现。

**本批风险量化**：18 行中 18 行都满足 `site_used == min(ext_sites)` —— 即**全部**用最低地址命中。只有 `00473B10` 撞上「最低地址恰好是栈临时对象」；其余 13 个 `ctor_body` 行的最低地址装表点恰好都是 `this`。属**侥幸**而非规则保证：`CCFileClass` 的 vt 有 185 个装表点（绝大多数是栈临时对象），这类高扇出 vt 极易再踩。

## 7. 执行器 REPORT.md 与事实的差异

| # | REPORT 说法 | 事实 | 判定 |
|---|---|---|---|
| 1 | §0/§5「18 行全部取得完整 ④ 数据」「6 项字节复核全通过」 | 属实（本审计独立复算一致） | 相符 |
| 2 | §4 计数 `OK 13 / CLASS_FIX 5 / SKIP 0 / SKIP-ALREADY 0` | 属实 | 相符 |
| 3 | §3 `mov_abs 4 / ctor_body 14 / reg 0 / other 0` | **计数与自身标签一致，但其中 1 个 `ctor_body` 标签为错** | **受 #5 影响** |
| 4 | §4.1 CLASS_FIX 5 行明细（原表 vt/类、改取表 vt/类、装表点/宿主） | 逐格与独立复算一致 | 相符 |
| 5 | §4.1「改取表均：同址持有该 entry、COL offset=0、有体外装表点、6 项字节复核全真、槽值==entry」 | 5/5 属实 | 相符 |
| 6 | §6「行行不同 18/18」 | 属实 | 相符 |
| 7 | §7 `coverage.tsv` sha `412ED7E3…` / `gamemd.exe` sha `73201CC0…` | 本审计实测同值，两文件确未改 | 相符 |
| 8 | 第 3 行「卡号 **R16-D1-WIDE-B1**（批次 B2）」 | 本批卡号应为 **B2**；B1 是上一批 | **笔误** |
| 9 | §4.1 引用「卡面 §3.4」 | 卡面 `_cards\R16-D1-WIDE-B.md` 无 §3.4 小节，实为 §3 第 4 条 | 编号不准 |
| 10 | §4.1 触发源用 `final.tsv`（ext[0] 决定性表） | 卡面 §3 第 4 条原文要求触发源是 **`sieve_all.tsv` 里记的 `vt`**，但 `sieve_all.tsv` **无 vt 列**（11 列为 entry…n_supporting_artifacts）。执行器改用 `final.tsv` 未在 REPORT 披露此替换 | **未披露的替换** |

## 8. 必改清单

**必改 2 条：**

**M1（阻塞）`00473B10` 装配方式/宿主重取或改判。** 现 `site=004014AC` / `host=004011C0` / `form=ctor_body` 三项组合不成立（目标为栈槽，宿主非构造器）。二选一：
- **(a) 改取 `this` 目标装表点**（推荐）：`site=00473A9B` / `host=00473A80`（真 CCFileClass ctor，44 B），或 `00473A12`/`00473A4F`。同步改 `fields.tsv` 的 `install_site`/`install_host` 与 ④ 正文（`装表点`、`宿主`、`实测指令` 三处）；六项字节复核与槽位事实不受影响。
- **(b) 保留 `004014AC` 但改判形态**：`form` 不得为 `ctor_body`（栈临时对象，非构造器体内），且 ④ 须如实写明「写入栈上临时对象，非 `this`」。

无论哪种，当前 ④ 的 `装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 mov dword ptr [esp + 0x20], 0x7e16b0）` 都是**内部自相矛盾**（说 `[reg]` 却引 `[esp+0x20]`），必须重写。

**M2 `REPORT.md:3` 卡号笔误**：`卡号 R16-D1-WIDE-B1（批次 B2）` → 应为 B2 卡。

**建议 2 条：**

- **S1** 在 REPORT 披露「卡面 §3.4 触发源 `sieve_all.tsv` 无 vt 列，实际改用 `final.tsv` 决定性表」这一替换，并订正为「§3 第 4 条」。
- **S2** `0054E890`/`0054EA70` 的 ④「④ 表属类与行名类一致，均为 `T_DynamicVectorClass_PAUKamikazeControl__`」措辞过硬（真实 RTTI 是模板展开名）。建议加限定词如「按标识符逐 token 一致」，与 `fields.tsv` note 口径对齐。不阻塞。

**流程建议：**
- **S3** 根治脆弱启发式：`derive_raw.py:160` 的 `es[0]` 应改为**优先选 `this` 目标装表点**（按基址寄存器回溯判定），而非最低地址；`generate.py:91` 的 `elif op: ctor_body` 必须加「目标为 `this` 且宿主非析构」前置校验，否则应降为 `reg`/`other`。这是 B1、B2 的共同根因，不修则 B3/B4 必再犯。

## 9. 产物

| 文件 | 说明 |
|---|---|
| `AUDIT_REPORT.md` | 本报告 |
| `verdict.tsv` | 18 行 × A–F 逐项判决（17 PASS / 1 FAIL） |
| `audit_b2.py` | 自写 PE 解析 / RTTI / 装表点索引 / 六项复算 → `_facts.txt` `_facts.json` |
| `audit_b2b.py` | 对齐反汇编 + `this` 归属 + 宿主身份 → `_facts2.txt` `_facts2.json` |
| `audit_b2c.py` | A–F 判定 + CLASS_FIX 复核 → `_verdict.txt` `_verdict.json` |
| `audit_b2d.py` | 脆弱启发式量化 + 析构宿主扫描 → `_fragility.txt` `_fragility.json` |
| `audit_b2e.py` | 生成 `verdict.tsv` |
| `_scan.txt` | 18 行全部候选表树（独立枚举，供 CLASS_FIX 对照） |

**只读声明**：`gamemd.exe` 全程 `rb` 打开，sha256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` 未变；`coverage.tsv` 只读，sha256 `412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1` 未变；未写 `R16_D1_WIDE_B2\` 任何文件。
