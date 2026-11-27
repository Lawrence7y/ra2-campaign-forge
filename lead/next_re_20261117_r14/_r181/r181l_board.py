#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181l_board.py —— 看板头部插入第 181 轮记录。CR 保持 0，总行数 <= 300。
fail-closed：旧 sha 命中才写。
"""
import hashlib, io, os, sys

BRD = 'STATUS_BOARD.md'
BASE = 'R17_LEAD_BASELINE'
fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

txt = io.open(BRD, encoding='utf-8', newline='').read()
SHA = hashlib.sha256(txt.encode('utf-8')).hexdigest()
ck('P1 CR=0', txt.count('\r') == 0, txt.count('\r'))
ck('P2 行数 226', txt.count('\n') == 226, txt.count('\n'))
# S-688：我凭上一轮记忆写成「R172 用 🔵」，实测是 🟢。判据不应依赖颜色标记（那是装饰），
# 改为断言「第一段是第 172 轮」且「段头格式合法」，颜色只如实打印。
ck('P3 第一段是第 172 轮（不依赖颜色标记）',
   txt.startswith('## ') and '第 172 轮' in txt.split('\n')[0], txt[:40])
ck('P4 尚无第 181 轮', '第 181 轮' not in txt, txt.count('第 181 轮'))

SEC = """## 🟢 R17 第 181 轮（2026-11-27 15:4x–16:0x）· 连续九轮只登记的「主门禁看不见事实层」本轮闭合：`check_disc.py` 新增 **C19**，但首版判据被跨家族审计当场证为**僵尸快照**，重写为指针驱动后才算真闭合

**一 · 先量，再改。** 两次独立计数（`_r180/r180a`、`_r181/r181a`；正控在 `_r161/gate_runner.py` 上得 facts_floors=**14** / FACT_INDEX=**5** / FACT_INDEX_CURRENT=**0**）测得 `check_disc.py` 对 facts_floors / FACT_INDEX / FACT_INDEX_CURRENT 的子串出现各 **0**。比计数更硬的是分辨率反证：把 V563 的 F24 grade 由 `[已证]` 改成 `[流程]`、以副本路径跑三门 —— `facts_floors` **exit 1 / 3 FAIL**（D0 sha drifted、D5 点名 `('F24','[已证]','[流程]')`、D10 指针 sha != on-disk），`check_disc` **exit 0 / 0 FAIL**。同一改动，一门看得见、一门完全看不见。

**二 · 首版错在哪（本轮最值钱的一条）。** v1 的 C19 五条判据里 (a)(b)(c) 的靶子路径全硬编码 `R17_R131_FACTINDEX_V563`。纪律「历史版本一律保留不删不改」⇒ 升到 V564 之后 V563 仍在盘、sha 与字节都不变 ⇒ 这三条**永远通过**。跨家族审计 **#432 的 Q4** 提出，主会话沙箱复算成立。这与 check_disc 历史缺陷 C7b/C11b/C18 同型，且**比现状更坏**：现状至少没人误以为台账被检查过。

**三 · 实测差分把我两次预期都钉正（S-681 / S-682）。** 沙箱造 V564 副本（与 V563 逐字节相同）：**工况 A**（指针只改目录字段、相对路径未改，即指针自相矛盾）⇒ v1 与 v2 **都** FAIL，**不构成区分度**（我最初以为 v1 会全绿）；**工况 B**（指针整体升版且自洽）⇒ v1 的 (a)(b)(c) **报绿**、(d) **报红**（升版瞬间的一次性哨兵），v2 报 `EXPECT_CUR='…/V563/FACT_INDEX.tsv' vs pointer='…/V564/FACT_INDEX.tsv'` ⇒ **抓到「两门各查各的版本、两门都报绿」这一真实失效**。⇒ 审计结论**订正**为「v1 的 (a)(b)(c) 是僵尸、(d) 是升版瞬间的一次性哨兵」，而不是「整条 C19 退化」。

