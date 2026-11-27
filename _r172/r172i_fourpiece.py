# -*- coding: utf-8 -*-
"""R172 I：四件套追加（R14_COMMON §2.177 / 台账 §1227 / LEAD_LOCK PC / 看板第 172 轮）。

写入纪律：每件先在 R17_LEAD_BASELINE 用打开模式 xb 独占建备份 -> 断言旧 sha256 与 CR -> 一次性追加 -> 回读校验。
CR 目标：R14_COMMON 1081 / 台账 337 / LEAD_LOCK 137 / 看板 0（四项全部保持不变）。
"""
import hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(TIER, 'STATUS_BOARD.md')
BAK = os.path.join(TIER, 'R17_LEAD_BASELINE')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

def state(p):
    d = io.open(p, 'rb').read()
    return d, hashlib.sha256(d).hexdigest(), d.count(b'\r'), d.count(b'\n'), len(d), d.endswith(b'\n')

SEC_RC = (
 '## 2.177 · R172：F24 的「逐次限定」给出**可失败的分句级判据**（BODY 型 4 次原本 3 次在场、实测只差 1 次）；'
 'F23 的「两份清单同给 sha」被证为**只有一份给**；FACT_INDEX 指针落后 3 版被补齐（V551→V552→V553）\n\n'
 '**一 · R171 待办①（给出「客观」判据）已交付，且它推翻了 R171 自己的指认.** 判据：先在**同括号深度**内以 。；： 与分句级逗号切分句'
 '（半角逗号两侧皆数字时视为千分位、不作界；括注内部的 。；： 与逗号都不切），限定词表取 11-22 / 快照 / 失效 / 不是现盘 / 非现盘 / 现盘 / 相对 七词'
 '，某次 4,417 记为「逐次在场」当且仅当限定词与它**同分句**且（同括号深度 或 该限定所在括号组是值之后的后置括注）。'
 '`r172a` **11 断言**、`r172b` **8 断言**，每条正控配一条反控。\n'
 '在 V551 上实测：10 次出现、逐次在场 **3/10**；按「后跟 件/文件」判为 **BODY 型 4 次**（语料体量），其中在场 **3 次**，'
 '**唯一不在场的是 ST@959**（溯源链终值 4,418→4,413→4,413→4,416→4,417）。⇒ **R171 判为「真裸用、该改」的 ST@449 在分句级其实在场**'
 '（限定在紧随其后的后置括注「（**2026-11-22 快照值**，非现盘体量；…）」内），R171 的指认方向反了；真正该改的是它没点名的那一次。\n'
 '**二 · 改动只有 1 处，且是纯插入.** V552（F23 作用域，见三）之后写 **V553**：F24.statement 在链尾括注内插入 '
 '「（**2026-11-22 快照值，非现盘体量**）」共 **48 B**，SequenceMatcher 报 **1 insert**；'
 '同判据复算 **BODY 型在场 4/4**、需要逐次限定集合为空。剩下 6 次不在场者分别是 ROWS 型 2 次（清单行数）、IDENT 型 1 次（恒等式右端）、'
 'OTHER 型 3 次（两处是「划分恒等式右端」与「本版均已改」的技术行），**不属语料体量、不需要限定**。\n'
 '**三 · F23 的「两份清单互证 sha」是错的，只改作用域、不改任何计数.** F23.limitations 原文写「出处为两份**互不相同**的清单——'
 '`_r67/unique_content_4417.tsv` 第 1022 行与 `R17_R101_TIER_FINAL_4417/tier_final_4417.tsv` 第 1022 行」。'
 '实测：`unique_content_4417.tsv` 为 **7 列**（含 sha256 列）、该摘要**全文恰 1 次**；`tier_final_4417.tsv` 为 **4 列**'
 '（rel/bytes/source/why_content）、**无 sha 列、全文该摘要 0 次** ⇒ 后者只能佐证**路径与字节数**，**不能佐证摘要**。'
 '两表第 1022 行的 rel 与 bytes 逐字相同（`next_re_20261117_r14/COVERAGE/coverage.tsv` / 4147334）。'
 'V552 就地补作用域（**+422 B**，只改 F23.limitations 一个单元），**458 / 291 / 293 / 1,196 / 12 / 2 / 9 与分母 1,654 一字未动**。\n'
 '**四 · 落盘与门禁（三段实跑，非引用旧输出）.** V551→**V552**（120,962 B / `28155d36…`，差分行恰 1 = F23、变化单元恰 1 = limitations）、'
 'V552→**V553**（121,010 B / `988a9567…`，差分行恰 1 = F24、变化单元恰 1 = statement）；两轮的母本均一字未改。'
 '`facts_floors` 两轮各 5 行重钉（`CUR_SHA256` / `TOTAL_BYTES` / `FLOORS[F23]→(1785,8200)` / `FLOORS[F24]→(10613,31158)` / `MASTER`，'
 '`2da2851e…` → `72cad997…` → `ce436f7a…`；每轮都先用 **ast 从源码取常量**复算命中上一轮 MASTER 作 fail-closed 硬闸，未命中不写盘）；'
 '`gate_runner` 两轮各 5 行（仅版本样）。实跑：`check_disc` **exit 0 / 无行首 FAIL**（C16 NOTE 逐字 `170 sections measured (pinned 170) … unpinned 0`）、'
 '`facts_floors` **exit 0**（D0 `988a9567` / D8 121,010 / D9 `ce436f7a`）、`gate_runner` **G1=G2=G3=ok**。`GATE_VER` **未升**（仍 R166）。\n'
 '**五 · FACT_INDEX_CURRENT.md 指针落后 3 版，本轮补齐.** 改前指针仍指 **V550 / `d85034b0…` / 120,495 / R170 / V530..V550 21 份**，'
 '而现盘已有 **24** 份（V530..V553）⇒ R171 只改了 `facts_floors` 与 `gate_runner`、**没改这个指针文件**（它不被任何门禁读，所以门禁全绿没暴露）。'
 '已改为 **V553 / `988a9567…` / 121,010 / R172 / V530..V553 24 份**，CR 仍 0，举例句里的 V547 保留。\n'
 '**六 · 未取得（不粉饰）.** ① **跨家族回件未拿到**：执行员 #403 与审计员 #405 在收口前 `wait_subagents` 连续三次超时（无回件、无 OVERTIME 标记），'
 '本轮结论**全部由主会话自测脚本产出**，**不得写成「已过跨家族审计」**；② F35 的 grade 仍未改（`[流程]`），'
 '且本轮实测**没有**发现 F35 行内矛盾（statement 的「有一手代码权威」与 limitations 的「定义有代码权威、无外部规范权威」指向同一事实，'
 '「都过强」判的是「缺一手权威」与「已有一手权威」两句，**都不是** statement 的原句）—— 我原先的「行内自相矛盾」假设当场被 `r172c` G9/G10 证伪；'
 '③ `coverage.tsv` 与 `PANEL.md` 仍不可读 ⇒ F23 四计数与 F35 严格列仍不可重数；④ C7 三死分支仍各 0 行；'
 '⑤ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑥ `a2_sites` 原始生成器与 86.19% 原值仍未复原到可重算。\n'
 '**七 · 自错 S-588..S-591（四条，全部由可失败断言当场抓出，无一条进入结论或正文数字）.** '
 '**S-588** `r172e` Q1 写「含 V551 恰 5 处」却把 V551（5）与 R17_R123（1）两串**相加**得 6 ⇒ 假 FAIL；'
 '**S-589** 同一脚本 Q2b 用 `^GATE_VER` 正则去断言 `gate_runner`，而它**本来就没有行首 GATE_VER 赋值**（R170 PA7 已记）⇒ 正则返回 None 抛 AttributeError；'
 '两处同族（**断言里写了本该被测量的量**）。**S-590** `r172g` M4b 一次把目录号与 sha **同时**改坏，`--ignore-pin` 也救不回 D6/D8 缩水断言 ⇒ 假 FAIL，'
 '改成「只改 sha 一处」后 M5b/M5c/M5d 三条成立。**S-591** `r172a` 第一版把 `4,417` 里的**千分位逗号**当分句界、第二版又把**括注内的逗号与分号**当界，'
 '两次都把「值」与紧随其后的括注限定切到两个分句里 ⇒ 判成 2/10；改为「分隔符只有与值同括号深度时才切」后 3/10，并补 C5–C11 **七条**正反控把这三种切错钉死。\n'
 '**八 · 交付清单.** `_r172/`：`r172a_f24_clause.py`（11 断言）、`r172b_f24_referent.py`（8）、`r172c_f23_f35_verify.py`（23）、'
 '`r172d_write_v552.py`（20）、`r172e_repin.py`（facts_floors 段）、`r172e2_gate_runner.py`（17）、`r172f_write_v553.py`（12）、'
 '`r172g_repin_v553.py`（25，含 1 条被 S-590 修正前的反控）、`r172h_pointer.py`（15）、`r172i_fourpiece.py`（本段）。\n'
)

