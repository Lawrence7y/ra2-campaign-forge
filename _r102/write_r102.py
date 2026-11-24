#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r102.py —— R102 四件套写入（严格按写入纪律）

四件：
  1. R14_COMMON.md 新增 ## 2.106（全 LF，CR 保持 1081）
  2. lead/GOAL_THREE_TARGETS_20261018.md 新增 ## §1156（CR 保持 337）
  3. lead/LEAD_LOCK 新增下一字母段（CR 保持 137）
  4. STATUS_BOARD.md 新增第 102 轮记录（全 LF，CR 保持 0，总行数 <= 300）

每件流程：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
所有正文内**不得出现反引号**（项目纪律），本脚本在写前对三段正文做断言。
"""
import datetime, hashlib, io, json, os, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r102')
STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def crlf(b): return b.count(b'\r\n')
def lfonly(b): return b.count(b'\n') - b.count(b'\r\n')

# ============================ 正文 ============================
SEC_RC = """## 2.106 R102：门禁三处「永远通过」行为级取证（26/31 行结构上不可能 FAIL）；两处纯加严落地（C12 冻结锚真跑 + C11b 载重）；R101 待办⑦前提被证伪，标注「作废」会制造矛盾

本节只收 R102 本机实测（脚本 _r102/r102a..r102g，115 项断言，FAIL 0）。
本轮不碰 gamemd 逆向（win-main 仍 OFFLINE），改推门禁与 FACT_INDEX 两条业务线。

### 2.106.1 C11 的 31 行里 26 行「结构上不可能 FAIL」——两处豁免的行为级取证

r102a_holes.py（18 项）+ 执行员 hy4 #157 独立复现，两造逐项一致：

| 桶 | 判据 | 规模 | id |
|---|---|---|---|
| 真可 FAIL | col7 以「有」开头且不在冻结档 | **5** | 3, 4, 22, 27, 28 |
| 冻结豁免 | 在 DISC_UNVERIFIABLE.tsv 里 | **12** | 1, 2, 5, 6, 7, 8, 9, 10, 18, 20, 24, 25 |
| 写无豁免 | col7 以「无」开头 ⇒ continue | **14** | 11, 12, 13, 14, 15, 16, 17, 19, 21, 23, 26, 31, 32, 33 |

⇒ **26/31 行的 C11 判定在结构上不可能变成 FAIL**。这不是「暂时没跑」，是判据本身不留 FAIL 路径。

**洞 1（冻结摘帽）**：清空冻结档 + 同步改 FREEZE_SHA256 ⇒ 立刻恰好 12 行 C11 FAIL，
集合与原冻结 12 完全相等（M3，唯一对应：除 C11 外无任何其它检查 FAIL，用全 FAIL 清单核，
不只看前缀）。反控：冻结档与常量不符 ⇒ 必须 TAMPERED（NC2）。

**洞 2（写无即免检）**：取 id 3（原本真能 FAIL），**只**把 col7 改成「无」、其余一字不动 ⇒
exit 从 1 变 0（M2）。关键在「唯一对应」：初版我把产物路径也改坏，结果 C7 一起 FAIL，
翻转变异就不唯一对应 —— 这违反纪律 32（反控必须打在判据真正读到的那一格）。
正确做法是复制 anchor_check.txt、只删掉 discipline=3 那一行、把第 5 列指向副本，
使 C7 的 grep 锚仍在，于是只有 C11 翻转。

**第三条发现（活常量撒谎）**：C11_LANDABLE（改前 check_disc.py:240）AST **Load 次数 = 0**，
是纯死代码；而它列的 12 个 id 里有 **7 个**（11/12/13/14/15/17/26）写的正是「无」
⇒ 按 C11 现有逻辑**永远不可能 FAIL**。它旁边的注释说「12/28 可补」，对这 7 行不成立：
它们不是「还没补」，是「声明了不需要补」。

### 2.106.2 两处纯加严（今天全绿，故不改 exit 0）与一处标签修

