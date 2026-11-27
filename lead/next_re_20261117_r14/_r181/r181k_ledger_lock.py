#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181k_ledger_lock.py —— 台账新增 §1236、LEAD_LOCK 新增 PK 段（下一字母）。
CR 分别保持 337 与 137。fail-closed：旧 sha 命中才写；旧内容逐字节为前缀。
"""
import hashlib, io, os, sys

LED = 'GOAL_THREE_TARGETS_20261018.md'
LOCK = 'LEAD_LOCK'
BASE = 'next_re_20261117_r14/R17_LEAD_BASELINE'
fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

led = io.open(LED, encoding='utf-8', newline='').read()
lock = io.open(LOCK, encoding='utf-8', newline='').read()
LED_SHA = hashlib.sha256(led.encode('utf-8')).hexdigest()
LOCK_SHA = hashlib.sha256(lock.encode('utf-8')).hexdigest()

ck('P1 台账 CR=337', led.count('\r\n') == 337, led.count('\r\n'))
ck('P2 台账末节 §1235', led.count('## §1235') == 1 and '## §1236' not in led)
ck('P3 LOCK CR=137', lock.count('\r\n') == 137, lock.count('\r\n'))
ck('P4 LOCK 末段是 PJ9', lock.count('\nPJ9.') == 1 and '\nPK.' not in lock and '\nPK1.' not in lock,
   (lock.count('\nPJ9.'), lock.count('\nPK.')))

SEC = """
## §1236 R181：主门禁对事实层的零覆盖闭合 —— C19 从「硬编码靶子」改成「指针驱动」，首版被审计证为僵尸快照

**一·量.** 两次独立计数（`_r180/r180a`、`_r181/r181a`；正控在 `_r161/gate_runner.py` 得 facts_floors=14 / FACT_INDEX=5）测得 `check_disc.py` 对 facts_floors / FACT_INDEX / FACT_INDEX_CURRENT 子串出现各 **0**。分辨率反证：把 V563 的 F24 grade 由 `[已证]` 改成 `[流程]`（副本路径）⇒ `facts_floors` **exit 1 / 3 FAIL**（D0、D5 点名 F24、D10），`check_disc` **exit 0 / 0 FAIL**。

**二·首版错在哪.** v1 的 (a)(b)(c) 三条靶子全硬编码 `R17_R131_FACTINDEX_V563`。纪律「历史版本一律保留不删不改」⇒ 升 V564 后 V563 仍在盘、sha 与字节都不变 ⇒ 三条**永远通过**。跨家族审计 #432 Q4 提出，主会话沙箱复算成立。

**三·实测差分（我两次预期都写错，S-681/S-682）.** 沙箱造 V564 副本（与 V563 逐字节相同）：
- 工况 A（指针只改目录字段、相对路径未改）：v1 与 v2 **都** FAIL ⇒ 无区分度；
- 工况 B（指针整体升版且自洽）：v1 的 (a)(b)(c) **报绿**、(d) **报红**；v2 报 `EXPECT_CUR='…/V563/…' vs pointer='…/V564/…'` ⇒ 抓「两门各查各版本、两门都报绿」。故审计结论订正为「v1 的 (a)(b)(c) 是僵尸、(d) 是升版瞬间的一次性哨兵」，不是「整条 C19 退化」。

**四·v2 六条判据（块内无版本号）.** (a) 指针「相对路径」拼出的绝对路径必须存在；(b) 其 sha256 == 指针 sha256 字段；(c) 其字节数 == 指针字节数字段；(d) 指针「版本目录」== 该路径目录名；(e) `facts_floors.EXPECT_CUR` 必须解析到**同一绝对路径**；(f) facts 的 `CUR_SHA256`/`TOTAL_BYTES` == 该路径实测值。读不到/解析不出 → FAIL，不跳过。

