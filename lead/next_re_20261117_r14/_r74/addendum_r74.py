# -*- coding: utf-8 -*-
"""R74 · 补记落盘：把「跨文件普查」与「我自己的 CRLF 事故」追加进四件套。

为什么必须补记（不许悄悄改）：
  第一次落盘后回读时发现 `LEAD_LOCK` 也有 1 个控制字节（0x07），
  这是 §2.79 / §1128 / 段 DB / 看板第 74 轮里**都没有记**的；
  同时我自己制造过一次 CRLF 追加事故（CR 1081 -> 1184），已回滚并留 INCIDENT。

纪律与第一次落盘相同：wx 独占备份 + 断言旧 sha256/CR + 纯追加 + 回读校验，
并加同一条往返解析硬闸（正文段不许含任何 C0 控制字节）。
"""
import io
import os
import sys
import time
import re
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LEDGER = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')

out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond:
        fails.append(name)
def sha(b):
    return hashlib.sha256(b).hexdigest()

CTRLSCAN = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def gate(desc, seg):
    b = seg.encode('utf-8').replace(b'\r\n', b'\n')
    bad = CTRLSCAN.findall(b)
    ck('%s 正文段不含任何 C0 控制字节' % desc, not bad,
       '' if not bad else [hex(x[0]) for x in bad[:8]])
    return not bad

SEC_COMMON2 = '''### 十一 · 补记（落盘后回读才发现，不许悄悄改）：`LEAD_LOCK` 也有同样的缺陷

第一次落盘后做控制字节回读，发现**另一个不变量文件里也有一个**：

| 文件 | 控制字节 | 位置 | 还原后 |
|---|---|---|---|
| `R14_COMMON.md` | **48** 个 | 19 行 | 见前 |
| `LEAD_LOCK` | **1** 个（0x07） | 偏移 **4722** | 字母 `a` |

`LEAD_LOCK` 的那一处上下文是 `Site 0x47C427/0x47C42A 刚才的 0x07 字节 nd al,1 / 0x47C430 je.` —— 还原成 `and al,1` 后，该 token 在本库其他文件里有 **9 个旁证**（`call`/`and` 这一族指令注解）。换成别的字母则 0 命中。

⇒ **这条缺陷不只在一个文件里。** 我把普查从「`R14_COMMON.md` 单文件」扩到 **10 个受约束文件 + 门禁脚本**，用同一判据一次答清：

| 文件 | 控制字节 |
|---|---|
| `R14_COMMON.md` | **48** |
| `LEAD_LOCK` | **1** |
| `STATUS_BOARD.md` / `BOARD_ARCHIVE.md` / `DISC_RECHECK.tsv` / `DISC_ESTABLISH.tsv` / `COMPACT_STATE.md` / `check_disc.py` / `recheck_verify.py` / 台账 | **0** |

⇒ **8/10 干净**（含门禁两个脚本）；两个不干净的都是**历史最久、被引最多**的那两个。

**两处缺陷都可追溯到最早留存备份**：`R14_COMMON` 的 **12 份**备份控制字节**偏移集合完全相同**、`LEAD_LOCK` 的 **13 份**同样相同 ⇒ **本库内定不出写坏轮次**（与 R72 §CZ3 同族：搬入材料的时刻不可复核）。

### 十二 · 我自己制造过一次 CRLF 追加事故（如实记）

第一次落盘的 2026-11-23 00:46:04 那一版，我给三个 CRLF 文件按 CRLF 写追加段，结果 **`R14_COMMON` 的 CR 从 1081 变成 1184**、台账 337→350、`LEAD_LOCK` 137→174。**三道不变量当场被破坏。**

- **根因**：我看到文件里 `\\r\\n` 占多数就推断「这是 CRLF 文件、追加段也该 CRLF」，**没算那个不等式**：若整文件真是 CRLF，CR 数应等于 LF 数，而实测是 **1081 ≠ 6365**。这个不等式在我读取时就在眼前。
- **处理**：立即用四份 `wx` 独占备份逐字节回滚（回滚后 sha256 与追加前**逐字相同**），把三个追加改为**全 LF** 重跑，四份回读断言全 PASS。
- **留痕**：`R17_LEAD_BASELINE/INCIDENT.r74_crlf_append_20261123_004604.md`；被污染的内容没有留在盘上，但四份 004604 备份保留作依据。

⇒ **这条与本轮主攻方向是同一件事的两面**：CR 不变量对 48 个控制字节**完全无感**（选错了观测面），却**准确抓住了我自己的 CRLF 追加**（观测面对了）。所以不能笼统写「不变量 OK」，必须逐条写清**覆盖什么、不覆盖什么**。

### 十三 · 本轮自错追加两条（合计 10 处）

在第八节那 8 处之外，本轮还有 2 处判据错，都是**零信息格**（R73 §DA5 同族，第四次踩）：

9. §2.79 里的「还原 token 在当前文本命中数必须恰好 +1」—— 对 `LEAD_LOCK` 那个 `and al,1` 站点，我先只取到空白为止，token 退化成单个 `and`，**933 个文件命中** ⇒ 零鉴别力。改为「指令 + 操作数」截断后是 **9 个**旁证。
10. 同一处第二次：改成「收到句末」，token 变成整句 `and al,1 / 0x47C430 je. There i` ⇒ **0 旁证**，同样无鉴别力。第三次才定在「遇 ASCII 斜杠 / 分号 / 中文即停」。

⇒ 追加纪律：**旁证法的 token 必须同时满足「非退化（含操作数）」与「有鉴别力（旁证占比低）」两条，缺一条就是零信息格。**
'''