SEC_LED = (
 '## §1227 · R172：F24「逐次限定」的分句级判据落地（BODY 4/4 在场）；F23「两份清单同给 sha」被证伪并只改作用域；指针落后 3 版被补齐（V551→V553）\n\n'
 '**一 · 判据.** 同括号深度内以 。；： 与分句级逗号切分句（千分位逗号不作界、括注内的 。；： 与逗号不作界），限定词 7 词，'
 '要求「同分句 + 同括号深度 或 值之后的后置括注」。`r172a` 11 断言 / `r172b` 8 断言，正反控成对。\n'
 '**二 · 结论（推翻 R171 的指认）.** V551 上 10 次出现、在场 3/10；BODY 型（后跟 件/文件）4 次、在场 3 次，'
 '**唯一不在场是 ST@959**。R171 指认的 ST@449 在分句级**在场**（限定在紧随的后置括注内）⇒ 方向反了。\n'
 '**三 · 改动.** V553 在链尾括注内插入「（**2026-11-22 快照值，非现盘体量**）」**48 B**，SequenceMatcher **1 insert**；'
 '复算 BODY 型 **4/4 在场**、待改集合空。其余 6 次为 ROWS 2 / IDENT 1 / OTHER 3，不属语料体量。\n'
 '**四 · F23 作用域证伪.** `unique_content_4417.tsv` **7 列**含 sha256、该摘要全文 **1** 次；`tier_final_4417.tsv` **4 列**无 sha 列、'
 '该摘要全文 **0** 次 ⇒ 「两份清单互证摘要」不成立，后者只证路径与字节。V552 就地补作用域（**+422 B**），'
 '**458/291/293/1,196/12/2/9 与 1,654 一字未动**。\n'
 '**五 · 落盘与门禁.** V551→**V552**（120,962 B / `28155d36…`）→**V553**（121,010 B / `988a9567…`），'
 '两轮各 1 行 × 1 单元变化、母本一字未改；`facts_floors` 两轮各 5 行（MASTER `2da2851e…`→`72cad997…`→`ce436f7a…`，'
 '每轮先 ast 复算旧 MASTER 命中作 fail-closed 硬闸）；`gate_runner` 两轮各 5 行；三段实跑 exit 0 / G1=G2=G3=ok、`GATE_VER` 仍 R166。\n'
 '**六 · 指针.** `FACT_INDEX_CURRENT.md` 改前仍指 V550 / 120,495 / R170 / 21 份（R171 漏改、无门禁读它），已补到 V553 / 121,010 / R172 / 24 份，CR 0。\n'
 '**七 · 未取得.** 跨家族回件未拿到（#403 / #405 三次 wait 超时，结论全由主会话自测脚本产出，不写「已过跨家族审计」）；'
 'F35 grade 未改且「行内矛盾」假设被 G9/G10 当场证伪；`coverage.tsv`/`PANEL.md` 仍不可读；C7 三死分支仍 0；'
 'C11 五条未动；`a2_sites` 生成器与 86.19% 原值仍不可重算。\n'
 '**八 · 自错 S-588..S-591.** 断言里写进本该被测量的量（S-588 两串相加、S-589 对无 GATE_VER 的文件用 ^GATE_VER 正则）、'
 '一次改两个不变式致 --ignore-pin 失效（S-590）、分句切分把千分位/括注内标点当界连错两版（S-591）。全部当场抓出，无一条进结论。\n'
)

