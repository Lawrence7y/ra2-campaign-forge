# _er_N9_205_P6_B0CD48_ERRATUM.md — N-9:205「静态 u64 窗口读可闭」对 [0xB0CD48] 不成立 · 勘误登记

- 登记域：lead/n9_erratum_20261108/（唯一写域；本件只登记，不改任何上游原件）
- 登记日期：2026-11-08
- 铁律遵守：零真机（未启动任何 exe）、零采样代码（无 hook/MiniDump/SuspendThread/StackWalk/注入/ctypes/OpenProcess/ReadProcessMemory）、全部证据 = 磁盘文件只读 + struct 解 PE 头；未 commit、未 push。
- 产物：本件 + `_er_check_b0cd48.py`（sha256 f3896d81ce1697c8710950dc15834264ee14e1701198efc65e81b61df65f873b，5209 字节）+ `_er_check_b0cd48_out.txt`（sha256 73f76c8c69a62db350c27759a50bdd8386f7c6c9dc249891877afd64f2ecd7a9，3104 字节）。

## 0 被核对象指纹（本会话 hashlib 实算）

| 件 | SHA256 | 字节数 |
|---|---|---|
| lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md（勘误主对象=N-9 复核件） | 5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9 | 32281 |
| lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md（反驳承载件） | e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7 | 28648 |
| lead/spec_static_closure_20261108/_sc_scan_out.txt（反驳证据存档） | c715898ee1339fa6fdd303a2e93a75f7fec4d92ff725d5f2e6251d76a001a075 | 44255 |
| lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md | 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262 | 26485 |
| lead/static_spec_n9_20261107/_n9_STATIC_COUNT_SPEC.md（上游转录件） | 1817d9ce264b28d3630ee3d596fcaec798afa42733c4a366eaefe14daa5fe281 | 19949 |
| lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md（转录/授权卡） | 7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0 | 29619 |
| lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md（前提原始出处件） | ebacbfcae71c0de3c65d6a0cb573cc9467366f0ecc6bcb8bc570e018c3255bd0 | 19335 |
| lead/spec_static_closure_20261108/_sc_CLOSURE_20261108.md（闭口回件） | 9b8695a3a107cecb4f7884f7e32749cbaaf0fbb333c7f7d19dabb7e425d81b67 | 23490 |
| ra2youli/gamemd.exe（被核镜像） | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 | 4825360 |
| ra2bench/gamemd.exe（旁证副本） | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 | 4825360 |

前四行与编排方所载指纹逐字一致（ALL_MATCH=True，本会话实算）。ra2youli/gamemd.exe 与 _sc_scan.py:13 期望语料指纹 73201cc0… 一致（本会话实算 True）；ra2bench/gamemd.exe 与之字节全同（同 SHA），判定对两副本同值。

## 1 原表述逐字抄录（带行号，本会话实读）

**勘误主对象 = STATIC_COUNT_SPEC.md（下称 N-9 复核件）:205**，位于 §6.2：

```
N-9:198| ### 6.2 搜索缺口（静态可闭、既有材料未做）
N-9:205| | P6 | F8 两个 FPU 常量数值（静态 u64 窗口读可闭） | F8V:169/:222 |
```

**它在讨论什么**：N-9 复核件 §6.1 收录「运行期未验边界（永久缺口——运行期才可定，静态铁律下不可验；承接 N9 §4 P1-P11）」（:187），§6.2 收录「搜索缺口（静态可闭、既有材料未做）」（:198），把 P6/P7/P8/P11 与 S1-S4 归入后者，即判定它们**不需要运行期、静态即可闭**。
**它给出的前提**：「静态 u64 窗口读可闭」——像读 .rdata 常量那样，直接从文件镜像按 qword（u64）窗口读出两个 FPU 常量的数值。同件内更早的表述：

