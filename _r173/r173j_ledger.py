#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 J：追加台账 §1228（纯追加，CR 保持 337）。"""
import hashlib, io, json, os, sys, time

LED = '/home/t628/projects/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md'
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
OLD_CR = 337
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(LED, 'rb').read()
ck('A1 CR == 337', raw.count(b'\r') == OLD_CR, raw.count(b'\r'))
txt = raw.decode('utf-8')
# S-603：首版 A2 写 '## §1228' in txt（缺 not），断言方向与名称相反 ⇒ 假 FAIL。
ck('A2 尚无 §1228', txt.count('## §1228') == 0, txt.count('## §1228'))
ck('A3 末尾是 §1227 段', txt.rstrip().count('## §1227') == 1, txt.rstrip()[-120:].replace('\n', '|'))
old_sha = hashlib.sha256(raw).hexdigest()

SEC = '''
## §1228 · R173：F24「bounds 段 16,711,118 B」被证为**算术差不是字节跨度**（实测值跨度 16,711,104，差 14 B 是 JSON 结构开销）；F35「V540..V544 共存 / V545 起回收」逐版成立但**共存起点是 V540 不是 V534**；F23 的 18/4 两口径与 COVERAGE 全树失联闭世界复算（V553→V554）

**一 · 三个宽度必须分开测.** 16,711,118 在 F24 两列共出现 **8** 次（statement 4 + limitations 4），其中「恰为被剔的 bounds 段」型 **1** 次。顶层 span 扫描器（字符串转义感知 + 括号配平）实测：现盘 `a2_sites.json` **17,624,355 B**、sha256 前缀 `7a8447d1d816cdc3`；**bounds 值跨度 16,711,104 B** = **1,392,592** 条 × **12 B**；calls 值跨度 913,228 B（6,728 键）。三口径：值跨度 **16,711,104** / 删整条成员 **16,711,116** / 现盘减快照清单 **16,711,118**。**可失败部分**：±32 B 窗口内以 16,711,118 为宽度试删 **65** 个起点，得合法 JSON 的 **0** 个；删 913,238 起 16,711,116 B **合法**（键只剩 calls、删后 913,239 B）；删 913,250 起 16,711,104 B **不合法**；删 913,237 起 16,711,118 B **不合法**。⇒ 「差额对、『恰为 bounds 段』错」，14 B = 键名 8 + 冒号 1 + 空白 1 + 结构字符（实测分布见 `r173a` B4）。既有 8 个 16,711,118 **一字未动**。

**二 · F35 版本范围逐版复算（V530..V553 共 24 个连续版本）.** V540..V544 五版 statement 长恒 **1054** 且「不是独立实现」各 **1** 次、limitations 里该半句恒 **0** 次；V545..V553 九版 limitations 该半句恒 **3** 次 = **R139 段 1 + R165 段 2（引文）**；原句「另有 3 个独立脚本含同一逐字判据」V534..V544 各 **1** 次、V545 起**不带引号 0 次 / 带引号 1 次**。**新边界**：V534..V539 六版 statement 长 **156**、不含该半句 ⇒ 「两列相反」只在 V540..V544 成立。**须带的作用域**：V553 limitations 里「不是独立实现」共 **3** 次，引用时须写「含 2 次引文」。

**三 · 一手权威与血缘四点（不依赖已失输入）.** `strict_panel.py` **6,481 B** / sha256 前缀 `731c98ea4910f5e9`；第 **78** 行 `if "[未证]" not in sem:`、第 **76** 行 `if grade == "[已证]":`，缩进 **8 vs 12** ⇒ 嵌套；全文 `[未证]` 恰 **2** 次（行 14/78）、裸「未证」也恰 2 次、代码形态恰 1 次；`sem = r[3]` 在**第 67 行**、`d[s]["atlas_n"] += 1` 在**第 69 行**。血缘四点：四脚本（strict_panel/precheck/simulate/verify）全满足「同一 PROJ + 同一对输入 + 同一判据串」；`merge_panel.py` **三缺二**、全文「未证」**0** 次。**N2 反控**：只用「同一 PROJ」误纳得 **5** 个，加另两条才是 **4** 个。

**四 · F23 两口径与 COVERAGE 闭世界.** 清单 **4,417** 行 4 列；basename 精确 `coverage.tsv` 恰 **18** 条、**distinct 字节值 18**、**存活 0**；rel 含 `/COVERAGE/` 恰 **28** 条、其中 basename 为 coverage.tsv 的 **4** 条、**存活全 0**（`COVERAGE/` 目录不存在）；`function_atlas.tsv` 清单恰 **1** 条 **427,038 B**、存活 0、全库 `os.walk` **0**、父目录不存在。**反控**：仓库根基准仍 0、`a2_sites.json` 判存活为真、basename→contains 条数 18→**41**。⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 `n` 分母**现盘无任何文件可重数**。

**五 · 落盘与门禁.** V553→**V554**：**123,851 B** / `5de4084b76bbd0e7…` / 55 行 5 列 / CR 0；差分行**恰 2**（F24/F35）、每行变化单元**恰 1**（第 5 列）、SequenceMatcher 各 **1 insert 落末尾**、其余 **52×5 逐字节相同**、母本一字未改；**+2,841 B**。门禁五点重钉（`EXPECT_CUR`→V554、`CUR_SHA256`→5de4084b…、`TOTAL_BYTES`→123,851、`MASTER_SHA256` `ce436f7a…`→**`5f3ba93cb0f091e3`**，每步 ast 取常量 + 旧常量复算旧 MASTER 命中作硬闸）；`gate_runner` 只改 `LEDGER` **1** 处。三段实跑：`check_disc` **exit 0**（C16 **171** 节 pinned 171 / unpinned 0）、`facts_floors` **exit 0**（D0/D8/D9）、`gate_runner` **G1=G2=G3=ok**；`GATE_VER` 仍 **R166**。**如实登记**：`r173g` 在写 `gate_runner` 之后的 D2 是一条方向写反的假 FAIL（**S-602**），导致「写盘已发生、脚本 exit 1」；`r173h` **14 断言 0 FAIL** 写后复验（H4 MASTER 自洽、H14 G3c/G3d 为 PASS 非 None 假通过）。自错 **S-596/S-597/S-598/S-599/S-600/S-601/S-602** 七条全由可失败断言当场抓出、无一条进结论。
'''

