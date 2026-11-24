# T4_review · 对 `T4_IMPACT.md` 的独立复核（T4 复核员，2026-11-06）

> 复核对象：`W11_EXCEPT_FRESHNESS/T4_IMPACT.md`（29,837 B，mtime 2026-11-06 03:59）及其探针
> `_w11_t4.py` / `_w11_t4_out.txt`。本复核零写入（除本文件）；全部结论来自本会话实跑命令与实读文件。
> 总判：**CONFIRMED**——指纹、扫描、引文链、降级论证、新发现登记链全部独立复算成立；
> 另有 6 条 objection（其中 3 条为可核的事实/引文小错，均不动摇任何判定档），无 mustFix 级问题。

---

## 0 · 四项强制检查

### 0.1 回件是否真含自算 qc151_trip.py 指纹 —— **过**
- `T4_IMPACT.md:5` 头部含 `SHA256 = 517889c6…ba636，字节数 = 399508，行数 = 7291`，`:6` 声明自算命令与两轮一致。
- 本复核独立重跑（2026-11-06 04:4x）：
  `sha256sum out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`
  → `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`；
  `wc -c` → `399508`；`wc -l` → `7291`。**与回件逐位一致。**
- 探针 `_w11_t4_out.txt:3` 亦独立重算同一指纹（`sha256=517889c6… bytes=399508 lines=7291`），三方一致。
- 附加：`gamemd.exe` 头部指纹 `73201cc0…67476` 亦本复核重算成立（`./ra2bench/gamemd.exe`，4,825,360 B），
  且与 2026-10-17 独立文书 `ERRATA_EXCEPT_RESTORE.md:30`（sha 前 16 位 `73201cc021497c95`）互证。

### 0.2 ★ modifiedForbiddenFile —— **未违（false）**
证据（全部本复核实跑）：
1. `qc151_trip.py` mtime = `2026-10-20 00:08:02 +0800`（`stat`）——早于任务窗口 17 天；SHA 与回件一致 ⇒ 未被改。
2. `out/` 整树不入 git（`.gitignore:33` 为 `out/`，`git check-ignore -v` 实证），故以 mtime 敏感期全扫代替：
   `find out/re_work -type f -newermt "2026-11-05 20:00"` → **恰 2 件**，均为 Mimosa 钩子的会话簿记
   （`…/qc151_u0400_trip/.mimosa/hook-state|hook-status/sess_dwf-…-actor_2_1…json`，03:19/03:23）。
   该 `.mimosa/hook-state` 树在 out 树内有 2026-09-25 以来的长期历史，属插件基础设施写入，
   非回件内容写入；out 树内**没有任何证据件（except.txt / except_post_* / 趟 json / 文书）被触碰**。
3. 探针 `_w11_t4.py`（161 行）源码逐行读：全部 `open(path,"rb")` 只读；唯一写目标是
   `_w11_t4_out.txt`（`:21` 字面量绝对路径，在写域内）。**探针不可能写 out/re_work。**
4. `git status`：tracked 侧台账三件（GOAL/PENDING/ROUND_LOG）确有改动，但其 mtime = `2026-11-06 04:23`，
   晚于 T4 交付（03:59），属领队 04:2x 重大订正轮（`GOAL_RE_CONTINUOUS.md:247` 自记），非 T4 所为；
   T4 自报写域内 3 件 + `.tmp` 1 件（见 objection 4）与文件系统实况吻合。

### 0.3 T3 测试是否真跑过、四分支是否覆盖 —— **过（且本复核重跑复现）**
- `_w11_t3_test_out.txt`：`Ran 14 tests` / `OK` / `PASS=14 FAIL=0` / `EXIT=0`。
- 四分支逐一在列：分支1 源件缺失（test_01）、分支2 原样遗留（test_02）、分支3 内容变化（test_03）、
  分支4 复制失败 write（test_04）＋ read 变体（test_04b）；另有 T2 盲区（同内容重写 test_06）、
  时钟回拨（test_09）、纯函数性（test_11）等加测。
- 本复核亲自重跑：`python -I -X utf8 candidate/test_except_freshness.py` → `Ran 14 tests … OK / PASS=14 FAIL=0 / EXIT=0`。
  沙箱 = `tempfile.mkdtemp(dir=W11_EXCEPT_FRESHNESS)`（test:30-32），tearDown `rmtree`——不触 out/re_work。

