#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 G：四件套追加（R14_COMMON §2.180 / 台账 §1230 / LEAD_LOCK PF / 看板第 175 轮 + 归档最早 2 段）

写入纪律：wx 独占备份 -> 断言旧 sha 与 CR -> 全部断言跑完 -> 一次性写 -> 回读。
CR 不变量：R14_COMMON 1081 / 台账 337 / LEAD_LOCK 137 / 看板 0 / 归档 2952。
看板归档触发：写入后行数 >= 260 ⇒ 先搬走**最早** 2 段（第 168、167 轮）到 BOARD_ARCHIVE。
"""
import hashlib, io, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
F1 = os.path.join(TIER, 'R14_COMMON.md')
F2 = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
F3 = os.path.join(ROOT, 'lead/LEAD_LOCK')
F4 = os.path.join(TIER, 'STATUS_BOARD.md')
F5 = os.path.join(TIER, 'BOARD_ARCHIVE.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r175/r175g_fourpiece.json')
stamp = time.strftime('%Y%m%d_%H%M%S')
EXP_CR = {F1: 1081, F2: 337, F3: 137, F4: 0, F5: 2952}
LIMIT, TRIGGER = 300, 260

fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = bool(cond)

blobs = {p: io.open(p, 'rb').read() for p in (F1, F2, F3, F4, F5)}
print('== W1 · 写入前 CR/行数 ==')
for p, exp in EXP_CR.items():
    ck('W1 %s CR == %d' % (os.path.basename(p), exp), blobs[p].count(b'\r') == exp, blobs[p].count(b'\r'))
    print('     %-20s bytes=%-9d LF=%d sha=%s' % (os.path.basename(p), len(blobs[p]), blobs[p].count(b'\n'),
                                                  hashlib.sha256(blobs[p]).hexdigest()[:16]))
bd_lines = blobs[F4].count(b'\n')
ck('W1b 看板写入前 253 行（实测）', bd_lines == 253, bd_lines)

print('== W2 · 新锚串写入前 0 次 ==')
for p, key in ((F1, '## 2.180'), (F2, '## §1230'), (F3, 'PF · R17 第 175 轮'), (F4, '## 🔵 R17 第 175 轮')):
    ck('W2 %s 在 %s 里 0 次' % (key, os.path.basename(p)), blobs[p].decode('utf-8').count(key) == 0,
       blobs[p].decode('utf-8').count(key))

SEC1 = '''## 2.180 · R175：F24 三口径的「两两差 2 B」被字节测反（实测差集 {12, 2, 14}），并把 5 处被测反的措辞改正入 V557；「清单 913,237 无盘上实物」首次登记

**一 · 差集不是「2 B 与 2 B」.** `r175a_f24_span_recheck.py` **35 断言 0 FAIL**（独立实现：json.loads 取元素数 + 只数方括号的配平法 + 删段判合法，不走 R173 的转义感知顶层扫描器）。现盘 `a2_sites.json` = **17,624,355 B** / sha256 前缀 **7a8447d1d816cdc3**；顶层键只有 calls/bounds；bounds 元素 **1,392,592**、calls 键 **6,728**。值跨度（`[` 到匹配 `]`）**16,711,104**；删「前置逗号 + 键名 + 值」整条成员 **16,711,116**；算术差 17,624,355 − 913,237 **16,711,118**。两两差实测是 **12 / 2 / 14**：12 逐字节等于 `raw[913238:913250] == b', "bounds": '`，2 = `raw[913237]` 的 calls 收尾 `}` 与 `raw[17624354]` 的文档收尾 `}` 各 1 B，14 = 12 + 2。**R173 落盘的「三个数两两差 2 B」是假句**（`_r173/r173a` 的 `measured` 里只记了三个宽度与 `delta_minus_span: 14`，从未记过两两差）。

**二 · 12n 是恒等式、不是逐条长度（采纳审计员 A4/A5 并由主会话复算成立）.** `r175c_audit414_recompute.py` **35 断言 0 FAIL**：bounds 段内本体长度分布实测**只有 {10}**（1,392,592 条）、条目间分隔符分布实测**只有 {b', ': 1,392,591}**、末条之后到 `]` 前**剩 0 B** ⇒ `span = 2 + 10n + 2(n−1) = 12n`，方括号的 +2 与少一个分隔符的 −2 精确抵消。反控两条：本体改 9 B 得 15,318,512、分隔符改 1 B 得 15,318,513，**都不等于** 12n ⇒ 12 只在「10 B 本体 + 2 B 分隔符」成立。⇒ R173 与 V556 里那句「1,392,592 条 × 12 B（每条为 8 位十六进制加引号逗号，恰 12 字节）」**数值对、解释错**（末条没有尾随逗号）。

**三 · 清单 913,237 是声明净额、盘上无实物（本轮首次登记）.** `lead/` 全树 `os.walk` 实测大小恰 913,237 B 的文件 **0 个**；`tier_final_4417.tsv` 里 `a2_sites.json` 恰 **1** 行、`bytes` 列写 **913237**、`why_content` 写「对象抄本 | R59剔除bounds段(纯地址清单,86.19%无字节对应)」⇒ 它是**剔除 bounds 段后的记账额**。闭合式：`len(b'"calls": ')` **9** + `dumps(calls)` **913,228** = **913,237**（与 §2.72 第五节「差 9 B = 键名足迹」一致），且 calls 值跨度实测**恰 913,228**、其末字节 `raw[913237]` 就是 calls 的收尾 `}`。更强的独立判据（审计员 A3 补，主会话复算通过）：`json.dumps(obj, ensure_ascii=False).encode()` 与磁盘原文**逐字节全等 17,624,355 B**；反控 `separators=(',', ':')` 与 `sort_keys=True` 两种参数实测**都不等** ⇒ 该全等不是恒真。⇒ 「清单 913,237 vs 现盘 17,624,355 差 +16,711,118」不是两件文物的差，而是**记账口径差**。

**四 · 假句在落盘件里的分布（逐处定位，不预估）.** `r175b_false2b_copies.py` **5 断言 0 FAIL**：「两两差 2 B」族全库 **4 处** —— FACT_INDEX V556 的 F24.limitations **2 处**（cell 内偏移 7,359 / 17,580）、`R14_COMMON.md` **1 处**、`LEAD_LOCK` **1 处**；statement 内 **0 处**。反控两条：正控串「恰为被剔的 bounds 段」在 F24.statement 命中 **1** 次（扫描器可用）、伪串「两两差 3 B」全库 **0** 次。

**五 · 落盘 V556 → V557（5 处改正 + 1 段补记，只动 F24 的 2 列）.** `r175e_write_v557.py` **41 断言 0 FAIL**（fail-closed：全部断言在写盘之前，S-619 纪律）：C1 statement「bounds 段 16,711,118 B」→ **16,711,104 B** + 订正说明；C2 statement「差 +16,711,118 B 恰为被剔的 bounds 段」→ 记账差（不删数）；C3 limitations「三个数两两差 2 B」→ **差集 {12, 2, 14}**；C4 limitations「三种宽度两两相差 2 B 与 2 B」→ 同；C5 limitations「1,392,592 条 × 12 B…」→ 10 B 本体 + 2 B 分隔符 + 方括号 = **12n 恒等式**；C6 limitations 末尾追加 R175 补记段（含「清单 913,237 无实物」与判别力自评）。V557 = **128,363 B** / sha256 **fc78f3780ef2f320d9bc86555625aaacc7a5198ea1f8fe62648d5a62bb6bdf07** / 55 行 5 列 / CR 0；statement **10,613 → 10,996 B**、limitations **33,011 → 35,453 B**、全文 **+2,825 B**；变化单元恰 {1, 4}，其余 **53 行 × 5 列逐字节相同**，母本 V556 一字未改。**计数如实**：statement 内 16,711,118 改后仍 **4** 次（删 1 处段长形态 + 加 1 处引文），但「作为段长」的形态由 **1 → 0**。

**六 · 门禁重钉与反向验证.** `r175f_repin.py` **35 断言 0 FAIL**：先用 ast 从 `facts_floors` 取 12 个字面量常量、**用旧常量复算旧 MASTER 命中 9ec2296e… 作硬闸**（不同源即禁止写盘），再重钉 `EXPECT_CUR`→V557 / `CUR_SHA256`→fc78f378… / `TOTAL_BYTES`→128,363 / `FLOORS['F24']` (10613,33011)→(10996,35453) / `MASTER_SHA256` 9ec2296e…→**e5cb63ff73ed3d12**，facts 差异 **5 行**；`gate_runner` 只改目录号 **1 行**（实测它不持有旧 sha 与旧 MASTER 字面量，各 0 次）。两条反控：把新 sha 换回 V556 ⇒ MASTER 变化；F24 floor 调大 1 ⇒ MASTER 变化。三段实跑：`facts_floors` **exit 0**（D8 128363 / D9 e5cb63ff）、`gate_runner` **G1=G2=G3=ok**、`check_disc` **exit 0**；`GATE_VER` 仍 **R166**。**反向验证**：显式传 V556 实测 **3 红**（D0 sha 漂移、D6 F24.stmt/lim 缩水、D8 125,538 < 128,363）。

**七 · 跨家族（本轮两件都有回件，一件带 OVERTIME）.** 执行员 #413（hy4flash-free / exec / **2** 回合 / **0.97** 分 / 无 OVERTIME）逐值复现 8 项：文件字节 17,624,355、sha 前 16 **7a8447d1d816cdc3**、顶层键 `['bounds', 'calls']`、bounds **1,392,592**、calls **6,728**、`b', "bounds": '` 恰 1 次且 `raw[913238:913250]` 逐字节等于该 12 B、`raw[913237]` 是 `}`、删成员后 **913,239** 且合法且键只剩 calls —— **与主会话逐值相同，唯一分歧是它报值跨度 16,711,103**（结束偏移取 17,624,353 而非值末 17,624,354，**口径差 1**），已写入 V557 补记。审计员 #414（deepseek / audit / **11** 回合 / **8.37** 分 / **`[OVERTIME: 实测 8.37' vs 预算 6.0']`** 如实登记）A1 成立（并给出「913,237 是自指减法」的独立论证，主会话复算成立且已并入第三节）、A3 **部分成立**（`dumps` 口径同得 16,711,104 但与括号配平**同前提、非独立复核**，并建议改用全文件逐字节回环 —— **采纳**）、A4 **不成立→其结论成立**（原措辞「每条 12 B」错，主会话复算成立并改正）、A5 成立（12n 恒等式）、A6 逐条指认 r175a 的纯字面量断言（E1/E2a/E2b/E2d/C7）与低判别力断言（D1）—— **全部复算成立并写入 V557 补记的判别力自评**。

**八 · 自错 S-626..S-632（七条，全部由可失败断言当场抓出；无一条进入 V557 正文以外的结论）.** **S-626** 沿用 R173 的「每条 12 B」，实测本体只有 10 B、分隔符 `, ` 2 B；**S-627** 把应然数写进断言标签（`'... == 2' if len(ctx)==2 else ...'`），实测 4 处；**S-628** 断言「`ensure_ascii=True` 必然与原文不等」，实测该文件全 ASCII ⇒ 两种参数**逐字节相同**，真判别力反控须换 `separators`/`sort_keys`；**S-629** 把「bounds 段内的本体数」当「全文本体数」，实测全文 **1,467,573**（多出 calls 段的 74,981 = 6,728 键 + 68,253 值）；**S-630 最重**：我把 calls 值区间取成 `raw[10:913237]`（少取末字节）得 913,227，并据此「订正」审计员的 9 + 913,228 = 913,237 —— **审计员对、我错**，已加两条可失败反控（该区间 `json.loads` 必失败、末字节偏移必为 913,237）钉住；**S-631** 拿 F35 的锚串去定位 F24 的末句（F24 里根本没有那句），实测 0 次后改用真实末句；**S-632** 预估 statement 的 16,711,118 改后为 3 次、实测 4 次（订正句自身引用了原值）。**族谱**：S-626/S-628/S-630/S-632 属「把应然数当实测」（第六次复发）；S-627 属「断言标签带应然数」；S-629 属「作用域错」；S-631 属「跨条目串用」。

**九 · 未取得（不粉饰）.** ① 审计员 #414 的 A7（r175b 是否漏检）与 A8（是否存在第三种读数使 16,711,118 恰为某真实跨度）在其 11 回合内**未作答**（回件在 A6 处截断）⇒ 这两条只能由主会话自测覆盖，A8 的反面已由「两两差 12/2/14」给出但**未穷举**；② `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 的 458/291/293/1,196,1,654 与 F35 的 n 分母仍不可重数；③ F23（`未取得`）/ F35（`[流程]`）的 grade 未改（改 grade 是裁定）；④ C7 三死分支 exists/bytes=/none 仍各 0 行；⑤ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑥ `a2_sites` 原始生成器已复原（R164）但 86.19% 原值仍不可重算；⑦ `_ext/f_partial_triage/` 两件未补版本号。
'''

SEC2 = '''## §1230 · R175：F24 的「两两差 2 B」被字节测反（实测差集 {12, 2, 14}，12 = `, "bounds": ` 的字节数）；5 处被测反的措辞改正入 V557，并首次登记「清单 913,237 盘上无实物」（V556→V557）

**一 · 判据先行：相邻差必须逐字节找到实体，找不到实体就不许写进正文.** `r175a` **35 断言 0 FAIL**（独立于 R173 的实现：`json.loads` 取元素数、只数方括号的配平法、删段判合法）。三口径实测 **16,711,104 / 16,711,116 / 16,711,118**；两两差 **12 / 2 / 14**：**12** 逐字节等于 `raw[913238:913250] == b', "bounds": '`；**2** = `raw[913237]`（calls 收尾 `}`）与 `raw[17624354]`（文档收尾 `}`）各 1 B；**14** = 12 + 2。⇒ R173 落的「三个宽度两两相差 2 B 与 2 B」是**假句**，V556 里它在 F24.limitations 有 **2** 处、`R14_COMMON` **1** 处、`LEAD_LOCK` **1** 处（`r175b` **5 断言 0 FAIL**，正控 1 次 / 伪串 0 次）。

**二 · 「12n」是恒等式不是逐条长度（跨家族审计 A4/A5 成立并由主会话复算）.** `r175c` **35 断言 0 FAIL**：bounds 段内本体长度分布**只有 {10}**（1,392,592 条）、分隔符分布**只有 {b', ': 1,392,591}**、末条后到 `]` 前**剩 0 B** ⇒ `2 + 10n + 2(n−1) = 12n`。两条反控：本体 9 B ⇒ 15,318,512、分隔符 1 B ⇒ 15,318,513，**都不等于** 12n。⇒「1,392,592 条 × 12 B（每条…恰 12 字节）」**数值对、解释错**。

**三 · 清单 913,237 是声明净额、盘上 0 实物.** `lead/` 全树 `os.walk` 实测恰 913,237 B 的文件 **0 个**；`tier_final_4417.tsv` 该行 `bytes` = **913237**、`why_content` 写「R59剔除bounds段」；闭合式 `9`（`b'"calls": '`）+ `913,228`（`dumps(calls)`）= **913,237**，calls 值末字节偏移恰 **913,237**。审计员 A3 补的更强判据（主会话复算通过）：`json.dumps(obj, ensure_ascii=False).encode()` 与磁盘原文**逐字节全等 17,624,355 B**，而 `separators=(',', ':')`、`sort_keys=True` 两条反控**都不等** ⇒ 非恒真。⇒ F24 里「清单 vs 现盘差 +16,711,118」是**记账口径差**，不是两件文物的差。

**四 · 落盘与门禁.** V556 → **V557** = **128,363 B** / **fc78f3780ef2f320d9bc86555625aaacc7a5198ea1f8fe62648d5a62bb6bdf07** / 55 行 5 列 / CR 0；5 处改正 + 1 段补记，只动 F24 的 statement 与 limitations（变化单元 {1,4}，其余 53 行 × 5 列逐字节相同），statement **10,613 → 10,996**、limitations **33,011 → 35,453**、全文 **+2,825 B**；「作为段长的 16,711,118」由 **1 → 0** 处（总数仍 4，因订正句自身引用原值）。`r175f` **35 断言 0 FAIL**：ast 取常量 + 旧常量复算旧 MASTER 命中 `9ec2296e…` 作硬闸 → 重钉 `EXPECT_CUR`/`CUR_SHA256`/`TOTAL_BYTES`/`FLOORS['F24']`/`MASTER_SHA256`（**e5cb63ff73ed3d12**），facts 差异 **5 行**、gate_runner **1 行**（不持有 sha 字面量，实测 0 次）。三段实跑全 ok、`GATE_VER` 仍 **R166**；**反向验证**：显式传 V556 实测 **3 红**（D0/D6/D8）。

**五 · 跨家族（两件皆有回件）.** 执行员 #413（hy4 / **2** 回合 / **0.97** 分 / 无 OVERTIME）八项逐值复现，唯一分歧是值跨度报 **16,711,103**（结束偏移取 17,624,353，**口径差 1**）。审计员 #414（deepseek / **11** 回合 / **8.37** 分 / **`[OVERTIME: 实测 8.37' vs 预算 6.0']`** 如实登记）A1 成立、A3 部分成立（`dumps` 口径**同前提非独立**，建议改用全文件逐字节回环 —— 采纳）、A4 成立（「每条 12 B」措辞错 —— 采纳并改正）、A5 成立（12n 恒等式）、A6 成立（指认 r175a 的 5 条纯字面量断言与 D1 低判别力 —— 采纳并写入补记）；**A7/A8 未作答**（回件在 A6 处截断）。

**六 · 自错七条（S-626..S-632）.** S-626 沿用「每条 12 B」；S-627 断言标签带应然数（2 vs 实测 4）；S-628 `ensure_ascii` 反控方向错（该文件全 ASCII，两参数逐字节相同）；S-629 把「段内本体数」当「全文本体数」（实测全文 1,467,573，多出的 74,981 = 6,728 键 + 68,253 值）；**S-630 最重：我把 calls 值区间少取末字节得 913,227 并据此「订正」审计员 —— 审计员对、我错**，已加两条可失败反控钉住；S-631 拿 F35 的锚串定位 F24 末句（实测 0 次）；S-632 预估 3 次实测 4 次。**族谱**：「把应然数当实测」第四次……（本轮为第六次复发）/「作用域错」/「跨条目串用」。

**七 · 未取得.** A7/A8 未由审计员覆盖且**未穷举**；`coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 四计数与 F35 n 分母仍不可重数；F23/F35 grade 未改（裁定不是取证）；C7 三死分支仍 0 行；C11 id 3/4/22/27/28 未动；86.19% 原值仍不可重算；`_ext/f_partial_triage/` 两件未补版本号。
'''

SEC3 = '''

PF · R17 第 175 轮（2026-11-27 14:1x–14:5x）· F24 的「三口径两两差 2 B」被字节测反（实测差集 {12, 2, 14}，12 逐字节就是 `, "bounds": ` 的 12 B）；5 处被测反的措辞改正入 V557；跨家族两件都有回件，审计员 11 回合 8.37 分带 OVERTIME

PF1. 🔴 **交付一：差集是 {12, 2, 14}，不是「2 B 与 2 B」.** `r175a` **35 断言 0 FAIL**（实现独立于 R173：`json.loads` 取元素数 + 只数方括号的配平法 + 删段判合法）。三口径 **16,711,104 / 16,711,116 / 16,711,118**；12 逐字节等于 `raw[913238:913250] == b', "bounds": '`，2 = calls 收尾 `}` 与文档收尾 `}` 各 1 B，14 = 12 + 2。R173 的「两两相差 2 B 与 2 B」是**假句**，在 V556 的 F24.limitations 有 **2** 处、`R14_COMMON` **1** 处、`LEAD_LOCK` **1** 处（`r175b` 5 断言，正控 1 / 伪串 0）。

PF2. 🔴 **交付二：「12n」是恒等式，不是逐条 12 字节.** `r175c` **35 断言 0 FAIL**：bounds 段本体长度分布**只有 {10}**、分隔符分布**只有 {b', ': 1,392,591}**、末条后到 `]` 前**剩 0 B** ⇒ `2 + 10n + 2(n−1) = 12n`。反控：本体 9 B ⇒ 15,318,512、分隔符 1 B ⇒ 15,318,513，均**不等于** 12n。

PF3. 🔴 **交付三：清单 913,237 盘上 0 实物（本轮首次登记）.** `lead/` 全树恰 913,237 B 的文件 **0 个**；清单该行 `bytes` = 913237、`why_content` 写「R59剔除bounds段」；闭合 `9 + 913,228 = 913,237`，calls 值末字节偏移恰 **913,237**。审计员 A3 补的更强判据（我复算通过）：`json.dumps(obj, ensure_ascii=False).encode()` 与原文**逐字节全等 17,624,355 B**，而 `separators=(',', ':')` / `sort_keys=True` 两条反控**都不等**。

PF4. ✅ **交付四：落盘 V556 → V557（5 处改正 + 1 段补记，只动 F24 两列）.** **128,363 B** / `fc78f3780ef2f320…` / 55 行 5 列 / CR 0；statement **10,613 → 10,996**、limitations **33,011 → 35,453**、全文 **+2,825 B**；变化单元恰 {1,4}、其余 **53 行 × 5 列逐字节相同**、母本一字未改；「作为段长的 16,711,118」**1 → 0** 处（总数仍 4，订正句自身引原值）。

PF5. ✅ **交付五：门禁重钉 fail-closed + 反向验证三红.** `r175f` **35 断言 0 FAIL**：ast 取 12 常量、**旧常量复算旧 MASTER 命中 `9ec2296e…`** 作硬闸 → 重钉 `EXPECT_CUR`/`CUR_SHA256`/`TOTAL_BYTES`/`FLOORS['F24']` (10613,33011)→(10996,35453) / `MASTER_SHA256` → **`e5cb63ff73ed3d12`**（facts 差异 **5 行**）；`gate_runner` 只改目录号 **1 行**（实测不持有旧 sha/旧 MASTER 字面量，各 0 次）。两反控：新 sha 换回 V556 ⇒ MASTER 变；F24 floor +1 ⇒ MASTER 变。三段实跑全 ok、`GATE_VER` 仍 **R166**；显式传 V556 实测 **D0 + D6 + D8 三红**。

PF6. 📌 **跨家族：两件都有回件（本轮罕见）.** 执行员 #413（hy4 / **2** 回合 / **0.97** 分 / 无 OVERTIME）八项逐值复现，唯一分歧 **16,711,103**（结束偏移取 17,624,353，口径差 1，已写入 V557 补记）。审计员 #414（deepseek / **11** 回合 / **8.37** 分 / **`[OVERTIME: 实测 8.37' vs 预算 6.0']`** 如实登记）：A1 成立、A3 **部分成立**（`dumps` 与括号配平同前提、非独立复核，建议全文件逐字节回环 —— 采纳）、A4 成立（措辞错 —— 采纳改正）、A5 成立、A6 成立（指认 5 条纯字面量断言 + D1 低判别力 —— 采纳）；**A7/A8 未作答**（回件在 A6 处截断）。

PF7. 📌 **S-626..S-632 七条自错（全部由可失败断言当场抓出）.** S-626 沿用「每条 12 B」；S-627 断言标签带应然数（2 vs 实测 4）；S-628 `ensure_ascii` 反控方向错（该文件全 ASCII，两参数逐字节相同）；S-629 段内本体数当全文（全文 **1,467,573** = 1,392,592 + 74,981，74,981 = 6,728 键 + 68,253 值）；**S-630 最重：calls 值区间少取末字节得 913,227，并据此「订正」审计员 —— 审计员对、我错**，已加两条可失败反控；S-631 拿 F35 锚串定位 F24 末句（实测 0 次）；S-632 预估 3 实测 4。**族谱**：「把应然数当实测」第六次复发 /「作用域错」/「跨条目串用」。

PF8. 📌 **未取得（不粉饰）.** ① 审计员 A7/A8 未作答且**未穷举**；② `coverage.tsv` / `function_atlas.tsv` 仍不可读 ⇒ F23 四计数与 F35 n 分母仍不可重数；③ F23（`未取得`）/ F35（`[流程]`）grade 未改（裁定不是取证）；④ C7 三死分支 exists/bytes=/none 仍各 0 行；⑤ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑥ `a2_sites` 生成规则已复原（R164）但 86.19% 原值仍不可重算；⑦ `_ext/f_partial_triage/` 两件未补版本号。
'''

SEC4 = '''
## 🔵 R17 第 175 轮（2026-11-27 14:1x–14:5x）· F24 的「三口径两两差 2 B」被字节测反（实测差集 **{12, 2, 14}**，12 逐字节就是 `, "bounds": ` 的 12 B）；5 处被测反的措辞改正入 V557；「清单 913,237 盘上 0 实物」首次登记

**入口**：R174 待办 ①（F24 的 statement 仍写「差 +16,711,118 B 恰为被剔的 bounds 段」，而 limitations 已判它错）。本轮不改 grade、不改任何既有数字的记账口径，只把**被字节测反的措辞**改正，并给差集找到逐字节实体。五脚本 **121 断言 0 FAIL**（a 35 / b 5 / c 35 / d 17 / e 41 / f 35 —— 含三条订正前的自错断言已改正）。

| 口径 | 值 | 盘上实体 |
|---|---:|---|
| bounds 值跨度 | **16,711,104** | `[` 到匹配 `]` = 2 + 10n + 2(n−1) |
| 删整条成员 | **16,711,116** | 前置逗号起、含 `, "bounds": ` 12 B |
| 算术差 | **16,711,118** | 17,624,355 − 913,237（**记账口径差**）|

**判据一（差集逐字节）**：两两差 **12 / 2 / 14** —— 12 逐字节等于 `raw[913238:913250] == b', "bounds": '`；2 = `raw[913237]`（calls 收尾 `}`）与 `raw[17624354]`（文档收尾 `}`）各 1 B；14 = 12 + 2。R173 落的「三个宽度两两相差 2 B 与 2 B」是**假句**，全库 **4** 处（V556 的 F24.limitations 2 / R14_COMMON 1 / LEAD_LOCK 1；statement 0 处）。

**判据二（12n 是恒等式）**：bounds 段内本体长度分布实测**只有 {10}**（1,392,592 条）、分隔符分布实测**只有 {b', ': 1,392,591}**、末条之后到 `]` 前**剩 0 B** ⇒ `2 + 10n + 2(n−1) = 12n`（括号 +2 与少一个分隔符 −2 抵消）。反控：本体 9 B ⇒ 15,318,512、分隔符 1 B ⇒ 15,318,513，均**不等于** 12n。⇒「1,392,592 条 × 12 B（每条…恰 12 字节）」**数值对、解释错**。

**判据三（913,237 无实物）**：`lead/` 全树 `os.walk` 实测大小恰 913,237 B 的文件 **0 个**；清单该行 `bytes` = **913237**、`why_content` 写「R59剔除bounds段」；闭合 `len(b'"calls": ')` **9** + `dumps(calls)` **913,228** = **913,237**，calls 值末字节偏移恰 **913,237**。审计员补的更强判据（主会话复算通过）：`json.dumps(obj, ensure_ascii=False).encode()` 与原文**逐字节全等 17,624,355 B**，而 `separators=(',', ':')` / `sort_keys=True` **都不等** ⇒ 非恒真。

**落盘**：V556 → **V557**（**128,363 B** / `fc78f3780ef2f320…` / 55 行 5 列 / CR 0）：C1 statement「bounds 段 16,711,118 B」→ **16,711,104 B**；C2「恰为被剔的 bounds 段」→ 记账差；C3/C4「两两差 2 B」→ **差集 {12, 2, 14}**；C5「每条 12 B」→ 12n 恒等式；C6 limitations 末尾追加 R175 补记。statement **10,613 → 10,996 B**、limitations **33,011 → 35,453 B**、全文 **+2,825 B**；变化单元恰 {1,4}、其余 **53 行 × 5 列逐字节相同**、母本一字未改；「作为段长」的 16,711,118 **1 → 0** 处（总数仍 4，订正句自身引原值）。

**门禁**：`r175f` 用 ast 取 12 常量、**旧常量复算旧 MASTER 命中 `9ec2296e…`** 作硬闸 → 重钉 `EXPECT_CUR`/`CUR_SHA256`/`TOTAL_BYTES`/`FLOORS['F24']`/`MASTER_SHA256`（**`e5cb63ff73ed3d12`**），facts 差异 **5 行**、gate_runner **1 行**；两反控（新 sha 换回 V556、F24 floor +1）均使 MASTER 变化。三段实跑全 ok、`GATE_VER` 仍 **R166**；**反向验证**显式传 V556 实测 **D0+D6+D8 三红**。

**跨家族（两件皆有回件）**：执行员 #413（hy4 / **2** 回合 / **0.97** 分 / 无 OVERTIME）八项逐值复现，唯一分歧值跨度 **16,711,103**（结束偏移取 17,624,353，口径差 1，已写入补记）；审计员 #414（deepseek / **11** 回合 / **8.37** 分 / **`[OVERTIME: 实测 8.37' vs 预算 6.0']`** 如实登记）A1 成立 / A3 部分成立（同前提非独立，建议全文件回环 —— 采纳）/ A4 成立（措辞错 —— 采纳改正）/ A5 成立 / A6 成立（5 条纯字面量断言 + D1 低判别力 —— 采纳）；**A7/A8 未作答**。

**自错 S-626..S-632（七条，全部由可失败断言当场抓出）**：S-626 沿用「每条 12 B」；S-627 断言标签带应然数（2 vs 实测 4）；S-628 `ensure_ascii` 反控方向错（该文件全 ASCII）；S-629 段内本体数当全文（实测全文 1,467,573 = 1,392,592 + 74,981，74,981 = 6,728 键 + 68,253 值）；**S-630 最重：calls 值区间少取末字节得 913,227 并据此「订正」审计员 —— 审计员对、我错**；S-631 拿 F35 锚串定位 F24 末句（实测 0 次）；S-632 预估 3 实测 4。**族谱**：「把应然数当实测」第六次复发 /「作用域错」/「跨条目串用」。

**未取得**：① 审计员 A7/A8 未作答且**未穷举**；② coverage.tsv / function_atlas.tsv 仍不可读 ⇒ F23 四计数与 F35 n 分母仍不可重数；③ F23/F35 grade 未改（裁定不是取证）；④ C7 三死分支仍 0 行；⑤ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑥ 86.19% 原值仍不可重算；⑦ `_ext/f_partial_triage/` 两件未补版本号。
'''

print('== W3 · 构造新内容 ==')
t1 = blobs[F1].decode('utf-8'); t2 = blobs[F2].decode('utf-8'); t3 = blobs[F3].decode('utf-8')
t4 = blobs[F4].decode('utf-8'); t5 = blobs[F5].decode('utf-8')
n1 = t1 + '\n' + SEC1
n2 = t2 + '\n' + SEC2
n3 = t3 + SEC3
ck('W3a R14_COMMON 新 CR 仍 1081', n1.encode('utf-8').count(b'\r') == 1081, n1.encode('utf-8').count(b'\r'))
ck('W3b 台账新 CR 仍 337', n2.encode('utf-8').count(b'\r') == 337, n2.encode('utf-8').count(b'\r'))
ck('W3c LEAD_LOCK 新 CR 仍 137', n3.encode('utf-8').count(b'\r') == 137, n3.encode('utf-8').count(b'\r'))
ck('W3d 三件新内容都以母本为前缀', n1.startswith(t1) and n2.startswith(t2) and n3.startswith(t3), True)
ck('W3e R14_COMMON §2.180 恰 1 次', n1.count('## 2.180') == 1, n1.count('## 2.180'))
ck('W3f 台账 §1230 恰 1 次', n2.count('## §1230') == 1, n2.count('## §1230'))
ck('W3g LEAD_LOCK PF 段恰 1 次', n3.count('PF · R17 第 175 轮') == 1, n3.count('PF · R17 第 175 轮'))

# ---- 看板 + 归档 ----
n4_try = t4 + SEC4
lines_try = n4_try.count('\n')
print('     看板写入后预计 %d 行（阈值 %d）' % (lines_try, TRIGGER))
arch_add = ''
if lines_try >= TRIGGER:
    bl = t4.split('\n')
    heads = [i for i, l in enumerate(bl) if l.startswith('## ')]
    ck('W4a 看板段头数 >= 4（可安全搬走最早 2 段）', len(heads) >= 4, len(heads))
    cut = heads[2]
    arch_add = '\n'.join(bl[:cut]) + '\n'
    n4 = '\n'.join(bl[cut:]) + SEC4.lstrip('\n').join(['\n', '']) if False else ('\n'.join(bl[cut:]).lstrip('\n') + SEC4)
    if not n4.startswith('## '):
        n4 = '\n'.join(bl[cut:])
        n4 = n4 + SEC4
    ck('W4b 搬走的是最早 2 段（第 168、167 轮）', 'R17 第 168 轮' in arch_add and 'R17 第 167 轮' in arch_add,
       ('168' in arch_add, '167' in arch_add))
    ck('W4c 搬走后看板不再含第 168/167 轮', 'R17 第 168 轮' not in n4 and 'R17 第 167 轮' not in n4,
       ('R17 第 168 轮' in n4, 'R17 第 167 轮' in n4))
    n5 = t5.rstrip('\n') + '\n\n' + arch_add.rstrip('\n') + '\n'
else:
    n4 = n4_try
    n5 = t5
    ck('W4a 未触发归档（写入后 < 260 行）', True, lines_try)
ck('W5a 看板新 CR == 0', n4.encode('utf-8').count(b'\r') == 0, n4.encode('utf-8').count(b'\r'))
ck('W5b 看板新行数 <= 300', n4.count('\n') <= LIMIT, n4.count('\n'))
ck('W5c 看板新行数 < 260（不触发下一轮立刻归档）', n4.count('\n') < TRIGGER, n4.count('\n'))
ck('W5d 归档新 CR 仍 2952', n5.encode('utf-8').count(b'\r') == 2952, n5.encode('utf-8').count(b'\r'))
ck('W5e 第 175 轮段在看板恰 1 次', n4.count('R17 第 175 轮') == 1, n4.count('R17 第 175 轮'))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'res': res}, ensure_ascii=False, indent=1))
    sys.exit(1)

print('== W6 · wx 备份 + 一次性写盘 ==')
for name, p, old, new in (('R14_COMMON.md', F1, t1, n1), ('GOAL_THREE_TARGETS', F2, t2, n2),
                          ('LEAD_LOCK', F3, t3, n3), ('STATUS_BOARD.md', F4, t4, n4),
                          ('BOARD_ARCHIVE.md', F5, t5, n5)):
    raw = io.open(p, 'rb').read()
    osha = hashlib.sha256(raw).hexdigest()
    assert raw.decode('utf-8') == old, name + ' 母本被外部改动'
    bak = os.path.join(BASE, '%s.before_r175_%s_%s.bak' % (name, name, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('W6a %s 备份 sha 命中旧 sha' % name,
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == osha, os.path.basename(bak))
    io.open(p, 'w', encoding='utf-8', newline='').write(new)
    back = io.open(p, 'rb').read()
    ck('W6b %s 回读与内存构造一致' % name, back == new.encode('utf-8'), len(back))
    ck('W6c %s 回读 CR == 期望' % name, back.count(b'\r') == EXP_CR[p], back.count(b'\r'))
    print('     %-22s %d -> %d B / %d 行 / CR %d / sha %s' %
          (name, len(raw), len(back), back.count(b'\n'), back.count(b'\r'), hashlib.sha256(back).hexdigest()[:16]))

res.update({'fails': fails, 'assertions': n, 'archived': len(arch_add.split('\n')) if arch_add else 0})
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