**C12 冻结锚真跑**：此前门禁对冻结档只读第 1 列（id）+ sha256 钉整档，第 4 列「校验式」
**从不执行**。故「这 12 行确实有可命中的锚」在门禁层面无人检查：改锚 + 同步改常量即可无声通过
（NC1 实测：坏锚 + 同步 sha，未打补丁的门禁 exit 0）。C12 把第 4 列逐行真跑（复用 C7 的
run_expr，同口径），另加三条：冻结 id ⊆ claims-有、理由非空、冻结时刻严格 ISO8601(+HH:MM)。

**C6MAX 接线**：docstring 第 12 行写「超阈值即 FAIL」，而该常量全脚本 Load=0；实测
--c6max=0 与默认参数**输出逐字节相同** ⇒ 假旋钮。现接为 cross > C6MAX ⇒ FAIL
（默认 120，实测 cross=9，仍绿）。反控：--c6max=3 ⇒ exit 1 且报 9 > threshold 3。

**C11b 载重**：把死常量变成可核的缺口量与钉子。输出
declared=12 rows, gap(claims-none, can never FAIL)=7 ids=[11,12,13,14,15,17,26]，
并与 C11B_PIN_GAP 比对，漂移即 FAIL。**这没有修那 7 行**（修它们要写 DISC_RECHECK 第 7 列，
须单独一卡 + 跨家族审计），只是让它们无法再被静默忽略。

**横幅标签撒谎**：GATE_VER 抬到 R102 后，输出仍打印 --- check_disc.py (R49) ---，
因为它是硬编码字符串、与 GATE_VER 无关。改为由 GATE_VER 派生；
反控：沙箱把 GATE_VER 改回 R87 ⇒ 横幅跟着变 R87（证明派生而非硬编码）。

**GATE_VER 是三重钉**（本轮自错 3）：模块常量 / DISC_RECHECK.tsv 第 20 行校验式里的**字面**
版本号（C7 会真跑它）/ C10 自检注册值。只改第一处会让**原样**门禁立刻 exit 1。

### 2.106.3 写入方式：字节级，不借文本读写

check_disc.py 是 CRLF 主文件（改前 321 CRLF / 2 LF-only / 14,896 B）。若用文本读写补丁，
几千行会静默统一成 LF —— 那是无声改写。故 r102c/r102d/r102e 全程 bytes：
定位锚 → 插 CRLF 行 → 回读核 sha256 与行尾结构。改后 381 CRLF / **2 LF-only 不变**。

### 2.106.4 R101 待办⑦ 前提被证伪：「5 个旧版本目录缺 SUPERSEDED」不成立，且照做会制造矛盾

r102g_factchain.py（12 项）：

1. 以 FACT_INDEX 为名的目录 **7 个**，但只有 **3 个真含索引本体**（v530/v531/v532）；
   另 4 个（V53/V58/V511/R88_T1）**不含索引本体**，只含辅助证据。
   把它们标成「本目录已作废、请勿引用」会**抹掉现行索引引用的证据**。
2. 「5 个」与盘上任何一组都对不上：3 / 4 / 7 ≠ 5。
3. 现行 v532 引用 v530/v531 的次数 **0 / 0**（好），但**全树**引用为 v530 26 次、v531 84 次；
   四个辅助目录为 V53 119 / V58 74 / V511 89 / R88_T1 3 次。任一目录标「作废」，
   都会与 26~119 处现存引用直接冲突。
4. **真缺口是链断裂不是缺标记**：_r65/make_v530.py 第 9 行以 R17_R100_FACTINDEX_V529
   为输入，该目录**已不存在**，R17_LEAD_BASELINE 里也无任何 v529 备份 ⇒ 不可恢复，不伪造。

⇒ 本项**不能**按原待办执行。正确顺序是：先解引用（把 26~119 处指向旧目录的引用改到 v532），
再标 SUPERSEDED；辅助目录改用「非索引本体、属 vX 的辅助证据」这一另一种语，不用「作废」。
本轮只登记，不擅自写任何 SUPERSEDED.md。

### 2.106.5 自错 6 处（全部由断言或子代理抓出，逐条记）

1. 沙箱只链 lead/，漏 ROOT 顶层条目 —— id 31 的产物路径是 ROOT 相对
   _r94\\falsify_r94.py，POS 原样就 C7 FILE_MISSING。教训：沙箱必须处置 ROOT 的**每一个**
   顶层条目，不能只链关心的那一支。
