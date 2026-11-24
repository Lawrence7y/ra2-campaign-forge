# R55-T4-AUDIT53 · 独立审计报告

审计员：t4-audit53（独立；只读；仅写本目录）
时间：2026-11-22（Asia/Shanghai）
被审对象：`§2.53` 传导链、`FACT_INDEX` v5.27 `F24`、R55-T2「三态」方案
纪律：盘上实测集合运算；逐字引用+文件/行/键；读不到写「未取得」；不改被审文件。

---

## 数据采集说明（先于结论）

- 三个清单实测于并发改动之前：`tier_final.tsv` 当时 4518 数据行 + 表头，sum(bytes)=724,479,859；与分析卡给的数字一致。审计进行中，另有 agent 在 `tier_final.tsv:4520` 追加了一行 `DISC_RECHECK discipline=28 round=R55 ... conclusion=PASS`（非本审计员所为）。该行 round=R55 超出 `recheck_verify.py` 的 ROUND_WINDOWS（max R53），实测 `verify_recheck_line` 返回 `False / R4 no round window for R055`。**本审计的所有集合运算基于干净的 4518 行状态**（证据：`analysis.json`）。
- 控制台中文显示乱码只是 pwsh 编码；所有结果写入本目录 JSON 后用 UTF-8 读回，数据本身正确。

---

## Q1 · 传导链的算术与集合关系对不对？

**判定：算术/集合 全对。**

逐字引用（被审断言）：
- `R14_COMMON.md:4420-4422`：「`tier_final = P1a（3,786 件 / 714,228,639 B，全在 C′ 内）∪ 逐件判为对象者（732 件 / 10,251,220 B，0 件在 C′ 内） = 4,518 件 / 724,479,859 B`」
- `R14_COMMON.md:4425`：「那 732 件里属 C′ 的有 0 件、属 1,242 UNDECIDED 桶的有 732 件」
- `R14_COMMON.md:4437-4440`：「新 `tier_final` = 3,786 + 627 = 4,413 件」「字节 = 714,228,639 + 29,944,200 = 744,172,839 B」「两式互核：`4,518 − 732 + 627 = 4,413`；`724,479,859 − 10,251,220 + 29,944,200 = 744,172,839`」

盘上实测（`analysis.json`，键名逐项）：
- `R17_R88_T1_SEMDEF\tier_final.tsv`：4518 行、`tf_sum_bytes=724479859`；`why_content` 含 `P1a` 者 `p1a_rows=3786 / p1a_bytes=714228639`；其余 `manual_rows=732 / manual_bytes=10251220`。`p1a_plus_manual_rows=4518`、`p1a_plus_manual_bytes=724479859`。
- `R17_R78_T1_RECLASS\files_tier_Cprime.tsv`：18712 行。实测 `manual_in_Cprime_count=0`（**732 件属 C′ 的 = 0**）、`manual_not_in_Cprime_count=732`；`p1a_in_Cprime_count=3786`、`p1a_not_in_Cprime_count=0`。
- `R17_R92_T1_REJUDGE\rejudge1242.tsv`：1242 行；`new_verdict=对象抄本` 者 `rejudge_new_obj_count=627 / rejudge_new_obj_bytes=29944200`；`old_verdict=对象抄本` 者 732 件 / 10,251,220 B（与 tier_final 的 732 件为同一集合：`manual_minus_oldobj=0`、`oldobj_minus_manual=0`、`p1a_in_oldobj=0`）。
- 两式互核：`new_tf_count_formula=4413`、`new_tf_bytes_formula=744172839`；`new_tf_count_sub=4413`、`new_tf_bytes_sub=744172839`。四式一致。

一处需说明但不构成错误：`tier_final.tsv` 的 `oldC` 列在 732 件里 727 个 Y / 5 个 N；但 `oldC`=「旧 C」（`R17_R88_T1_SEMDEF\REPORT.md:231`：「KEEP∩旧C 4,338 / 573,217,609，KEEP∖旧C 180 / 151,262,250」），**不是 C′**，与「0 件在 C′ 内」不矛盾。

