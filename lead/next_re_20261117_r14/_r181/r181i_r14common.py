#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181i_r14common.py —— R14_COMMON 追加 §2.186。CR 必须保持 1081（本文件是 CRLF 混排：
既有 1081 处 CRLF，新增块全用 LF）。fail-closed：旧 sha 命中才写。
"""
import hashlib, io, os, sys

P = 'R14_COMMON.md'
EXPECT_SHA = None   # 先实测再填，见下
EXPECT_CR = 1081
BASE = 'R17_LEAD_BASELINE'

txt = io.open(P, encoding='utf-8', newline='').read()
raw = open(P, 'rb').read()
SHA = hashlib.sha256(raw).hexdigest()
fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

ck('P1 CR == 1081（保持）', txt.count('\r\n') == EXPECT_CR, txt.count('\r\n'))
ck('P2 文件以 LF 结尾', raw.endswith(b'\n') and not raw.endswith(b'\r\n'))
ck('P3 尚无 §2.186', '## 2.186' not in txt)
# S-686：P4 首版断言「文件末尾 200 字符含 S-670」，实测末尾确实含 S-670，但更准确的
# 判据是「最后一节是 2.185 且尚无 2.186」——按节号扫，不靠尾串。
import re as _re
_secs = [m.group(1) for m in _re.finditer(r'(?m)^##\s*(\d+(?:\.\d+)*)', txt)]
ck('P4 末节号 == 2.185（实测）', _secs and _secs[-1] == '2.185', _secs[-1] if _secs else None)
ck('P4b 节号有序且 2.185 恰 1 处', txt.count('## 2.185') == 1, txt.count('## 2.185'))
LAST = txt.rstrip('\n').split('\n')[-1]
print('OLD_SHA=%s' % SHA)

BLOCK = """
## 2.186 R181：主门禁对事实层的零覆盖闭合（C19 指针驱动），且首版判据被跨家族审计当场证为「僵尸快照」

R181 把连续九轮只登记的「主门禁看不见事实层」从登记变成可失败断言，并使它在**升版之后仍然有分辨力**——这一点是首版做错、被跨家族审计 #432 的 Q4 当场钉出、主会话复算成立后重写的。

**一·先量，再改.** 两次独立计数（`_r180/r180a`、`_r181/r181a`，正控在 `_r161/gate_runner.py` 上得 facts_floors=14 / FACT_INDEX=5 / FACT_INDEX_CURRENT=0）测得 `check_disc.py` 对 facts_floors / FACT_INDEX / FACT_INDEX_CURRENT 的子串出现各 **0**。分辨率反证比计数更硬：把 `FACT_INDEX.tsv` 的 F24 grade 由 `[已证]` 改成 `[流程]`、以副本路径跑三门 —— `facts_floors` **exit 1 / 3 FAIL**（D0 sha drifted、D5 点名 `('F24','[已证]','[流程]')`、D10 指针 sha != on-disk），`check_disc` **exit 0 / 0 FAIL**。同一改动，一门看得见、一门完全看不见。

**二·首版 C19（v1）四条判据，其中三条是僵尸.** v1 写 (a) facts CUR_SHA256、(b) facts TOTAL_BYTES、(c) 指针 sha、(d) 指针字节、(e) 指针版本目录，**靶子路径全部硬编码 `R17_R131_FACTINDEX_V563`**。审计 #432 的 Q4 指出：纪律规定「历史版本一律保留不删不改」⇒ 升到 V564 之后 V563 那份文件仍在盘上、sha 与字节都不变 ⇒ (a)(b)(c) **永远通过**，与 check_disc 历史缺陷 C7b/C11b/C18 同型，且比现状更坏（现状至少没人误以为台账被查过）。