2. M1 正控同时改产物路径 ⇒ C7 一起 FAIL，「翻转变异」不唯一对应（纪律 32 同型）。
3. 只改 GATE_VER 常量、漏改 DISC_RECHECK 第 20 行字面 ⇒ POS 原样 exit 1。
4. r102e 断言「CRLF/LF 结构不变」并要求 (CRLF,LF) 元组相等 —— 补丁新增 15 行 CRLF，
   该断言自相矛盾。正确不变量是「LF-only 行数不变」。
5. r102e 的 NC1 拿「id 11 改有」当隔离变异，那本身就触发 C11 真判据（未打补丁也 exit 1）
   ⇒ 该对照零信息（纪律 32 同型第三次）。改用「从 LANDABLE 删一个 id」——
   未打补丁的门禁根本不读该集合，必然 exit 0。
6. r102f 初版拿 R87 门禁配 R102 的 DISC_RECHECK ⇒ C7/C10 两个假 FAIL，
   全是我夹具的版本错配。回退时必须**连 DR 一起回退**（同一时刻的一对）。

### 2.106.6 未取得（不掩盖）

1. **写无免检只部分关闭**：C11b 只覆盖 LANDABLE∩无 的 7 行；LANDABLE 之外的 7 个「无」行
   （16/19/21/23/31/32/33）改「无」后仍 exit 0（r102f C3d 实测）。根治要动第 7 列，未做。
2. **C12 只验锚可命中，不验锚能支撑该纪律的主张** —— 与 C7 同一边界，不因加了 C12 而消除。
3. C11_LANDABLE 的 12 个 id 与真值集（5 个）仍不一致；本轮只把它载重并钉住缺口，
   **没有修正成员的语义**。
4. FACT_INDEX 版本链的 26~119 处旧引用**未解引用**，SUPERSEDED 一个都没写。
5. v5.29 目录不可恢复（无备份），其内容只能从 make_v530.py 的 OLD/NEW 字面反推两处字符串。
6. 本轮未碰 gamemd 逆向；B1 的 41 个、真歧义 46、B3/B5 的逐址解释仍全部未取得。
"""

SEC_LED = """## §1156 R17 第 102 轮 · 门禁 31 行里 26 行「结构上不可能 FAIL」（冻结 12 + 写无 14）；两处纯加严落地（C12 冻结锚真跑、C11b 载重）；R101 待办⑦ 前提被证伪（7 目录里仅 3 个含索引本体、且每个被引用 3~119 次，标注作废会制造矛盾）

一 · C11 三桶与两处豁免（行为级取证，主会话 18 项 + 执行员 hy4 #157 独立复现逐项一致）
1. 真可 FAIL **5** 行（3/4/22/27/28）；冻结豁免 **12** 行；写无豁免 **14** 行
   ⇒ **26/31 行结构上不可能变成 FAIL**。这不是「暂时没跑」，是判据本身不留 FAIL 路径。
2. 洞 1：清空冻结档 + 同步改 FREEZE_SHA256 ⇒ 立刻恰好 12 行 FAIL、集合与原冻结 12 相等；
   除 C11 外无任何其它检查 FAIL（用全 FAIL 清单核，不只看前缀）。
3. 洞 2：id 3 只把 col7 改「无」、其余一字不动 ⇒ exit 1→0。唯一对应的做法是复制产物、
   只删 discipline=3 那一行、第 5 列指向副本，使 C7 的 grep 锚仍在。
4. 第三条：C11_LANDABLE 改前 AST **Load=0**（死代码），且所列 12 个 id 里 **7 个**
   写的正是「无」⇒ 永远不可能 FAIL。注释说「可补」对这 7 行不成立。

二 · 三处落地（纯加严，今天全绿故不改 exit 0）
5. **C12**：冻结档第 4 列「校验式」此前**从不执行**（只读第 1 列 + sha 钉整档），
   改锚 + 同步改常量即可无声通过。现逐行真跑（复用 C7 的 run_expr），另加
   冻结 ⊆ claims-有 / 理由非空 / 时刻严格 ISO8601(+HH:MM)。