new_txt = txt.rstrip('\n') + '\n' + SEC
new_raw = new_txt.encode('utf-8')
ck('B1 追加后 CR 仍 337', new_raw.count(b'\r') == OLD_CR, new_raw.count(b'\r'))
ck('B2 旧内容是新文件前缀（截掉追加段后逐字节相同）',
   new_raw.startswith(raw.rstrip(b'\n')), True)
ck('B3 §1228 出现恰 1 次', new_txt.count('## §1228') == 1, new_txt.count('## §1228'))
ck('B4 §1227 仍在', new_txt.count('## §1227') == 1, new_txt.count('## §1227'))

bak = os.path.join(BASE, 'GOAL_THREE_TARGETS_20261018.md.before_r173_1228_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('C1 备份独占创建、sha256 == 旧 sha', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == old_sha,
   os.path.basename(bak))

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails)); sys.exit(1)

with open(LED, 'w', encoding='utf-8', newline='') as f:
    f.write(new_txt)
back = open(LED, 'rb').read()
ck('D1 回读逐字节一致', back == new_raw, len(back))
ck('D2 回读 CR 仍 337', back.count(b'\r') == OLD_CR, back.count(b'\r'))
ck('D3 sha256 已变', hashlib.sha256(back).hexdigest() != old_sha, hashlib.sha256(back).hexdigest()[:16])

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('LEDGER: %d B / CR %d / sha %s' % (len(back), back.count(b'\r'), hashlib.sha256(back).hexdigest()[:16]))
json.dump(dict(fails=fails, asserts=n, bytes=len(back), cr=back.count(b'\r'),
               sha=hashlib.sha256(back).hexdigest(), backup=os.path.basename(bak)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173j_ledger.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
