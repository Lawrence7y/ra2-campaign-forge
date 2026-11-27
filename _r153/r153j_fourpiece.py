#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 J：四件套一次性写入（R14_COMMON §2.158 / 台账 §1208 / LEAD_LOCK OK / 看板第 153 轮）。

写入纪律：每件先 wx 独占备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验。
幂等：每段先判目标串是否已存在（S-378）。
"""
import hashlib
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(D, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(D, 'STATUS_BOARD.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')

EXPECT = {
    'R14_COMMON': (RC, '9fa9c4f6625f', 1081),
    'LEDGER': (LED, 'ad33ab08905a', 337),
    'LEAD_LOCK': (LOCK, '12ced0cf45a1', 137),
    'BOARD': (BRD, 'ff59d96c2ccd', 0),
}
fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


for k, (p, sha, cr) in EXPECT.items():
    raw = open(p, 'rb').read()
    ck('pre %s sha %s' % (k, sha), hashlib.sha256(raw).hexdigest().startswith(sha),
       hashlib.sha256(raw).hexdigest()[:12])
    ck('pre %s CR == %d' % (k, cr), raw.count(b'\r') == cr, raw.count(b'\r'))


def backup(p):
    b = os.path.join(BAKDIR, os.path.basename(p) + '.before_r153_%s.bak'
                     % time.strftime('%Y%m%d_%H%M%S'))
    fd = os.open(b, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(b), os.path.exists(b))
    return b


def append_tail(p, marker, block, old_sha, cr):
    raw = open(p, 'rb').read()
    ck('%s 旧 sha' % os.path.basename(p),
       hashlib.sha256(raw).hexdigest().startswith(old_sha), hashlib.sha256(raw).hexdigest()[:12])
    ck('%s 旧 CR == %d' % (os.path.basename(p), cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    txt = raw.decode('utf-8')
    if marker in txt:
        ck('%s 幂等：marker 已存在，跳过写入' % os.path.basename(p), True)
        return
    backup(p)
    new = txt if txt.endswith('\n') else txt + '\n'
    new = new + block
    open(p, 'wb').write(new.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致' % os.path.basename(p), back == new.encode('utf-8'))
    ck('%s CR 未变 == %d' % (os.path.basename(p), cr), back.count(b'\r') == cr, back.count(b'\r'))
    ck('%s marker 已写入' % os.path.basename(p), marker in back.decode('utf-8'))


S2158 = """
## 2.158 【R153, 2026-11-27】FACT_INDEX 甲类锚点判据的**鉴别力**首测：F08 那一项结构上不可能失败；F23 的「已失」要分「曾存在」与「从未存在」两态

### 一 · 起因
R152 待办 4 挂了三轮的「F08 的 evidence_paths 第二项锚点改粒度」，一直停在「只登记、不敢改」。
本轮不做改动，只做一件此前没人做的事：**去测那条判据本身有没有鉴别力**。
结论是它没有 —— 而这一点同时解释了「为什么三轮都看不出该不该改」。

### 二 · R149 §1204 一 的判据在 F08 上恒真
`_r146/r149a_lostpath.py` 的 ANCHOR 表给 F08 只挑了两个 token：`0x449440` 与 `a′`。
两者都在台账 `§1064` 内 ⇒ **该条判据不可能失败**。
而 F08 真正要证明的 a–e 三个地址 `0x47C3D0` / `0x6F322F` / `0x6F2B40`
在 `§1064` **全节（含事项 1–6）各 0 次**，只在 `R14_COMMON` §2.9 一 内（各 1 次）。
把这三地址并入锚点后，判据立刻出现 **3 个未命中**（`_r153/r153g` 第三部分）。
⇒ 「锚点全部命中」在原口径下为真，但**它证明的是「挑的词在节里」，不是「该条内容在节里」**。

### 三 · ANCHOR 表不是从 statement 机械导出的
12 条里有 **10 条**含 statement 里根本不出现的词：F06 的 `C2`/`14`/`00`、F07 的 `[edx+0xA8]`、
F08 的 `a′`、F09 的 `86`、F11 的 `双口径`、F12 的 `只测量`、F13 的 `C3`/`C2`/`modrm`、
F14 的 `勘误`、F15 的 `84`、F16 的 `slot73`。
⇒ R149 那句「锚点取自 statement 自己的地址与数字」只能读成**取意**，不能读成**机械导出**；
任何把它当「已自动核过 statement」的引用都是**过强引用**。