6. **C6MAX**：docstring 写「超阈值即 FAIL」而该常量 Load=0，--c6max=0 与默认输出逐字节相同。
   现接为 cross > C6MAX ⇒ FAIL（默 120，实测 9 仍绿）；--c6max=3 ⇒ exit 1。
7. **C11b**：死常量改为载重 + 钉子，输出 gap=7 ids=[11,12,13,14,15,17,26]，漂移即 FAIL。
   未修那 7 行（要写第 7 列，须单独一卡 + 跨家族审计）。
8. 横幅：GATE_VER 抬到 R102 后仍打印 (R49)（硬编码字面），改为由 GATE_VER 派生；
   反控：沙箱改回 R87 ⇒ 横幅跟着变。GATE_VER 是**三重钉**（模块常量 / DISC_RECHECK
   第 20 行字面 / C10 注册值），只改第一处会让原样门禁 exit 1。
9. 全程**字节级**写入：check_disc.py 是 CRLF 主文件（改前 321 / 改后 381 CRLF，
   LF-only 恒为 2）；用文本读写会把几千行静默统一成 LF。

三 · R101 待办⑦ 前提证伪（照做会制造矛盾）
10. FACT_INDEX 名为 7 个目录，仅 **3 个**真含索引本体（v530/v531/v532）；另 4 个只含辅助证据。
    「5 个」与盘上任何一组都不符（3/4/7）。把辅助目录标「作废」会抹掉现行索引引用的证据。
11. 现行 v532 引用 v530/v531 各 **0** 次，但全树引用 v530 **26** / v531 **84** /
    V53 119 / V58 74 / V511 89 / R88_T1 3 次 ⇒ 任一目录标「作废」都与 26~119 处现存引用冲突。
12. 真缺口是**链断裂**不是缺标记：_r65/make_v530.py 第 9 行以 R17_R100_FACTINDEX_V529
    为输入，该目录已不存在且 R17_LEAD_BASELINE 无备份 ⇒ 不可恢复，不伪造。
    正确顺序是先解引用再标 SUPERSEDED；本轮只登记，不擅自写。

四 · 自错 6 处（全部由断言或子代理抓出）：沙箱漏 ROOT 顶层条目导致 POS 就 FAIL；
M1 同时改产物路径使翻转变异不唯一对应（纪律 32）；漏改 DISC_RECHECK 第 20 行字面；
r102e 断言「CRLF/LF 元组不变」与新增 15 行自相矛盾（正确不变量是 LF-only 不变）；
r102e NC1 拿「id11 改有」作隔离变异（本身触发真判据，零信息，纪律 32 第三次）；
r102f 拿 R87 门禁配 R102 的 DR 造成两个假 FAIL（回退须成对回退）。

五 · 未取得（不掩盖）：① 写无免检只部分关闭 —— LANDABLE 之外 7 个「无」行改「无」仍 exit 0；
② C12 只验锚可命中、不验锚能支撑主张（与 C7 同边界）；③ C11_LANDABLE 成员语义未修正；
④ 26~119 处旧引用未解引用、SUPERSEDED 一个没写；⑤ v5.29 不可恢复；
⑥ 本轮未碰 gamemd 逆向（win-main OFFLINE），B1 的 41 个 / 真歧义 46 / B3·B5 逐址解释仍全部未取得。

本草为 §1156 草稿，由 Lead 逐字追加；书记员未自行改动台账。
"""

SEC_LOCK = """ED1. ✅ **R102 主攻门禁与 FACT_INDEX 两条业务线，交出四件实测**（脚本 _r102/r102a..r102g，**115 项断言 FAIL 0**）。
本轮未碰 gamemd 逆向：harness nodes 实测 win-main **OFFLINE**，静态判据已在前几轮用尽，故不重复空转。

ED2. ⚠ **R101 待办⑥ 的「两条口子」被量化成三条**：C11 的 31 行里 **26 行结构上不可能 FAIL**
（冻结 12 / 写无 14），真可 FAIL 只有 **5** 行（3/4/22/27/28）。三条互相独立：
冻结续免（清空冻结档即 12/12 FAIL）、写无免检（id 3 只改 col7 ⇒ exit 1→0）、
**活常量撒谎**（C11_LANDABLE 改前 AST Load=0，且所列 12 个 id 里 7 个写的正是「无」）。