---

## Q2 · 「件数降而字节升」的归因对不对？

**判定：归因不成立（卡片自设检验不过；且两个点名大件根本未被重判为对象）。**

逐字引用（被审归因）：
- `R14_COMMON.md:4457`（§2.53 第四节）：「说明原因（**旧判据误判体量最大的几件**）」
- `FACT_INDEX.tsv:25`（v5.27 F24 statement）：「因为旧判据把**体量最大的几件**误判为过程」
- `R14_COMMON.md:4355-4356`（§2.52）：「旧判据的 `strong-proc-frame` 与「行首 VA 占比」把体量最大的几件（`mesh_imm32.json` 5.7 MB、`entry_to_vt.json` 764 KB）判成了过程或未决。」

盘上实测（`analysis.json` / `analysis2.json`，按 `rejudge1242.tsv` 的 `old_verdict=对象抄本 ∧ new_verdict=过程输出` 筛出 227 件）：

227 件「对象→过程」字节 Top5（合计 2,209,327 B）：
1. `next_re_20261112_r02/W48_menu_independent/EVIDENCE/01_parse_resources.stdout.txt` = **278,059 B**（rejudge1242.tsv:94）
2. `next_re_20261112_r02/W56_gate_writer_scan/EVIDENCE/w56_scan2_stdout.txt` = **208,688 B**（:122）
3. `next_re_20261112_r02/W47_baseline_adjudication/EVIDENCE/pe_probe.stdout.txt` = **181,564 B**（:91）
4. `next_re_20261116_r12/W163_dirtyrect/EVIDENCE/dual_bfs.stdout.txt` = **117,215 B**（:321）
5. `next_re_20261117_r14/S21_DIRECT/_audit/EVIDENCE/conflict18_mine.json` = **92,100 B**（:1175）

Top5 合计 = 877,626 B = **227 桶字节的 39.72%**（`top5_pct_of_o2p`）；但占「误判字节」21,609,436 B（`§2.52:4343`「旧判据误判 260 件 / 21,609,436 B」）仅 **4.06%**（`top5_pct_of_misjudged`）；占净增 19,692,980 B 的 4.46%。Top10 占 227 桶 55.71%。**前 5 件在误判字节里占比 4.06%——按卡片「若前几件占比不显著，我的归因就是错的」的判据，归因不成立。**

致命反证 —— 被点名的两个「体量最大的几件」根本没被重判为对象：
- `mesh_imm32.json`：`rejudge1242.tsv:1070` 逐字 `5693169 ... 过程输出 ... 过程输出 ... N ... tiny-status` → old=过程输出、new=过程输出、`changed=N`。
- `entry_to_vt.json`：`rejudge1242.tsv:896` 逐字 `764653 ... 过程输出 ... 过程输出 ... N ... tiny-status` → 同样 `changed=N`。

⇒ 这两件在新旧口径下**都是过程输出**，从未进入对象集合，**不可能是新对象字节的来源**。

真正的字节来源（实测，`analysis2.json`）：
- `a2_sites.json` = **17,624,355 B**（`rejudge1242.tsv:361`，old=过程输出→new=对象抄本，`changed=Y`、`old_basis=tiny-status`），单件占净增 19,692,980 B 的 **89.5%**，占新对象 29,944,200 B 的 **58.9%**。
- 其余大额：`AUDIT_SWEEP.json` 913,278 B（过程→对象）、`q3_cfg.json` 846,854 B（无法判定→对象）、`rtti_audit.json` 644,537 B（无法判定→对象）。
- 字节闭合实测：`p2o_bytes=19400109`（33 件过程→对象）＋`u2o_bytes=2502198`（89 件无法判定→对象）−`o2p_bytes=2209327`（227 件对象→过程）`= new_minus_old_obj_bytes=19692980`。

⇒ **准确归因不是「对象→过程里误判了大件」，而是「过程→对象方向里一件 17.6 MB 的 `a2_sites.json` 被翻成对象」**。方向都被写反了。