### 四 · 「33 个锚点」的 33 是拆词口径的函数（撤回我自己的一版错判）
我先把 33 判成「与脚本实测 27 不一致」，**那是方向错**（见第六节 S-379）。实测四种拆词口径：
原样不拆 **27**、只拆空格 **29**、空格与加号都拆 **34**、
**空格与加号都拆且方括号串不拆 = 33**（且 33/33 全部逐字命中）。
⇒ **33 不是算错，是口径没写进正文**。凡引该数必须同写拆词口径，
否则 27 / 29 / 33 / 34 四个数都能被说成「按脚本算的」。

### 五 · F23：「已失」必须分两态，且两态现在可机械区分
此前 F23 只写「三目录均不存在」，这只证**现在不在**，不证**从未存在**。
11-22 快照 `files_tier_A_snap2.tsv`（2,351,479 B / 数据行 24,723）在册 `R17_R41_RECOMPUTE` **三件**：
`REPORT.md` **11,824 B** @2026-11-21T11:54:25Z、`crosscheck.json` **1,864 B** @11:54:38Z、
`numbers.tsv` **2,289 B** @11:54:34Z，合计 **15,977 B**，三条 mtime 都落在 R41 之后、快照之前；
同清单 `COVERAGE/coverage.tsv` 主份 **4,147,334 B** @2026-11-21T04:56:21Z 一并可反查。
反控：11,824 B 在快照内**唯一**（排除改名存活）。
⇒ 正确措辞是「**曾在册、内容不可读**」，不是「可能从未存在」。
**结论不变（计数仍不可重数），理由要照此写。**

### 六 · 自错 S-379..S-382（四条，两条方向错）
- **S-379（方向错）**：把「33 个锚点」判成与脚本实测 27 不一致，并据此写「本轮未复现该计数」。
  实测 33 在「空格与加号都拆、方括号串不拆」口径下**恰好复现且 33/33 全命中** ⇒ 原判作废。
- **S-380（方向错）**：断言「F08 是覆盖率最低的 fid」。实测覆盖率 0% 的有 **5 个并列**
  （F09/F11/F12/F13/F14），排序无意义；F08 的缺陷方向恰与它们**相反**
  （它们是「锚点在、statement 无」，F08 是「statement 有、anchor 无」）。
- **S-381**：断言「F08 是唯一在 §1064 内彻底没有 a–e 三串的条目」。实测**有 ABSENT token 的
  fid 共 6 个**（F08/F10/F13/F16）；真正的区分不在「有没有缺」，而在缺的内容**落在哪**。
- **S-382**：`r153h` 里把 `extra = set()` 当字典用，直接 `TypeError`；改 `dict` 后通过。
  与前族同：断言里写进了本该被查询的量。

### 七 · 未取得（不粉饰）
1. F08 的 `evidence_paths` **本轮未改**（改它须单独一卡 + 门禁回归，R150/R151/R152/R153 四轮挂账）。
2. `coverage.tsv` 与 `R41_RECOMPUTE` 三件的**内容仍不可读**，F23 的 458/291/293/1,196 与 1,654 仍**不可重数**。
3. 「33 个锚点」的**原始拆词口径仍无一手记录**：四件里都只写数、不写口径；本轮只证「存在一个使 33 成立的拆词规则」，
   **不证** R149 当时用的就是它。
"""

S1208 = """
## §1208 R153 · FACT_INDEX 甲类锚点判据的鉴别力首测：F08 那一条结构上不可能失败（ANCHOR 只挑了两个 §1064 内必中的 token，a–e 三地址在 §1064 全节 0 次）；「33 个锚点」的 33 是拆词口径的函数（27/29/34/33 四值）；F23 的「已失」分出「曾在册」态