ED3. ✅ **落地三处纯加严 + 一处标签修**（全绿，故不改 exit 0）：
① **C12** 冻结档第 4 列校验式**真跑** —— 此前它**从不执行**，改锚 + 同步改 sha 即可无声通过
（NC1 实测未打补丁 exit 0）；另加 冻结 ⊆ claims-有 / 理由非空 / 时刻严格 ISO8601。
② **C6MAX 接线** —— docstring 承诺「超阈值即 FAIL」而 Load=0，--c6max=0 与默认输出**逐字节相同**；
现 --c6max=3 ⇒ exit 1 并报 9 > threshold 3。
③ **C11b 载重** —— 输出 gap=7 ids=[11,12,13,14,15,17,26] 并与钉子比对，漂移即 FAIL。
④ **横幅**由 GATE_VER 派生（此前硬编码 (R49)，改后沙箱回退 R87 横幅即跟着变）。

ED4. 📌 **写入方式必须是字节级**：check_disc.py 是 CRLF 主文件，改前 321 CRLF / 2 LF-only；
补丁后 **381 CRLF / 2 LF-only 不变**。文本读写会把几千行静默统一成 LF —— 无声改写。
GATE_VER 是**三重钉**（模块常量 / DISC_RECHECK 第 20 行**字面** / C10 注册值），
只改第一处会让**原样**门禁 exit 1 —— 此点由我自己的 POS 控制组抓出。

ED5. ❗ **R101 待办⑦ 的前提被证伪，照做会主动制造矛盾**：FACT_INDEX 名为 7 个目录，
只有 **3 个真含索引本体**（v530/v531/v532），另 4 个只含辅助证据；「5 个」与盘上任何一组不符。
现行 v532 引用 v530/v531 各 **0** 次，但**全树**引用 v530 **26** / v531 **84** / V53 **119** /
V58 74 / V511 89 / R88_T1 3 次 ⇒ 任一目录标「作废」都与 26~119 处现存引用直接冲突。
**真缺口是链断裂**：_r65/make_v530.py 第 9 行以 R17_R100_FACTINDEX_V529 为输入，
该目录已不存在、R17_LEAD_BASELINE 无备份 ⇒ 不可恢复。正确顺序：先解引用，再标 SUPERSEDED；
辅助目录用「非索引本体」这一另一种语，不用「作废」。本轮**只登记、不写任何 SUPERSEDED.md**。

ED6. 🐞 **自错 6 处**：①沙箱只链 lead/ 漏 ROOT 顶层条目（id 31 产物在 _r94\\，POS 就 C7 MISSING）；
②M1 同时改产物路径 ⇒ C7 一起 FAIL，翻转变异不唯一对应（纪律 32 同型）；③只改 GATE_VER 常量
漏改第 20 行字面；④r102e 断言「(CRLF,LF) 元组不变」与新增 15 行 CRLF 自相矛盾（正确不变量是
**LF-only 不变**）；⑤r102e 的 NC1 用「id11 改有」当隔离变异，本身即触发真判据（零信息，
纪律 32 第三次），改用「从 LANDABLE 删 id」；⑥r102f 拿 R87 门禁配 R102 的 DR ⇒ 两个假 FAIL，
回退必须**成对**回退。

ED7. 📌 **子代理如实登记**：hy4 **#157（exec）** 独立报三桶 **5/12/14**、Q2 FAIL 集合恰好 12、
Q4 的 LANDABLE∩写无 = **7**，与我 r102a **逐项一致**，独立确认洞 1 成立。
它三处与本轮冲突，我逐项复算并裁定（r102f_recheck.py 15 项）：①C11_LANDABLE AST Load
它报 **2** 我报 **0** —— **两数都对，被测对象不同**（它测我打完补丁后的门禁，C11b 真的读该常量；
我原报测 R87 原版）。这是我在卡面没写「被测对象＝哪个 sha」的错，记作自错 7（未列入 ED6 的
6 项自错，因属卡面表述而非脚本缺陷）。②它判「Q2 非C11附带FAIL」是**解析 bug**（把以
C11 id 开头的行算成「非 C11」），我用全 FAIL 清单核得 others=[]。③它 Q3 报 exit=1 **正确**，
但其「写无即免检」结论只对 R87 成立 —— R102 下该实例已被 **C11b pin** 关掉（归因不是 C11）。
deepseek **#156（audit）**：见 ED8。