---

## Q3 · 3,786 与 627 之间有没有重复？

**判定：断言成立，但卡上写的是推理；本审计已实测。**

逐字引用（`R14_COMMON.md:4426`）：「**`tier_final` 从来不是 C′ 的子集** —— 它是「C′ ∩ P1a」加「C′ 外那桶里已判为对象的件」。」卡里的推理形式是「627 全在 C′ 外、P1a 全在 C′ 内 ⇒ 无交集」。

盘上实测（`analysis.json` 键 `Q3`）：
- `new_obj_in_Cprime_count=0`、`new_obj_not_in_Cprime_count=627`（627 全在 C′ 外 ✓）
- `p1a_in_Cprime_count=3786`、`p1a_not_in_Cprime_count=0`（P1a 全在 C′ 内 ✓）
- **`new_obj_3786_p1a_intersection=0`（交集实测 = 0 件，`intersection_rels=[]`）** ⇒ 断言成立。
- 附带：`new_obj_already_in_old_tf=505`（627 中 505 件本就在旧 tier_final）、`new_obj_vs_manual732_intersection=505`；另 `u2o_count=89`、`p2o_count=33`，故 122 件确为新增（`R14_COMMON.md:4434`「新出现的对象 122 件」成立）。

⇒ 推理的前提均实测为真，结论实测为真；把「推理」升级为「实测」即可。

---

## Q4 · 「三态」方案会不会变成「变相消告警」？

**判定：变相消告警。改完之后 C11 抓不到「无→有」造假。**

逐字引用（方案）：
- `_cards\R55-T2-TRISTATE.md:21`：「**有·无自产出机制**：确实回跑过，但产物形态（叙述/他人报告/手编一次性）不可能自产出凭证 ⇒ **不 FAIL，但必须在输出里显式计数**」
- `_cards\R55-T2-TRISTATE.md:37`：C11 改为「`有·无自产出机制` 者 → **不 FAIL**，但计入 `unverifiable` 并在输出显式打印」
- `_cards\R55-T2-TRISTATE.md:39`：「关键：**记录的语义变精确了，没有一条从「有」变成「无」**」
- `_cards\R55-T2-TRISTATE.md:43`：「不得把任何一行从「有」改成「无」——只允许「有」→「有·可核」或「有·无自产出机制」。」

现状 C11（`check_disc.py:222/238`）：「col7 以「有」开头者，其产物必须含一条通过 recheck_verify 的自描述行，否则 FAIL」「`if not later.startswith('有'): c11_unver += 1; continue`」。实测现状 `C11 col7 machine-check: ok=0 fail=17 unverifiable(claims none)=11`（`R14_COMMON.md:4260`）。

**构造（一次无→有造假，实测，`analysis3.json`）**：以纪律 11 为例，`DISC_RECHECK.tsv:12` 逐字第 7 列「无（仅立条当轮自带）」，产物 `lead\next_re_20261117_r14\_r38\checkC3_report.md` 实测 `DISC_RECHECK` 行数 = 0。
- 造假动作：只把第 7 列改为「有·无自产出机制」，其余六列与产物一律不动。
- 现行 C11：命中 `startswith('有')` → `verify_recheck_line` → `FAIL`（detail 逐字 `R1 line_count=0 (must be 1)`）⇒ **被抓到**。
- 拟改三态 C11（按 `R55-T2-TRISTATE.md:37` 分支）：落到「不 FAIL、计入 unverifiable」⇒ **抓不到**。`analysis3.json`：`forgery B: 无 -> 有·无自产出机制`，`caught_now=true, caught_after=false`。
- 对照：「无→有·可核」与「无→有（后续轮回跑）」两种造假在拟改 C11 下**仍能**被抓（`caught_after=true`），唯独新状态是免检安全港。