### 0.4 T1 三分类是否每条有「文件:行号」支撑 —— **过**
`T1_SEMANTICS.md:24-32` 三分类表 8 行，每行附行号链（:228/:623-669/:4946-4958/:677、:6394-6408、
:5939/:6042-6052、新鲜性 0 处/:4420、:4591-4598、writer-only、:4561）。本复核对其中 qc151 源码行
逐条抽验：`:4561 def copy_post_except_evidence`、`:4574-4578 src/exists()/rec.add/return None`、
`:4591-4596 carrier_post_state` 五件 size/sha256、`:5938-5939 _except_evidence_copy 内唯一调用`、
`:5953 restore_carrier`、`:6042-6052 run_guarded_steps 序列`、`:6394-6406 passive_read/SKIPPED_U5`、
`:672 except_set_diff` —— **全部与源码实况一致**。T4 §2 对 T1 的引用（「与 W11-T1 一致」）成立。

---

## 1 · 扫描与「311/41」的独立复算与对账

本复核独立实跑（2026-11-06 04:4x）：

| 命令 | 结果 |
|---|---|
| `grep -rl -a -e except_post -e new_exception_count -e no_new_exception lead/ --include="*.md" \| wc -l` | **48**（回件 §0 行1 称 33） |
| 同上 md+txt | **102 文件 / 2312 行**（回件：43 文件字面量清单 / 311 PRIMARY / 345 SECONDARY） |
| 单关键词（md+txt 行数） | except_post 2067 / new_exception_count 245 / no_new_exception 76 |
| `grep … docs/` | **0**（§0 行2「docs/ 零命中」成立） |
| `_w11_t4_out.txt:4-5` | `PRIMARY hits: 311 by keyword {'except_post': 260, 'new_exception_count': 45, 'no_new_exception': 6}`、`per-file 41 files`，GOAL=34/PENDING=5/ROUND_LOG=7 与 §2 各节条数自洽 |

**对账结论**：2312 与 311 的差额已逐文件归因（见下），**不构成对任何判定档的反驳**，但「全仓 311 处」
的措辞比实况强（见 objection 1）：
- **W11 自家/同级输出（11 件）**：T3_CANDIDATE/T4_IMPACT/PATCH_SUGGESTION/reviews 等，多在探针运行（03:49）后才落盘；
- **.txt 工具输出（约 50 件，超出 TASK §4 规定的 md 范围）**：普查/清单/评审 stdout，如
  `S544…/_list_except_out.txt`(107)、`_rc/_all_except_repo.txt`(113)、`c1606…/except_files.txt`(112)、
  `EXIT_CENSUS/_verify_probe_out.txt`(74)、`D22_RULING/_d22_facts_out.txt`(117)、`goal2_rc4…/_except_list.txt`(88)、
  bench 语料 txt——均为「文件名清单/普查输出」，非判断文书；
- **W9 reviews Q1/Q3/Q4_review.md（11/15/25 命中，03:49 时已在盘而未入 43 件清单）**——真实的覆盖缺口，
  本复核逐行读其命中行：内容全部为「113 份普查记录 / 结论须限定口径，不得外推」的根因同向表述
  （如 Q4_review:231「手上这一件 EXCEPT + 113 份 except_post 上被坐实，不能外推成」），**无需新增降级**；
- **03:49 后台账追加**：`GOAL_THREE_TARGETS:9286` 等为新落账（领队 04:2x 订正轮），非 T4 漏扫。
- **正面使用穷查**：`grep except_post | grep -E "崩溃|死因|确证|死于|crash"` 全 md+txt 过滤后，
  S543-V2 三件之外**无任何一处**把 except_post 当某趟崩溃的正面证据（其余命中均为「无信息量/要重估/REFUTED/
  防线」表述）——§6「唯一正面崩溃证据使用只有 S543-V2 一处」在本复核独立扫描下**成立**。

---

## 2 · 引文抽查（约 40 处，全部本复核实读）