```
N-9:139| - §5.1 一次性读取（:162-169）：`[0x887324]` → 视口原点 `[P+0xB0/B4]` → 屏宽高 `[0xB0CE30/34]` → 投影 FPU 常量 `[0xB0CD48]`/`[0x7E1738]`（两个 qword）。
N-9:145| - 数值（两个 8 字节 double）未读出：F8V:169「数值本轮未读出，标未验」；F8V:222「规格阶段不需要，实现阶段必读」。静态 u64 窗口读即可闭；本任务按铁律不新增探针，未读（§6.2 P6）。
```

**前提来源考**：N-9 复核件标注的出处 F8_VISIBILITY.md:169/:222 本身**没有**静态可闭断言——
```
F8V:169| | 4 | 投影 FPU 常量 | `[0xB0CD48]`(double), `[0x7E1738]`(double) | qword×2 | `0x6D21E2 fmul` / `0x6D21EC fadd`（数值本轮未读出，标未验） |
F8V:222| 3. 投影 FPU 常量 `[0xB0CD48]/[0x7E1738]` 的**数值**未读出（规格阶段不需要，实现阶段必读）；
```
F8V 只写「未读出/标未验/实现阶段必读」；「静态 u64 窗口读可闭」是 N-9 复核件 :145 自己的归类推断，随后进入 :205 §6.2 表，并被上游转录件 _n9:81/:109 与 PERF:139/:161 承接。

## 2 反驳证据逐条核对（STATIC_GAP_CLOSURE.md P6 段 + _sc_scan_out.txt，本会话实读）

| # | 被核项 | 承载（文件:行） | 核对结果 |
|---|---|---|---|
| 1 | `[0x7E1738]=0.5`（.rdata 直读） | GAP_CLOSURE:98；_scan:85（sec=.rdata 文件映射域=[0x007E1000,0x00812000) 文件映射=True）、_scan:86（qword=0x3FE0000000000000 double=0.5）；方法校验锚 _scan:24（qword(0x7E27F8)==900.0 OK） | ✅ 本会话独立复算：.rdata RAWPTR=0x3E1000 → 文件偏移 0x3E1738 字节 `000000000000e03f` = 0.5；0x7E27F8 → 偏移 0x3E27F8 = 0x408C200000000000 = 900.0。映射法在该段正确 |
| 2 | `[0xB0CD48]` 落 .data 零初始化域、文件镜像无值 | GAP_CLOSURE:99；_scan:58（VA=0x00B0CD48 sec=.data 文件映射域=[0x00812000,0x0087E000) 文件映射=False）、_scan:59（数值不在文件镜像内（BSS 零初始化域）） | ✅ 本会话独立 PE 解析证实（见 §3）；但按 :99 「.data 零初始化域」表述准确，:173 「（BSS，…）」应读作「BSS 型（.data 节内零初始化尾）」——该 PE 无独立 .bss 节（§3 判定第 4 条） |
| 3 | 全部访存 12 条 = 唯一写者 0x6D1BDD fstp + 11 条 fmul 读 | GAP_CLOSURE:99；_scan:72（=12 条）、:73（0x006D1BDD fstp qword ptr [0xb0cd48]）、:74-84（11 条 fmul） | ✅ 存档一致；本会话字节实证写点在文件镜像内真实存在：文件偏移 0x2D1BDD = `DD 1D 48 CD B0 00`（即 fstp qword [0xB0CD48] 编码）。注：12 条清单为存档转引（_scan:72-84），本会话未重演 capstone 全量反汇编，但不影响判定（见 §3 第 5 条） |
| 4 | 写者宿主函数 0x6D1BB0（前邻 nop 填充、尾 ret） | GAP_CLOSURE:99；_scan:754-762（ret@0x6D1BA7 + nop×8 @0x6D1BA8-B0AF）、_scan:763-774（fld@0x6D1BB0 … ret@0x6D1BE3） | ✅ 函数体起点 0x6D1BB0 处文件偏移 0x2D1BB0 字节 = `DD 05 28 17 7E 00`（fld qword [0x7E1728]）实证在案 |
| 5 | 表达式 ret(0x4CACB0,[0xB0CD88],[0xB0CD8C])×(60.0/[0xB0CD78]) | GAP_CLOSURE:99；指令序列 _scan:763-774：fld [0x7E1728]→fdiv [0xB0CD78]→mov eax/ecx←[0xB0CD8C]/[0xB0CD88]→push×2→fstp [0xB0CE18]→call 0x4CACB0→fmul [0xB0CE18]→add esp,8→fstp [0xB0CD48] | ✅ 逐指令与公式转写一致；本会话字节实证：0x6D1BB6 = `DC 35 78 CD B0 00`（fdiv [0xB0CD78]）、0x6D1BCF = `E8`（call）；[0x7E1728] 直读 = 60.0（qword 0x404E000000000000，文件偏移 0x3E1728）——GAP_CLOSURE:99 「fld [0x7E1728]（=60.0）」成立 |
| 6 | 「各输入均为运行期初始化/计算量」 | GAP_CLOSURE:99；未追声明 GAP_CLOSURE:101 | ✅ 本会话独立：0xB0CD78、0xB0CD88、0xB0CD8C、0xB0CE18 全部落在 .data 零初始化尾（d=0x2FAD78/0x2FAD88/0x2FAD8C/0x2FAE18 ≥ RAWSZ 0x6C000）⇒ 文件镜像均无值 |