**四 · v2 六条判据（块内无任何版本号）。** (a) 指针「相对路径」拼出的绝对路径必须存在；(b) 其 sha256 == 指针 sha256 字段；(c) 其字节数 == 指针字节数字段；(d) 指针「版本目录」== 该路径目录名；(e) `facts_floors.EXPECT_CUR` 必须解析到**同一绝对路径**（审计 Q5① 的零常量联动点，抓「升版漏改其一」）；(f) facts 的 `CUR_SHA256`/`TOTAL_BYTES` 必须等于**指针解析出的那份文件**的实测值。读不到或解析不出 → **FAIL 而不是跳过**（与 facts_floors D10 同纪律）。

**五 · 否决审计的一条建议。** Q2 建议把 `facts_floors.py` 的 sha256 嵌进 check_disc —— **否决**：那会让每次改事实层门禁都必须同步改主门禁，新造一个假 FAIL 面（代价 1 处 + 连锁 4 处重钉，且 `_r160/r160c_gen_guard.py` 不认识 check_disc ⇒ 回填只能靠人；`R17_LEAD_BASELINE/facts_floors.py*.bak` 实测 **33** 份 = 历史重生成 ≥33 次）。v2 改用词法解析 `EXPECT_CUR` + ast 取两常量，两侧都不新增手抄常量。

**六 · 两轮 fail-closed 写盘 + 16 条反控。** v1 `57,837 → 62,955 B / 8de20d8e…`（差分判据：新旧两版在同一镜像里 FAIL 集合**逐条相同**）；v2 `62,955 → 66,335 B / 4e37535b…`（CR=0 全程）。反向 **8 组 16 条断言 0 FAIL**：指针 sha 末位改坏 / 字节数字段改坏 / 版本目录改错 / 指针文件删除 / 台账改 1 字节 / facts `CUR_SHA256` 与现盘脱钩 / facts_floors.py 文件删除 —— 每条 exit 1 且出现对应 C19 FAIL 行。

**七 · C16 随两节重钉 178 → 180。** §2.185 实测 **7,821 B** ⇒ 门槛 **3,910**；§2.186 实测 **7,025 B** ⇒ **3,512**；`C16_FLOORS` 178 → **180** 条，pin `110cd3e8…` → **`70f66602…`**（旧表复算命中旧 pin 作硬闸，三反控均使 sha 变）。终态 `180 sections measured (pinned 180) … unpinned 0`。

**八 · 看板归档。** 写四件套前实测看板 **283 行 ≥ 260**，按纪律搬走最早两段（R164 + R171，**12,071 B** 含分隔换行）到 `BOARD_ARCHIVE.md`；严格账 **60,013 = 12,071 + 47,942** 逐字节闭合；归档 CR **2952 → 2952**、看板 CR 保持 **0**、行数 283 → **226**。重跑归档脚本被自己的旧 sha 闸拒绝 ⇒ fail-closed 可验证。

**九 · 自错 S-671..S-686（16 条，全部由可失败断言当场抓出，无一条进入结论）。** 沙箱漏软链 `place_r87` 模块致 rc=1 而 FAIL 行 0（S-671/672，异常被当成判据失败）；新块调用不存在的 `sha()` 致 NameError（S-673）；把「沙箱 rc==0」当判据 ⇒ **假 FAIL**（镜像里 id 31 的相对路径产物本来就 FILE_MISSING，旧版同样 3 条），改为新旧同镜像差分（S-674/675）；用 ast 顶层常量取 `EXPECT_CUR`，而它是 `os.path.join(...)` 是 Call ⇒ 取不到，v2 在**正常盘面**上也 FAIL（S-676/677）；想 exec facts_floors 的常量区，但首个 print 在 332 行、D0..D10 副作用在此之前已发生（S-678，改词法解析）；`r'''` 块内写含单双引号的字符类 ⇒ 整个 BLOCK 语法错（S-679）；块内用 `TIER` 而 check_disc 里叫 `R14`（S-680）；两次写错「v1 在升版工况下的表现」（S-681/682，均由实测钉正并据此把审计结论改得更精确）；反向断言过窄（S-683）；搬走字节写 12,070 实为 **12,071**（S-684）；行数口径混用（S-685）；末节判据靠尾串（S-686）。**族谱**：「把应然数当实测」**第十二次复发**（S-674/681/682/684）；「环境缺陷被当成判据失败」**新族**（S-671/674）。