SEC_LOCK = (
 'PC · R17 第 172 轮（2026-11-27 13:0x–13:4x）· F24 的「逐次限定」终于有了可失败判据，而它当场把 R171 的指认方向推翻；F23「两份清单互证 sha」被证伪；指针落后 3 版\n\n'
 'PC1. 🔴 **交付一：分句级判据（R171 待办①的正面回答），以及它带来的反证.** 判据三段：① 分隔符只有与值**同括号深度**时才切分句'
 '（半角逗号两侧皆数字视为千分位；括注内部的 。；： 与逗号都不切）；② 限定词表 7 词；③ 在场 = 同分句 且（同括号深度 或 值是「被后置括注限定」）。'
 '`r172a` **11 断言**、`r172b` **8 断言**，正反控成对。V551 实测：10 次出现、在场 **3/10**；BODY 型 4 次、在场 **3 次**，**唯一不在场是 ST@959**。'
 '⇒ **R171 判「该改」的 ST@449 其实在场**（限定就在紧随其后的后置括注内），R171 的指认反了。\n\n'
 'PC2. ✅ **交付二：只改 1 处、纯插入、48 B.** V553 在溯源链尾括注内插入「（**2026-11-22 快照值，非现盘体量**）」；'
 'SequenceMatcher **1 insert**；同判据复算 BODY **4/4 在场**、待改集合空；其余 6 次为 ROWS 2 / IDENT 1 / OTHER 3（不属语料体量）。'
 '**这一处改的不是 R171 点的那一处** —— 这是本轮最值钱的差异。\n\n'
 'PC3. 🔴 **交付三：F23 的「两份清单互不相同、同给 sha」是错的.** `_r67/unique_content_4417.tsv` **7 列**含 sha256 列、'
 '该摘要全文**恰 1 次**；`R17_R101_TIER_FINAL_4417/tier_final_4417.tsv` **4 列**（rel/bytes/source/why_content）、**无 sha 列、全文 0 次**。'
 '⇒ 后者只证**路径与字节**、不证摘要。V552 就地补作用域（**+422 B**、只改 F23.limitations），'
 '**458/291/293/1,196/12/2/9 与分母 1,654 一字未动**；两表第 1022 行 rel 与 bytes 逐字相同（`COVERAGE/coverage.tsv` / 4147334）。'
 '（R159 OP8 与看板 R170 判据二都写着「两颗互不相同的清单」，本轮第一次去数它们的**列**。）\n\n'
 'PC4. ✅ **交付四：两次落盘 + 两轮门禁重钉，全部 fail-closed.** V551→**V552**（120,962 B / `28155d36…`）→**V553**（121,010 B / `988a9567…`），'
 '两轮各「1 行 × 1 单元」变化、母本分别一字未改。`facts_floors` 两轮各 5 行：`CUR_SHA256` / `TOTAL_BYTES` / `FLOORS[F23]→(1785,8200)` / '
 '`FLOORS[F24]→(10613,31158)` / `MASTER`（`2da2851e…`→`72cad997…`→`ce436f7a…`），每轮**先 ast 从源码取常量**复算旧 MASTER 命中作硬闸'
 '（S-582 纪律），未命中不写盘；`gate_runner` 两轮各 5 行仅版本样。三段实跑：`check_disc` exit 0 / 无行首 FAIL（NOTE 逐字 170 节 pinned 170、unpinned 0）、'
 '`facts_floors` exit 0（D0 `988a9567` / D8 121,010 / D9 `ce436f7a`）、`gate_runner` **G1=G2=G3=ok**；`GATE_VER` 仍 **R166**。\n\n'
 'PC5. 🔴 **交付五：`FACT_INDEX_CURRENT.md` 落后 3 版.** 改前指针仍指 **V550 / `d85034b0…` / 120,495 / R170 / V530..V550 21 份**，'
 '现盘已有 **24** 份 ⇒ R171 改了 `facts_floors` 与 `gate_runner`、**没改指针**。它不被任一门禁读（`grep` 三个门全 0 命中），'
 '所以门禁全绿也没暴露 —— 这是**又一次「门禁覆盖不到的地方悄悄过期」**。已补到 **V553 / `988a9567…` / 121,010 / R172 / 24 份**，CR 0，举例句 V547 保留。\n\n'
 'PC6. 📌 **S-587 同族复现：两处「断言里写进本该被测量的量」.** **S-588** `r172e` Q1 把 V551（5 次）与 R17_R123（1 次）**相加**得 6、'
 '却断言「恰 5 处」⇒ 假 FAIL。**S-589** 同脚本 Q2b 用 `^GATE_VER` 正则断言 `gate_runner`，而它**本来就没有行首 GATE_VER 赋值**（R170 PA7 已记）⇒ 正则 None、'
 'AttributeError。**S-590** `r172g` M4b 一次改坏目录号与 sha 两个不变式，`--ignore-pin` 也救不回 D6/D8 缩水断言 ⇒ 假 FAIL；改成只改 sha 一处后三条全成立。'
 '**S-591** `r172a` 连错两版：第一版把 `4,417` 的**千分位逗号**当分句界、第二版又把**括注内的逗号与分号**当界，两版都判 2/10；'
 '改为「分隔符只有同括号深度才切」后 3/10，并补 C5–C11 七条正反控把三种切错钉死。**四条全由可失败断言当场抓出，无一条进入结论或正文数字。**\n\n'
 'PC7. 📌 **未取得（不粉饰）.** ① **跨家族回件未拿到**：执行员 #403 与审计员 #405 在收口前 `wait_subagents` **连续三次超时**（无回件、无 OVERTIME 标记）'
 '⇒ 本轮结论**全部由主会话自测脚本产出**，**不得写成「已过跨家族审计」**（与 R166 #388 同类，须如实登记）；'
 '② **F35 的「行内矛盾」假设被我自己证伪**：statement「有一手代码权威」1 次 与 limitations「一手代码权威」1 次 指向同一事实，'
 'limitations 的「都过强」判的是「缺一手权威」与「已有一手权威」两句、**都不是** statement 的原句（`r172c` G9/G10）⇒ F35 本轮**不改正文、不改 grade**；'
 '③ `coverage.tsv` 与 `PANEL.md` 仍不可读（全盘 `find` 0 命中）⇒ F23 四计数与 F35 严格列仍不可重数；'
 '④ C7 三死分支 exists/bytes=/none 仍各 0 行；⑤ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；'
 '⑥ `a2_sites` 原始生成器与 86.19% 原值仍不可重算；⑦ `facts_floors.py` docstring 的「GATE 计数」声称仍未改。\n\n'
 'PC8. 📌 **本轮最终状态（以磁盘为准）.** 五项 CR：`R14_COMMON` **1081** / 台账 **337** / 本文件 **137** / 看板 **0** / 归档 **2952**。'
 'FACT_INDEX **V553**：**121,010 B / 55 行 / 5 列 / `988a9567…` / CR 0**；V551 与 V552 均一字未改。'
 '本轮**未升** `GATE_VER`、**未改** C16 逐节表（本节落盘后 C16 下界仍需在下一轮按 §2.177 实测量重钉 —— 如实登记为未完成项）。\n'
)