### 一 · 判据恒真：F08 的第二项证据
ANCHOR 表给 F08 只挑 `0x449440` 与 `a′`，两者都在 `§1064` 内 ⇒ 该条**不可能失败**。
F08 真正要证的三地址 `0x47C3D0` / `0x6F322F` / `0x6F2B40` 在 `§1064` 全节（含事项 1–6）**各 0 次**，
只在 `R14_COMMON` §2.9 一 内各 1 次；并入锚点后立刻 3 个未命中。

### 二 · ANCHOR 表 12 条里 10 条含 statement 里没有的词
`C2`/`14`/`00`（F06）、`[edx+0xA8]`（F07）、`a′`（F08）、`86`（F09）、`双口径`（F11）、
`只测量`（F12）、`C3`/`C2`/`modrm`（F13）、`勘误`（F14）、`84`（F15）、`slot73`（F16）。
⇒ 「锚点取自 statement 自身」只能读成取意，不能读成机械导出。

### 三 · 33 是拆词口径的函数
原样 27 / 只拆空格 29 / 空格与加号 34 / **空格与加号拆且方括号不拆 = 33（33/33 全命中）**。
⇒ 33 不是算错，是口径未写入正文；引用必须同写口径。

### 四 · F23 两态
快照在册 `R17_R41_RECOMPUTE` 三件：`REPORT.md` 11,824 B @2026-11-21T11:54:25Z、
`crosscheck.json` 1,864 B @11:54:38Z、`numbers.tsv` 2,289 B @11:54:34Z（合计 15,977 B）；
`COVERAGE/coverage.tsv` 主份 4,147,334 B @04:56:21Z。反控：11,824 B 快照内唯一。
⇒ 措辞改「曾在册、内容不可读」，**结论不变**。

### 五 · 规则 D
执行员 #347（hy4, exec）**succeeded** / 2 回合 / 1.22 分 / 无 OVERTIME；
审计员 #348（deepseek, audit）**partial**：`truncated_at_max_turns (36/35)` —— 如实登记。
两者独立同得 ANCHOR 合计 **27**、33 的传播面（台账 47326 / 归档 8297 / COMPACT_STATE 22 /
R14_COMMON 12599 / LEAD_LOCK 6938 / STATUS_BOARD 0 行）、`§1064` 内三串各 0 次。
**#348 有两处被我复算否定**：①「盘上无任何口径能复现 33」—— 四值表推翻；
② R14_COMMON 行号报 12602 —— 那是 `splitlines()` 口径（多切 `\x0b`×2、`\x0c`×1），
`split("\n")` 与 CRLF 归一都得 **12599**。#347 同样报 12602，**同一口径差，不是数据错**。
#348 另报 R14_COMMON 含 **43** 个 NUL 字节 —— 复算成立（首 5 个在 L186/L187）。

### 六 · 自错 S-379..S-382
S-379（方向错：把 33 判成不一致）、S-380（方向错：「F08 覆盖率最低」，实测 5 个并列 0%）、
S-381（「F08 是唯一有 ABSENT」，实测 6 个）、S-382（`set()` 当 dict 用致 TypeError）。
**四条全是判据/口径缺陷，无一条数据错。**