## 3 关键判定：[0xB0CD48] 是否真的文件镜像无值（本会话独立实跑）

实跑命令：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_check_b0cd48.py"`（exit=0；全量输出 = `_er_check_b0cd48_out.txt`，sha256 73f76c8c…）。要点：

1. **镜像指纹**：ra2youli/gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476、4825360 字节，与语料指纹一致（R0 SHA_MATCH_CORPUS_73201cc0=True）。ra2bench/gamemd.exe 与其字节全同。
2. **PE 节表**（本会话独立解析，IMAGEBASE=0x00400000，5 节）：.text VA=0x401000/RAWSZ=0x3E0000；.rdata VA=0x7E1000/RAWSZ=0x31000；**.data VA=0x812000/VSZ=0x367BE4/RAWPTR=0x412000/RAWSZ=0x6C000（VSZ≫RAWSZ，ZEROINIT_TAIL=YES）**；.rsrc VA=0xB7A000；.detour VA=0xB93000。
3. **[0xB0CD48] 判定**：RVA=0x70CD48 → 唯一命中 .data（0x812000 ≤ 0x70CD48 < 0x812000+0x367BE4=0xB79BE4，且 .rsrc/.detour 起点更高、无重叠），节内偏移 d=0x2FAD48 ≥ RAWSZ=0x6C000 ⇒ **va2off 无解、文件镜像该 VA 无任何字节**；其位置是 .data 节内零初始化尾 VA∈[0x87E000, 0xB79BE4)（尾长 0x2FBBE4 字节）。假想线性文件偏移 0x70CD48 超出 .data 镜像末端 0x28ED48 字节，且全文件仅 0x49A110 字节。**「静态 u64 窗口读」在该地址无值可读——反驳成立。**
4. **精确化注记**：该 PE 仅 5 节、**无独立 .bss 节**；0xB0CD48 所在是 .data 节的零初始化尾（BSS 型存储）。GAP_CLOSURE:99 「落在 .data 零初始化域」表述准确；GAP_CLOSURE:173 「（BSS，运行期计算值）」的「BSS」须按 BSS 型理解，作节名理解则不确——术语精确化，非新疵点。
5. **判定的稳健性**：文件镜像无值是 PE 头层面的结构性事实，与「唯一写者」归因无关——即使 _scan 的 12 条访存清单不完备（本会话未重演全量反汇编），只要文件镜像无初值，该 qword 的任何运行期值都只能来自运行期写入；写点字节 `DD 1D 48 CD B0 00`（文件偏移 0x2D1BDD）与整链指令编码已逐一从文件镜像实证（§2 表 #3/#4/#5）。输入端 0xB0CD78/88/8C 亦文件镜像无值 ⇒ 无法静态求值链条。
6. **同法对照**（证映射法无系统性偏差）：[0x7E1728]=60.0、[0x7E1738]=0.5、[0x7E27F8]=900.0 三点直读全中（文件偏移 0x3E1728/0x3E1738/0x3E27F8）——.rdata 段映射正确，.data 尾部不可读是地址本身超出 RAWSZ 所致，非工具误差。