SEC_BOARD = (
 '## 🟢 R17 第 172 轮（2026-11-27 13:0x–13:4x）· F24 的「逐次限定」终于有了**可失败的分句级判据**，而它当场把 R171 的指认方向推翻（该改的不是 ST@449，是 ST@959）；F23「两份清单同给 sha」被证伪并只改作用域（V551→V553）\n\n'
 '**入口**：R171 待办①（「F24 仍缺一个客观的在场判据」）与 R169/R170 待办里 F23 的「两份清单」表述。本轮只做**可机械判定**的措辞与判据，'
 '不改任何计数、不改任何 grade。脚本 `_r172/r172a..r172i`，收口 **0 FAIL**。\n\n'
 '| 项 | 本轮前 | 本轮实测/改动 |\n|---|---|---|\n'
 '| F24 逐次在场判据 | 无（R171 只证分数漂移 1/6..3/6） | **分句级：同括号深度切分句 + 后置括注**，11+8 断言正反控成对 |\n'
 '| BODY 型（语料体量）4 次 | R171 判「ST@449 真裸用」 | **ST@449 其实在场**；唯一不在场是 **ST@959**（方向相反）|\n'
 '| V553 改动 | — | 链尾括注插入 **48 B**、1 insert；复算 BODY **4/4 在场** |\n'
 '| F23「两份清单同给 sha」 | 正文如此写 | **证伪**：一份 7 列给 sha（全文 1 次）、一份 4 列无 sha 列（全文 0 次）|\n'
 '| FACT_INDEX_CURRENT.md | 指 V550 / R170 / 21 份 | **落后 3 版**，已补到 V553 / R172 / 24 份 |\n\n'
 '**判据一（分句级）**：分隔符只有与值**同括号深度**时才切分句（千分位逗号不作界、括注内部 。；： 与逗号不作界）；限定词 7 词；'
 '在场 = 同分句 且（同括号深度 或 值之后的后置括注）。V551 实测 10 次出现、在场 **3/10**；BODY 型 4 次、在场 3 次，**唯一不在场 ST@959**。\n\n'
 '**判据二（F23 作用域）**：`_r67/unique_content_4417.tsv` **7 列**含 sha256、该摘要全文 **1** 次；'
 '`R17_R101_TIER_FINAL_4417/tier_final_4417.tsv` **4 列**无 sha 列、全文 **0** 次；两表第 1022 行 rel 与 bytes 逐字相同。'
 '⇒ 后者只能佐证路径与字节，**不能佐证摘要**。\n\n'
 '**判据三（F35 不改）**：我原拟的「F35 行内自相矛盾」当场被证伪 —— statement「有一手代码权威」1 次 与 limitations「一手代码权威」1 次 同指一事，'
 '「都过强」判的是「缺一手权威」与「已有一手权威」两句、**都不是** statement 原句（`r172c` G9/G10）⇒ F35 正文与 grade 本轮均不动。\n\n'
 '**落盘**：V551 → **V552**（F23 作用域，**120,962 B / `28155d36…`**，差分行恰 1 = F23、变化单元恰 1 = limitations，**+422 B**）→ '
 '**V553**（F24 限定，**121,010 B / `988a9567…`**，差分行恰 1 = F24、变化单元恰 1 = statement，**+48 B**）；'
 '两轮母本 V551 / V552 均一字未改。门禁：`facts_floors` 两轮各 5 行（`MASTER` `2da2851e…`→`72cad997…`→`ce436f7a…`，'
 '每轮**先 ast 复算旧 MASTER 命中**作 fail-closed 硬闸）、`gate_runner` 两轮各 5 行（仅版本样）；'
 '实跑 `check_disc` **exit 0 / 无行首 FAIL**、`facts_floors` **exit 0**（D0 `988a9567` / D8 121,010 / D9 `ce436f7a`）、`gate_runner` **G1=G2=G3=ok**；`GATE_VER` 仍 **R166**。'
 '**指针**：`FACT_INDEX_CURRENT.md` 被 R171 漏改（仍指 V550/120,495/R170/21 份），本轮补到 V553/121,010/R172/**24** 份，CR 0。\n\n'
 '**跨家族**：执行员 #403（hy4flash-free/exec）与审计员 #405（deepseek/audit）均已派发，但收口前 `wait_subagents` **连续三次超时、无回件也无 OVERTIME 标记**'
 '⇒ **本轮无审计结论**，结论全部由主会话自测脚本产出，**不写「已过跨家族审计」**。\n\n'
 '**未取得**：① `coverage.tsv` / `PANEL.md` 仍不可读（全盘 find 0 命中）⇒ F23 四计数与 F35 严格列仍不可重数；② F35 grade 未改；'
 '③ C7 三死分支仍各 0 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 生成器与 86.19% 原值仍不可重算；'
 '⑥ **C16 逐节表本轮未重钉**（§2.177 落盘后下一轮须按实测量重钉，如实登记为未完成项）。\n\n'
 '**自错 S-588..S-591（四条，全部由可失败断言当场抓出，无一条进入结论或正文数字）**：S-588 把 V551(5) 与 R17_R123(1) 两串**相加**却断言「恰 5 处」；'
 'S-589 对**本来没有**行首 `GATE_VER` 的 `gate_runner` 用 `^GATE_VER` 正则 ⇒ AttributeError；S-590 一次改坏两个不变式致 `--ignore-pin` 救不回来 ⇒ 假 FAIL；'
 'S-591 分句切分连错两版（千分位逗号 / 括注内标点被当界），两版都判 2/10。\n\n'
)