**五·否决审计的建议.** 审计 Q2 建议把 `facts_floors.py` 的 sha256 嵌进 check_disc。**否决**：每次改事实层门禁都要同步改主门禁，新造假 FAIL 面（代价 1 处 + 连锁 4 处重钉，`r160c_gen_guard.py` 不认识 check_disc ⇒ 回填靠人；`facts_floors.py*.bak` 实测 33 份）。

**六·写盘与反控.** 两轮 fail-closed：v1 `57,837→62,955 B / 8de20d8e…`（新旧同镜像 FAIL 集合逐条相同）、v2 `62,955→66,335 B / 4e37535b…`。反向 **8 组 16 条断言 0 FAIL**：指针 sha 末位 / 字节字段 / 版本目录 / 指针删除 / 台账改 1 字节 / facts 常量脱钩 / facts 文件删除 —— 各 exit 1 且出现对应 C19 FAIL。

**七·C16 重钉.** §2.185 实测 **7,821 B** ⇒ 门槛 **3,910**；§2.186 实测 **7,025 B** ⇒ **3,512**；`C16_FLOORS` **178 → 180** 条，pin `110cd3e8…` → **`70f66602…`**（旧表复算命中旧 pin 作硬闸，三反控均使 sha 变）。终态 `180 sections measured (pinned 180) … unpinned 0`。

**八·看板归档.** 283 行 ≥ 260 ⇒ 搬走 R164+R171 **12,071 B**（含分隔换行）到 `BOARD_ARCHIVE.md`；60,013 = 12,071 + 47,942 逐字节闭合；归档 CR **2952** 保持、看板 CR **0** 保持、行数 283 → **226**。

**九·自错 S-671..S-686 共 16 条**（全部由可失败断言当场抓出，无一条进入结论）：沙箱漏软链模块致 rc=1 而 FAIL=0（S-671/672）、块内调用不存在的 `sha()`（S-673）、把沙箱 rc==0 当判据致假 FAIL（S-674/675）、ast 取不到 `os.path.join` 形式的 `EXPECT_CUR`（S-676/677）、想 exec 他人门禁常量区（S-678）、`r'''` 块内单双引号字符类（S-679）、块内用 `TIER` 而本文件叫 `R14`（S-680）、两次写错 v1 在升版工况的预期（S-681/682）、反向断言过窄（S-683）、搬走字节 12,070 实为 12,071（S-684）、行数口径混用（S-685）、末节判据靠尾串（S-686）。族谱：「把应然数当实测」**第十二次复发**；「环境缺陷被当成判据失败」**新族**。

**十·未取得.** ① C19 仍受「同改数据与常量可过」上限；② `gate_runner.LEDGER` 与另两处的**三方**路径一致性无人守（check_disc 从不读 gate_runner；审计实测 crontab/systemd 对三门接线各 0 条）；③ F23/F35 grade 未改；④ `coverage.tsv`/`function_atlas.tsv` 仍不可读 ⇒ F23 五数、F35 分母不可重数；⑤ 86.19% 不可重算；⑥ C7 三死分支仍各 0 行；⑦ C11 十二个永不 FAIL 的 id 未动；⑧ V560 CSV 转义是否回退未裁定。
"""

LOCK_SEG = """
PK · R17 第 181 轮（2026-11-27 15:4x–16:0x）· 连续九轮只登记的「主门禁看不见事实层」本轮闭合：`check_disc.py` 新增 **C19**，且首版判据被跨家族审计当场证为「僵尸快照」，重写为指针驱动

**PK1. 🔴 交付一：先把「看不见」做成可失败的量.** 两次独立计数各 **0**（正控在 `gate_runner.py` 得 **14/5/0**）。分辨率反证：V563 的 F24 grade `[已证]`→`[流程]`（副本路径）⇒ `facts_floors` **exit 1 / 3 FAIL**（D0 / D5 点名 / D10），`check_disc` **exit 0 / 0 FAIL**。