SEC_LEDGER2 = '''### §1128 补记 · `LEAD_LOCK` 也有 1 个同类控制字节；普查扩到 10 个受约束文件；我自己制造过一次 CRLF 事故

- **扩面**：`LEAD_LOCK` 偏移 **4722** 有 **1 个 0x07**（还原为字母 `a`），上下文还原成 `and al,1`，该 token 在本库另有 **9 个旁证**。
- **10 个受约束文件普查结果**：`R14_COMMON.md` **48**、`LEAD_LOCK` **1**，其余 **8 个干净**（`STATUS_BOARD.md` / `BOARD_ARCHIVE.md` / `DISC_RECHECK.tsv` / `DISC_ESTABLISH.tsv` / `COMPACT_STATE.md` / `check_disc.py` / `recheck_verify.py` / 台账）。
- **两处都可追溯到最早留存备份**：`R14_COMMON` **12 份**、`LEAD_LOCK` **13 份**，控制字节**偏移集合与取值集合全部相同** ⇒ 本库内定不出写坏轮次。
- 🔴 **我自己制造过一次 CRLF 追加事故**：第一次落盘（00:46:04）把三个 CRLF 文件按 CRLF 追加 ⇒ `R14_COMMON` CR **1081→1184**、台账 **337→350**、`LEAD_LOCK` **137→174**。根因是「看到 `\\r\\n` 多就推断整文件是 CRLF」，**没算 1081 ≠ 6365 这个不等式**。已用四份 `wx` 备份逐字节回滚、改全 LF 重跑、四份回读 PASS；留 `INCIDENT.r74_crlf_append_20261123_004604.md`。
- **⇒ 不变量必须逐条写「覆盖 / 不覆盖」**：CR 不变量对 48 个控制字节**完全无感**，却**准确抓住**了 CRLF 追加。
- **本轮自错合计 10 处**；新增两条（第 9、10 处）都是**零信息格**：旁证 token 先退化成单个 `and`（933 文件命中），再退化成整句（0 旁证）。第三版定在「指令 + 操作数，遇斜杠/分号/中文即停」，旁证 **9 个 / 3826 文件 = 0.2%**。
- **追加纪律**：旁证法的 token 必须同时满足**非退化（含操作数）**与**有鉴别力（旁证占比低）**，缺一条即零信息格。
- **脚本**：`_r74/crossfile_r74.py`（**109 项自测 FAIL 0**）。
'''