## 4 勘误条目（登记不裁断，原件一律不改）

**【E-1】N-9:205 P6 前提「静态 u64 窗口读可闭」对 [0xB0CD48] 不成立（半成立前提）**

- **原表述**：N-9:205「| P6 | F8 两个 FPU 常量数值（静态 u64 窗口读可闭） | F8V:169/:222 |」（其 §6.2 节题 ：198「静态可闭、既有材料未做」为该前提的上位表述）；同件 ：145「静态 u64 窗口读即可闭」、:139 将 `[0xB0CD48]`/`[0x7E1738]` 并列为「两个 qword」一次性读取。
- **实测事实**：[0x7E1738] 落 .rdata 文件映射域，直读 = 0.5（本会话实证）；[0xB0CD48] 落 .data 节内零初始化尾（VA∈[0x87E000,0xB79BE4)，d=0x2FAD48≥RAWSZ=0x6C000），**文件镜像无值**；其值由唯一写点 fstp@0x6D1BDD（宿主 0x6D1BB0）按 ret(0x4CACB0,[0xB0CD88],[0xB0CD8C])×(60.0/[0xB0CD78]) 运行期算出，输入端三个地址同样文件镜像无值 ⇒ 该地址数值**结构性静态不可闭**。前提对两常量之一成立、对另一不成立。
- **影响范围**：①N-9 §6.2 分类表 P6 行：应降为「半闭半开」（[0x7E1738] 可闭、[0xB0CD48] 结构性开口）；②N-9 §5.2 缺口①（:143-145）与 §5.1 基线（:139）的「两个 qword」并读表述；③PERF:139 的 P6 联引与 PERF:161 Q3 授权卡「S1/S2/S3/S4/P6/P7/P8/P11 **均**静态可闭」——P6 一半不可静态闭（闭口任务实际已按「部分闭口单列」处置，GAP_CLOSURE:96/:173/:183）；④上游转录 _n9:81/:109 同语；⑤F8 实现阶段取值（F8V:222「实现阶段必读」）：不能文件窗口读，须运行期读取或先闭输入链（0xB0CD78/88/8C 写者、0x4CACB0 语义，GAP_CLOSURE:101 未做项）。
- **建议处置**：**保留原表述、加勘误注记**（原件不可改）：在 N-9:205/:145 处挂注「P6 前提仅对 [0x7E1738] 成立；[0xB0CD48] 为 .data 零初始化尾运行期计算值，静态 u64 窗口读无值可读——勘误见 lead/n9_erratum_20261108/_er_N9_205_P6_B0CD48_ERRATUM.md，反驳原件 STATIC_GAP_CLOSURE.md §4.1/:99-100、_sc_CLOSURE_20261108.md:63/:164」；**下游引用须带限定**：凡引 N-9:205、PERF:161 Q3、PERF:139 者，须注明「P6 半闭半开、[0xB0CD48] 静态不可闭」；F8 实现排程相应改道。

## 5 downstreamImpact（需加限定的已交付件清单）