TARGETS = [
    (RC, 'R14_COMMON.md', SEC_RC, 1081),
    (LED, 'GOAL_THREE_TARGETS_20261018.md', SEC_LED, 337),
    (LOCK, 'LEAD_LOCK', SEC_LOCK, 137),
    (BOARD, 'STATUS_BOARD.md', SEC_BOARD, 0),
]

for path, name, sec, cr_expect in TARGETS:
    raw, sha, cr, lf, size, endnl = state(path)
    ck('W0 %s 基线：CR %d / 末尾有换行' % (name, cr_expect), cr == cr_expect and endnl, (cr, endnl))
    add = sec
    if lf and raw.endswith(b'\n\n') is False:
        add = '\n' + sec
    new_raw = raw + add.encode('utf-8')
    bak = os.path.join(BAK, name + '.before_r172_%s.bak' % 'seg')
    if os.path.exists(bak):
        bak = os.path.join(BAK, name + '.before_r172_v2.bak')
    with io.open(bak, 'xb') as f:
        f.write(raw)
    ck('W1 %s 备份独占创建且字节相同' % name, io.open(bak, 'rb').read() == raw)
    io.open(path, 'wb').write(new_raw)
    b2 = io.open(path, 'rb').read()
    ck('W2 %s 回读逐字节 == 待写' % name, b2 == new_raw)
    ck('W3 %s CR 仍 %d' % (name, cr_expect), b2.count(b'\r') == cr_expect, b2.count(b'\r'))
    ck('W4 %s 前缀未被改动（旧字节是新的前缀）' % name, b2[:len(raw)] == raw)
    print('  %s: %d B -> %d B（+%d）/ LF %d -> %d' % (name, size, len(b2), len(b2) - size, lf, b2.count(b'\n')))