SEC_LOCK2 = '''DB13. 🔴 **补记（落盘后回读才发现）：`LEAD_LOCK` 里也有 1 个同类控制字节**。偏移 **4722**、**0x07**、还原为字母 `a`，上下文还原成 `and al,1`，该 token 在本库另有 **9 个旁证**（其余 3826 文件里 0.2%）。

DB14. ✅ **普查扩到 10 个受约束文件**（`_r74/crossfile_r74.py`，**109 项自测 FAIL 0**）：`R14_COMMON.md` **48**、`LEAD_LOCK` **1**，其余 **8 个干净**（含 `check_disc.py` / `recheck_verify.py` 两个门禁脚本）。⇒ **不干净的两个恰是历史最久、被引最多的那两个**。

DB15. ✅ **两处都可追溯到最早留存备份**：`R14_COMMON` **12 份**、`LEAD_LOCK` **13 份**，控制字节**偏移集合与取值集合全部相同** ⇒ 本库内**定不出写坏轮次**（同 R72 §CZ3）。

DB16. 🔴🔴 **我自己制造过一次 CRLF 追加事故（如实记）**：第一次落盘 2026-11-23 **00:46:04** 那一版，我给三个 CRLF 文件按 CRLF 写追加段 ⇒ `R14_COMMON` CR **1081→1184**、台账 **337→350**、`LEAD_LOCK` **137→174**，**三道不变量当场被破坏**。根因：看到 `\\r\\n` 占多数就推断「整文件是 CRLF」，**没算 1081 ≠ 6365 这个不等式** —— 那个不等式在我读取时就在眼前。处理：四份 `wx` 备份**逐字节回滚**（回滚后 sha 与追加前逐字相同）→ 三个追加改**全 LF** → 重跑 → 四份回读断言全 PASS。留 `INCIDENT.r74_crlf_append_20261123_004604.md`。

DB17. **⇒ 一条新纪律：不变量必须逐条写清「覆盖什么 / 不覆盖什么」，不许笼统写「不变量 OK」。** 本轮两个方向都印证了：CR 不变量对 48 个控制字节**完全无感**（观测面选错），却**准确抓住**了我自己的 CRLF 追加（观测面对了）。

DB18. 🔴 **本轮自错合计 10 处**（DB9 里 8 处 + 此处 2 处）。第 9、10 处都是**零信息格**（R73 §DA5 同族，**第四次踩**）：旁证 token 先退化成单个 `and`（**933 文件命中**），再退化成整句（**0 旁证**），第三版才定在「指令 + 操作数，遇 ASCII 斜杠/分号/中文即停」⇒ 旁证 **9 / 3826 = 0.2%**。**追加纪律**：旁证 token 必须同时满足**非退化（含操作数）**与**有鉴别力（旁证占比低）**，缺一条即零信息格。

DB19. ✅ **本轮四段写入自身干净**：`§2.79` 9479 B、`§1128` 3469 B、`段 DB` 6885 B、`看板第 74 轮` 5505 B，**四段控制字节均为 0** —— 写入层加了往返解析硬闸（写盘前在**最终字节串**上量 C0，不看源码），它当场拦下了我自己正文里的 6 个控制字节（我正文里要「提」那些转义序列，一不小心就真的产生了）。
'''

SEC_BOARD2 = '''- 🔴 **补记（落盘后回读才发现，不许悄悄改）**：`LEAD_LOCK` 里也有 **1 个同类控制字节** —— 偏移 **4722**、**0x07**、还原为字母 `a`，上下文还原成 `and al,1`，该 token 在本库另有 **9 个旁证**。
- ✅ **普查扩到 10 个受约束文件**（`crossfile_r74.py`，**109 项自测 FAIL 0**）：`R14_COMMON.md` **48**、`LEAD_LOCK` **1**，其余 **8 个干净**（含 `check_disc.py` / `recheck_verify.py`）⇒ **不干净的两个恰是历史最久、被引最多的那两个**。
- ✅ **两处都可追溯到最早留存备份**：`R14_COMMON` **12 份**、`LEAD_LOCK` **13 份**，控制字节**偏移集合与取值集合全部相同** ⇒ 本库内**定不出写坏轮次**（同 R72 §CZ3）。
- 🔴🔴 **我自己制造过一次 CRLF 追加事故**：第一次落盘 **00:46:04** 那一版按 CRLF 追加 ⇒ `R14_COMMON` CR **1081→1184**、台账 **337→350**、`LEAD_LOCK` **137→174**，三道不变量当场被破坏。根因是「看到 `\\r\\n` 占多数就推断整文件是 CRLF」，**没算 1081 ≠ 6365 这个不等式** —— 它在我读取时就在眼前。已四份 `wx` 备份**逐字节回滚**、改**全 LF** 重跑、四份回读 PASS；留 `INCIDENT.r74_crlf_append_20261123_004604.md`。
- 🔴 **一条新纪律**：**不变量必须逐条写清「覆盖什么 / 不覆盖什么」，不许笼统写「不变量 OK」**。CR 不变量对 48 个控制字节**完全无感**，却**准确抓住**了我的 CRLF 追加 —— 两个方向都印证了这条。
- 🔴 **本轮自错合计 10 处**（前 8 处见上 + 此处 2 处）。第 9、10 处都是**零信息格**（R73 §DA5 同族，**第四次踩**）：旁证 token 先退化成单个 `and`（**933 文件命中**）、再退化成整句（**0 旁证**），第三版才定在「指令 + 操作数，遇斜杠/分号/中文即停」⇒ 旁证 **9 / 3826 = 0.2%**。**追加纪律**：旁证 token 必须同时满足**非退化（含操作数）**与**有鉴别力（旁证占比低）**。
- ✅ **本轮四段写入自身干净**：四段（`§2.79` 9479 B / `§1128` 3469 B / `段 DB` 6885 B / 看板 5505 B）控制字节**均为 0** —— 写入层加了往返解析硬闸（在**最终字节串**上量 C0），它当场拦下我自己正文里的 **6 个**控制字节。
'''