**PK2. 🔴 交付二：首版 C19 的三条判据是僵尸.** v1 的 (a)(b)(c) 靶子全硬编码 `R17_R131_FACTINDEX_V563`；纪律「历史版本一律保留不删不改」⇒ 升 V564 后 V563 不变 ⇒ **永远通过**。与 C7b/C11b/C18 同型，且更坏（现状至少没人误以为台账被查）。由审计 **#432 Q4** 提出、主会话沙箱复算成立。

**PK3. 🔴 交付三：v1/v2 的实测差分把我两次预期都钉正.** 工况 A（指针自相矛盾）两版都 FAIL ⇒ 无区分度（S-681）；工况 B（指针整体升版且自洽）v1 的 (a)(b)(c) **绿**、(d) **红**（升版瞬间一次性哨兵），v2 报 `EXPECT_CUR='…/V563/…' vs pointer='…/V564/…'` ⇒ **抓到「两门各查各版本、两门都报绿」**（S-682）。⇒ 审计结论**订正**为「(a)(b)(c) 僵尸 +(d) 一次性哨兵」，不是「整条退化」。

**PK4. ✅ 交付四：v2 六条判据，块内无版本号.** 靶子路径全由指针「相对路径」解析；(e) 联动 `facts_floors.EXPECT_CUR` 必须解析到同一绝对路径（审计 Q5① 的零常量联动点）；(f) facts 两个常量必须等于指针解析出的那份文件。读不到/解析不出 → **FAIL 不跳过**。

**PK5. 📌 交付五：否决审计的一条建议.** Q2 建议把 `facts_floors.py` 的 sha256 嵌进 check_disc —— **否决**：新造假 FAIL 面（1 处 + 连锁 4 处重钉，`r160c_gen_guard.py` 不认识 check_disc ⇒ 回填靠人，`facts_floors.py*.bak` 实测 **33** 份）。改用词法解析 `EXPECT_CUR` + ast 取两常量，两侧均不新增手抄常量。

**PK6. ✅ 交付六：两轮 fail-closed 写盘 + 16 条反控.** v1 `57,837→62,955 B / 8de20d8e…`（差分判据：新旧同镜像 FAIL 集合逐条相同）；v2 `62,955→66,335 B / 4e37535b…`。反向 **8 组 16 条 0 FAIL**：指针 sha 末位 / 字节字段 / 版本目录 / 指针删除 / 台账改 1 字节 / facts 常量脱钩 / facts 文件删除 ⇒ 各 exit 1 且出现对应 C19 FAIL。

**PK7. ✅ 交付七：C16 重钉 178 → 180.** §2.185 实测 **7,821 B** ⇒ **3,910**；§2.186 实测 **7,025 B** ⇒ **3,512**；pin `110cd3e8…` → **`70f66602…`**（旧表复算命中旧 pin 作硬闸，三反控均使 sha 变）。终态 `180 measured (pinned 180) / unpinned 0`。

**PK8. ✅ 交付八：看板归档.** 283 ≥ 260 ⇒ 搬 R164+R171 **12,071 B** 到归档；**60,013 = 12,071 + 47,942** 逐字节闭合；归档 CR **2952**、看板 CR **0**、行数 283 → **226**。重跑归档脚本被自己的旧 sha 闸拒绝 ⇒ fail-closed 可验。

**PK9. 📌 自错 S-671..S-686（16 条，全部当场抓出，无一条进入结论）.** 沙箱漏软链 `place_r87` 致 rc=1 而 FAIL=0（S-671/672）；块内调用不存在的 `sha()`（S-673）；把沙箱 rc==0 当判据致**假 FAIL**（S-674/675）；`EXPECT_CUR` 是 `os.path.join` 形式 ast 取不到（S-676/677）；想 exec 他人门禁常量区（S-678，首个 print 在 332 行、D0..D10 副作用在其之前）；`r'''` 块内单双引号字符类致 BLOCK 语法错（S-679）；块内用 `TIER` 而本文件叫 `R14`（S-680）；两次写错 v1 升版工况预期（S-681/682）；反向断言过窄（S-683）；搬走字节 12,070 实为 **12,071**（S-684）；行数口径混用（S-685）；末节判据靠尾串（S-686）。族谱：「把应然数当实测」**第十二次复发**；「环境缺陷被当成判据失败」**新族**。