# 段落唯一性 / 看板行数
d = io.open(RC, encoding='utf-8').read()
ck('X1 R14_COMMON 新增 §2.177 恰 1 处', d.count('\n## 2.177 · R172') == 1, d.count('\n## 2.177 · R172'))
d2 = io.open(LED, encoding='utf-8').read()
ck('X2 台账新增 §1227 恰 1 处', d2.count('\n## §1227 · R172') == 1, d2.count('\n## §1227 · R172'))
d3 = io.open(LOCK, encoding='utf-8').read()
ck('X3 LEAD_LOCK 新增 PC 段恰 1 处（行首锚定）', len([1 for l in d3.split('\n') if l.startswith('PC · R17 第 172 轮')]) == 1)
ck('X3b LEAD_LOCK 的 PA1 / PB1 各仍 1 处（未误伤前轮）',
   len([1 for l in d3.split('\n') if l.startswith('PA1.')]) == 1 and len([1 for l in d3.split('\n') if l.startswith('PB1.')]) == 1)
d4 = io.open(BOARD, encoding='utf-8').read()
board_lines = d4.count('\n')
ck('X4 看板第 172 轮段恰 1 处', d4.count('## 🟢 R17 第 172 轮') == 1)
ck('X5 看板总行数 %d <= 300（< 260 故未触发归档）' % board_lines, board_lines <= 300, board_lines)
ck('X6 看板 CR 仍 0', d4.encode().count(b'\r') == 0 if isinstance(d4, str) else io.open(BOARD, 'rb').read().count(b'\r') == 0)

print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