### 七 · 未取得
① F08 的 evidence_paths 本轮未改（须单独一卡 + 门禁回归，四轮挂账）；
② 两件内容仍不可读，F23 计数仍不可重数；
③ 33 的原始拆词口径无一手记录 —— 本轮只证「存在使 33 成立的规则」，不证 R149 用的是它。
"""

SOK = """
OK1. ✅ **交付一：F08 的第二项证据判据恒真（R152 待办 4 的根因首次被量化）.** `_r146/r149a_lostpath.py` 的 ANCHOR 表给 F08 只挑两个 token `0x449440` 与 `a′`，两者都在台账 `§1064` 内 ⇒ 该条**不可能失败**。而 F08 要证的 a–e 三地址 `0x47C3D0` / `0x6F322F` / `0x6F2B40` 在 `§1064` 全节（事项 1–6）**各 0 次**，只在 `R14_COMMON` §2.9 一 内各 1 次；并入后立刻出现 **3 个未命中**（`_r153/r153g`）。
OK2. 🔴 **交付二：ANCHOR 表不是从 statement 机械导出的，12 条里 10 条有 statement 里没有的词.** `C2`/`14`/`00`(F06)、`[edx+0xA8]`(F07)、`a′`(F08)、`86`(F09)、`双口径`(F11)、`只测量`(F12)、`C3`/`C2`/`modrm`(F13)、`勘误`(F14)、`84`(F15)、`slot73`(F16) ⇒ R149 的「锚点取自 statement 自身」只能读成**取意**。
OK3. 🔴 **交付三：「33 个锚点」的 33 是拆词口径的函数（撤回我自己的首判）.** 原样 **27** / 只拆空格 **29** / 空格与加号 **34** / 空格与加号拆且方括号不拆 **33**（且 33/33 全命中）⇒ 33 不是算错、是**口径未写入正文**；我先前写「与脚本实测 27 不一致」是**方向错**（S-379）。
OK4. ✅ **交付四：F23 的「已失」分出「曾在册」态.** 11-22 快照在册 `R17_R41_RECOMPUTE` 三件 **11,824 / 1,864 / 2,289 B**（合计 15,977 B），mtime 2026-11-21T11:54:25/38/34Z 均落在 R41 之后、快照之前；`COVERAGE/coverage.tsv` 主份 4,147,334 B @04:56:21Z。反控：11,824 B 快照内唯一 ⇒ **「曾在册、内容不可读」而非「可能从未存在」**；结论不变。
OK5. ✅ **交付五：落盘 v5.41 -> v5.42，只追加两行 limitations.** `R17_R114_FACTINDEX_V542/FACT_INDEX.tsv`：**90,976 -> 93,245 B**，sha `f31c8fdc…` -> `1a1de6c5…`，54 数据行 / 全 LF / 56 段；**只有 F08 与 F23 两行第 5 列变化**，其余 **52 行逐字节相同**，`grade` / `evidence_paths` 一字未动。
OK6. ✅ **规则 D：两家独立 + 主会话逐条复算，两条外部主张被否定.** 执行员 **#347（hy4, exec）succeeded** / 2 回合 / 1.22′ / 无 OVERTIME；审计员 **#348（deepseek, audit）partial** —— `truncated_at_max_turns (36/35)`，如实登记。两家独立同得 ANCHOR 合计 **27**、33 的传播面、`§1064` 三串各 0 次。**#348 两条被我复算否定**：①「盘上无任何口径能复现 33」—— 四值表推翻；② R14_COMMON 行号 12602 —— 那是 `splitlines()` 口径（多切 `\\x0b`×2/`\\x0c`×1），`split("\\n")` 与 CRLF 归一都是 **12599**。#347 同报 12602，**同一口径差、非数据错**。#348 报 R14_COMMON 内 **43** 个 NUL 字节 —— 复算成立（首 5 个在 L186/L187）。
OK7. 📌 **口径分歧登记（不是矛盾）.** 「33 个锚点」在 R14_COMMON 的行号：`split("\\n")` = **12599**、`splitlines()` = **12602**、CRLF 归一 = **12599**；差 3 全部来自 `\\x0b`×2 + `\\x0c`×1。凡引行号须写「按哪种切行口径」。
OK8. 📌 **未取得（不粉饰）.** ① F08 的 `evidence_paths` **本轮未改**（须单独一卡 + 门禁回归，R150/R151/R152/R153 四轮挂账）；② `coverage.tsv` 与 `R41_RECOMPUTE` 三件**内容仍不可读**，F23 的 458/291/293/1,196 与 1,654 仍**不可重数**；③ 33 的**原始拆词口径无一手记录** —— 本轮只证「存在使 33 成立的拆词规则」，**不证** R149 当时用的就是它。
OK9. 🔴 **自错 S-379..S-382（四条，两条方向错，无一条数据错）.** **S-379（方向错）** 把「33 个锚点」判成与 27 不一致，实测 V4 拆词口径恰好复现 33/33。**S-380（方向错）** 断言「F08 覆盖率最低」，实测 0% 有 5 个并列（F09/F11/F12/F13/F14）且 F08 缺陷方向相反。**S-381** 断言「F08 是唯一有 ABSENT token」，实测 6 个（F08/F10/F13/F16）。**S-382** `r153h` 把 `set()` 当 dict 用致 `TypeError`。病根与前族同：**断言里写进本该被查询的量**。
"""

BRD_SEC = """
## 🟢 R17 第 153 轮（2026-11-27 05:0x–05:2x）· 去测「那条判据有没有鉴别力」：F08 第二项证据结构上不可能失败（ANCHOR 只挑了两个必中 token，a–e 三地址 §1064 全节 0 次）；「33 个锚点」的 33 是拆词口径的函数（27/29/34/33）