**逐位成立**（抽样列示）：
- qc151 源码：`:4561/:4574-4581/:4591-4596/:5938-5939/:5953/:6042-6052/:6394-6406/:672`（见 §0.4）。
- GOAL（UTF-8 实读）：`:378`（except_post sha256 完全相同+6694b75e）、`:5466`（§555 标题 37 archive）、
  `:5473`、`:5475-5478`（107 份同哈希/非任何一趟崩溃证据）、`:5519-5525`（harness 5/环境 2/人为 1/无法判定 29/游戏崩溃 0）、
  `:5531`（`new_exception_count=0`）、`:5539`（19 有/18 无）、`:5565`、`:5570-5571`（未独立验证自陈）、`:5578`、
  `:8541-8543`（无信息量/全部要重估）、`:8573/:8577-8578`（亲验边界+留给 W9）、`:8749`（全仓 113 份逐字节）、
  `:8804`（选项 A）、`:8875`（§555 停止作为已验证结论引用）、`:8876/:8885/:8888`（D-22 动作表/F2）、
  `:8902-8928`（§595 根因+代码块与 :4574-4581 逐行对应）、`:8961`（dist {0:59}）、`:8969-8970/:8976-8982/:8988-8990/:8997`。
- S543-V2 三件：`VERDICT.md:165`（except_post…0x007CFC9F…EXCEPTION_SINGLE_STEP）、
  `V2/REPORT.md:157-168`、`V2/RECHECK.md:104-111`——「死因确证」正面使用属实，降级有据。
- T42E4 下游纠正：`01_timeline.md:64/:81/:137/:156`、`02_verify.md:21-22/:62-63/:176`、`04_boundary.md:45/:92`、
  `RULING_D16_7a15fa33/AUDIT.md:498`（「异常残件误作崩溃：未重算 107 份；不以 e4 except_post 推退出方式」）。
- 门禁设计：`BASELINE_MEASURE_DESIGN.md:304`（V7 行）/`:407`（C9 行）确以 `new_exception_count==0` 为门，
  「需重估（设计）」恰当；`E2_GATE_VERDICT.md:42`（V4 FAIL 在案）/:45（V7 PASS）属实。
- S544 三路：`7255362d` RECHECK:229-236/239-242/280、REPORT:78-89/218；`ae38d56c` RECHECK:20/87-97、
  REPORT:25-27/101-108、VERDICT:25/46；`c1606d35` RECHECK:221-231/248/253、REPORT:111-118/208-210/282、
  VERDICT:36/55/93/112 —— 全部命中且与 §2.10-2.12 的「维持/维持+边注」描述一致。
- 其他：`XVERIFY_TRIPS:285`、`S544_TRI:87-88`、`ROUND_LOG:112/148/3297/4971/4975/4977/5767`、
  `EXIT_CENSUS 01:13/15/111/113`、`02:91`、`L1_NO_HARNESS_REPRO:29`、`CORPUS:187/189/246`、
  `ERRATA_CARRIER_REBUILD.md:9/:22`。
- **PENDING_DECISIONS `:28-31/:60-61/:65/:73-74`**：该文件 04:23 被重构（git diff 261 insertions，mtime 04:23:40），
  现行文本已对不上；本复核改用**探针 03:49 快照**（`_w11_t4_out.txt` PENDING 节）核——
  `:28-31` =「该 EXCEPT 件 = 全仓 113 份 except_post_*.txt 同一份（6694b75e，113/113）」、
  `:60-61` =「毫无信息量/全部要重估」、`:65` =「(A) 先修观测」、`:73-74` =「(C)…except_post 写入逻辑可能污染新证据」——
  **与回件描述逐字吻合**（引用在当时为真，现因台账重构而漂移，非 T4 之过）。

**新发现（§5-1）核实成立**：`out/re_work/.../qc164_a4_prep_20261017/ERRATA_EXCEPT_RESTORE.md` 实录
qc124 期载体漂移 `ca175a71→6694b75e`（26,405 B / 1046 行，mtime **2026-10-16T19:21:11+08:00**），
定性「qc124 观测趟运行期写出（游戏整体重写 except.txt）」，漂移留痕 `raw/except.drift.6694B75E.26405B.bin`；
登记链 `VERDICT_T11.md:149`（GBK）确含 `except.txt mtime = 2026-10-16 19:21:11` + 「母本 0 写入 | CONFIRMED」。
→ 对 W9-Q4 未验项「游戏是否会写载体 except.txt」的「仓内登记链至少一次（内容变化型）」回答**成立**。

**Mimosa 拦截**：`.mimosa/finding-ledger/v1/events/batch-pretooluse-….json` 实有 `finding_blocked` 记录
（type=finding_blocked，at=2026-11-05T19:26:43Z＝本地 03:26:43，对本会话探针件）——拦截为真；
但「6 次、行号 107/125/124/123/122/123」无法从现存批次台账逐次枚举（批次件只留聚合记录）。
该披露不承载判定，不影响结论。