**12 条 FAIL→no-FAIL 实测**（`analysis3.json:flip_12_rows`）：纪律 1,2,5,6,7,8,9,10,18,20,24,25 共 12 条，当前全 FAIL，三态后全 UNVERIFIABLE（`flip_summary: n=12, currently_FAIL=12, after_noFAIL=12`）。门禁计数由 ok=0/fail=17/unver=11 变为 ok=0/fail=5/unver=23（`gate_counts`）。

⇒ 理由：①「没有一条从有变成无」只是**字面**成立（「有·无自产出机制」里仍有「有」字），**功能**上 12 条红灯被摘掉；②新状态的定义就是「结构上不可能自产出凭证」⇒ 它**按设计不可证伪**，C11 把它设为不 FAIL 等于给「无→有」造假开了一条免检通道，正是 `R14_COMMON.md:4285` 自己写过的「把 C11 关掉/降级成 NOTE ⇒ 回到『无→有造假仍 PASS』的原状」。**这是给红灯换了个更好听的名字并把 12 盏灯调到黄灯，不是真精确。**

---

## Q5 · F24 的「必须件数与字节同时给出」能不能机器检查？

**判定：可机检，但不能按卡里给的「出现件/B 形式必须成对」天真写法——那条会误报。**

逐字引用（`FACT_INDEX.tsv:25`，F24 statement）：「**引用本值必须件数与字节同时给出，单报件数会得出「语料变少」的相反结论**」。

实测（`analysis4.json`）：
- 天真检查式（同一句里每个「N 件/文件」都要配 N B）：在 F24 现文上 **FAIL**，误报 2 处——`3,786 件` 与 `732 件` 出现在口径句「…`why=P1a`…3,786 件 ∪ …732 件），形态证据（P1b 378）、兜底（P0 14,548）…」里，B 在别的句子。`n_violations=2`。
- 注册表式（canonical pair anywhere）：`new_4413_744172839=true`、`old_4518_724479859=true`，`verdict=PASS`。

**可执行的检查式**（对「F24 本值」而非任意语料值）：
```
CANON = { (4,413, 744,172,839), (4,518, 724,479,859),
          (24,723, 1,589,964,358), (24,478, 1,558,495,337) }   # F24 里被当作「语料值/规模值」的规范对
for (c,b) in CANON:
    cs, bs = f"{c:,}", f"{b:,}"              # F24 用千分位
    if regex(rf'{cs}\s*(?:件|文件)') in stmt and bs not in stmt:
        FAIL(f'F24: 报了件数 {cs} 却未同报字节 {bs} B')
    if bs in stmt and cs not in stmt:
        FAIL(f'F24: 报了字节 {bs} B 却未同报件数 {cs}')
# 方向句专项：件数 4,518→4,413 与字节 724,479,859→744,172,839 必须同现
if '4,518' in stmt and '4,413' in stmt:
    assert '724,479,859' in stmt and '744,172,839' in stmt
```
该式对现文 F24 全部 PASS，且能抓住「只写 4,413 件不写 744,172,839 B」的违规。

**为什么不能按卡片原话做通用式**：F24 statement 是 3,659 字的复合文本，同一句里合法地混着组件数（3,786/732/378/14,548/266/1,242）与规模数（24,723/24,478），组件数按文体本就不必逐件带 B；「件/B 必须成对」会强制给每个组件数配 B，既误报又会把 statement 撑成不可读。⇒ **可机检，但必须缩小到规范值对（canonical registry），且只能约束「引用本值」这个动作，不能约束 statement 里所有数字。**

---

## Q6 · 最诚实的一句话

**§2.53 应改为**：保留传导链算术（4,518→4,413 件、724,479,859→744,172,839 B、两式互核 4413/744172839 成立、627∩P1a=0 实测成立），但把归因句「旧判据误判体量最大的几件」改成——「**件数降而字节升，主因是过程→对象方向单件 `a2_sites.json` 17,624,355 B（占净增 19,692,980 B 的 89.5%）；对象→过程 227 件的 Top5 仅占误判字节 4.06%，§2.52 点名的 `mesh_imm32.json`/`entry_to_vt.json` 实测 `changed=N`、仍为过程输出，不是成因**」。