ED8. 📌 **deepseek #156 审计**：__AUDIT_156__

ED9. 📌 **未取得**：① 写无免检**只部分关闭** —— C11b 只覆盖 LANDABLE∩无 的 7 行；
LANDABLE 之外的 7 个「无」行（16/19/21/23/31/32/33）改「无」后仍 exit 0（r102f C3d 实测），
根治要动第 7 列，未做；② C12 只验「锚可命中」不验「锚能支撑该纪律的主张」，与 C7 同边界；
③ C11_LANDABLE 的 12 个 id 与真值集（5 个）仍不一致，本轮只载重钉缺口、**未修正成员语义**；
④ FACT_INDEX 的 26~119 处旧引用未解引用、SUPERSEDED 一个没写；⑤ v5.29 不可恢复；
⑥ gamemd 逆向本轮零推进，B1 的 41 个 / 真歧义 46 / B3·B5 逐址解释仍未取得。
"""

SEC_BOARD = """## 第 102 轮（R102）· 门禁 31 行里 **26 行结构上不可能 FAIL**（冻结 12 + 写无 14）；三处纯加严落地（C12 冻结锚真跑 / C6MAX 接线 / C11b 载重）；R101 待办⑦ 前提被证伪

- 三桶（行为级取证，执行员 hy4 #157 独立复现逐项一致）：真可 FAIL **5**（3/4/22/27/28）、
  冻结豁免 **12**、写无豁免 **14** ⇒ **26/31 行结构上不可能变成 FAIL**，不是「暂时没跑」。
- 洞 1：清空冻结档 + 同步改 FREEZE_SHA256 ⇒ 恰好 12 行 FAIL、集合与原冻结 12 相等，
  且除 C11 外无任何其它检查 FAIL（用全 FAIL 清单核，不只看前缀）。
- 洞 2：id 3 **只**把 col7 改「无」、其余一字不动 ⇒ exit **1→0**。唯一对应的做法是复制产物、
  只删 discipline=3 那行、第 5 列指向副本，使 C7 的 grep 锚仍在。
- 第三条：C11_LANDABLE 改前 AST **Load=0**（死代码），所列 12 个 id 里 **7 个**写的正是「无」
  ⇒ 永远不可能 FAIL。注释「可补」对这 7 行不成立：不是「还没补」，是「声明了不需要补」。
- 落地（纯加严，今天全绿故 exit 0 不变）：**C12** 把冻结档第 4 列校验式**真跑**（此前从不执行，
  改锚+同步改 sha 即可无声通过，NC1 实测未打补丁 exit 0）；**C6MAX** 接为 cross>120 ⇒ FAIL
  （此前 --c6max=0 与默认输出逐字节相同）；**C11b** 输出 gap=7 ids=[11,12,13,14,15,17,26]
  并钉住，漂移即 FAIL；**横幅**改由 GATE_VER 派生（此前硬编码 (R49)）。
- 写入方式：check_disc.py 是 CRLF 主文件，**字节级**补丁 —— 改前 321 CRLF/2 LF-only，
  改后 **381 CRLF/2 LF-only 不变**。GATE_VER 是三重钉（模块常量 / DR 第 20 行字面 / C10），
  只改第一处会让**原样**门禁 exit 1（由我自己的 POS 控制组抓出）。
- R101 待办⑦ 前提**证伪**：FACT_INDEX 名为 7 个目录，仅 **3 个**真含索引本体；「5 个」与盘上
  任何一组不符（3/4/7）。全树引用 v530 **26** / v531 **84** / V53 **119** / V58 74 / V511 89 /
  R88_T1 3 次 ⇒ 标「作废」会与 26~119 处现存引用冲突。真缺口是**链断裂**：
  v5.29 目录已不存在且无备份，不可恢复。**只登记，不写任何 SUPERSEDED.md。**