### 一 · 一句话

R152 待办 4「F08 的 evidence_paths 第二项锚点改粒度」挂了四轮不敢动，本轮不动作、只做一件事：**测那条判据本身有没有鉴别力**。结论是没有 —— 这同时解释了「为什么四轮都看不出该不该改」。

### 二 · 判据恒真（F08 的第二项证据）

`_r146/r149a_lostpath.py` 的 ANCHOR 表给 F08 只挑 `0x449440` 与 `a′`，两者都在台账 `§1064` 内 ⇒ **该条不可能失败**。

| 量 | 值 |
|---|---|
| ANCHOR(F08) token 数 | 2（`0x449440` / `a′`） |
| 这两个在 §1064 内 | 2/2 |
| F08 statement 内容 token | 5 |
| 其中 a–e 三地址在 §1064 内 | **0/3**（`0x47C3D0` / `0x6F322F` / `0x6F2B40`） |
| 这三地址在 `R14_COMMON` §2.9 一 内 | 1 / 1 / 1 |
| 并入锚点后的未命中 | **3** |

### 三 · ANCHOR 表不是机械导出的

12 条里 **10 条**含 statement 里根本不出现的词：`C2`/`14`/`00`(F06)、`[edx+0xA8]`(F07)、`a′`(F08)、`86`(F09)、`双口径`(F11)、`只测量`(F12)、`C3`/`C2`/`modrm`(F13)、`勘误`(F14)、`84`(F15)、`slot73`(F16)。⇒「锚点取自 statement 自身」只能读成**取意**。

### 四 · 「33 个锚点」的 33 是拆词口径的函数

| 口径 | 合计 |
|---|---|
| 原样不拆 | 27 |
| 只拆空格 | 29 |
| 空格与加号都拆 | 34 |
| **空格与加号拆、方括号串不拆** | **33（33/33 全命中）** |

⇒ 33 不是算错，是**口径未写进正文**。我先前写「与脚本实测 27 不一致」是**方向错**（S-379）。

### 五 · F23 的「已失」分出「曾在册」态

11-22 快照在册 `R17_R41_RECOMPUTE` 三件：`REPORT.md` **11,824 B** @2026-11-21T11:54:25Z、`crosscheck.json` **1,864 B** @11:54:38Z、`numbers.tsv` **2,289 B** @11:54:34Z（合计 **15,977 B**），mtime 全部落在 R41 之后、快照之前；`COVERAGE/coverage.tsv` 主份 **4,147,334 B** @04:56:21Z。反控：11,824 B 在快照内**唯一**。⇒ 措辞改「**曾在册、内容不可读**」，**结论不变**。

### 六 · 落盘 v5.41 -> v5.42

`R17_R114_FACTINDEX_V542/FACT_INDEX.tsv`：**90,976 -> 93,245 B**，sha `f31c8fdc…` -> `1a1de6c5…`，54 数据行 / 全 LF / 56 段；**只有 F08 与 F23 两行第 5 列变化**，其余 **52 行逐字节相同**，`grade` / `evidence_paths` 一字未动。

### 七 · 规则 D

执行员 **#347（hy4, exec）succeeded** / 2 回合 / 1.22′ / 无 OVERTIME；审计员 **#348（deepseek, audit）partial** —— `truncated_at_max_turns (36/35)`，**如实登记**。两家独立同得 ANCHOR 合计 **27**、33 的传播面、`§1064` 三串各 0 次。**#348 两条经复算被否定**：①「盘上无任何口径能复现 33」；② R14_COMMON 行号报 12602（`splitlines()` 口径，多切 `\x0b`×2 / `\x0c`×1；`split("\n")` 与 CRLF 归一都是 **12599**）。#347 也报 12602 —— **同一口径差，非数据错**。#348 另报 R14_COMMON 含 **43** 个 NUL 字节，**复算成立**（首 5 个在 L186/L187）。

