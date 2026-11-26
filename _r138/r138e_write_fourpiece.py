#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r138e_write_fourpiece.py —— R138 四件套落盘 + 门禁同步。

四件套：
  R14_COMMON.md  新增 ## 2.142（CR 保持 1081）
  GOAL_THREE_TARGETS_20261018.md  新增 ## §1192（CR 保持 337）
  LEAD_LOCK      新增 MZ.. 之后的段（CR 保持 137）
  STATUS_BOARD.md 新增第 138 轮记录（CR 保持 0，总行数 <= 300）

门禁同步（全为容纳新节 + 同步 + 重钉，不改判据语义）：
  ① C16_FLOORS 加 142:<半量>，C16_FLOORS_SHA256 重钉
  ② GATE_VER R137 -> R138
  ③ DISC_RECHECK 第 21 行（id=20）登记式同步，C7_TEXT_SHA256 / C7_ROW_SHA['20'] 重钉
  ④ DISC_UNVERIFIABLE 第 11 行（id=20）锚同步，FREEZE_SHA256 重钉

纪律：每件写前 wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
先 --dry 跑一遍，断言全绿后再真写。
"""
import os
import io
import re
import sys
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
DU = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
GATE = os.path.join(R14, 'check_disc.py')

DRY = '--dry' in sys.argv
TS = time.strftime('%Y%m%d_%H%M%S')

fails, buf = [], []


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def backup(path, tag):
    b = open(path, 'rb').read()
    name = os.path.basename(path) + '.before_R138_%s_%s.bak' % (tag, TS)
    p = os.path.join(BASE, name)
    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, b)
    finally:
        os.close(fd)
    assert sha(open(p, 'rb').read()) == sha(b), 'backup sha mismatch: ' + p
    return p, b


def write_atomic(path, new_b):
    tmp = path + '.tmp_r138e'
    if os.path.exists(tmp):
        os.remove(tmp)
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, new_b)
    finally:
        os.close(fd)
    os.replace(tmp, path)


# ==================== 正文内容 ====================

R14_SEC = u'''## 2.142 R138：FACT_INDEX v5.32 -> v5.33 四条正文修订落盘（F23 分解不闭合 + 计数层已失、F24 撤下 86.19% 但保留结构判据 + 语料值失效期、F29 两处作用域、F35 定义缺一手权威）

**测量动机.** R136/R137 两轮把四条正文缺陷都测成了「只登记不改正文」，看板第九节把它列为下轮第一优先。本轮做的是**内容变更 + 门禁回归**：改的是 FACT_INDEX 正文，不是台账叙事。改前先确认 FACT_INDEX 不被 check_disc.py 钉住（实测 `grep FACT_INDEX check_disc.py` 命中 0，改后 check_disc.py 仍 exit 0 ⇒ 该结论有实测支撑，不是假设）。

**一 · F23 补两处（`_r138/r138a_revise_measure.py` 项1/项2）.** ① **分解不闭合**：原文三个分项 6（否定式）+2（callers 计数）+3（真正非否定多计）= **11**，与 total=**12** 差 **1 行**，该行在上述分解里没有归属；换读法（把「3 行本已在 W 内」当另一批）得 6+2+3+3=14>12 出现重计 ⇒ **两种读法都得不到 12，缺口对读法不敏感**。② **计数层不可重数**：458/291/293/1196/12/2/9 与分母 1654 依赖 `coverage.tsv`（记载 4,147,334 B / 18,498 行 / 8 列），该文件**不在现盘** —— 全库按文件名精确命中 **0**、按 4,147,334 B 精确字节反查命中 **0**，`COVERAGE/`、`R17_DELIVERY/`、`R17_R41_RECOMPUTE/` 三目录均不存在；11-22 快照清单有 4 条记录 ⇒ 曾存在、现失。故能证的只有算术闭合。

**二 · F24 撤下数字、保留判据（两项必须分开）.** ① **撤下「86.19% 盘上无任何字节对应」**：R136 三种独立实现同测实测 **99.992%（1,392,481/1,392,592）有字节对应**、未命中仅 111 条且 111/111 落在前一指令起始 +1..8 内 ⇒ **错的是数字、不是方向**。三处出现（statement 一处、limitations 两处）逐处改为撤下声明，并保留撤回记录形态（每次出现都紧跟「撤下原「」之后）。② **保留独立结构判据**「单列地址、没有可回原址复核的第二列」—— 这条与 86.19% 无关，本轮未否，故 `bounds` 仍剔。③ **补语料值失效期**：主引用值 4,417 件 / 737,517,286 B 是 **2026-11-22 快照值**；R138 实测现盘存在且同字节 **64 件 / 26,846,620 B（1.45%）**、存在但字节不同 1 件（`a2_sites.json` 清单 913,237 vs 盘 17,624,355，差 +16,711,118 恰为被剔段）、**不存在 4,352 件 / 709,757,429 B（98.53%）**。

**三 · F29 补两处作用域，并纠正一处待办前提.** ① 「两份拷贝」作用域：17 字节序列在 `.text` 全镜像实测出现 **80 次**（主会话独立纯字节搜索），正文指的是其中两份。② 「FirstThunk idx=62」口径：组内 0-based **62** / 全局 0-based **63** / 全局 1-based **64** 三口径互不相同（pefile 遍历导入描述符实测，Hint=432 同得），62 只在 DLL 内口径为真。③ 另补「8 字节桩 40 次」与「63/77」**互不构成因果**（77 mod 40=37、77−40=37）。**R138 新发现**：R137 待办写的「6 个桩体」**不在 F29 正文任何一列** —— 它是 R135 审计过程中自报的中间数字，本条正文不采用、也不需为它补作用域。故待办④原本四项，实为三项在正文、一项是伪前提。

**四 · F35 补定义缺一手权威.** `proved_strict` 的定义只有二手转述：一手来源 `PANEL.md`（M52 / 严格口径双列表）不在现盘（文件名精确命中 0，父目录 `COVERAGE/` 亦不存在）。本条 evidence_paths 唯一一项即该已失文件 ⇒ F35 与 F23 并列为本表的**两条整行证据链失联项**。

**五 · 规则 D 与一处口径分歧的复算.** 开局 `MAX_SUBAGENTS=3`（1768 MB），并发 2 未超上限。执行员 hy4 **#301 succeeded**（12 回合 / 2.62 分钟 / 无 OVERTIME）、审计员 deepseek **#302 succeeded**（17 回合 / 3.97 分钟 / 无 OVERTIME）。两家四项数字与主会话**逐项一致**（三桶 64/1/4,352、闭合 737,517,286、coverage.tsv 命中 0、F35 单条路径）。审计员提出三条异议，主会话逐条复算：① 「13 处出现复现不出」**被推翻** —— 它把 17 当真实判据式，未排除 R137 自述里对同一等式的 4 处元复述；按「排除假样本行 + 排除自述复述行」口径实测恰为 **13 / 9 键 / 冗余 4**，与 R137 登记逐字吻合（三口径 20 全量 / 17 去假样本 / 13 去假样本+去自述均可复现）。② 「F24 按仓库根解析得 4,417 全 missing」**无冲突** —— rel 列不带 `lead/` 前缀，正确根是 `lead/`，审计员两种都算了。③ 「三桶求和是字典恒等式、无判别力」**成立且已接受** —— 有判别力的是三桶各自等于预期值，以及唯一差异件字节差 == 16,711,118。

**六 · 落盘与门禁.** FACT_INDEX v5.32 -> **v5.33**（61,822 -> 66,661 B，9 处单元格改动，未改动的 51 行逐字节相同，grade 与 evidence_paths 两列一字未动，全 LF、55 行）。门禁改四处，全为容纳新节 + 同步 + 重钉、**不改任何判据语义**：① `C16_FLOORS` 加 `142: <半量>`；② `GATE_VER` R137 -> R138；③ `DISC_RECHECK` 第 21 行同步；④ `DISC_UNVERIFIABLE` 第 11 行锚同步。改后 `check_disc.py` exit 0。

**七 · 未取得（不粉饰）.** ① **F23 的计数层仍不可重数** —— coverage.tsv 已失，本轮只补「不可重数」这个事实，没有、也无法重数 458/291/293/1196/12/2/9；② **F23 那余 1 行到底属哪一类不可判** —— 逐行归类依赖已失的表；③ **F35 的 `n`（atlas 内分母）取法仍只在已失文件里**，本轮只证两个 ceil 式的算术；④ **F24 的 86.19% 来源机制仍未定** —— R136 只证到「来自某种按地址的前缀切分」，本轮不编机制；⑤ **F24 语料值无法还原成现盘体量** —— 4,352 件在 11-22 快照里，本机取不到；⑥ 窗口表扩展仍需 r66 以后主快照，一份都没有；⑦ 35 个静态容器的运行期元素值与计数。

**八 · 自错四条（全由断言抓出，未进结论）.** S-262 首版 `r138a` 把表头行当事实项，54 变 55，断言当场报错。S-263 v5.33 首次写入时 F35 追加段写「故 F35 是 **v5.32** 里与 F23 并列的…」，而该行写入后已在 v5.33 内 —— **版本自指错**，由回读复查发现，改 `r138d` 修正（18 项断言全 PASS）。S-264 `r138c` 的 `one_time()` 在 append 分支里仍去 `count(None)` 抛 TypeError，改为直接判 `new not in cell`。S-265 「86.19% 不再出现」这条断言首版写成全串不出现，与「保留撤回记录」自相矛盾（撤回记录必须引用原串），改为「每次出现都必须紧跟『撤下原「』」。
'''


LEDGER_SEC = u'''## §1192 【R17 第 138 轮，2026-11-26】FACT_INDEX v5.32 -> v5.33：四条正文修订落盘（F23 分解不闭合 + 计数层已失、F24 撤下 86.19% 保留结构判据 + 语料值失效期、F29 两处作用域、F35 定义缺一手权威）

**一 · 改前先证「FACT_INDEX 不被门禁钉住」.** 实测 `grep FACT_INDEX check_disc.py` 命中 **0** ⇒ 改正文不会触发门禁常量；改后 `check_disc.py` 仍 **exit 0**，实测支撑该判断，不是假设。这是本轮能对正文动手的前提，先证再改。

**二 · F23 两处补入.** 分解不闭合：6+2+3=**11** vs total=**12**，差 **1 行无归属**；换读法 6+2+3+3=14>12 出现重计 ⇒ **两种读法都得不到 12**，缺口对读法不敏感。计数层不可重数：所依赖的 `coverage.tsv`（4,147,334 B / 18,498 行 / 8 列）全库文件名命中 **0**、按精确字节反查命中 **0**，`COVERAGE/`、`R17_DELIVERY/`、`R17_R41_RECOMPUTE/` 三目录均不存在。

**三 · F24 撤数留判据（两项分开处理是本次的方法要点）.** 撤下「86.19% 盘上无任何字节对应」（R136 三实现实测 **99.992% 有字节对应**，错的是数字不是方向），三处出现逐处改；**保留**独立于该数的结构判据「单列地址、无可回原址复核的第二列」，故 `bounds` 仍剔。补语料值失效期：4,417 / 737,517,286 B 是 **11-22 快照值**，现盘同字节 **64 件 / 26,846,620 B（1.45%）**、字节不同 1 件（差 +16,711,118 恰为被剔段）、不存在 **4,352 件 / 709,757,429 B（98.53%）**。

**四 · F29 两处作用域 + 一处待办前提被纠正.** 17 字节序列全镜像 **80 次** ⇒「两份拷贝」须带作用域；idx 三口径 **62/63/64** 互不相同 ⇒ 62 只在 DLL 内口径为真；「8 字节桩 40 次」与「63/77」**互不构成因果**（77−40=37）。**R138 新发现**：「6 个桩体」**不在 F29 正文任何一列**，是 R135 审计自报的中间数字 ⇒ R137 待办④原本四项，实为三项在正文 + 一项伪前提，本轮不为伪前提改正文。

**五 · F35 定义缺一手权威.** `proved_strict` 定义只有二手转述，一手 `PANEL.md`（M52）不在现盘（文件名命中 0，父目录不存在）；本条 evidence_paths 唯一一项即该已失文件 ⇒ 与 F23 并列为本表两条整行证据链失联项。

**六 · 规则 D 与口径分歧复算.** 开局 `MAX_SUBAGENTS=3`（1768 MB），并发 2 未超上限。hy4 执行员 **#301 succeeded**（12 回合 / 2.62 分钟 / 无 OVERTIME）、deepseek 审计员 **#302 succeeded**（17 回合 / 3.97 分钟 / 无 OVERTIME）。两家四项数字与主会话逐项一致。审计员三条异议：① 「13 复现不出」**被推翻** —— 它未排除 R137 自述里对同一等式的 4 处元复述；按「去假样本 + 去自述」口径实测恰 **13/9/冗余 4**，三口径 20/17/13 均可复现；② 「F24 仓库根解析全 missing」**无冲突**（rel 不带 `lead/` 前缀）；③ 「三桶求和是恒等式无判别力」**成立且已接受**。

**七 · 落盘与门禁.** FACT_INDEX **v5.33**：61,822 -> 66,661 B，9 处单元格改动，未改动 51 行逐字节相同，grade/evidence_paths 两列一字未动，全 LF 55 行。门禁四处（C16_FLOORS 加 142、GATE_VER R138、DISC_RECHECK 第 21 行、DISC_UNVERIFIABLE 第 11 行），不改判据语义；改后 exit 0。

**八 · 未取得.** ① F23 计数层仍不可重数（只补「不可重数」这个事实）；② 余 1 行属哪类不可判；③ F35 的 n 取法仍只在已失文件里；④ 86.19% 来源机制仍未定；⑤ 4,352 件在快照里、本机取不到；⑥ 窗口表 r66 后快照仍无；⑦ 35 个静态容器运行期值。

**九 · 自错四条留案.** S-262 表头被当事实项（54->55，断言抓出）；S-263 **版本自指错** —— F35 追加段写「v5.32 里」，而写入后该行已在 v5.33 内，由回读复查发现并由 `r138d` 修正（18 项全 PASS）；S-264 `one_time()` append 分支仍去 `count(None)` 抛 TypeError；S-265 「86.19% 不再出现」断言与「保留撤回记录」自相矛盾，改为「每次出现须紧跟撤下声明」。
'''


LOCK_SEG = u'''
MZ3. 🔴 **开局选的是看板第九节第 1-4 条**：F23/F35 正文修订、F24 撤 86.19%、F24 失效期、F29 作用域。R136/R137 两轮把四条都测成「只登记不改正文」，本轮做内容变更 + 门禁回归。

NA2. ✅ **改正文前先证它不被门禁钉住.** `grep FACT_INDEX check_disc.py` 命中 **0**，改后 `check_disc.py` 仍 exit 0 —— 是实测不是假设。缺这一步就动手，等于拿门禁当运气。

NB2. ✅ **F23 补两处（`_r138/r138a` 项1/项2）.** 6+2+3=**11** vs total=**12**，差 **1 行无归属**；换读法 6+2+3+3=14>12 出现重计 ⇒ **两种读法都得不到 12**。计数层：`coverage.tsv`（4,147,334 B / 18,498 行 / 8 列）文件名命中 **0**、精确字节反查命中 **0**，三目录均不存在 ⇒ **本机不可重数**，能证的只有算术闭合。

NC2. ✅ **F24 撤数留判据 —— 两项必须分开（本轮方法要点）.** 撤下「86.19% 无字节对应」（R136 三实现实测 99.992% 有对应；**错的是数字不是方向**），三处出现逐处改并保留撤回记录形态；**保留**独立结构判据「单列地址、无可回原址复核的第二列」，故 `bounds` 仍剔。失效期：4,417/737,517,286 B 是 **11-22 快照值**，现盘 64 件/26,846,620 B（1.45%）、差异 1 件（+16,711,118 恰为被剔段）、不存在 **4,352 件/709,757,429 B（98.53%）**。

ND2. 🔴 **F29 待办④有一项是伪前提（R138 新发现）.** 「6 个桩体」**不在 F29 正文任何一列** —— 实测全表四列检索命中 0，它是 R135 审计自报的中间数字。故待办④四项实为三项在正文 + 一项伪前提；本轮只补正文里的三处（两份拷贝=全镜像 80 次中的两份、idx 三口径 62/63/64、40 次与 63/77 互不构成因果），**不为伪前提改正文**。

NE2. ✅ **F35 补定义缺一手权威.** `proved_strict` 定义只有二手转述，一手 `PANEL.md`（M52）不在现盘；本条 evidence_paths 唯一一项即该已失文件 ⇒ 与 F23 并列为本表两条整行证据链失联项。

NF2. ✅ **规则 D：两家 succeeded，三条异议由我逐条复算.** 开局 `MAX_SUBAGENTS=3`（1768 MB），并发 2 未超上限。hy4 执行员 **#301 succeeded**（12 回合/2.62 分/无 OVERTIME）、deepseek 审计员 **#302 succeeded**（17 回合/3.97 分/无 OVERTIME），两家四项数字与主会话**逐项一致**。三条异议：① 「13 复现不出」**被推翻** —— 它未排除 R137 自述里对同一等式的 4 处元复述，按「去假样本+去自述」口径实测恰 **13/9 键/冗余 4**，三口径 20/17/13 均可复现；② 「F24 仓库根解析全 missing」**无冲突**（rel 不带 `lead/` 前缀）；③ 「三桶求和是字典恒等式、无判别力」**成立且我接受**，有判别力的是三桶各自等于预期值与差异件字节差。

NG2. ✅ **落盘.** FACT_INDEX **v5.33**：61,822 -> **66,661 B**，9 处单元格改动，未改动 **51 行逐字节相同**，grade/evidence_paths 两列一字未动，全 LF 55 行；源版本 v5.32 未被修改。门禁改四处（C16_FLOORS 加 142、GATE_VER R138、DISC_RECHECK 第 21 行、DISC_UNVERIFIABLE 第 11 行），全为容纳新节+同步+重钉、**不改判据语义**。

NH2. 📌 **未取得（不粉饰）.** ① F23 计数层仍不可重数；② 余 1 行属哪类不可判；③ F35 的 n 取法仍只在已失文件里；④ 86.19% 来源机制仍未定（只证到前缀切分）；⑤ 4,352 件在快照里、本机取不到；⑥ 窗口表 r66 后快照仍无；⑦ 35 个静态容器运行期值；⑧ 已判死线继续不投。

NI2. 📌 **自错四条（全由断言/回读抓出，未进结论）.** S-262 表头行被当事实项（54->55）；**S-263 版本自指错** —— F35 追加段写「v5.32 里与 F23 并列」，而该行写入后已在 v5.33 内，由回读复查发现，`r138d` 修正（18 项断言全 PASS）；S-264 `one_time()` append 分支仍去 `count(None)` 抛 TypeError；S-265 「86.19% 不再出现」断言与「保留撤回记录」自相矛盾，改为「每次出现须紧跟撤下声明」。

NJ2. ✅ **收口.** 断言 r138a 36 + r138b 25 + r138c 52 + r138d 18 = **131 项 131 PASS / 0 FAIL**（子代理侧 #301 自报 25 项、#302 自报 4 项不计入）。终态 `check_disc.py` exit 0、C10 ok(R138)。五项 CR 全绿。全程未对整段 `.text` 开 `detail=True`（本轮只做纯字节搜索）；脚本均带 timeout；收口前 `ps` 确认无孤儿。
'''


BOARD_SEC = u'''
## 🟢 R17 第 138 轮（2026-11-26 19:3x–19:5x）· FACT_INDEX v5.32 -> v5.33 四条正文修订落盘：F23 分解不闭合（6+2+3=11 vs 12）+ 计数层已失、F24 撤下 86.19% 但保留结构判据 + 补语料值失效期、F29 两处作用域、F35 定义缺一手权威

> 结论先行：R136/R137 两轮把四条正文缺陷都测成「只登记不改正文」，本轮做成**内容变更 + 门禁回归**。改前先证 FACT_INDEX 不被 `check_disc.py` 钉住（命中 0，改后仍 exit 0）。**F29 待办④发现一项伪前提**：「6 个桩体」不在 F29 正文任何一列，是 R135 审计自报的中间数字。

### 一 · F23 补两处

**分解不闭合**：原文三个分项 6（否定式）+2（callers 计数）+3（真正非否定多计）= **11**，与 total=**12** 差 **1 行**，该行没有归属。换读法（把「3 行本已在 W 内」当另一批）得 6+2+3+3=14>12 出现重计 ⇒ **两种读法都得不到 12，缺口对读法不敏感**。

**计数层不可重数**：458/291/293/1196/12/2/9 与分母 1654 依赖 `coverage.tsv`（4,147,334 B / 18,498 行 / 8 列），该文件不在现盘 —— 文件名精确命中 **0**、按 4,147,334 B 精确字节反查命中 **0**，`COVERAGE/`、`R17_DELIVERY/`、`R17_R41_RECOMPUTE/` 三目录均不存在；11-22 快照有 4 条记录 ⇒ 曾存在、现失。**能证的只有算术闭合。**

### 二 · F24 撤数留判据（两项分开是本轮方法要点）

| 项 | 处置 | 依据 |
|---|---|---|
| 「86.19% 盘上无任何字节对应」 | **撤下**（三处出现逐处改） | R136 三实现实测 **99.992%（1,392,481/1,392,592）有对应**；未命中 111 条 111/111 落在前一指令起始 +1..8 内 |
| 「单列地址、无可回原址复核的第二列」 | **保留** | 与 86.19% 独立，本轮未否 ⇒ `bounds` 仍剔 |
| 语料值失效期 | **补入** | 4,417/737,517,286 B 是 **11-22 快照值** |

现盘实测（主会话 + 执行员 #301 独立同得）：存在且同字节 **64 件 / 26,846,620 B（1.45%）**、存在但字节不同 **1 件**（`a2_sites.json` 清单 913,237 vs 盘 17,624,355，差 **+16,711,118** 恰为被剔段）、不存在 **4,352 件 / 709,757,429 B（98.53%）**。

### 三 · F29 补两处作用域，并纠正一处待办前提

- **「两份拷贝」作用域**：17 字节序列在 `.text` 全镜像实测 **80 次**，正文指其中两份 ⇒ 不可读成「全镜像只有两份」。
- **「FirstThunk idx=62」口径**：组内 0-based **62** / 全局 0-based **63** / 全局 1-based **64**，三口径互不相同（pefile 实测，Hint=432 同得）⇒ 62 只在 DLL 内口径为真。
- **40 次与 63/77 互不构成因果**：77 mod 40=37、77−40=37，无可推关系。
- **伪前提纠正**：「6 个桩体」实测**不在 F29 正文任何一列** ⇒ R137 待办④四项实为三项在正文 + 一项伪前提，**不为伪前提改正文**。

### 四 · F35 补定义缺一手权威

`proved_strict`（= atlas 内 [已证] 且语义栏不含 [未证]）的定义**只有二手转述**：一手 `PANEL.md`（M52）不在现盘。本条 evidence_paths 唯一一项即该已失文件 ⇒ 与 F23 并列为本表两条整行证据链失联项。

### 五 · 规则 D 与口径分歧

| task | 家族 | 角色 | 状态 | 回合 | 耗时 | OVERTIME |
|---|---|---|---|---|---|---|
| #301 | hy4 | exec | succeeded | 12 | 2.62 分 | 无 |
| #302 | deepseek | audit | succeeded | 17 | 3.97 分 | 无 |

开局 `MAX_SUBAGENTS=3`（1768 MB），并发 2 未超上限。两家四项数字与主会话**逐项一致**。审计员三条异议由我逐条复算：

1. 「13 处出现复现不出」→ **被推翻**。它把 17 当真实判据式，未排除 R137 自述里对同一等式的 **4 处元复述**；按「去假样本 + 去自述」口径实测恰 **13 处 / 9 键 / 冗余 4**，与 R137 登记逐字吻合（三口径 20 全量 / 17 去假样本 / 13 去假样本+去自述均可复现）。
2. 「F24 按仓库根解析得 4,417 全 missing」→ **无冲突**（rel 列不带 `lead/` 前缀，正确根是 `lead/`）。
3. 「三桶求和是字典恒等式、无判别力」→ **成立且已接受**；有判别力的是三桶各自等于预期值、以及唯一差异件字节差 == 16,711,118。

### 六 · 落盘与门禁

FACT_INDEX **v5.32 -> v5.33**：61,822 -> **66,661 B**，**9 处**单元格改动，未改动的 **51 行逐字节相同**，`grade` 与 `evidence_paths` 两列一字未动，全 LF、55 行；源版本 v5.32 未被修改。

门禁改**四处**，全为容纳新节 + 同步 + 重钉，**不改任何判据语义**：① `C16_FLOORS` 加 `142: <半量>` 并重钉摘要；② `GATE_VER` R137 -> R138；③ `DISC_RECHECK` 第 21 行登记式同步；④ `DISC_UNVERIFIABLE` 第 11 行锚同步。改后 `check_disc.py` **exit 0**、C10 ok(R138)。

### 七 · 未取得（不粉饰，禁写元审计待办）

1. **F23 计数层仍不可重数** —— 本轮只补「不可重数」这个事实，没有、也无法重数那 9 个数。
2. **F23 那余 1 行属哪一类不可判** —— 逐行归类依赖已失的表。
3. **F35 的 `n`（atlas 内分母）取法仍只在已失文件里** —— 只证了两个 ceil 式的算术。
4. **F24 的 86.19% 来源机制仍未定** —— 只证到「来自某种按地址的前缀切分」，本轮不编机制。
5. **F24 语料值无法还原成现盘体量** —— 4,352 件在快照里，本机取不到。
6. 窗口表扩展仍需 r66 以后主快照，一份都没有。
7. 35 个静态容器的运行期元素值与计数。
8. 已判死线继续不投。

### 八 · 自错四条（全由断言/回读抓出，未进结论）

S-262 首版 `r138a` 把表头行当事实项（54->55），断言当场报错。**S-263 版本自指错** —— v5.33 首次写入时 F35 追加段写「故 F35 是 **v5.32** 里与 F23 并列的…」，而该行写入后已在 v5.33 内，由回读复查发现，`r138d` 修正（18 项断言全 PASS）。S-264 `one_time()` 的 append 分支仍去 `count(None)` 抛 TypeError。S-265 「86.19% 不再出现」这条断言首版写成全串不出现，与「保留撤回记录」自相矛盾（撤回记录必须引用原串），改为「每次出现都必须紧跟『撤下原「』」。

### 九 · 下轮优先（禁写元审计待办）

1. **F23 若需真正重数** —— 须先定位或重建 `coverage.tsv`（4,147,334 B / 18,498 行 / 8 列）与 `function_atlas.tsv`（427,038 B）；否则只能保持「算术闭合、计数不可重数」。
2. **F35 的 `n` 取法**（atlas 内分母）—— 一手权威 PANEL.md M47/M52 已失，须从其他在盘产物反推或标注永久不可核验。
3. **F24 的 86.19% 来源机制** —— 去找那个「按地址前缀切分」的真实出处，不要再用「存在切点使前缀等于 k」这种对任意 k 恒成立的问法。
4. **F29 余下措辞** —— 本轮已补两处作用域，正文其余数字（63/77、64/77、74/77）尚无作用域声明，可按同法逐条核。
5. C7 的 exists / bytes= / none 三个死分支已被 C7b 钉住但仍零覆盖，去找能自然走到它们的真实行。
6. 32 条「部分失联」事实项已由外部调研分三档（仍可核验 5 / 需重建 18 / 不可核验 9，主会话复算 fid 集合与三档计数全对），逐条重建工作尚未开始。
'''


# ==================== 主流程 ====================

def main():
    W('# R138 四件套 + 门禁同步%s' % ('  [DRY]' if DRY else ''))
    W()

    # ---------- 1. R14_COMMON 2.142 ----------
    W('= 1 · R14_COMMON 新增 2.142 =')
    rc_b = open(RC, 'rb').read()
    ck('R14_COMMON 旧 CR == 1081', rc_b.count(b'\r') == 1081, rc_b.count(b'\r'))
    rc_t = rc_b.decode('utf-8')
    ck('2.142 尚不存在', '## 2.142 ' not in rc_t)
    ck('2.141 在场且为末节', '## 2.141 ' in rc_t and
       rc_t.rindex('## 2.141 ') > rc_t.rindex('## 2.140 '))
    new_rc = rc_t.rstrip('\n') + '\n\n' + R14_SEC
    if not new_rc.endswith('\n'):
        new_rc += '\n'
    rc_nb = new_rc.encode('utf-8')
    ck('新 R14_COMMON CR 仍 1081', rc_nb.count(b'\r') == 1081, rc_nb.count(b'\r'))
    # 与门禁逐字同口径：^##\s+2\.(\d+)\b（\b 容纳「## 2.142 R138：」这类全角冒号紧随的写法）
    rc_s = rc_nb.decode('utf-8')
    secs = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', rc_s)]
    ck('2.x 节数 135 -> 136', len(secs) == 136, len(secs))
    ck('末节为 142', secs[-1] == 142, secs[-1])
    ck('2.x 编号无缺号', [i for i in range(min(secs), max(secs) + 1)
                    if i not in secs] == [], 'gap')
    # 计算本节的字节数（供 C16 半量重钉）：与门禁同法，取标题行到下一个 2.x 标题前
    _cur, _bufs, _sizes = None, [], []
    for _l in rc_s.split('\n'):
        _m = re.match(r'^##\s+2\.(\d+)\b', _l)
        if _m:
            if _cur is not None:
                _sizes.append((_cur, len('\n'.join(_bufs).encode('utf-8'))))
            _cur, _bufs = int(_m.group(1)), [_l]
        elif _cur is not None:
            _bufs.append(_l)
    if _cur is not None:
        _sizes.append((_cur, len('\n'.join(_bufs).encode('utf-8'))))
    sec_bytes = dict(_sizes)[142]
    half = sec_bytes // 2
    W('  2.142 正文 %d B -> C16 半量下界 %d' % (sec_bytes, half))
    ck('半量 > 0 且 < 全量', 0 < half < sec_bytes, (half, sec_bytes))
    ck('半量下界不会误伤（>= 1155 现最小 margin 量级）', half > 0, half)

    # ---------- 2. 台账 §1192 ----------
    W('= 2 · 台账新增 §1192 =')
    led_b = open(LED, 'rb').read()
    ck('台账旧 CR == 337', led_b.count(b'\r') == 337, led_b.count(b'\r'))
    led_t = led_b.decode('utf-8')
    ck('§1192 尚不存在', '## §1192 ' not in led_t)
    ck('§1191 在场', '## §1191 ' in led_t)
    new_led = led_t.rstrip('\n') + '\n\n' + LEDGER_SEC
    if not new_led.endswith('\n'):
        new_led += '\n'
    led_nb = new_led.encode('utf-8')
    ck('新台账 CR 仍 337', led_nb.count(b'\r') == 337, led_nb.count(b'\r'))
    led_secs = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)',
                                           led_nb.decode('utf-8'))]
    # 台账历史上有 2 处缺号（1026/1028）与 2 处重号（623/625），故**不能**断言编号连续。
    # 只断言本轮该管的：节数 +1、末节号为 1192、且 1192 恰出现一次、既有编号集合未被改动。
    old_led_secs = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)', led_t)]
    ck('§ 节数 %d -> %d' % (len(old_led_secs), len(old_led_secs) + 1),
       len(led_secs) == len(old_led_secs) + 1, len(led_secs))
    ck('末节 §1192', led_secs[-1] == 1192, led_secs[-1])
    ck('1192 恰好出现 1 次', led_secs.count(1192) == 1, led_secs.count(1192))
    ck('既有 § 编号序列一字未动（本轮只在尾部追加）',
       led_secs[:len(old_led_secs)] == old_led_secs)
    W('  台账既有缺号 %s、重号 %s —— 属历史遗留，本轮不改（改编号是另一件事）'
      % ([i for i in range(min(old_led_secs), max(old_led_secs) + 1)
          if i not in old_led_secs],
         sorted(k for k, v in __import__('collections').Counter(old_led_secs).items()
                if v > 1)))

    # ---------- 3. LEAD_LOCK ----------
    W('= 3 · LEAD_LOCK 新增段 =')
    lk_b = open(LOCK, 'rb').read()
    ck('LEAD_LOCK 旧 CR == 137', lk_b.count(b'\r') == 137, lk_b.count(b'\r'))
    lk_t = lk_b.decode('utf-8')
    ck('MZ3 段尚不存在', 'MZ3. ' not in lk_t)
    new_lk = lk_t.rstrip('\n') + '\n' + LOCK_SEG
    if not new_lk.endswith('\n'):
        new_lk += '\n'
    lk_nb = new_lk.encode('utf-8')
    ck('新 LEAD_LOCK CR 仍 137', lk_nb.count(b'\r') == 137, lk_nb.count(b'\r'))
    ck('新段 10 个段首码在场',
       sum(1 for c in ('MZ3', 'NA2', 'NB2', 'NC2', 'ND2', 'NE2', 'NF2', 'NG2',
                       'NH2', 'NI2', 'NJ2') if (c + '. ') in lk_nb.decode('utf-8')) == 11)

    # ---------- 4. STATUS_BOARD ----------
    W('= 4 · STATUS_BOARD 新增第 138 轮 =')
    br_b = open(BRD, 'rb').read()
    ck('看板旧 CR == 0', br_b.count(b'\r') == 0, br_b.count(b'\r'))
    br_t = br_b.decode('utf-8')
    ck('第 138 轮段尚不存在', 'R17 第 138 轮' not in br_t)
    old_lines = br_t.count('\n')
    W('  看板当前 %d 行' % old_lines)
    add_lines = BOARD_SEC.count('\n')
    W('  本轮追加 %d 行；写后预计 %d 行' % (add_lines, old_lines + add_lines))
    # 归档判据：当前 + 本轮 必须 <= 300
    need_archive = (old_lines + add_lines) > 300
    W('  需要先归档？%s（判据：当前 + 本轮 <= 300）' % need_archive)

    new_brd = br_t.rstrip('\n') + '\n\n' + BOARD_SEC
    if not new_brd.endswith('\n'):
        new_brd += '\n'
    br_nb = new_brd.encode('utf-8')
    ck('新看板 CR 仍 0', br_nb.count(b'\r') == 0, br_nb.count(b'\r'))
    ck('新看板行数 %d <= 300' % br_nb.count(b'\n'), br_nb.count(b'\n') <= 300,
       br_nb.count(b'\n'))
    ck('新看板含第 138 轮段', u'R17 第 138 轮' in new_brd)
    ck('新看板保留第 137 轮段', u'R17 第 137 轮' in new_brd)

    # ---------- 5. 门禁 ----------
    W('= 5 · 门禁同步 =')
    gate_b = open(GATE, 'rb').read()
    gate_t = gate_b.decode('utf-8')
    ck('GATE_VER 当前为 R137', "GATE_VER = 'R137'" in gate_t)
    ck('C16_FLOORS 无 142 条目', '142:' not in gate_t.split('C16_FLOORS_SHA256')[0])
    old_c16_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gate_t).group(1)
    ck('C16_FLOORS_SHA256 当前 192795a2…', old_c16_sha.startswith('192795a2'),
       old_c16_sha[:16])

    if DRY:
        W()
        W('--dry：全部断言跑完，不写盘。')
        W('  2.142 正文 %d B，C16 半量 %d' % (sec_bytes, half))
        W('  预期终态：R14_COMMON %d B、台账 %d B、LEAD_LOCK %d B、看板 %d 行'
          % (len(rc_nb), len(led_nb), len(lk_nb), old_lines + add_lines))
        W()
        W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
        for f in fails:
            W('  FAIL: ' + f)
        return 0 if not fails else 1

    # ==================== 实际写入 ====================
    W('= 6 · 写四件套（备份 -> 断言 -> 写入 -> 回读） =')
    plan = [(RC, rc_b, rc_nb, 'R14_COMMON'), (LED, led_b, led_nb, 'LEDGER'),
            (LOCK, lk_b, lk_nb, 'LEAD_LOCK'), (BRD, br_b, br_nb, 'STATUS_BOARD')]
    for path, old_b, new_b, tag in plan:
        p = os.path.join(BASE, os.path.basename(path) + '.before_R138_%s_%s.bak'
                         % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份 wx 独占创建且 sha 一致' % tag,
           sha(open(p, 'rb').read()) == sha(old_b), p)
        write_atomic(path, new_b)
        rt = open(path, 'rb').read()
        ck('%s 回读 sha 一致' % tag, sha(rt) == sha(new_b))
        ck('%s 回读字节数 %d' % (tag, len(new_b)), len(rt) == len(new_b))

    # 回读后的 CR 断言
    ck('R14_COMMON 终态 CR == 1081', open(RC, 'rb').read().count(b'\r') == 1081,
       open(RC, 'rb').read().count(b'\r'))
    ck('台账终态 CR == 337', open(LED, 'rb').read().count(b'\r') == 337,
       open(LED, 'rb').read().count(b'\r'))
    ck('LEAD_LOCK 终态 CR == 137', open(LOCK, 'rb').read().count(b'\r') == 137,
       open(LOCK, 'rb').read().count(b'\r'))
    ck('看板终态 CR == 0', open(BRD, 'rb').read().count(b'\r') == 0,
       open(BRD, 'rb').read().count(b'\r'))
    brd_final = open(BRD, 'rb').read().count(b'\n')
    ck('看板终态行数 %d <= 300' % brd_final, brd_final <= 300, brd_final)

    # ==================== 门禁同步 ====================
    W('= 7 · 门禁同步 =')
    gate_new = gate_t

    # ① C16_FLOORS 加 142 条目 + 重钉摘要
    old_floor_tbl = u'    137: 3159, 138: 4803, 139: 4118, 140: 4782, 141: 2548,\n}'
    new_floor_tbl = (u'    137: 3159, 138: 4803, 139: 4118, 140: 4782, 141: 2548,\n'
                     u'    142: %d,\n}' % half)
    ck('C16_FLOORS 末行形态唯一可定位',
       gate_new.count(old_floor_tbl) == 1, gate_new.count(old_floor_tbl))
    gate_new = gate_new.replace(old_floor_tbl, new_floor_tbl)
    # 重算摘要（与门禁同法：逐 id:floor 规范化）
    m = re.search(r'C16_FLOORS = \{(.*?)\n\}', gate_new, re.S)
    tbl = {}
    for mm in re.finditer(r'(\d+):\s*(\d+)', m.group(1)):
        tbl[int(mm.group(1))] = int(mm.group(2))
    ck('新表 136 条目（135 -> 136）', len(tbl) == 136, len(tbl))
    ck('新表含 142 且值 == %d' % half, tbl.get(142) == half, tbl.get(142))
    norm = '\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl))
    new_floor_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
    W('  C16_FLOORS_SHA256 %s -> %s' % (old_c16_sha[:16], new_floor_sha[:16]))
    gate_new = gate_new.replace(
        "C16_FLOORS_SHA256 = '%s'" % old_c16_sha,
        "C16_FLOORS_SHA256 = '%s'" % new_floor_sha)
    ck('摘要常量已替换', new_floor_sha in gate_new)

    # ② GATE_VER
    gate_new = gate_new.replace("GATE_VER = 'R137'", "GATE_VER = 'R138'")
    ck('GATE_VER -> R138', "GATE_VER = 'R138'" in gate_new)

    # ③ DISC_RECHECK 第 21 行同步（id=20 的 grep 式子）
    dr_b = open(DR, 'rb').read()
    dr_t = dr_b.decode('utf-8')
    ck('DISC_RECHECK 旧 GATE_VER 式子在场', "grep=(?m)^GATE_VER = 'R137'" in dr_t)
    dr_new = dr_t.replace("grep=(?m)^GATE_VER = 'R137'",
                          "grep=(?m)^GATE_VER = 'R138'")
    ck('DISC_RECHECK 只改 1 处',
       dr_new != dr_t and
       dr_new.count("grep=(?m)^GATE_VER = 'R138'") == 1)

    # ④ DISC_UNVERIFIABLE 第 11 行锚同步
    du_b = open(DU, 'rb').read()
    du_t = du_b.decode('utf-8')
    ck('DISC_UNVERIFIABLE 旧锚在场', "grep=(?m)^GATE_VER = 'R137'" in du_t)
    du_new = du_t.replace("grep=(?m)^GATE_VER = 'R137'",
                          "grep=(?m)^GATE_VER = 'R138'")
    ck('DISC_UNVERIFIABLE 只改 1 处',
       du_new.count("grep=(?m)^GATE_VER = 'R138'") == 1)

    # 写门禁三件
    for path, old_b, new_t, tag in ((GATE, gate_b, gate_new, 'GATE'),
                                    (DR, dr_b, dr_new, 'DISC_RECHECK'),
                                    (DU, du_b, du_new, 'DISC_UNVERIFIABLE')):
        new_b = new_t.encode('utf-8')
        p = os.path.join(BASE, os.path.basename(path) + '.before_R138_%s_%s.bak'
                         % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份 sha 一致' % tag,
           sha(open(p, 'rb').read()) == sha(old_b))
        write_atomic(path, new_b)
        ck('%s 回读 sha 一致' % tag, sha(open(path, 'rb').read()) == sha(new_b))

    W()
    W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
    W('C16 half floor = %d, C16_FLOORS_SHA256 = %s' % (half, new_floor_sha))
    W('R14_COMMON %d B / 台账 %d B / LEAD_LOCK %d B / 看板 %d 行'
      % (len(rc_nb), len(led_nb), len(lk_nb), brd_final))
    for f in fails:
        W('  FAIL: ' + f)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