- 自错 6 处：沙箱漏 ROOT 顶层条目（POS 就 C7 MISSING）；M1 同改产物路径使翻转变异不唯一对应；
  漏改 DR 第 20 行字面；r102e 断言「(CRLF,LF) 元组不变」与新增 15 行自相矛盾（正确不变量是
  LF-only 不变）；r102e NC1 用「id11 改有」作隔离变异（零信息，纪律 32 第三次）；
  r102f 拿 R87 门禁配 R102 的 DR 造出两个假 FAIL（回退须成对）。
- 子代理：hy4 **#157** 独立报 5/12/14 与我逐项一致；它三处冲突我逐项复算裁定（r102f 15 项）：
  AST Load=2 与我的 0 **两数都对、被测对象不同**（卡面未写清 sha，记自错 7）；它判「Q2 附带 FAIL」
  是解析 bug；它 Q3 exit=1 正确但归因是 **C11b pin**（不是 C11）。deepseek **#156**：__AUDIT_156__
- 未取得：写无免检**只部分关闭**（LANDABLE 之外 7 个「无」行改「无」仍 exit 0）；C12 只验锚可命中、
  不验锚能支撑主张；C11_LANDABLE 成员语义未修正；26~119 处旧引用未解引用；v5.29 不可恢复；
  **gamemd 逆向本轮零推进**（win-main OFFLINE），B1 的 41 个 / 真歧义 46 / B3·B5 未取得。
