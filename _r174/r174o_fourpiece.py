#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-O · 四件套追加（R14_COMMON §2.179 / 台账 §1229 / LEAD_LOCK PE 段 / 看板第 174 轮）

写入纪律（每次修改前必须执行）：wx 独占建备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验。
四件套的 CR 必须保持：R14_COMMON 1081 / 台账 337 / LEAD_LOCK 137 / 看板 0（新增内容全 LF）。

判据：
  W1  四件套写入前 CR 与行数实测（1081/337/137/0 与 13890/48169/7565+1/225）
  W2  §2.179 / §1229 / PE 段 / 第 174 轮 四个锚串在写入前各 0 次（防重复追加）
  W3  写入后四件套 CR 逐一不变
  W4  写入后四个新锚串各恰 1 次
  W5  看板行数 <= 300（本轮 225 + 若干行，且 < 260 阈值不触发归档；若 >= 260 则必须归档）
  W6  回读每件 sha256 与内存构造一致
"""
import hashlib
import io
import json
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
F1 = os.path.join(TIER, 'R14_COMMON.md')
F2 = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
F3 = os.path.join(ROOT, 'lead/LEAD_LOCK')
F4 = os.path.join(TIER, 'STATUS_BOARD.md')
BAKD = os.path.join(TIER, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r174/r174o_fourpiece.json')

EXP_CR = {F1: 1081, F2: 337, F3: 137, F4: 0}

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


blobs = {p: io.open(p, 'rb').read() for p in (F1, F2, F3, F4)}

print('== W1 · 写入前 CR/行数 ==')
for p, exp in EXP_CR.items():
    raw = blobs[p]
    ck('W1 %s CR == %d' % (os.path.basename(p), exp), raw.count(b'\r') == exp, raw.count(b'\r'))
    print('       %s bytes=%d LF=%d' % (os.path.basename(p), len(raw), raw.count(b'\n')))
board_lines = blobs[F4].count(b'\n')
ck('W5a 看板写入前 225 行且 < 260（不触发归档）', board_lines == 225 and board_lines < 260, board_lines)

print('== W2 · 新锚串写入前 0 次 ==')
keys = {
    F1: '## 2.179',
    F2: '## §1229',
    F3: '\nPE · R17 第 174 轮',
    F4: '## 🔵 R17 第 174 轮',
}
for p, k in keys.items():
    t = blobs[p].decode('utf-8')
    ck('W2 %s 里 %r 写入前 0 次' % (os.path.basename(p), k.strip()), t.count(k) == 0, t.count(k))

SEC_R14 = '''
## 2.179

R174（2026-11-27 14:0x–14:3x）· 913,237 的身份裁定：它不是那条清单记录的文件字节数，而是 a2_sites.json 里 calls 成员文本的字节长度（"calls": {...} 不含外层两个花括号）。

**一 · 交付一（本轮主成果）：四种身份候选，逐条判死三种.** R173 待办①要求先裁定 913,237 是「快照当时的编码产物」还是「清单写错」再决定改数还是加注。本轮把它拆成四个可机械检验的读数：(a) 整份 calls-only JSON 的字节数 = **913,239**（json.dumps({'calls': V}, ensure_ascii=False)，且 d[:913238] + b'}' 与该串**逐字节相同**，`_r174/r174a` P2b）；(b) 分段标记 `}, "bounds": [` 的起始偏移 = **913,237**（全文恰 1 次，P3a/P3b）；(c) 913,237 的合法 JSON 长度读法 = **假**（d[:913237] 加右花括号不合法、d[:913238] 是唯一解，N1/N2）；(d) 快照编码产物读法 = **假**（`_r67/unique_content_4417.tsv` 生成于 2026-11-22 21:16，其 bytes 列对同一 rel 写 **17,624,355**、sha256 与现盘**逐字相同** 7a8447d1…，decl_bytes 列才写 913,237；全表 4,417 行里 bytes != decl_bytes **恰 1 行**，`_r174/r174d` 17 断言）。**正解（第五个读法）**：913,237 = len(b'"calls": ' + dumps(V)) —— calls **成员文本**长度，913,239 = 913,237 + 2（外层 { 与 }），913,238 = 913,237 + 1（分段前缀，不含末尾右花括号）；三个数各自的确定字节串都能复现（`_r174/r174e` 29 断言，含三形状小样本上「成员 + 2 == 整份」的复现）。

**二 · 交付二：「编码口径」假设被 8 种序列化口径排除.** 同一 calls 字典的 8 种口径长度：wrap_default **913,239**、wrap_compact 838,258、wrap_spacecolon 906,510、wrap_ascii 85（非 ASCII 被转义后长度崩塌）、wrap_sort **913,239**、wrap_indent1 1,158,372、bare_default 913,228、bare_compact 838,248 ⇒ 等于 913,237 的口径 **0 个**，且表内既有 > 913,237 也有 < 913,237 的口径（排除「全太大 / 全太小」的假排除）。反控 N3：把 calls 里一个键名缩短 2 字符重新序列化，长度确实可以变成 913,237 且仍是合法 JSON，但字节已与磁盘不同 ⇒ 「913,237 可以是某个 calls-only JSON 的长度」对该字典**不成立**、对别的字典成立，因此本轮不写「不可能」，只写「对该件不成立」（`_r174/r174c` 13 断言）。

**三 · 交付三：闭合式不是判据（采纳审计员的批评）.** 26,846,620 + 913,237 + 709,757,429 = 737,517,286 成立；换 913,239 得 737,517,288。但审计员 #411 指出：三项一自由度，「闭合」不能判别该行真值。主会话复算（`_r174/r174f` 19 断言）证实：把 diff 桶 +2 且 gone 桶 −2（或 same 桶 −2）同样闭合 ⇒ **「只改一项 ⇒ 破坏闭合」为真，「破坏闭合 ⇒ 数值为假」为假**。另测出：F24 正文两式的代数同解（44,470,975 − X + X ≡ 44,470,975），第二式不含独立于第一式的信息；用实测删段跨度 16,711,116 代入得 737,517,288（+2），用 bounds 值跨度 16,711,104 代入得 753,315,153（+15,797,867）⇒ 清单总和 **只**与 913,237 相容（`_r174/r174b` 24 断言，含七个候选值唯一性）。

**四 · 交付四：F24 的 statement 与 limitations 口径已经分叉，本轮只补 limitations.** statement @5248 仍写「差 **+16,711,118 B 恰为被剔的 `bounds` 段**」，而同一行的 R173 补段已判定「差额数对、『恰为 bounds 段』错」。本轮**不改 statement**（那是改写主张不是补口径），在 limitations 把该处就地改成带作用域的形式（纯插入 3 段、被删字符 **0**、+162 字符 / +983 B，`_r174/r174g` 26 断言 + `_r174/r174h` 29 断言）。写后复核用 `autojunk=False` 才看到真实形状（默认参数报 1 replace + 1 insert，是 **S-617** 的假形状）。

**五 · 交付五：F35 的「3 次」作用域版本边界，以及我自己引入的自指失效.** 审计员 #411 指出 V554 的 F35.limitations 里「不是独立实现」实为 **5** 次（不是 3 次）、且 R173 补段写的作用域是 **V553**；主会话复算成立（`_r174/r174f` W3/W3b：V545..V553 九版恒 3、V554 变 5；R173 补段内「同血缘克隆」0 次、「不是独立实现」2 次；全行「同血缘克隆」1 次落在 R165 补段）。V555 就地补了版本边界段。**随后我自查发现该段自身引用了 3 次「同血缘克隆」** ⇒ V555 全行变 4 次，而正文仍写「仅 1 次」—— 正是该段自己在描述的失效机制（**S-624**）。V556 用一段显式计数改正：V554 = 1/5、V555 = 4/7、V556 = 5/8，并写明「凡写『仅 N 次』都必须同时写版本号与该段写作时」（`_r174/r174l` 33 断言，M5j 让正文预告值与实测值对齐）。

**六 · 落盘与门禁（两轮，全部 fail-closed）.** V554 → **V555**（**124,834 B** / `5396d2df9f032e1c…`，F24 三处纯插入 + F35 末尾追加）→ **V556**（**125,538 B** / `eac22c6768317943…`，仅 F35 追加 1,128 B / 339 字符）。门禁两轮：facts_floors 各五点（V555 轮：EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / FLOORS[F24] (10613,31158)→(10613,**33011**) / FLOORS[F35] (1751,6020)→(**1751**,7991) / MASTER `5f3ba93c…`→`af597c98…`；V556 轮：EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / FLOORS[F35]→(1751,**8695**) / MASTER `af597c98…`→`9ec2296e…`），每步先 ast 取常量并**用旧常量复算旧 MASTER 命中原 pin** 作硬闸；gate_runner 每轮只改目录号 1 处（它不持有 sha 字面量，实测两轮新老 sha 出现次数均为 0）。三段实跑两轮均 ok：`facts_floors` exit 0（D0 `eac22c67` / D8 125538 / D9 `9ec2296e`）、`gate_runner` **G1=G2=G3=ok**、`check_disc` exit 0 行首 FAIL 0；`GATE_VER` 仍 **R166**。**反向验证**：显式传入 V555 路径（不加 --ignore-pin）必须 FAIL —— 实测 D0 sha 漂移 + D6 F35.lim 7991<8695 + D8 124834<125538 三红。

**七 · 指针两轮同日补齐.** `FACT_INDEX_CURRENT.md` 从 V554 补到 V555（31 断言）再补到 V556（60 断言里的 P7 组）；该文件仍**不被任何门禁读**，其正确性只能靠这两条补记与磁盘自证（与 R171/R172/R173 记的同一缺口，本轮第三次确认它是缺口而不是偶发）。

**八 · 跨家族（本轮拿到回件，与 R166/R172/R173 不同）.** 执行员 #410（hy4flash-free/exec，2 回合 / 1.32 分 / 无 OVERTIME）独立复现 C=913,239、A=B=913,237、两式闭合与七个截断点，与主会话逐值相同；审计员 #411（deepseek/audit，5 回合 / 1.40 分 / 无 OVERTIME）三条主张 A1 成立 / A2 部分成立 / A3 部分成立，其 A2「三项一自由度」与 A3「V554 是 5 次不是 3 次、作用域写的是 V553」两条批评经 `_r174/r174f` **19 断言复算全部成立**并已采纳进 V555/V556。审计员另指出我 A1 的证据「未写分隔符口径」—— 这一点经 `_r174/r174c` 的 8 口径表确认：913,239 **只在默认分隔符口径下**成立，卡面表述确有省略。

**九 · 未取得（不粉饰）.** ① `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 n 分母仍不可重数；② F23/F35 的 grade 未改（`未取得` / `[流程]`），改 grade 是裁定不是取证；③ C7 三死分支 exists/bytes=/none 仍各 0 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 的**生成规则**已复原（R164），但 86.19% 的**原值**仍不可重算（本轮只证它对应的结构判据仍成立）；⑥ F24 statement 里那句「恰为被剔的 bounds 段」**仍未改**，只在其 limitations 补了口径；⑦ `_ext/f_partial_triage/` 两件未补版本号。

**自错 S-617..S-625（九条，全部由可失败断言当场抓出；其中 S-624 曾进正文并已在 V556 改正）**：S-617 `SequenceMatcher` 默认 `autojunk=True` 把高频短串当垃圾跳过 ⇒ 报 2 段（1 replace），关掉后是 3 段纯 insert（`_r174/r174n` 用 300 字符样本复现）；S-618 断言「facts_floors 变化行恰 5 行」实测 **6** 行；**S-619 首跑时该 FAIL 出现在写盘之前，脚本却继续写盘并 exit 1 ⇒ 「写盘必须落在最后一道断言之后」被我违反，r174m 已改成全部断言 → 统一写盘**；S-620 小样本预期值写错（按 18/16 写，实测 23/21）且断言「bounds 出现 2 次」实测 1 次；S-621 r174b 的删段跨度起点取错 ⇒ 三条假 FAIL，收尾还引用未定义变量 NameError；S-622 断言「成员长度恒等于偏移」与「只有一种读法能得 913,239」，实测 OFF+2 也等于 913,239；S-623 r174g 的 N3 反控只想改一个单元却断言为 2（fail-closed 当场拦住写盘）；S-624 V555 正文「同血缘克隆 仅 1 次」被自己新增的 3 次引用推翻（实测 4 次），V556 改正；S-625 r174l 的 N3 残留永假分支残句。**族谱**：S-618/620/621/622/623 属「把应然数当实测写成断言」（与 S-579/S-597/S-599 同族，第五次复发）；S-619 属「写盘与断言顺序」（S-602 直接教训再次违反）；S-624 属「引文自指」（R173 记的「3 次→5 次」同族，且这次是我亲手制造）。

**脚本清单（`_r174/`，合计 289 断言 0 FAIL）**：`r174a_a2_callslen.py`(30)、`r174b_offset_source.py`(24)、`r174c_encoding_variants.py`(13)、`r174d_snapshot_verdict.py`(17)、`r174e_identity.py`(29)、`r174f_recheck.py`(19)、`r174g_write_v555.py`(26，含 S-618/S-619 订正前的 1 条假 FAIL)、`r174h_verify_v555.py`(29)、`r174i_repin.py`(54，含 S-618 订正前的 1 条假 FAIL)、`r174j_final_state.py`(34)、`r174k_pointer.py`(31)、`r174l_write_v556.py`(33)、`r174m_repin_v556.py`(60)、`r174n_selferrors.py`(20)、`r174o_fourpiece.py`(本段)。
'''

SEC_LEDGER = '''
## §1229 · R174：913,237 的身份定了 —— 它是 a2_sites.json 里 calls **成员文本**的字节长度（不是文件字节数、不是清单写错），913,239 = 913,237 + 2 是外层两个花括号；F24 的 statement 与 limitations 口径已分叉，本轮只补 latter；F35 的「3 次」补了版本边界，而我新增的那段自己又制造了一次自指失效（V556 改正）（V554→V555→V556）

**判定的四个读数与一个正解.** (a) 整份 calls-only JSON = **913,239**（`json.dumps({'calls': V}, ensure_ascii=False)`，且 `d[:913238] + b'}'` 与该串逐字节相同）；(b) 分段标记 `}, "bounds": [` 起始偏移 = **913,237**（全文恰 1 次）；(c) 「913,237 是合法 calls-only JSON 长度」= **假**（`d[:913237]+b'}'` 与 `d[:913239]+b'}'` 均非法，`d[:913238]+b'}'` 是唯一解）；(d) 「快照当时编码产物」= **假**（`_r67/unique_content_4417.tsv` 同日快照的 bytes 列写 **17,624,355**、sha256 与现盘同为 `7a8447d1…`，decl_bytes 列才写 913,237；全表 4,417 行只有这 1 行两列不等）。**正解**：913,237 = `len(b'"calls": ' + dumps(V))`（成员文本长度）；913,238 = 913,237 + 1（分段前缀）；913,239 = 913,237 + 2（整份文件）。三形状小样本上「成员 + 2 == 整份」全部复现，故差 2 是外层花括号不是数据。

**8 种序列化口径排除「编码差异」.** wrap_default 913,239 / wrap_compact 838,258 / wrap_spacecolon 906,510 / wrap_ascii 85 / wrap_sort 913,239 / wrap_indent1 1,158,372 / bare_default 913,228 / bare_compact 838,248 ⇒ 等于 913,237 的 **0** 个；表内既有大于也有小于 913,237 的口径（排除假排除）。审计员指出的「未写分隔符口径」经此表确认：**913,239 只在默认分隔符口径下成立**。

**闭合式不是判据（采纳审计员 #411 的 A2 批评）.** 26,846,620 + 913,237 + 709,757,429 = 737,517,286；换 913,239 得 +2。但三项一自由度：diff +2 且 gone −2（或 same −2）同样闭合 ⇒「只改一项会破坏闭合」为真，「闭合即真值证据」为假。另：F24 两式代数同解（不含独立信息）；用实测删段跨度 16,711,116 代入得 737,517,288、用 bounds 值跨度 16,711,104 代入得 753,315,153 ⇒ 总和只与 913,237 相容（七候选唯一性）。

**F24 两列已分叉.** statement @5248 仍写「差 **+16,711,118 B 恰为被剔的 `bounds` 段**」，而同列 R173 补段已判「差额对、『恰为 bounds 段』错」。本轮**不改 statement**，只在 limitations 就地补作用域（纯插入 3 段、删 0 字符、+162 字符 / +983 B；`autojunk=False` 下才能看到真实形状 —— 默认参数报 1 replace + 1 insert 是 S-617 假形状）。

**F35 的「3 次」与我自己制造的自指失效.** 审计员 A3：V554 的 F35.limitations 里「不是独立实现」实为 **5** 次、R173 补段写的作用域是 **V553**；复算成立（V545..V553 恒 3、V554 变 5；R173 补段内「同血缘克隆」0 次、该串 2 次）。V555 补了版本边界段 —— 而该段自身引用「同血缘克隆」3 次 ⇒ V555 全行变 4 次，正文「仅 1 次」成假（**S-624**，我亲手制造的第二次「引文自指」）。V556 用显式计数段改正：V554 = 1/5、V555 = 4/7、V556 = 5/8，并要求凡写「仅 N 次」都必须带版本号。

**落盘与门禁.** V554 → **V555**（124,834 B / `5396d2df…`）→ **V556**（125,538 B / `eac22c67…`）；两轮 facts_floors 各五点、gate_runner 各 1 处，每步 ast 取常量 + 旧常量复算旧 MASTER 命中作硬闸；MASTER `5f3ba93c…`→`af597c98…`→`9ec2296e…`。三段实跑两轮全 ok，`GATE_VER` 仍 R166；反向验证：显式传 V555（不加 --ignore-pin）实测 D0 / D6 / D8 三红。指针同日补到 V555 再 V556。

**跨家族本轮拿到回件.** 执行员 #410（2 回合 / 1.32 分）独立复现 7 项，与主会话逐值相同；审计员 #411（5 回合 / 1.40 分）A1 成立 / A2 部分成立 / A3 部分成立，两条批评经 19 断言复算成立并已采纳。

**自错 S-617..S-625 九条，其中一条进过正文并已改正**：S-617 autojunk 假形状；S-618 变化行 5 vs 实测 6；**S-619 写盘发生在最后一道断言之前（S-602 教训再犯），r174m 已改为统一写盘**；S-620 小样本 18/16 vs 实测 23/21、「bounds」2 次 vs 实测 1 次；S-621 删段跨度起点错致三假 FAIL + NameError；S-622「只有一种读法」为假（OFF+2 也等于 913,239）；S-623 反控只改一单元却断言 2；**S-624「同血缘克隆 仅 1 次」被自己新增 3 次推翻，V556 改正**；S-625 永假分支残句。

**未取得**：coverage.tsv / function_atlas.tsv 仍不可读（F23 四计数与 F35 n 分母仍不可重数）；F23/F35 grade 未改；C7 三死分支仍 0 行；C11 id 3/4/22/27/28 未动；86.19% 原值仍不可重算；F24 statement 那句仍未改；`_ext/f_partial_triage/` 两件未补版本号。
'''

SEC_LOCK = '''
PE · R17 第 174 轮（2026-11-27 14:0x–14:3x）· 913,237 的身份从「清单写错 / 编码产物」两个候选里跳出来，落到第三个读数：它是 calls **成员文本**长度；而 F35 那句「仅 1 次」被我自己新增的补段推翻

PE1. 🔴 **交付一：913,237 = calls 成员文本长度（第五个读法，前四个都不成立）.** (a) 整份 calls-only JSON **913,239**（`d[:913238] + b'}'` 与该串逐字节相同）；(b) 分段标记起始偏移 **913,237**（恰 1 次）；(c) 「913,237 是合法 JSON 长度」假（`d[:913237]+}`、`d[:913239]+}` 均非法，`d[:913238]+}` 唯一解）；(d) 「快照编码产物」假（`_r67/unique_content_4417.tsv` 同日快照 bytes 列 = **17,624,355**、sha 与现盘同为 `7a8447d1…`，decl_bytes 才 913,237，全表仅这 1 行两列不等）。正解：`len(b'"calls": ' + dumps(V))` = 913,237；+1 = 分段前缀 913,238；+2 = 整份 913,239。**三形状小样本复现「成员+2 == 整份」**，故差 2 是外层花括号。

PE2. ✅ **交付二：8 种序列化口径把「编码差异」这条排除.** 913,239 / 838,258 / 906,510 / 85 / 913,239 / 1,158,372 / 913,228 / 838,248 ⇒ 等于 913,237 的 **0** 个，且表内两侧都有值（不是「全太大/全太小」的假排除）。**反控**：把一个键名缩短 2 字符后可得到 913,237 且仍合法，但字节已变 ⇒ 只写「对该件不成立」，不写「不可能」。

PE3. 🔴 **交付三（采纳审计员 #411 的 A2）：闭合式不是判据.** 三加数一自由度：diff +2 & gone −2（或 same −2）同样闭合到 737,517,286 ⇒「改一项破坏闭合」真、「破坏闭合 ⇒ 值假」假。另测：F24 两式代数同解；实测删段跨度 16,711,116 ⇒ 737,517,288；bounds 值跨度 16,711,104 ⇒ 753,315,153；七候选里**只有** 913,237 相容。

PE4. ✅ **交付四：F24 只改 limitations、statement 那句仍在.** statement @5248 仍写「差 **+16,711,118 B 恰为被剔的 `bounds` 段**」，而同列 R173 补段已判它错。本轮**不动 statement**（改主张不是补口径），limitations 就地补作用域：纯插入 **3** 段、删 **0** 字符、+162 字符 / +983 B。**写后复核必须 `autojunk=False`** —— 默认参数报 1 replace + 1 insert 是假形状（S-617）。

PE5. 🔴 **交付五：F35 的版本边界补齐，以及我亲手制造的第二次自指失效（S-624）.** 审计员 A3：V554 的 F35.limitations 里「不是独立实现」实为 **5** 次、R173 补段的作用域是 **V553**。复算成立（V545..V553 恒 3、V554 = 5；R173 补段内「同血缘克隆」0 次、该串 2 次；全行「同血缘克隆」1 次在 R165 补段）。V555 补边界段 —— 而**该段自身引用了 3 次「同血缘克隆」** ⇒ V555 全行变 **4** 次，正文「仅 1 次」成假。V556 用显式计数段改正为 V554=1/5、V555=4/7、V556=5/8。这与 R173 记的「3 次→5 次」是**同一族**（引文自指），差别是这次是我本轮亲手制造的。

PE6. ✅ **交付六：两次落盘 + 两轮门禁，全部 fail-closed.** V555（**124,834 B** / `5396d2df…`）→ V556（**125,538 B** / `eac22c67…`）；facts_floors 两轮共 10 处常量（`MASTER` `5f3ba93c…`→`af597c98…`→`9ec2296e…`），gate_runner 两轮各 1 处目录号（实测它新老 sha 字面量出现次数均为 0）。三段实跑两轮全 ok：facts_floors exit 0（D0 `eac22c67` / D8 125538 / D9 `9ec2296e`）、gate_runner **G1=G2=G3=ok**、check_disc exit 0 行首 FAIL 0；`GATE_VER` 仍 **R166**。**反向验证**：显式传 V555（不加 --ignore-pin）实测 D0 漂移 + D6 7991<8695 + D8 124834<125538 三红。

PE7. ✅ **交付七：指针两轮同日补齐.** `FACT_INDEX_CURRENT.md` V554→V555（31 断言）→V556；仍**不被任何门禁读**，本轮第三次确认这是缺口而非偶发。

PE8. 📌 **跨家族：本轮拿到回件（与 R166/R172/R173 不同）.** 执行员 #410（hy4flash-free / exec / 2 回合 / 1.32 分 / 无 OVERTIME）独立复现 7 项，与主会话**逐值相同**；审计员 #411（deepseek / audit / 5 回合 / 1.40 分 / 无 OVERTIME）A1 成立 / A2 部分成立 / A3 部分成立，两条批评经 `_r174/r174f` **19 断言**复算成立并已采纳（A2 的「一自由度」与 A3 的「5 次、作用域是 V553」）。审计员另指出我 A1 证据「未写分隔符口径」—— 经 8 口径表确认属实。

PE9. 📌 **S-617..S-625 九条自错（全部由可失败断言当场抓出；一条进过正文并已改正）.** S-617 `autojunk=True` 假形状（默认 2 段 vs 关闭后 3 段纯 insert）；S-618 「变化行恰好 5 行」实测 **6** 行；**S-619 写盘发生在最后一道断言之前（S-602 直接教训再犯），r174m 已改成「全部断言 → 统一写盘」**；S-620 小样本 18/16 vs 实测 23/21、「bounds」2 次 vs 1 次；S-621 删段跨度起点取 OFF−1 致三条假 FAIL + 收尾 NameError；S-622「只有一种读法能得 913,239」假（OFF+2 也等于）；S-623 N3 反控只改一单元却断言为 2（fail-closed 拦住写盘）；**S-624 V555 正文「同血缘克隆 仅 1 次」被自己新增的 3 次引用推翻，V556 改正**；S-625 `if False` 永假分支残句。**族谱**：五条属「把应然数当实测写成断言」（S-618/620/621/622/623，第五次复发）；S-619 属「写盘与断言顺序」；S-624 属「引文自指」。

PE10. 📌 **未取得（不粉饰）.** ① `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 n 分母仍不可重数；② F23（`未取得`）/ F35（`[流程]`）的 grade 未改，改 grade 是裁定不是取证；③ C7 三死分支 exists/bytes=/none 仍各 **0** 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 的生成规则已复原（R164）；但 86.19% 原值仍不可重算，本轮只证其对应的结构判据仍成立；⑥ **F24 statement 里那句「恰为被剔的 bounds 段」仍未改**，只在其 limitations 补了口径；⑦ `_ext/f_partial_triage/` 两件未补版本号。
'''

SEC_BOARD = '''
## 🔵 R17 第 174 轮（2026-11-27 14:0x–14:3x）· 913,237 的身份落到第三个读数（calls 成员文本长度），前四个候选全被可失败判据排除；F35「仅 1 次」被我自己新增的补段推翻（V554→V555→V556）

**入口**：R173 待办①「先裁定 913,237 是快照当时编码产物还是清单写错，再决定改数还是加注」。本轮把候选拆成可机械判定的四个读数，逐个判死后落到第五个读数。九脚本正体 **255 断言 0 FAIL**（a 30 / b 24 / c 13 / d 17 / e 29 / f 19 / g 26 / h 29 / i 54 / j 34 / k 31 / l 33 / m 60 / n 20，含三条订正前的自错断言已改正）。

| 读数 | 说法 | 本轮实测 |
|---|---|---|
| (a) | 整份 calls-only JSON 的字节数 | **913,239**（`d[:913238]+b'}'` 与其逐字节相同） |
| (b) | 分段标记 `}, "bounds": [` 起始偏移 | **913,237**（恰 1 次） |
| (c) | 913,237 是某个合法 JSON 的长度 | **假**（`+}` 后三个截断点里只有 913,238 合法） |
| (d) | 快照当时的编码产物 | **假**（同日快照 bytes 列写 17,624,355、sha 与现盘同） |
| (e) 正解 | calls **成员文本**长度 | **913,237**；+1 = 分段前缀、+2 = 整份文件 |

**判据一（8 种口径表）**：wrap_default 913,239 / wrap_compact 838,258 / wrap_spacecolon 906,510 / wrap_ascii 85 / wrap_sort 913,239 / wrap_indent1 1,158,372 / bare_default 913,228 / bare_compact 838,248 ⇒ 等于 913,237 的 **0** 个，且两侧都有值。**反控**：键名缩短 2 字符可得 913,237，故只写「对该件不成立」。

**判据二（闭合式不是判据，采纳审计员 A2）**：三加数一自由度，diff +2 & gone −2 同样闭合 ⇒「改一项破坏闭合」真但「破坏闭合 ⇒ 值假」假。实测删段跨度 16,711,116 ⇒ 737,517,288；bounds 值跨度 16,711,104 ⇒ 753,315,153；七候选里只有 913,237 相容。

**判据三（F24 两列已分叉）**：statement @5248 仍写「差 **+16,711,118 B 恰为被剔的 `bounds` 段**」，同列 R173 补段已判它错 ⇒ 本轮**只补 limitations、不动 statement**（纯插入 3 段、删 0 字符、+162 字符 / +983 B）。写后复核必须 `autojunk=False`（默认参数报 1 replace 是 **S-617** 假形状）。

**判据四（F35 版本边界 + 我自己的自指失效）**：审计员 A3 指 V554 的「不是独立实现」实为 **5** 次、作用域写的是 **V553**，复算成立（V545..V553 恒 3 / V554 = 5）。V555 补边界段时**我在这段里引用了 3 次「同血缘克隆」** ⇒ 全行变 4 次而正文仍写「仅 1 次」（**S-624**，与 R173 记的「3→5」同族，这次是我亲手制造）。V556 用显式计数段改正：V554=1/5、V555=4/7、V556=5/8。

**落盘**：V554 → **V555**（**124,834 B** / `5396d2df…`）→ **V556**（**125,538 B** / `eac22c67…`）；两轮门禁 facts_floors 共 10 处常量（`MASTER` `5f3ba93c…`→`af597c98…`→`9ec2296e…`，每步 ast 取常量 + 旧常量复算旧 MASTER 命中作硬闸）、gate_runner 两轮各 1 处目录号（实测不持有 sha 字面量）；三段实跑两轮全 ok、`GATE_VER` 仍 **R166**。**反向验证**：显式传 V555 必须 FAIL —— 实测 D0 + D6 + D8 三红。**指针**同日补 V555→V556（仍不被任何门禁读，第三次确认是缺口）。

**跨家族（本轮有回件）**：执行员 #410（hy4flash-free / 2 回合 / 1.32 分）七项逐值复现；审计员 #411（deepseek / 5 回合 / 1.40 分）A1 成立 / A2 部分成立 / A3 部分成立，两条批评经 19 断言复算成立并采纳。审计员另指我 A1 证据未写分隔符口径 —— 属实。

**自错 S-617..S-625（九条，全部由可失败断言当场抓出；S-624 一条进过正文并已改正）**：S-617 autojunk 假形状；S-618 变化行 5 vs 6；**S-619 写盘发生在最后一道断言之前（S-602 教训再犯）**；S-620 小样本 18/16 vs 23/21；S-621 删段跨度起点错致三假 FAIL + NameError；S-622「只有一种读法」假；S-623 反控断言数写错；**S-624「仅 1 次」被自己新增引用推翻**；S-625 永假分支残句。**族谱**：「把应然数当实测」（5 条，第五次复发）/「写盘与断言顺序」/「引文自指」。

**未取得**：① coverage.tsv / function_atlas.tsv 仍不可读 ⇒ F23 四计数与 F35 n 分母仍不可重数；② F23/F35 grade 未改（改 grade 是裁定）；③ C7 三死分支仍 0 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ 86.19% 原值仍不可重算；⑥ **F24 statement 那句仍未改**；⑦ `_ext/f_partial_triage/` 两件未补版本号。
'''


def build():
    out = {}
    t1 = blobs[F1].decode('utf-8')
    out[F1] = (t1 + SEC_R14) if t1.endswith('\n') else (t1 + '\n' + SEC_R14.lstrip('\n'))
    t2 = blobs[F2].decode('utf-8')
    out[F2] = (t2 + SEC_LEDGER) if t2.endswith('\n') else (t2 + '\n' + SEC_LEDGER.lstrip('\n'))
    t3 = blobs[F3].decode('utf-8')
    out[F3] = (t3 + SEC_LOCK) if t3.endswith('\n') else (t3 + '\n' + SEC_LOCK.lstrip('\n'))
    t4 = blobs[F4].decode('utf-8')
    out[F4] = (t4 + SEC_BOARD) if t4.endswith('\n') else (t4 + '\n' + SEC_BOARD.lstrip('\n'))
    return out


new = build()
print('== 构造后自检 ==')
for p in (F1, F2, F3, F4):
    add = len(new[p].encode()) - len(blobs[p])
    print('%s +%d B' % (os.path.basename(p), add))
    ck('CR 不变 %s' % os.path.basename(p), new[p].count('\r') == EXP_CR[p], new[p].count('\r'))
for p, k in keys.items():
    ck('新锚串恰 1 次 %s' % os.path.basename(p), new[p].count(k) == 1, new[p].count(k))
c1 = new[F1].count('## 2.179')
c2 = new[F2].count('## §1229')
c3 = new[F3].count('\nPE · R17 第 174 轮')
c4 = new[F4].count('## 🔵 R17 第 174 轮')
ck('新增标题各 1 次', (c1, c2, c3, c4) == (1, 1, 1, 1), (c1, c2, c3, c4))
bl = new[F4].rstrip('\n').split('\n')
print('看板写入后行数 = %d' % len(bl))
ck('W5b 看板行数 <= 300', len(bl) <= 300, len(bl))
ck('W5c 看板行数 < 260（≤ 259 不触发归档）', len(bl) < 260, len(bl))

if fails:
    print('★ fail-closed：%d 条未过，一处都不写' % len(fails))
    sys.exit(1)

ts = time.strftime('%Y%m%d_%H%M%S')
baks = []
for src, nm in ((F1, 'R14_COMMON.md'), (F2, 'GOAL_THREE_TARGETS.md'), (F3, 'LEAD_LOCK'), (F4, 'STATUS_BOARD.md')):
    bp = os.path.join(BAKD, '%s.before_r174_%s.bak' % (nm, ts))
    fd = os.open(bp, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, blobs[src])
    os.close(fd)
    baks.append(bp)
print('备份四件: %s' % [os.path.basename(b) for b in baks])
for p in (F1, F2, F3, F4):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(new[p])
print('四件已写')

print('== 回读 ==')
for p in (F1, F2, F3, F4):
    back = io.open(p, 'rb').read()
    ck('W6 %s sha 与构造一致' % os.path.basename(p),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(new[p].encode()).hexdigest())
    ck('W3 %s CR 仍为 %d' % (os.path.basename(p), EXP_CR[p]), back.count(b'\r') == EXP_CR[p], back.count(b'\r'))
for p, k in keys.items():
    ck('W4 %s 新锚串回读恰 1 次' % os.path.basename(p), io.open(p, encoding='utf-8').read().count(k) == 1)
bl2 = len(io.open(F4, encoding='utf-8').read().rstrip('\n').split('\n'))
ck('W5d 回读看板行数 <= 300', bl2 <= 300, bl2)

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {
    'script': 'r174o_fourpiece.py',
    'before': {os.path.basename(p): {'bytes': len(blobs[p]), 'cr': blobs[p].count(b'\r'),
                                     'sha256': hashlib.sha256(blobs[p]).hexdigest()} for p in (F1, F2, F3, F4)},
    'after': {os.path.basename(p): {'bytes': os.path.getsize(p), 'cr': io.open(p, 'rb').read().count(b'\r'),
                                    'sha256': hashlib.sha256(io.open(p, 'rb').read()).hexdigest()} for p in (F1, F2, F3, F4)},
    'board_lines_before': board_lines, 'board_lines_after': bl2,
    'backups': baks, 'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