---

## 3 · Objections（按重要性）

1. **覆盖面账目不齐（最重要）**：§0 行1「33 个文件」从未与探针「41 文件」对账；「全仓 311 处逐一过堂」
   实为「43 件字面量清单上的 311 处」。03:49 已在盘的 `W9_SINGLESTEP_7CFC9F/reviews/Q1_review.md`(11)/
   `Q3_review.md`(15)/`Q4_review.md`(25) 未入清单。本复核已代为过堂：三件命中行全部为普查记录/口径限定
   表述，与 §2 既有判定档相容，**无新增降级**——但 headline 的「全仓」应限定为「lead/ 判断文书（43 件）∪
   docs/（零）」，.txt 工具输出层（约 2000 行命中）未过且 TASK 本就只令扫 md。
2. **ERRATA 计数错误（可核事实错）**：§0 行3 与 §5.4 称「out/re_work 树 19 件（2+16）」；
   本复核 `find out -name "ERRATA_*"` = **15 件**（2 件相关 + 13 件其他，无第 16-19 件）。
   不影响任何判定（§5.4 本就判其余「不涉及」），但数字应更正。
3. **两处引文不精确（可核错）**：(a) §3-3「16 个目录连 qc151_run_log.json 都缺（`:5592`…）」——
   GOAL `:5592` 实为 action_dispatch_table.tsv 行；该事实的正确行号是 **`:5492`/`:5555`**
   （EXIT_CENSUS `01:111` 引用正确，事实本身为真）。(b) §5-1 对 `VERDICT_T11.md:149` 的转述
   「全树最新 mtime = 2026-10-16 19:21:11（except.txt）」——原行为「最新 mtime = 2026-10-16 **19:16:13**…
   （except.txt mtime = 2026-10-16 19:21:11）」；19:21:11 与 CONFIRMED 属实，「全树最新」张冠李戴
   （T4 已自披露该件只做 GBK grep 直读）。
4. **写域技术性越域（已自报）**：`.tmp/w11_t4_filelist.txt`（97,395 B，03:45，find 中间清单）建在
   声明唯一写域（W11_EXCEPT_FRESHNESS/）之外。已披露于 §7.4、属新建草稿非禁改件、未入 git——
   按「违反即作废」字面属技术性违例，按实质（零污染既有件、零真机、零 out 写入）不作废。
5. **台账漂移**：PENDING/GOAL 于 04:23 被领队订正轮重构（+261 行；新 `:9286` 亦为订正轮所加），
   T4 若干行号（PENDING 全节、GOAL :5592 一带）现已对不上现行文件——非 T4 之过，
   但后续引用 T4 行号须按 `_w11_t4_out.txt` 03:49 快照对读。
6. **Mimosa「6 次」不可独立枚举**（见 §2 末）——披露真实（finding_blocked 在账），逐次数与行号不可复算。

## 4 · mustFix

无阻断项。建议在 W11 汇总件的「必须改项」里带一笔 §3.1-§3.3 的三处补正
（33↔41 对账+补 W9 三件 review 过堂记录、ERRATA 19→15、`:5592`→`:5492/:5555` 与 VERDICT_T11 转述订正），
均可在不改判定档的前提下落一行勘误。

## 5 · 结论

| 项 | 结果 |
|---|---|
| verdict | **CONFIRMED** |
| sha256BindingPresent | **true**（`T4_IMPACT.md:5` + `_w11_t4_out.txt:3`，本复核两轮重算逐位一致） |
| independentlyReproduced | **true**（指纹×2、关键词全扫×3 树、T3 套件重跑 PASS=14 FAIL=0 EXIT=0、约 40 处引文实读、ERRATA/VERDICT_T11 登记链、正面使用穷查） |
| modifiedForbiddenFile | **false**（qc151 mtime 2026-10-20；out/re_work 敏感期仅 2 件插件簿记；探针只读实证） |
| objections | 上列 6 条 |
| mustFix | 无阻断项（§3.1-3.3 建议补正） |

关键证据索引：本文件 §0-§2 所列全部命令与输出；探针快照 `_w11_t4_out.txt:3-5`；
`ERRATA_EXCEPT_RESTORE.md:12/:16`；`VERDICT_T11.md:149`（GBK）；`GOAL_THREE_TARGETS:5492/:5555/:8875`；
`git diff --stat HEAD -- lead/PENDING_DECISIONS.md`（261 insertions，mtime 04:23:40）。