### 八 · 自错 S-379..S-382（四条，两条方向错，无一条数据错）

**S-379（方向错）** 把 33 判成「与脚本 27 不一致」，实测 V4 口径恰好复现 33/33。**S-380（方向错）** 断言「F08 覆盖率最低」，实测 0% 有 5 个并列（F09/F11/F12/F13/F14），且 F08 缺陷方向与它们**相反**（它们是「锚点在、statement 无」，F08 是「statement 有、anchor 无」）。**S-381** 断言「F08 是唯一有 ABSENT token」，实测 **6 个**（F08/F10/F13/F16）；真区分不在「有没有缺」，在缺的内容落在哪。**S-382** `r153h` 把 `set()` 当 dict 用致 `TypeError`。

### 九 · 未取得（不粉饰）

1. F08 的 `evidence_paths` **本轮未改**（须单独一卡 + 门禁回归，R150/R151/R152/R153 四轮挂账）。
2. `coverage.tsv` 与 `R41_RECOMPUTE` 三件**内容仍不可读**，F23 的 458 / 291 / 293 / 1,196 与 1,654 仍**不可重数**。
3. 「33 个锚点」的**原始拆词口径无一手记录**：本轮只证「存在一个使 33 成立的拆词规则」，**不证** R149 当时用的就是它。

### 十 · 下轮优先（禁写元审计待办）

1. **F08 的 `evidence_paths` 改不改**：本轮已证原判据恒真，故「改粒度」的收益与风险都有了量化前提；仍须单独一卡 + 门禁回归（四轮挂账）。
2. **F23 的 `grade` 裁定书**（R151 待办 2，五轮挂账）：前置仍是「须单独裁 + 同时处理 R90 档 2 定性」。
3. **F35 旧句是否回收**：若要删，须先给「删后 V533/V534 溯源从哪里读」的替代入口。
4. 4 行过期肯定句（R14_COMMON L12061 / LEAD_LOCK L6647 / 台账 L47102 / 归档 L7527）的处置：只登记未改。
5. 动态项留 `win-main`：3,805 处寄存器 call/jmp 落点、blowfish.dll 注册链、35 静态容器运行期值、窗口表 r66 后快照。
6. 已判死线继续禁投：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。
"""

print('\n[写 R14_COMMON §2.158]')
append_tail(RC, '## 2.158 【R153', S2158, '9fa9c4f6625f', 1081)
print('\n[写台账 §1208]')
append_tail(LED, '## §1208 R153', S1208, 'ad33ab08905a', 337)
print('\n[写 LEAD_LOCK OK]')
append_tail(LOCK, '\nOK1. ✅ **交付一', SOK, '12ced0cf45a1', 137)
print('\n[写看板第 153 轮]')
append_tail(BRD, '## 🟢 R17 第 153 轮', BRD_SEC, 'ff59d96c2ccd', 0)

print('\n[终态复核]')
raw = open(RC, 'rb').read()
ck('R14_COMMON CR 保持 1081', raw.count(b'\r') == 1081, raw.count(b'\r'))
ck('R14_COMMON 含 §2.158', b'2.158' in raw)
raw = open(LED, 'rb').read()
ck('台账 CR 保持 337', raw.count(b'\r') == 337, raw.count(b'\r'))
ck('台账含 §1208', b'\xc2\xa71208' in raw or '§1208'.encode() in raw)
raw = open(LOCK, 'rb').read()
ck('LEAD_LOCK CR 保持 137', raw.count(b'\r') == 137, raw.count(b'\r'))
ck('LEAD_LOCK 含 OK1', 'OK1.'.encode() in raw)
raw = open(BRD, 'rb').read()
ck('看板 CR 保持 0', raw.count(b'\r') == 0, raw.count(b'\r'))
lines = raw.decode('utf-8').split('\n')
n_line = len([l for l in lines if l])
print('看板行数（非空）= %d ；split("\\n") 段数 = %d' % (n_line, len(lines)))
ck('看板非空行 <= 300', n_line <= 300, n_line)

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