**三态方案应改为**：保留「有·可核」与「无」两态及判别式，但**取消「有·无自产出机制」的免检**——或让该态仍以 `startswith('有')` 走 `recheck_verify`（则 12 条继续 FAIL，只是改名不消告警），或若坚持黄灯态，必须加一条不可伪造的独立凭证闸（外部可信时钟/独立落盘证据），且**禁止用它吸收「无→有」变更**（在 C11 里对「立条为无、现报有·无自产出机制」的行单独 FAIL），否则它就是 `§2.51:4285` 已否决的「降级成 NOTE」。

---

## OVERALL

**§2.53 的算术与集合关系成立、但「大件误判」归因错误且方向写反、需修正；三态方案是变相消告警（12 条 FAIL 转 no-FAIL、阻断 C11 抓无→有造假），应推翻。**

---

## 七行交付（照卡第四节格式）

```
Q1 | 算术/集合 对 | 732件属C′的=0 ; 两式互核=4518−732+627=4413 且 724,479,859−10,251,220+29,944,200=744,172,839（另 3786+627=4413、714,228,639+29,944,200=744,172,839，四式一致）; 不符处=无（oldC 列 727Y/5N 指旧C非C′，REPORT.md:231）
Q2 | 归因不成立 | 227件里字节 Top5: ①01_parse_resources.stdout.txt=278,059B ②w56_scan2_stdout.txt=208,688B ③pe_probe.stdout.txt=181,564B ④dual_bfs.stdout.txt=117,215B ⑤conflict18_mine.json=92,100B ; Top5 占误判字节(21,609,436B)=4.06%（占227桶=39.72%）; 且点名大件 mesh_imm32.json(5,693,169B)/entry_to_vt.json(764,653B) 实测 changed=N、仍过程输出；真因是过程→对象 a2_sites.json=17,624,355B(占净增89.5%)
Q3 | 实测 | 交集实测=0 件（627∩P1a=0；627全在C′外=0命中C′、P1a全在C′内=3786）; 断言成立（原为推理，已实测确认）
Q4 | 变相消告警 | 理由=「没有一条从有变成无」只是字面：12条(1,2,5,6,7,8,9,10,18,20,24,25)由FAIL转no-FAIL、门禁17FAIL→5FAIL；新态按定义不可证伪且被设为不FAIL(R55-T2-TRISTATE.md:21/37) ; 改后「无→有造假」还能被抓到吗: 不能(构造: 纪律11 第7列"无（仅立条当轮自带）"→"有·无自产出机制"，产物checkC3_report.md含0条DISC_RECHECK行；现行C11=FAIL/R1 line_count=0，拟改C11=UNVERIFIABLE不FAIL；分析键 forgery B caught_now=true caught_after=false)
Q5 | 可机检 | 检查式=CANON={(4413,744172839),(4518,724479859),(24723,1589964358),(24478,1558495337)}; 对每个(c,b): 若 statement 含千分位 c 的「N 件/文件」却不含 b 的千分位→FAIL(未双报)，反之含 b 却不含 c→FAIL；件数518→413同现则字节必须同现724,479,859与744,172,839。天真式「每个件/B必须同句成对」会在F24误报2处(3,786件/732件)，故只能按规范值对约束「引用本值」
Q6 | §2.53 应改为=保留4413/744172839与两式互核、627∩P1a=0实测；把归因改为「主因是过程→对象 a2_sites.json 17,624,355B 占净增89.5%；227件对象→过程Top5仅占误判字节4.06%，mesh_imm32/entry_to_vt changed=N 非成因」 ; 三态方案应改为=保留有·可核与无、取消「有·无自产出机制」免检（仍走recheck_verify继续FAIL）或加不可伪造独立凭证闸并对「立条无→现报有·无自产出机制」单独FAIL，否则即§2.51:4285已否决的降级NOTE
OVERALL | §2.53 算术与集合成立但大件归因错误且方向写反、需修正；三态方案是变相消告警（12条FAIL转no-FAIL、C11失去抓无→有造假能力），应推翻
```