**十 · 跨家族。** 执行员 **#431（hy4flash-free）** Q1–Q6 逐条作答，Q6 给出可复算最小命令，主会话**亲自复算**得同一结论（exit 1/3 FAIL vs exit 0/0 FAIL）。审计员 **#432（deepseek）** Q1–Q5 全答：**三条被采纳**（Q4 僵尸判据、Q5① 三方路径一致性并入 (e)、Q3 (d) 只覆盖 D10 的 (A) 项）、**一条被否决**（Q2 嵌 sha）。两件**均无 OVERTIME**。

**十一 · 未取得（不粉饰）。** ① C19 仍受「同改数据与常量可过」的指纹类共同上限（与 D9/D10 同族），v2 只消除「完全不被读」与「升版后恒真」两条；② 审计 Q5 提的三方路径一致性只覆盖了 facts↔指针这一对，`check_disc` **从不读** `gate_runner.py` ⇒ `gate_runner.LEDGER` 与另两处的三方一致性仍无人守（审计实测 crontab/systemd 对三门接线各 **0** 条）；③ F23（`未取得`）/ F35（`[流程]`）grade 仍未改（裁定不是取证）；④ `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 n 分母仍不可重数；⑤ 86.19% 原值仍不可重算；⑥ C7 三死分支 exists/bytes=/none 仍各 **0** 行；⑦ C11 十二个永不 FAIL 的 id 未动（现测 C11b gap=**12**）；⑧ V560 的 CSV 引号转义是否回退未裁定；⑨ 审计另指出 `check_disc.py:31` 的 `LED` 在 `:1040` 被称为 `'LEDGER'` 实为 `GOAL_THREE_TARGETS` 的**命名欺骗**，复算成立但改名会让 C10 自述行失配 ⇒ 须单独一卡。

"""

new = SEC + txt
ck('C1 CR 仍 0', new.count('\r') == 0, new.count('\r'))
ck('C2 总行数 <= 300', new.count('\n') <= 300, new.count('\n'))
ck('C3 第 181 轮恰 1 处', new.count('第 181 轮') == 1, new.count('第 181 轮'))
ck('C4 原内容逐字节保留为后缀', new.endswith(txt))
# S-687：C5 首版断言 S-671..S-686 每个编号都整串出现，而正文为了紧凑写成
# 「S-671/672」「S-676/677」这类省略式 ⇒ 假 FAIL。改为断言首尾与主要节点在场，
# 并单独统计出现过的编号，如实打印（不硬凑 16 个）。
_present = sorted(set(int(x) for x in __import__('re').findall(r'S-(\d{3})', new)))
ck('C5 新段含 S-671 与 S-686（首尾）', 671 in _present and 686 in _present, _present)

if fails:
    print('拒绝写盘'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)

import datetime
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bak = os.path.join(BASE, 'STATUS_BOARD.md.before_r181_r181_%s.bak' % ts)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
os.write(fd, txt.encode('utf-8')); os.close(fd)
ck('W1 备份等于旧文件', open(bak, 'rb').read() == txt.encode('utf-8'), os.path.basename(bak))
ck('W2 写前 sha 未变', hashlib.sha256(open(BRD, 'rb').read()).hexdigest() == SHA)
io.open(BRD, 'w', encoding='utf-8', newline='').write(new)
rb = open(BRD, 'rb').read()
ck('W3 回读 CR=0', rb.count(b'\r') == 0)
ck('W4 回读行数 <= 300', rb.count(b'\n') <= 300, rb.count(b'\n'))
print('bytes %d -> %d ; lines %d -> %d' % (len(txt.encode()), len(rb), txt.count('\n'), rb.count(b'\n')))
print('SHA=%s' % hashlib.sha256(rb).hexdigest())
print('fails=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