**三·v1 与 v2 在「升版」工况下的实测差分（我两次预期都写错，实测钉正）.** 沙箱造 V564 副本（内容与 V563 逐字节相同）并改指针，跑两版：
- 工况 A（指针只改目录字段、相对路径未改，即指针自相矛盾）：v1 与 v2 **都** FAIL ⇒ **不构成区分度**（我最初以为 v1 会全绿，S-681）。
- 工况 B（指针整体升版且自洽）：v1 的 (a)(b)(c) 三条**报绿**（僵尸确认）、(d) **报红**（升版瞬间的一次性哨兵）；v2 则报 `EXPECT_CUR='…/V563/FACT_INDEX.tsv' vs pointer='…/V564/FACT_INDEX.tsv'` ⇒ **抓到「两门各查各的版本、两门都报绿」这一真实失效**。故审计的结论应订正为「v1 的 (a)(b)(c) 是僵尸、(d) 是升版瞬间的一次性哨兵」，而不是「整条 C19 退化」（S-682）。

**四·v2 的判据（路径一律由指针解析，块内无版本号）.** (a) 指针「相对路径」拼出的绝对路径必须存在；(b) 其 sha256 == 指针「sha256」；(c) 其字节数 == 指针「字节数」；(d) 指针「版本目录」== 该路径目录名；(e) `facts_floors.py` 的 `EXPECT_CUR` 必须解析到**同一绝对路径**（这是审计 Q5① 提的零常量联动点，抓「升版漏改其一」）；(f) facts 的 `CUR_SHA256`/`TOTAL_BYTES` 必须等于**指针解析出的那份文件**的实测值。读不到或解析不出 → **FAIL 而不是跳过**（与 facts_floors D10 同纪律）。

**五·刻意否决的一条.** 审计 Q2 建议 (c) 项「把 facts_floors.py 的 sha256 嵌进 check_disc.py」。**否决**：那会让每次改事实层门禁都必须同步改主门禁，新造一个假 FAIL 面（实测代价 1 处 + 连锁 4 处重钉，且 `_r160/r160c_gen_guard.py` 不认识 check_disc ⇒ 回填只能靠人；`R17_LEAD_BASELINE/facts_floors.py*.bak` 实测 33 份 = 历史重生成 ≥33 次）。v2 改用「从 facts_floors 词法解析 EXPECT_CUR + ast 取 CUR_SHA256/TOTAL_BYTES」，两侧都不新增手抄常量。

**六·写盘与反向（16 条反控 0 FAIL）.** 两次 fail-closed 写盘：v1 `57,837 → 62,955 B / 8de20d8e…`（差分判据证明新旧两版在同一镜像里 FAIL 集合逐条相同）；v2 `62,955 → 66,335 B / 4e37535b…`（CR=0 全程）。反向 8 组共 16 条断言全 PASS：指针 sha 末位改坏 / 字节数字段改坏 / 版本目录改错 / 指针文件删除 / 台账改 1 字节 / facts CUR_SHA256 与现盘脱钩 / facts_floors.py 文件删除 —— 每条都 exit 1 且出现对应 C19 FAIL 行。

**七·看板归档.** 写四件套前实测看板 **283 行 ≥ 260**，按纪律搬走最早两段（R164 + R171，**12,071 B** 含分隔换行）到 `BOARD_ARCHIVE.md`，`r181h` 18 断言：60,013 = 12,071 + 47,942 **逐字节闭合**；归档 CR **2952 → 2952**、看板 CR 保持 **0**、行数 283 → **226**。重跑该脚本被自己的旧 sha 闸拒绝 ⇒ fail-closed 可验证。