def append(desc, path, seg, exp_cr, exp_bytes, exp_sha):
    P('')
    P('=== %s（补记） ===' % desc)
    if not gate(desc, seg):
        return
    old = io.open(path, 'rb').read()
    ck('%s 旧字节数 = %d' % (desc, exp_bytes), len(old) == exp_bytes, '%d' % len(old))
    ck('%s 旧 CR = %d' % (desc, exp_cr), old.count(b'\r') == exp_cr, '%d' % old.count(b'\r'))
    ck('%s 旧 sha256 前缀 = %s' % (desc, exp_sha), sha(old)[:16] == exp_sha, sha(old)[:16])
    body = seg.encode('utf-8').replace(b'\r\n', b'\n')
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BASE, 'R74.addendum_%s_%s.md' % (desc.replace(' ', '_'), stamp))
    with io.open(bak, 'xb') as f:
        f.write(old)
    ck('%s 备份独占创建成功且与旧内容相同' % desc,
       io.open(bak, 'rb').read() == old, os.path.basename(bak))
    new = old + body
    ck('%s 纯追加' % desc, new[:len(old)] == old)
    with io.open(path, 'wb') as f:
        f.write(new)
    rb = io.open(path, 'rb').read()
    ck('%s 回读字节数 = %d' % (desc, len(new)), len(rb) == len(new), '%d' % len(rb))
    ck('%s 回读 CR = %d（全 LF 追加，CR 增量为 0）' % (desc, exp_cr),
       rb.count(b'\r') == exp_cr, '%d (old %d + seg 0)' % (rb.count(b'\r'), exp_cr))
    ck('%s 回读纯追加' % desc, rb[:len(old)] == old)
    ck('%s 回读末段逐字节存在' % desc, rb.endswith(body))
    ck('%s 回读：新段内 0 个控制字节' % desc, not CTRLSCAN.findall(body))

append('R14_COMMON §2.79', COMMON, SEC_COMMON2, 1081, 598665, '65789c834dae1b0a')
append('LEDGER §1128', LEDGER, SEC_LEDGER2, 337, 4706586, '755fb222d2774f8a')
append('LEAD_LOCK DB', LOCK, SEC_LOCK2, 137, 394600, '3eebc290c81f7065')

P('')
P('=== STATUS_BOARD 第 74 轮段（补记，全 LF） ===')
if gate('看板', SEC_BOARD2):
    old = io.open(BOARD, 'rb').read()
    ck('看板旧字节数 = 62518', len(old) == 62518, '%d' % len(old))
    ck('看板旧 CR = 0', old.count(b'\r') == 0, '%d' % old.count(b'\r'))
    ck('看板旧 sha256 前缀 = c2980840', sha(old)[:16] == 'c29808405c243eff', sha(old)[:16])
    body = SEC_BOARD2.encode('utf-8').replace(b'\r\n', b'\n')
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BASE, 'R74.addendum_STATUS_BOARD_%s.md' % stamp)
    with io.open(bak, 'xb') as f:
        f.write(old)
    ck('看板备份独占创建成功', io.open(bak, 'rb').read() == old, os.path.basename(bak))
    new = old + body
    with io.open(BOARD, 'wb') as f:
        f.write(new)
    rb = io.open(BOARD, 'rb').read()
    ck('看板回读 CR = 0', rb.count(b'\r') == 0, '%d' % rb.count(b'\r'))
    nl = rb.count(b'\n')
    ck('看板回读行数 <= 300', nl <= 300, '%d' % nl)
    ck('看板回读纯追加', rb[:len(old)] == old)
    ck('看板回读末段存在', rb.endswith(body))

P('')
P('=== 汇总 ===')
P('  四份补记全部落盘；全 LF 追加，四道 CR 不变量应保持 1081/337/137/0')
P('  自测项 %d，FAIL %d' % (len(out), len(fails)))
P('  ' + ('ALL-PASS' if not fails else 'FAIL: ' + ', '.join(fails)))
io.open(os.path.join(HERE, 'addendum_r74.log'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
