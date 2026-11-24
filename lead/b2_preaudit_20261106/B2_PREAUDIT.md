# B2 设计预审判定书（N-2 · 设计预审硬门）

**判定对象（被审设计）**：`lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md`
- 实算 SHA256：`deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f`
- 实算字节数：`11638 B`（`wc -l` = 236 行）
- 实跑命令：`sha256sum lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` 与 `wc -c <同上两件>`

**对照母本**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`
- 实算 SHA256：`517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`
- 实算字节数：`399508 B`（`wc -l` = 7291 行）
- 与 `lead/b2_preaudit_20261106/TASK.md:34-35` 基准一致，未触发 STOP，未写 `STOP_MOTHER_DRIFT.md`。母本一个字节未改（铁律 3）。

**两路输入**：一路「六条旧错是否真修好」（只读母本核对 + 探针实跑），一路「B2 自引新风险」（只读静态审 + 离线合成复现）。两路的 `verdicts` 与 `notChecked` 由本判定书合并裁定；「复核未通过 / 无法核实的条目」为空数组，故无条目需降级为 `UNVERIFIABLE`。

**本判定书的门**：只回答「这份设计能不能拿去制作完整候选」。**不回答、也不等于「可以应用到母本」**——那是另一道门（B2_FIX_DESIGN.md:198「应用前必须重新走一遍 B1 的预审硬门」）。

verdict: NO

**为什么是 NO（判定规则逐条对照）**：
- 六条旧错中 `E1 = NOT_FIXED`（旧规则第一条即触发 NO）。
- 新增问题中 `severity=high` 共 5 条（N1/N2/N4/N5/N11；实跑 `grep -cE '^- \*\*N[0-9]+ .*severity=high' lead/b2_preaudit_20261106/B2_PREAUDIT.md` → `5`）（旧规则第二条亦触发 NO）。
- 两条规则各自独立足以判 NO。

---

## 一、六条旧错误的判定

#### E1 作用域断裂（`main` 局部变量在 `finalize_trip` 里引用）

- **判定：NOT_FIXED**
- **证据（文件:行）**：B2 只给了 `finalize_trip` 加形参（`B2_FIX_DESIGN.md:43-48`）与 `main` 调用点传参（`B2_FIX_DESIGN.md:52-64`，`:63` = `pre_freshness_snapshot=_pre_freshness_snapshot`）。但 `_pre_freshness_snapshot` 在 B2 全文只有 3 次出现（`:35` 叙述、`:63` 使用、`:200` 自问），**任何赋值定义形式的行 = []**（`_b2_probe_out.txt:95-99`）；B2 §2 `:190` 声称「`:6388` 后构造快照 +2 行」却无对应 diff hunk（B2 全文只有 4 个 hunk：`:43/:52/:75/:128`，`_b2_probe_out.txt:100-105`）。母本唯一调用点 `:5939` 现状仍是 `copy_post_except_evidence(rec, carrier_dir, out_dir)`（`qc151_trip.py:5939`；`_b2_probe_out.txt:15-16`），B2 全文无一处 `:5939` 传参代码块（实跑 `grep -n "pre_snapshot\|_except_evidence_copy\|5939\|6388" B2_FIX_DESIGN.md` 只命中 `:36/:114/:116/:130/:133/:184/:188/:190/:200` 的叙述或形参，无调用点 diff）。母本 `main` 有 5 个早退 `return`（`:6340/:6349/:6361/:6374/:6377`，`_b2_probe_out.txt:54`）全部早于 `bak = backup_carrier(...)` 的 `:6387`（`qc151_trip.py:6387`），却都要经 `finally`（`:7038`）→ `finalize_trip`（`:7117`）。B2 `:66`「默认值 None 向后兼容」只在调用方不传实参时成立，`:63` 明确传了实参。
- **一句话后果**：按 `:63` 直接引用未绑定名字，早退/异常路径必抛 `UnboundLocalError`，B1 的 `NameError`（`PRE_AUDIT.md:117-129`）只是从 `finalize_trip` 挪到了 `main`，正式 harness 收尾链被打断、原异常被替换。

#### E2 `exists` 键缺失 ⇒ 100% 误判

- **判定：PARTIAL**
- **证据（文件:行）**：键名层面已修——写入侧 `B2_FIX_DESIGN.md:82` 显式 `"exists": True`，`:88-90` 正确说明母本 `:4453-4456` 的 `continue` 分支不写 `bak[name]`（`qc151_trip.py:4453-4456` 实读确认）；判定侧 `:134`/`:141` 读同名 `exists`。探针把 B2 `:133-154` 算法逐字转写后合成 `{exists:True,sha256:X,mtime_pre:T}` + 未变 → `leftover_unchanged/high`（`_b2_probe_out.txt:130` MATCH），不再是 `PRE_AUDIT.md:131-142` 的 100% `new_first_appearance`。但端到端 100% 误判未消除：快照因 E1 未接线而恒为 `None`，B2 `:133` `_pre=dict(pre_snapshot or {})` 折叠成空字典 → 遗留件恒判 `new_first_appearance/high`（`_b2_probe_out.txt:136` MATCH 实跑；本人独立合成复现 `python -I -X utf8 -c "<转写 B2 :133-154 判定式>"` 输出 `pre=None (未采集), 跑后有历史件 -> ('new_first_appearance','high')`）。且 B2 `:223-224` 声称「无键⇒快照=`{exists:False}`」与 `:130/:133` 的 `None⇒{}` 语义未统一，全文无任何代码构造该快照。
- **一句话后果**：键名对齐只是局部修好，实际链路上历史遗留 `except.txt` 仍会被高置信误标为「本趟新出现」（B1 #2 危害换条路径复现）。

#### E3 `mtime_pre` vs `mtime` 键名不匹配

- **判定：PARTIAL**
- **证据（文件:行）**：键名不匹配已消——B2 `:83` 写 `mtime_pre`、`:100` 与 `:147` 均改读 `_pre.get("mtime_pre")`（不再是 `:99` 的 `mtime`），探针「同 sha + mtime 变」→ `rewritten_same_content/medium`（`_b2_probe_out.txt:131` MATCH），A 旁证分支在算法层可达。但该结果在正常路径根本不落盘（见 N4）。新增键 `captured_at_iso` 被静默丢弃：`TASK.md:47` 要求 `mtime_pre / captured_at_epoch / captured_at_iso` 三键、W11 candidate `:80` 有、B2 `:81-84` 只写 `exists/mtime_pre/captured_at_epoch`（实跑 `grep -n "captured_at_iso" B2_FIX_DESIGN.md` → 零命中、exit=1；`_b2_probe_out.txt:85/:185` 计数 0）。另 W11 candidate 用键名 `mtime`（`candidate/except_freshness.py:78/:90`），B2 统一为 `mtime_pre` 属内部自洽但与候选不同构。
- **一句话后果**：死代码在算法层复活了，但交付契约缩水且结论不输出，等于只修了半个键名问题。

#### E4 规约死锁（不许改 `finalize_trip` 签名，但合法接线必须改）

- **判定：PARTIAL**
- **证据（文件:行）**：设计层面承认并放开了签名——B2 `:103-118` 明写「我的 TASK 错误」、改动面三处→四处；母本 `finalize_trip` 确实只有 `:7117` 一个调用点（实跑 `grep -n "finalize_trip(" qc151_trip.py` 只命中 `:5900` def / `:7117` 调用 / `:7149` 文档字符串；`_b2_probe_out.txt:17`），B2 `:52-64` 改了它。但「同步改旧 TASK 的三处限制」未发生也按铁律 4 不可能发生——实跑 `grep -n "三处\|git diff\|不许扩大" lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md` 仍命中 `:42`「不许扩大」、`:94`/`:115`「只改了三处/三处改动全部落地」、`:83`/`:94`/`:134`「git diff」；B2 `:234` 自述「本文件不改任何文件」。且「四处是最小集」不成立（见 N7：§2 `:183-190` 列 8 处物理改动而只有 4 个 hunk）。
- **一句话后果**：死锁在 B2 文本里被宣布解除，旧 TASK 治理文件仍与 B2 矛盾，下一任执行代理仍会撞上 B1 #4 的同一个规约冲突。

#### E5 早退截断（判定内联在 `return None` 之后）

- **判定：PARTIAL**
- **证据（文件:行）**：早退那一半修好——B2 `:132-154` 把判定提到 `:155 if not _now_exists` 与 `:162 return None` 之前，`:156-161` 早退分支确实 `rec.add` 了 `evidence_freshness`，探针「`absent_both/n/a`」与「`vanished/high`」均 MATCH（`_b2_probe_out.txt:133-134`）。但出现反向截断：正常路径（`src` 存在，正是 W11 陈旧 `except.txt` 的场景）在 `:139-154` 算完四个分支 `_fresh` 后，`:163` 起至 hunk 结束 `:165` 没有任何 `rec.add` 或 `info` 写入；§2 `:186` 声称的「info +4 键」无 diff（实跑 `grep -n "freshness_verdict\|freshness_confidence\|freshness_note\|mtime_post\|captured_at_iso" B2_FIX_DESIGN.md` 输出：`freshness_verdict` 仅 `:205` 一句断言，`freshness_confidence`/`freshness_note` 零命中；`_b2_probe_out.txt:186-191`）。母本 `:4583-4587` 的 `info` 仍是 5 键且原样写进 `EXCEPT.evidence_copy`（实读确认）。
- **一句话后果**：早退路径有 F 结论，正常路径（要修的核心场景）算完就丢，补丁主路径空转。

#### E6 `git diff` 要求与 `.gitignore:33` 矛盾

- **判定：PARTIAL**
- **证据（文件:行）**：B2 自身文本里确已删净 `git diff` 要求并换成文件级 `diff -u` + SHA256（`B2_FIX_DESIGN.md:171-175`；实跑 `grep -n "git diff" B2_FIX_DESIGN.md` 输出 `:24/:171/:173/:175`，均为描述或删除该错误；`_b2_probe_out.txt:87`），`.gitignore:33 = out/` 亦实跑核实（`grep -n "out/" .gitignore` → `33:out/`；`_b2_probe_out.txt:6`）。但 `:175`「TASK 里彻底删掉 `git diff` 字样」这条指令未执行且受铁律 4 只读约束无法执行，旧 `TASK.md:83/:94/:134` 三条 `git diff` 要求仍在（同上 grep 输出）；B2 `:196-198` 只要求「重新走预审硬门」，未给出替换版任务书。
- **一句话后果**：B2 自己不再自相矛盾，但作为后续实现者治理依据的旧 TASK 矛盾未消除。

---

## 新增问题

> 合并两路 `NEW_ISSUE`。同 id 在两路中指向同一根因的已合并，两路互补的论据并入同一条；两路 id 编号不同的按「根因」归并并保留双路证据。每条均给 `severity` + `文件:行` + 一句话后果。`severity=high` 共 5 条（N1/N2/N4/N5/N11），任一条即足以判 NO。

- **N1 · severity=high · 异常/早退路径 `_pre_freshness_snapshot` 从未绑定**
  证据：`B2_FIX_DESIGN.md:63`（裸名传参）、`:66`（默认值只对其他调用方）、`:190`（声称 `:6388` 后构造但无 hunk）；母本 `qc151_trip.py:6293-6296` 只为 `bak/t0/pre_except_txt` 做 try 前预初始化（注释「★ 未取到即 None/空」），`:6340/:6349/:6361/:6374/:6377` 五个早退全早于 `:6387`，`:7030-7037 except BaseException → raise`，`:7038 finally` 无条件进、`:7043-7047` 明写 finally 内异常会取代返回值向外传播（`_b2_probe_out.txt:54,99,146-151`）。本人独立实跑 `python -I -X utf8 -c "<合成 main/finally，形参名按 B2 :48 对齐>"` 输出：`PATH early_return -> RAISED UnboundLocalError: cannot access local variable '_pre_freshness_snapshot' ...`、`PATH caught_exception -> RAISED UnboundLocalError: ...`、`PATH normal -> NORMAL`。
  后果：B1 的 `NameError` 从 `finalize_trip` 挪到 `main`，早退/异常路径收尾链被打崩、原异常被替换；默认值 `None` 对此无保护。

- **N2 · severity=high · 空/None 快照把历史遗留件恒判 `new_first_appearance/high`**
  证据：`B2_FIX_DESIGN.md:48/:130/:133/:134/:141-142`；母本 `qc151_trip.py:436-441` Recorder 口径「未读到写未测；不可测写 null；本类不提供写 False 表示未知的口子」、`:5949-5952` 明把 `bak={}` 当「未备份⇒未测⇒null」、`:5961-5963`/`:5974-5976` 同惯例。本人独立实跑 `python -I -X utf8 -c "<转写 B2 :133-154 判定式>"` 输出 `pre=None (未采集), 跑后有历史件 -> ('new_first_appearance','high')` 与 `pre={} , 跑后有历史件 -> ('new_first_appearance','high')`；`_b2_probe_out.txt:136-138,152-156`。实跑 `grep -n "未测\|error\|未采集\|null\|is_new" B2_FIX_DESIGN.md` 仅输出 `:89` 一句关于 `backup_carrier` 的说明，无任何未测/错误判定分支（`PRE_AUDIT.md:79-84,180-181` 已判同类情形 `conflictsWith677=true`）。
  后果：即使实施者自行补 `=None` 预初始化堵住 N1，B1 #2 的 100% 误判在异常路径原样复活，且没有「未测」/error 出口。

- **N3 · severity=medium · `{}` 与 `{"exists": False}` 被折叠成同一状态**
  证据：`B2_FIX_DESIGN.md:133/:202-204/:222-226`（§3 把 `{}` 写成合法合成测试输入，只区分「bak 无键」vs「有键」两态，没有「未采集」第三态）；对照 `candidate/except_freshness.py:47/:155-157/:204-207` 有显式 `error_pre_snapshot` 与 `is_new=None` 出口，B2 把它删了。本人独立实跑输出：`now_exists=True {} -> ('new_first_appearance','high') | {exists:False} -> ('new_first_appearance','high')`；`now_exists=False {} -> ('absent_both','n/a') | {exists:False} -> ('absent_both','n/a')`；`_b2_probe_out.txt:139-145`。（一路原记为「语义不等价」的疑点，两路实跑结论一致为**等价**；等价本身是缺陷，不按疑点写未成立。）
  后果：「快照缺失/传参丢失/跑前未测」与「跑前确认无件」被压平并强制给出 `high` 置信 F 结论，验收矩阵把混淆固化。

- **N4 · severity=high · 正常路径四个判定分支算了却从不输出（W11 核心场景空转）**
  证据：`B2_FIX_DESIGN.md:137-154` 计算 `_fresh`，`:155-162` 仅在 `if not _now_exists` 分支 `rec.add`，`:163` 之后到 hunk 结束 `:165` 无任何落盘；§2 `:186` 声称的 info +4 键无 diff（`_b2_probe_out.txt:186-191`；实跑 `grep -n "freshness_verdict..." B2_FIX_DESIGN.md` 见 E5）。上游 `lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md:56` 明确要求 info 新增 `mtime_post / freshness_verdict / freshness_confidence / freshness_note`；母本 `qc151_trip.py:4583-4586` 现状 `info = {"source","evidence_path","size","sha256","note"}`（实读）。B2 `:192`「净增 ≈ 31 行，删除 0 行」与 `:46/:61/:79/:99/:157` 共 5 行 `'-'` 删除行亦对不上（实跑 `grep -n "^-" B2_FIX_DESIGN.md` 确认）。
  后果：陈旧 `except.txt` 被当本趟证据的核心场景压根没有 F 结论产出，补丁等于空转；任何「净增31行/只改四处」的纯净性校验都会给出假阳性。

- **N5 · severity=high · 第五处①：`:5939` 唯一调用点无传参 diff（全趟恒走 N2 降级）**
  证据：实跑 `grep -n "^+" B2_FIX_DESIGN.md` 输出的全部 `+` 行 = `:42,:47,:48,:62,:63,:80,:81,:82,:83,:84,:100,:130,:132-161`，**无一行是 `copy_post_except_evidence(rec, carrier_dir, out_dir, pre_snapshot=...)`**；实跑 `grep -n "pre_snapshot\|_except_evidence_copy\|5939\|6388" B2_FIX_DESIGN.md` 只命中表格/叙述（`:36,:114,:116,:130,:133,:184,:188,:190,:200`），无 `:5939` 代码块。母本 `qc151_trip.py:5938-5939` 现状 `copy_post_except_evidence(rec, carrier_dir, out_dir)`，是该函数全仓唯一调用点（实跑 `grep -n "copy_post_except_evidence(" qc151_trip.py` → `:4561` def / `:5939` 调用）。B2 `:118` 仍宣称「四处改动是可论证的最小集」，`:200` 才把「能否真的传到」推给未来预审。
  后果：`copy_post_except_evidence` 加了 `pre_snapshot=None` 形参却没人传，所有趟（含正常趟）都走 N2 静默降级，W11 要修的缺陷反被固化进正式 harness。

- **N6 · severity=medium · B2 的 diff 示意不可套用 / 改动面账对不上**
  证据：`B2_FIX_DESIGN.md:43-48` 的 `finalize_trip` 签名 hunk 上下文跳过母本 13 个形参中的 7 个（`t0/pre_except_txt/out_dir/ownership/terminated_ok/main_return_code/mother_baseline`；`_b2_probe_out.txt:162-180`，母本 `qc151_trip.py:5900-5909` 实读）；`:52-64` 的调用点 hunk 亦省略 `:7118-7124` 的实参；`:192` 称「删除 0 行」但 `:46/:61/:79/:99/:157` 共 5 行是 `'-'` 删除行（实跑确认）。
  后果：4 个 hunk 与母本原文不符，无法构造无歧义的「应用后文件」，任何按 hunk 直接套用的尝试都会失败或改错位置。

- **N7 · severity=medium · 四处之外仍有该改而没给改法的第五/六/七处**
  证据：B2 §2 `:183-190` 列 8 个物理改动，但全文只有 4 个 `@@` hunk（`:43/:52/:75/:128`，`_b2_probe_out.txt:101-105`）；`:5939` 传参、`:6388` 后构造快照、`:4583-4586` info +4 键三处只出现在改动表里没有 diff（`_b2_probe_out.txt:117-123,157-161`）。因此 `:118`「四处是可论证的最小集」不成立。
  后果：设计自称的最小改动面是假账，实施者拿不到三处必要改法的代码。

- **N8 · severity=medium · 早退分支置信口径与候选语义倒错**
  证据：`B2_FIX_DESIGN.md:136-138`（`vanished` 标 `high`、`absent_both` 标 `n/a`）、`:160-161`；对照 `candidate/except_freshness.py:40-42` VERDICT_DOC、`:187-191`（`absent_both`: `is_new=False`, `confidence=low`, notes 含「不能证无崩溃」）、`:200-202`（`vanished`: `is_new=None`、须人工复核）。B2 `:192` 自称「无既有逻辑改动」，与候选口径不一致处未列差异说明。
  后果：高置信标签会让下游把「跑前在、跑后失」当成已确证的本趟写入证据。

- **N9 · severity=medium · 第五处②：旧 TASK 的「三处」与 `git diff` 门禁仍在且无作废机制**
  证据：实跑 `grep -n "三处\|git diff\|不许扩大" lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md` 输出 `:42/:83/:94/:115/:134`；`B2_FIX_DESIGN.md:103-118` 只说「我自己的死锁」、`:171-175` 只说「TASK 里彻底删掉」、`:234` 又声明「本文件不改任何文件」；本轮铁律 4 `lead/re_line_20261105/**` 只读。母本侧 `.gitignore:33 = out/` 实跑确认。
  后果：B1 #4/#6 的同一个死锁在下一任执行代理处原样重现。

- **N10 · severity=low · 数据契约静默缩水**
  证据：`lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md:47` 要求三键、`:55` 要求 `write_bytes` 失败时 `rec.add("ERROR",...)` 显式留痕再上抛、`:134` 验收要求 `RESTORE.backup_mtime_pre:except.txt`；`candidate/PATCH_SUGGESTION.md:37-44/:84-89` 含 `captured_at_iso`、`backup_mtime_pre` 留痕与复制失败守卫。B2 `:81-84` 只写 `exists/mtime_pre/captured_at_epoch`，`:127-165` 的 diff 无 try/except 复制守卫，`:192` 称「删除 0 行，无既有逻辑改动」；`captured_at_iso` 全文 0 次（`_b2_probe_out.txt:85/:185`）。另 `TASK.md:27` 称 B2 为 237 行，实跑 `wc -l lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` = `236`（11,638 B）；B2 `:206` 称「CARRIER_FILES 的 10 个件」而母本 `:213-214` AST 实算 5 个元素（`_b2_probe_out.txt:39-41`，「10」的依据未给）。
  后果：已批准的交付契约被静默缩减，行数/件数两处自述数字无依据。

- **N11 · severity=high · `freshness_verdict` 与 `except_set_diff` 的 E 口径隔离承诺不成立**
  证据：`B2_FIX_DESIGN.md:160-161`（`rec.add("EXCEPT", "evidence_freshness", _fresh[0], ...)`）、`:205`（纯断言，无测试/字段命名/不得进退出码的规约）；母本 `qc151_trip.py:436-454`（`Recorder.add` 是扁平 `(group,key,value)` 列表、group 仅是字符串）、`:672-708`（`except_set_diff`：E 唯一口径，`:677` 明令「不得用 sha 变化判 crash」）、`:702-707` 与 `:5986`（E 字段同在 `EXCEPT` group）、`:5985-5990`（E 唯一影响退出码处，未被 B2 改动，实读确认）。`PRE_AUDIT.md:80-84` 判同类情形「必然导致任何消费该字段的下游分析脚本、Nightwatch 或审查员直接误判为本趟发生了异常崩溃」、`:181 conflictsWith677 = true`、`:189` 列为阻断原因。专项核查结论：**未发现 E 函数本体被改**，B2 `:160` 只在早退路径写 F 且 note 明写「不做 crash 归因（:677）」，退出码仍唯一由 `setdiff.no_new_exception` 触发；但叠加 N1/N2/N5 后，异常路径与全部正常路径都会产出 `new_first_appearance/high`，正是 `PRE_AUDIT.md:181` 已判的风险机制（`_b2_probe_out.txt:189-190`）。B2 亦未给该键的字段契约（`freshness_confidence`/`freshness_note` 全文 0 次）。
  后果：F 字段结构与异常路径伪造结论使 `:205` 的隔离承诺沦为无实现约束的空断言；下游误读 `:677` 所禁「本趟新崩溃」的风险仍由 N2/N11 承载。

---

## 阻断与责任角色

**总阻断项**（再提交前必须全部消除）：
1. E1/N1/N5：作用域链未闭合——`_pre_freshness_snapshot` 无定义、`:5939` 无传参、`:6388` 无构造，早退/异常路径必崩。
2. E2/N2/N3/N8/N11：空/None 快照语义折叠、无「未测」出口、置信口径倒错，导致 100% 误标 `new_first_appearance/high`。
3. E5/N4/N6/N7：正常路径 F 结论不落盘、4 个 hunk 上下文与母本不符、§2 的 3 处「口头改动」无 diff、行数账对不上。
4. E4/E6/N9：旧 TASK 的三处限制与 `git diff` 门禁仍是有效治理文件，B2 无作废/替换机制。
5. N10：`captured_at_iso`、复制失败显式留痕、`RESTORE.backup_mtime_pre` 三项交付契约被静默删减。

**责任角色**：
- **设计者（`B2_FIX_DESIGN.md` 作者 / Leader）**：对 E1、E2、E5、N1、N2、N3、N4、N5、N6、N7、N8、N10、N11 负直接责任——六条旧错的「修法」只给示意 hunk、不给可套用代码，且自称「四处最小集/删除 0 行/无既有逻辑改动」与自身 §2 表格矛盾（`:118/:192`）。
- **任务书作者（旧 `lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md` 作者）**：对 E4、E6、N9 负直接责任——`:42`「不许扩大」、`:94/:115`「只改三处」、`:83/:94/:134`「git diff」三处限制未随 B2 作废。本轮铁律 4 使其为只读件，故不是「本判定书要求谁去改」，而是「再提交时须由有权者提供替换版任务书」。
- **候选实现者（下一任）**：负「不得按现设计直接制作/应用」的责任——B2 `:234` 自述「本文件不改任何文件」、`:196-198` 自述「只是设计，应用前必须重新走预审硬门」；若跳过本门直接套 4 个 hunk，将在早退路径触发 `UnboundLocalError`（N1 实跑）。

**再提交一次需要什么证据**（每条都要「文件:行」或「实跑命令+输出」）：
1. **完整可套用的 unified diff**：覆盖 §2 `:183-190` 全部 8 个物理改动，含 `:5939` 传参、`:6388` 后快照构造（且须在 5 个早退 `return` 之前预初始化）、`:4583-4586` info +4 键；`diff` 上下文须与母本 `qc151_trip.py:5900-5909/:7117-7125` 逐字对齐。
2. **应用后文件的 `ast.parse` 编译结果**：`python -I -X utf8 -c "import ast,io; ast.parse(io.open(r'<应用后文件>',encoding='utf-8').read())"` 退出码 0 + 完整输出。
3. **合成单测矩阵输出**：至少覆盖 `{}` / `{"exists":False}` / `None`（未采集）/ `{"exists":True,...}` × 跑后有件/无件，并显式给出「未测 ⇒ null / is_new=None」的判定分支与对应输出；须证明历史遗留件不再被判 `new_first_appearance/high`。
4. **正常路径落盘证据**：`EXCEPT.evidence_copy` 的 `info` 实含 `mtime_post / freshness_verdict / freshness_confidence / freshness_note`，且 `EXCEPT.evidence_freshness` 在正常路径有输出。
5. **早退/异常路径收尾不崩证据**：离线合成复现 5 个早退 + 捕获异常 + 正常三条路径，输出须显示 `finally` 内 `finalize_trip` 不再抛 `UnboundLocalError`，且原异常被保留。
6. **E/F 隔离规约**：给出 `freshness_verdict` 的字段契约、不得进退出码的规约与测试；证明 `except_set_diff`（母本 `:672-708`）未被改、退出码仍唯一由 `no_new_exception` 触发。
7. **治理文件一致性**：由有权者提供替换版任务书（或明确的作废声明），其中不再含「只改三处」「不许扩大」「git diff」；并给出 B2 `:206`「10 个件」与 `TASK.md:27`「237 行」的依据或更正。
8. **交付契约回填**：`captured_at_iso`、复制失败 `rec.add("ERROR",...)` 守卫、`RESTORE.backup_mtime_pre` 留痕三处的 diff 与实跑输出。
9. **独立复核 + 确定性门槛**：按 `lead/b2_preaudit_20261106/TASK.md:82-101`，`review/B2_PREAUDIT_REVIEW.md` 须含被核对象 SHA256 + 字节数与 `checkedEveryRow: true`，`check_b2_preaudit.py` 须 `python -I -X utf8` 实跑 exitCode=0 并附完整输出。

**本判定书不是应用许可**：即使上述证据齐备、下一版设计拿到 `verdict: YES`，其含义也仅为「可拿去制作完整候选」；「应用到母本」仍需另走 B2 `:196-198` 所要求的预审硬门与母本改动流程，本判定书不发放该许可。

---

## 未验

1. **未运行真机 harness / `qc151_trip.py` 本体**（铁律 1 零真机；`lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md:99` 连 `--help` 都禁）。本判定书所有运行时断言来自 `ast.parse` 静态解析母本 + 把 B2 `:133-154` 算法逐字转写后用合成字典离线实跑，**不是真机复现**。实跑命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b2_preaudit_20261106/_b2_probe.py` → `EXITCODE=0`，输出 `200 行 / 16296 B`；实跑 `sha256sum /tmp/_b2_out_before.txt lead/b2_preaudit_20261106/_b2_probe_out.txt` 两件同为 `57c49ca5…`（64 位完整值以本次命令输出为准，可复跑取得），`diff -q` → `IDENTICAL=yes`。本人另独立实跑两组合成复现（N1 的 main/finally、N2/N3 的判定式），命令与输出逐条列在对应条目。
2. **未验 B2 设计完整应用后的 `ast.parse` 编译结果**：只有 4 个示意 hunk 且上下文与母本不符（N6），无法构造无歧义的「应用后文件」，故语法可编译性、改动面 `difflib` 计数、六禁止面 API 计数（`TASK.md:97-98`）均未跑。
3. **未验 B2 §3 `:200-207` 要求的五项合成单测全矩阵**：无实现可跑；本人只离线复现了 `:202/:203` 的两个对例与 `:203/:204` 两个早退对例（见 N3/E5），未覆盖全部四/六分支矩阵，也未核 B2 `:209`「已当场验证：不成立」的原始过程。B2 `:206`「CARRIER_FILES 的 10 个件」来源未找到；本人独立用 AST 核母本 `:213-214` = 5 元素含 `except.txt`（`_b2_probe_out.txt:39-41`），结论与 B2 `:218` 一致但「10」无依据。
4. **未做 B2 §2 行号表（`:181-190`）与母本真实行号的逐格复核**：除本判定书引用到的 `:5939/:7117-7125/:6387/:6293-6296/:5900-5909/:4574-4599/:672-708/:436-454/:5949-5990` 外未逐一比对。
5. **未验母本 mtime**：只实算 SHA256 / `wc -c` / `wc -l`（见头部），与 `TASK.md:34-35` 基准一致故未触发 STOP，未写 `STOP_MOTHER_DRIFT.md`。
6. **未核 `PRE_AUDIT.md` 六条 error 的原始探针 `_b1_preaudit.py` 是否 100% 复现**：只读浏览了 `PRE_AUDIT.md:129` 的 NameError 自述与 `_b1_preaudit_out.txt:177-181` 的误判输出（该输出由一路 `notChecked` 转述，本人未打开该文件）；本判定书的判定独立基于母本原文、B2 原文、既有 `_b2_probe_out.txt` 与本人本次实跑。
7. **未审其它 harness 副本是否有独立调用链需同步**：一路 `notChecked` 报告 `grep -rn --include=*.py "finalize_trip(|copy_post_except_evidence(" lead/ out/.../qc151_u0400_trip/` 只确认 `lead/goal1_*_2026*/qc151_trip.harness{4,5,6,7}.py` 与 `out/.../qc151_trip.py.unapproved_*.py` 各自有同名函数与调用点，未逐文件核语义，也未确认它们是否属于本次正式 harness 写域；本人未重跑该命令，按「未验」记。
8. **未验证 `time.time()` / `hashlib` import 是否真的不需要新增**：一路 `notChecked` 只 greped 到母本 `:167 import hashlib`、`:173 import time`；亦未核 B2 `:80 src.stat()` 与母本 `:4460 dst.stat()` 在异常/TOCTOU 情形下的行为。
9. **未验下一版任务书是否会替换旧 `TASK.md` 的三处限制**：B2 `:196-198` 只写「应用前必须重走预审硬门」，未提供替换文本，且旧 `TASK.md` 属铁律 4 只读件。
10. **独立复核与确定性门槛本判定书未产出**：按本 ask 的交付范围，本判定书的唯一写域产物为 `lead/b2_preaudit_20261106/B2_PREAUDIT.md`；`TASK.md:5` 的 `review/B2_PREAUDIT_REVIEW.md`、`check_b2_preaudit.py` 未由本 ask 要求产出，故 `checkedEveryRow` 与门槛 `exitCode` 均无值可报，未伪造。本判定书不因此把自己标为「已复核」。
11. **只读件复核指纹**：母本 `517889c6…` / `399508 B`（本次实算）、B2 `deacab49…` / `11638 B`（本次实算）未变；`PRE_AUDIT.md`、`lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md`、`W11_EXCEPT_FRESHNESS/candidate/*` 的指纹由 `_b2_probe_out.txt:3-5` 与一路 `notChecked` 转述，本人本次未逐一重算。写域实跑 `find lead/b2_preaudit_20261106 -type f | sort` 输出 `TASK.md`、`_b2_probe.py`、`_b2_probe_out.txt`（另加本次新建的本判定书），未触碰写域外任何文件；不 commit、不 push。