| 件（指纹见 §0） | 需加限定处 | 性质 |
|---|---|---|
| lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md | :205（P6 行）、:145、:139、§6.2 节题 :198 | 勘误主对象 |
| lead/static_spec_n9_20261107/_n9_STATIC_COUNT_SPEC.md | :81「静态 u64 窗口读即可闭」、:109「搜索（静态 u64 窗口读可闭；本任务未执行）」 | 上游转录，同语受累 |
| lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md | :139（P6 联引）、:161（Q3「均静态可闭」授权卡，任务出处即此） | 授权卡限定 |
| lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md | :169（两常量并列 qword×2 一行——实现阶段读者若按行同法取值会踩 [0xB0CD48] 开口）；:222（「实现阶段必读」须注明取值方式受限） | 非前提载体（原文无静态可闭断言），仅需引用限定，不构成疵点 |
| lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md | :162 只写「未读出」，无该前提 | **无需勘误** |
| lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md、_sc_CLOSURE_20261108.md | :50/:99-100、:44/:63/:164 已自带修正 | 反驳承载件，无需加注 |

## 6 实跑命令清单（本会话）

1. `python -I -X utf8 -c`（hashlib 四件指纹复算）→ 与编排方指纹 ALL_MATCH。
2. `python -I -X utf8 -c`（STATIC_COUNT_SPEC.md:180-231 实读）→ §1 抄录。
3. `python -I -X utf8 -c`（STATIC_GAP_CLOSURE.md 全文关键词定位）→ P6 段 :94-101/:173/:183-184。
4. `python -I -X utf8 -c`（_sc_scan_out.txt :22-26/:56-100/:754-776 实读）→ §2 表 #1-#5。
5. `ls lead/spec_static_closure_20261108/` + `find … -iname "gamemd*.exe"` → 件清单与两副本定位。
6. `python -I -X utf8 -c`（_sc_scan.py :1-80/:80-135 实读）→ 扫描方法与 exe 路径、期望指纹（:9-13）。
7. `mkdir -p lead/n9_erratum_20261108`（建写域）。
8. Write `_er_check_b0cd48.py`；`python -I -X utf8 …_er_check_b0cd48.py > …_er_check_b0cd48_out.txt`（exit=0）→ §3 全部判定。
9. `ls lead | grep …` + `find … -iname "*F8V*" -o -iname "PERF*"` → 下游件定位。
10. `python -I -X utf8 -c`（PERF_REPAIR_HANDOFF.md:139/:161 实读）。
11. `grep -rn "静态 u64 窗口读" lead --include="*.md"` → 全仓引用面（8 处，见 §1/§4/§5）。
12. `python -I -X utf8 -c`（F8_VISIBILITY.md:160-171/:218-225 实读）→ 前提来源考。
13. `python -I -X utf8 -c`（STATIC_COUNT_SPEC.md:133-149 实读）→ :139/:145 语境。
14. `grep -rn "B0CD48" lead --include="*.md" -l` + `_n9_STATIC_COUNT_SPEC.md:81/:109` 实读 + 其指纹 → 19949 字节/1817d9ce…（与 N-9 复核件 :223 自记「1817d9ce…/19949B」互证一致）。
15. `python -I -X utf8 -c`（W8/PERF/_sc_CLOSURE 三件指纹 + W8:162 实读）。
16. `python -I -X utf8 -c`（ra2bench/gamemd.exe 指纹 + 0xB0CD48 节归属）→ 与 ra2youli 同 SHA、同判定。
17. `python -I -X utf8 -c`（F8_VISIBILITY.md 与本写域两产物指纹）。

## 7 未验/未做（如实）

- 未重演 _sc_scan.py 全量（capstone 647 条访存解码、逐指令 xref 未复跑）；12 条访存清单系存档转引（_scan:72-84）。**不影响 §3 判定**（结构性事实独立于访存清单完备性，见 §3 第 5 条）。
- 0x4CACB0 语义、0xB0CD78/88/8C 写者、60.0/[0xB0CD78] 的工程含义未追——同 GAP_CLOSURE:101 未做项，另立搜索任务；不补猜任何数值。
- 本会话零真机、零活进程接触、零采样代码；未 commit、未 push。