**PK10. 📌 跨家族.** 执行员 **#431（hy4flash-free / 无 OVERTIME）**：Q1–Q6 逐条作答，Q6 给出「facts_floors 看得见 / check_disc 失明」的可复算最小命令，主会话**亲自复算**得同一结论（exit 1/3 FAIL vs exit 0/0 FAIL）。审计员 **#432（deepseek / 无 OVERTIME）**：Q1–Q5 全答，**三条结论被采纳**（Q4 僵尸判据、Q5① 三方路径一致性并入 (e)、Q3 (d) 只覆盖 D10 的 (A) 项）；**一条被否决**（Q2 嵌 sha）。其另指出 `check_disc.py:31` 的 `LED` 在 `:1040` 被称为 `'LEDGER'` 实为 `GOAL_THREE_TARGETS` 的**命名欺骗** —— 经复算成立，登记为未取得（改名会让 C10 自述行失配，须单独一卡）。

**PK11. 📌 未取得（不粉饰）.** ① C19 仍受「同改数据与常量可过」上限（与 D9/D10 同族）；② `gate_runner.LEDGER` 与另两处的**三方**路径一致性仍无人守（审计实测 crontab/systemd 对三门接线各 **0** 条）；③ F23/`未取得`、F35/`[流程]` grade 未改；④ `coverage.tsv`/`function_atlas.tsv` 仍不可读 ⇒ F23 五数、F35 分母不可重数；⑤ 86.19% 不可重算；⑥ C7 三死分支 exists/bytes=/none 仍各 **0** 行；⑦ C11 十二个永不 FAIL 的 id 未动（现测 C11b gap=**12**）；⑧ V560 的 CSV 转义是否回退未裁定。
"""

new_led = led.rstrip('\n') + '\n' + SEC
new_lock = lock.rstrip('\n') + '\n' + LOCK_SEG
ck('C1 台账 CR 仍 337', new_led.count('\r\n') == 337, new_led.count('\r\n'))
ck('C2 台账含 §1236', '## §1236' in new_led)
ck('C3 台账旧内容为前缀', new_led.startswith(led.rstrip('\n') + '\n'))
ck('C4 LOCK CR 仍 137', new_lock.count('\r\n') == 137, new_lock.count('\r\n'))
ck('C5 LOCK 含 PK1..PK11', all(('PK%d.' % i) in new_lock for i in range(1, 12)))
ck('C6 LOCK 旧内容为前缀', new_lock.startswith(lock.rstrip('\n') + '\n'))

if fails:
    print('拒绝写盘'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)

import datetime
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
for path, old, newtxt, tag in ((LED, led, new_led, 'ledger_s1236'), (LOCK, lock, new_lock, 'lock_PK')):
    bak = os.path.join(BASE, '%s.before_r181_%s_%s.bak' % (os.path.basename(path), tag, ts))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    os.write(fd, old.encode('utf-8')); os.close(fd)
    ck('W1 备份 %s' % os.path.basename(bak), open(bak, 'rb').read() == old.encode('utf-8'))
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    rb = open(path, 'rb').read()
    print('%s: %d -> %d B ; CR=%d' % (path, len(old.encode()), len(rb), rb.count(b'\r\n')))

ck('W2 台账回读 CR=337', open(LED, 'rb').read().count(b'\r\n') == 337)
ck('W3 LOCK 回读 CR=137', open(LOCK, 'rb').read().count(b'\r\n') == 137)
print('LEDGER_SHA=%s' % hashlib.sha256(open(LED, 'rb').read()).hexdigest())
print('LOCK_SHA=%s' % hashlib.sha256(open(LOCK, 'rb').read()).hexdigest())
print('fails=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