**八·自错 S-671..S-685（全部由可失败断言当场抓出，无一条进入结论）.** S-671 沙箱只软链 6 个数据文件、漏 `place_r87` 模块 ⇒ rc=1 而 FAIL 行 0（异常被当成判据失败）；S-672 同因；S-673 新块调用 `sha()` 而 check_disc 里无该助手（NameError）；S-674 把「沙箱 rc==0」当判据 ⇒ 假 FAIL（镜像里 id 31 的相对路径产物本来就 FILE_MISSING，旧版同样 3 条），改为**新旧同镜像差分**；S-675 同一假 FAIL 在反向脚本里复现一次；S-676/S-677 用 ast 顶层常量取 `EXPECT_CUR`，而它是 `os.path.join(...)` 是 Call ⇒ 取不到，v2 在**正常盘面**上也 FAIL；S-678 想 exec facts_floors 的常量区，但首个 print 在 332 行、D0..D10 副作用在此之前已发生 ⇒ 执行他人门禁脚本不可接受，改词法解析；S-679 在 `r'''` 块里写含单双引号的字符类 ⇒ 整个 BLOCK 语法错；S-680 块内用了 `TIER`，而 check_disc 里叫 `R14`（TIER 是 facts_floors 的叫法）；S-681/S-682 两次把「v1 在升版工况下的表现」预期写错，两次都由实测钉正，并据此把审计结论订正得更精确；S-683 反向断言过窄（v2 从指针解析后先报「相对路径不存在」而非「目录不一致」）；S-684 把搬走字节写成 12,070，实测含分隔换行为 **12,071**；S-685 行数口径混用（换行符个数 vs 末行无换行）。**族谱**：「把应然数当实测」**第十二次复发**（S-674/S-681/S-682/S-684）；「环境缺陷被当成判据失败」**新族**（S-671/S-674）。

**九·未取得（不粉饰）.** ① C19 仍受「同改数据与常量可过」的指纹类共同上限（与 D9/D10 同族），v2 不消除它、只消除「完全不被读」与「升版后恒真」两条；② 审计 Q5 提的「三处路径一致性」已由 C19(e) 覆盖 facts↔指针这一对，但 **check_disc 从不读 `gate_runner.py`**，`gate_runner.LEDGER` 与另两处的三方一致性仍无人守（审计实测 crontab/systemd 对三门的接线各 0 条）；③ F23（未取得）/ F35（[流程]）grade 仍未改（裁定不是取证）；④ `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 n 分母仍不可重数；⑤ 86.19% 原值仍不可重算；⑥ C7 三死分支 exists/bytes=/none 仍各 0 行；⑦ C11 十二个永不 FAIL 的 id 未动；⑧ V560 的 CSV 引号转义是否回退未裁定。
"""

new = txt.rstrip('\n') + '\n' + BLOCK
ck('C1 新增块以 LF 结尾', new.endswith('\n') and not new.endswith('\r\n'))
ck('C2 新增块本身不含 CR', '\r' not in BLOCK, BLOCK.count('\r'))
ck('C3 CR 总数不变（仍 1081）', new.count('\r\n') == EXPECT_CR,
   new.count('\r\n'))
ck('C4 旧内容逐字节保留（新文件以旧文件为前缀，仅去掉尾部多余换行后追加）',
   new.startswith(txt.rstrip('\n') + '\n'))
ck('C5 包含新节标题', '## 2.186 R181' in new)

if fails:
    print('拒绝写盘'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)

import datetime
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bak = os.path.join(BASE, 'R14_COMMON.md.before_r181_s2186_%s.bak' % ts)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
os.write(fd, raw); os.close(fd)
ck('W1 备份等于旧文件', open(bak, 'rb').read() == raw, os.path.basename(bak))
ck('W2 写前 sha 未变', hashlib.sha256(open(P, 'rb').read()).hexdigest() == SHA)
io.open(P, 'w', encoding='utf-8', newline='').write(new)
rb = open(P, 'rb').read()
ck('W3 回读 CR == 1081', rb.count(b'\r\n') == EXPECT_CR, rb.count(b'\r\n'))
ck('W4 回读 sha == 沙箱新版', hashlib.sha256(rb).hexdigest() == hashlib.sha256(new.encode('utf-8')).hexdigest())
print('bytes %d -> %d ; lf %d -> %d' % (len(raw), len(rb), raw.count(b'\n'), rb.count(b'\n')))
print('NEW_SHA=%s' % hashlib.sha256(rb).hexdigest())
print('fails=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