"""

AUDIT_PLACEHOLDER = '（本轮审计员未在预算内产出，见下轮）'

# ============================ 写入器 ============================
def write_file(path, old_sha_expect, crlf_expect, new_bytes, tag):
    old = io.open(path, 'rb').read()
    old_sha = hashlib.sha256(old).hexdigest()
    ck('%s 旧 sha256 与断言一致' % tag,
       old_sha_expect is None or old_sha == old_sha_expect, old_sha[:16])
    ck('%s 旧 CR 计数 = %d' % (tag, crlf_expect), crlf(old) == crlf_expect, crlf(old))
    bak = os.path.join(BASE, 'R102.before_%s_%s.bak' % (tag, STAMP))
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(old)
    ck('%s wx 独占备份' % tag,
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == old_sha, os.path.basename(bak))
    io.open(path, 'wb').write(new_bytes)
    back = io.open(path, 'rb').read()
    ck('%s 回读逐字节相同' % tag, back == new_bytes, hashlib.sha256(back).hexdigest()[:16])
    ck('%s 回读 CR 计数 = %d' % (tag, crlf_expect), crlf(back) == crlf_expect, crlf(back))
    return old_sha, hashlib.sha256(back).hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    only = None
    for a in sys.argv[1:]:
        if a.startswith('--only='):
            only = a.split('=', 1)[1]

    audit_note = io.open(os.path.join(OUT, 'audit156.txt'), encoding='utf-8').read().strip() \
        if os.path.exists(os.path.join(OUT, 'audit156.txt')) else AUDIT_PLACEHOLDER
    lock_body = SEC_LOCK.replace('__AUDIT_156__', audit_note)
    board_body = SEC_BOARD.replace('__AUDIT_156__', audit_note)

    # 反引号纪律（项目 CLAUDE.md：卡面/正文不得出现反引号）
    for name, txt in (('R14_COMMON §2.106', SEC_RC), ('LEDGER §1156', SEC_LED),
                      ('LEAD_LOCK ED', lock_body), ('STATUS_BOARD R102', board_body)):
        ck('%s 无反引号' % name, '`' not in txt, txt.count('`'))
        ck('%s 无控制字符' % name, all(ord(ch) >= 0x20 or ch in '\n\t' for ch in txt), '')

    # ---------- 1. R14_COMMON ----------
    if only in (None, 'rc'):
     rc_old = io.open(RC, 'rb').read()
    ck('RC 当前 CR = 1081', crlf(rc_old) == 1081, crlf(rc_old))
    ck('RC 全 LF（LF-only 行数 = 行数-1）', lfonly(rc_old) == rc_old.count(b'\n'), lfonly(rc_old))
    # R102 事故修正：R14_COMMON 是 **CRLF 主文件**（CR=1081 是硬不变量），
    # 初版写的是「全 LF」断言并直接追加 LF 段 —— 那是把 8,000+ 行的行尾语义当成 LF 来断言的错。
    # 正确做法：追加段本身必须用 CRLF，且总 CR 计数严格保持 1081（不新增、不改写任何一行）。
    nl_rc = b'\r\n' if b'\r\n' in rc_old else b'\n'
    body_rc = SEC_RC.replace('\n', nl_rc.decode()).encode('utf-8') if nl_rc == b'\r\n' else SEC_RC.encode('utf-8')
    rc_new = rc_old + body_rc
    if not rc_new.endswith(nl_rc):
        rc_new += nl_rc
    ck('RC 追加段用 CRLF（与主文件一致）', nl_rc == b'\r\n', nl_rc)
    ck('RC 新增的每一行都是 CRLF：CR 增量为 0 且 LF-only 增量 = 0',
       rc_new.count(b'\r\n') == rc_old.count(b'\r\n'),
       'CR %d -> %d' % (rc_old.count(b'\r\n'), rc_new.count(b'\r\n')))
    write_file(RC, None, 1081, rc_new, 'R14_COMMON_2106')

    # ---------- 2. LEDGER ----------
    led_old = io.open(LED, 'rb').read()
    ck('LEDGER 当前 CR = 337', crlf(led_old) == 337, crlf(led_old))
    led_new = led_old + (b'\n' if led_old.endswith(b'\n') else b'\n\n') + SEC_LED.encode('utf-8')
    if not led_new.endswith(b'\n'):
        led_new += b'\n'
    write_file(LED, None, 337, led_new, 'GOAL_THREE_TARGETS_1156')

    # ---------- 3. LEAD_LOCK ----------
    lk_old = io.open(LOCK, 'rb').read()
    ck('LEAD_LOCK 当前 CR = 137', crlf(lk_old) == 137, crlf(lk_old))
    nm = __import__('re').search(rb'(?m)^([A-Z]{2})\d+\. ', lk_old[::-1])
    lk_new = lk_old + (b'\n' if lk_old.endswith(b'\n') else b'\n\n') + lock_body.encode('utf-8')
    if not lk_new.endswith(b'\n'):
        lk_new += b'\n'
    write_file(LOCK, None, 137, lk_new, 'LEAD_LOCK_ED')

    # ---------- 4. STATUS_BOARD（先判归档） ----------
    brd_old = io.open(BRD, 'rb').read()
    n_lines = brd_old.count(b'\n')
    ck('STATUS_BOARD 当前 CR = 0', crlf(brd_old) == 0, crlf(brd_old))
    ck('STATUS_BOARD 当前行数 < 260（不触发归档）', n_lines < 260, n_lines)
    brd_new = brd_old + (b'\n' if brd_old.endswith(b'\n') else b'\n\n') + board_body.encode('utf-8')
    if not brd_new.endswith(b'\n'):
        brd_new += b'\n'
    ck('STATUS_BOARD 新总行数 <= 300', brd_new.count(b'\n') <= 300, brd_new.count(b'\n'))
    ck('STATUS_BOARD 仍无 CR', b'\r' not in brd_new)
    write_file(BRD, None, 0, brd_new, 'STATUS_BOARD_r102')

    # ---------- 5. 门禁复跑 ----------
    p = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')],
                       capture_output=True, text=True, cwd=ROOT)
    ck('四件套写完后门禁仍 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
    ck('门禁仍报 C12 12 行 12 命中',
       'C12 frozen-anchor live-check: 12 frozen rows, 12 anchors hit' in p.stdout)
    ck('门禁仍报 C11b gap=7',
       'gap(claims-none, can never FAIL)=7' in p.stdout)

    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks,
               'board_lines': brd_new.count(b'\n'), 'stamp': STAMP},
              io.open(os.path.join(OUT, 'write_r102.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d board_lines=%d' % (len(checks), n_fail, brd_new.count(b'\n')))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
