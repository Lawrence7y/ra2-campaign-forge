#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 F：四件套 + FACT_INDEX 追加（写入纪律：wx 独占备份 -> 断言旧 sha -> 写 -> 回读）。"""
import hashlib, os, shutil, sys

ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=os.path.join(ROOT,'lead')
D14=os.path.join(LEAD,'next_re_20261117_r14')
BASE=os.path.join(D14,'R17_LEAD_BASELINE')
os.makedirs(BASE,exist_ok=True)
TAG='r149'
fails=[]

def ck(n,c,d=''):
    ok=bool(c)
    print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def crcount(p):
    return open(p,'rb').read().count(b'\r')

def sha(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest()

def backup(p):
    b=os.path.join(BASE, os.path.basename(p)+'.before_'+TAG+'.bak')
    fd=os.open(b, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o644)   # wx 独占
    with os.fdopen(fd,'wb') as f:
        f.write(open(p,'rb').read())
    return b

def append(p, text, expect_cr):
    old_sha=sha(p); old_cr=crcount(p); old_n=open(p,'rb').read().count(b'\n')
    b=backup(p)
    ck('backup wx 独占创建 '+os.path.basename(p), os.path.exists(b))
    ck('backup 字节等于源 '+os.path.basename(p), sha(b)==old_sha)
    raw=open(p,'rb').read()
    assert b'\r' not in text.encode('utf-8'), 'text has CR'
    with open(p,'ab') as f:
        f.write(text.encode('utf-8'))
    new_cr=crcount(p); new_n=open(p,'rb').read().count(b'\n')
    ck('CR 保持 '+str(expect_cr)+' ('+os.path.basename(p)+')', new_cr==expect_cr, new_cr)
    ck('仅追加（行数只增）('+os.path.basename(p)+')', new_n>old_n, f"{old_n}->{new_n}")
    # 回读：前缀 sha 必须等于旧 sha
    ck('前缀 sha 等于旧 sha ('+os.path.basename(p)+')',
       hashlib.sha256(open(p,'rb').read()[:len(raw)]).hexdigest()==old_sha)
    return old_sha

print("=== A. R14_COMMON 新增 §2.154 ===")
P=os.path.join(D14,'R14_COMMON.md')
ck('A0 旧 §2.153 是最后一节',
   open(P,encoding='utf-8').read().rstrip().rfind('## 2.153')>0)
SEC2154 = """
## 2.154 【R149, 2026-11-27】FACT_INDEX 失联路径的成分拆解：16 条里 5 条是台账合并、11 条才是真失；并把 R90「F23 档 2（可重算）」这条裁定的判据证伪

### 一 · 起因

R148 收口时把「F23 的 grade 该不该降」挂成下一轮第一待办，理由只有一句「evidence 2/2 全失联」。
本轮把它拆成两个可机械判定的小问题：① 全表 16 条失联路径是不是同一类东西；② R90 已下的「可重算 ⇒ 不降级不升格」这条裁定，其判据本身站不站得住。

### 二 · 16 条失联路径的成分（两类，不是一类）

口径：`FACT_INDEX.tsv`（v5.40，`fabd1e57…`）第 4 列按第一个左圆括号切掉锚点，反斜杠换正斜杠，依次相对 `lead/` 与仓库根判存在。实测 178 个证据项 / 43 个失联项 / 16 条唯一失联路径。

- **甲类（5 条）：台账合并型。** `R17_LEDGER_1062 / 1063 / 1063R / 1064 / 1065` 的 `SECTION.md` 目录不在，但 `GOAL_THREE_TARGETS_20261018.md` 里有同编号节 `§1062 / §1063 / §1064 / §1065`（`§1063R` 无同名节）。
  - 逐 fid 锚点复算（锚点取自 statement 自己的地址与数字，不用台账措辞）：F04/F06/F07/F08/F09/F10/F11/F12/F13/F14/F15/F16 共 **12 个 fid、33 个锚点全部逐字命中**。
  - `§1063R` 无同名节的解释在盘：`R17_LEDGER_1063/SUPERSEDED.md` 明写「台账 §1063 采用的是 `R17_LEDGER_1063R` 版本（129/125/5/19）」，且该目录自己标注「已作废，请勿引用」。
  - **反控（判据不得恒真）**：`§1063` 里同时存在被作废的旧值 `108/82/4/33` 与「不得引用」四个字；用自造串 `ZZZ_NOT_IN_LEDGER_QQQ` 查同一节必须 0 命中。
- **乙类（11 条）：真失。** `COVERAGE/PANEL.md`（8 个 fid 引用）、`R17_DELIVERY/DELIVERY_SUMMARY.md`（4 个）、`R17_AUDIT_R9`、`R17_AUDIT_FI_V5`、`NAMED_PUSH_AUDIT10`、`S10_KPROVED/_audit`、`S13_K10/_audit`、`S13_K12/_audit` 的 `VERDICT.md`、`GATE_BEHAV/PROGRESS.md`、`HANDOFF_R14_R3.md`、`HANDOFF_R16.md`。

**结论一：把「5 条台账合并」与「11 条真失」混成一个 16 来谈，会系统性高估失联严重度。** 甲类不构成内容失联。

### 三 · 但 F23 仍是全表唯一的零存活项

按同一口径统计「第 4 列一项都不存在」的行：**全表恰 1 行，是 F23，其 grade 仍是 `[已证]`。** 它的两项 `R17_DELIVERY/DELIVERY_SUMMARY.md(§2)` 与 `COVERAGE/PANEL.md(M86 / M93)` 都属乙类真失。所以第二节的结论**不能**用来给 F23 减负。

### 四 · R90「F23 档 2（可重算）」的判据被证伪

R90 原文（`BOARD_ARCHIVE.md:4915`）：「7 个数字全部可算术独立复现，不需任何已消失文件 —— 1654+5875+10969=18498、458+1196=1654、863+791=1654、458/1654=27.69%、291/1654=17.59%、293/1654=17.71%、863/1654=52.18%。⇒ `[已证]` 不是零证据，是『原件全失、数字仍可复核』。口径修正，不降级不升格。」

七式**全部为真**（逐位复算通过）。但它们**没有一条具鉴别力**：

| 式 | 性质 | 能否否决别的候选值 |
|---|---|---|
| `1654+5875+10969=18498` | 与 458 无关 | 否 |
| `458+1196=1654` | A + 非A，恒真 | 否 —— 换 A=300/400/500/600/900，令 none=1654−A，全部照样成立 |
| `863+791=1654` | 同上，任意二分 | 否 |
| 四个百分数 | **由计数算出**，是计数的函数 | 否 —— 属循环，不能反证计数 |

⇒ **「可重算」需要一条能否决候选值的约束；七式里一条都没有。** 这条裁定把「算术自洽」当成了「独立复现」，两者不同级。**R90 的「档 2」定性不成立，F23 应回到「零存活证据」处理，不能再用「数字仍可复核」给它兜底。**

### 五 · 1654 的来源是清楚的（不构成 F23 的减负，也不构成罪状）

审计提出「1,654 与 18,498 差 11 倍、缺筛选规则」。复算后**该措辞不成立**：两者不是筛选关系。`1,654 + 5,875 + 10,969 = 18,498` 整除全表行数 ⇒ 1,654 就是 grade 列取 `[已证]` 的计数。其增量链在台账逐卡可查：`1,481 +8 → 1,489`（M58）、`1,643 +7 → 1,650`（M76）、`1,650 +4 → 1,654`（M77），台账并明写「**不自行补算**该 +173」。coverage 快照 sha 亦有记载（`0046BAD9…`）。**真正的缺口只有一个：这些计数本身在现盘不可重数**（`coverage.tsv` 按 basename 全库 0 命中、按 4,147,334 B 精确字节反查 0 命中）。

### 六 · 两个「16 条」不是同一个集合（跨文档引用会混用）

`R14_COMMON` §2.92 的「去重 16 条」**含 `COVERAGE/coverage.tsv`**；FACT_INDEX 第 4 列口径的 16 条**不含**它（没有任何一行把 coverage.tsv 写进第 4 列）。数值相同、集合不同。**凡写「16 条」必须带口径。**

### 七 · F08 的锚点粒度问题（登记，不改）

F08 的第二项证据写 `R17_LEDGER_1064/SECTION.md(事项4)`，但台账 §1064 事项 4 记的是「R14_COMMON §2.10 已成文」这一文档动作，而 F08 的 a–e 细目实际在 **`R14_COMMON` §2.9 一**（逐字载有 `0x47C3D0` / `0x6F322F` / `0x6F2B40` / `1 写 / 0 非栈` / `8 / 0`）。F08 的第一项证据正是 `R14_COMMON.md(§2.9一/§2.10一/二)` ⇒ **内容是可核的，错的是第二项的锚点粒度**。本轮**只登记不改**（改 evidence_paths 属裁定变更，须单独一卡 + 门禁回归）。

### 八 · 未取得（不粉饰）

① F23 的 458/291/293/1,196/12/2/9 与 1,654 **仍不可重数**；② 乙类 11 条真失路径的内容，本轮只判「不在盘」，未逐条判可否用二手材料替代；③ F23 的 grade 本轮**未改**（见第九节）；④ 甲类 12 个 fid 的锚点命中的是**台账节**，不等于 `SECTION.md` 原文的逐字等价 —— 台账是并入版，可能有压缩。

### 九 · 给下一轮的硬约束（F23 grade 裁定的前置条件）

改 F23 的 grade 前必须先回答一个二选一，且**不得用「算术自洽」作答**：
- (甲) 补出在盘证据 —— 目前零存活，`COVERAGE/PANEL.md` 与 `DELIVERY_SUMMARY.md` 均无副本；
- (乙) 按「零存活证据」降级 —— 但这会与 R90 已下的「不降级」冲突，故须**先撤 R90 的档 2 定性**，再走单独一卡 + 门禁回归。

本轮只把前置条件写清，不动 grade。
"""
append(P, SEC2154, 1081)

print("\n=== B. 台账 新增 §1204 ===")
P2=os.path.join(LEAD,'GOAL_THREE_TARGETS_20261018.md')
SEC1204 = """
## §1204 R149 · FACT_INDEX 的 16 条失联路径分成两类（5 条台账合并 / 11 条真失）；R90「F23 档 2（可重算）」的七式全部为真但无一具鉴别力，该定性不成立

本轮只做两件可机械判定的事，并把一件已下的裁定证伪。

### 一 · 16 条失联路径不是一类

口径：`FACT_INDEX.tsv` v5.40（`fabd1e57…`）第 4 列按第一个左圆括号切锚点、反斜杠换正斜杠、相对 `lead/` 与仓库根判存在。实测 178 项 / 43 失联项 / 16 条唯一路径。

- **甲类 5 条（台账合并型，不构成内容失联）**：`R17_LEDGER_1062/1063/1063R/1064/1065` 的 `SECTION.md` 目录不在，但台账有 `§1062/§1063/§1064/§1065` 同名节。逐 fid 锚点取自 statement 自身地址与数字，**12 个 fid、33 个锚点全部逐字命中**。`§1063R` 无同名节的解释在盘：`R17_LEDGER_1063/SUPERSEDED.md` 明写台账 §1063 采用 1063R 版本（129/125/5/19），该目录自标「已作废，请勿引用」。
- **乙类 11 条（真失）**：`COVERAGE/PANEL.md`、`R17_DELIVERY/DELIVERY_SUMMARY.md`、`R17_AUDIT_R9`、`R17_AUDIT_FI_V5`、`NAMED_PUSH_AUDIT10`、`S10_KPROVED/_audit`、`S13_K10/_audit`、`S13_K12/_audit` 的 `VERDICT.md`、`GATE_BEHAV/PROGRESS.md`、`HANDOFF_R14_R3.md`、`HANDOFF_R16.md`。

⇒ 混成一个「16 条」谈会系统性高估失联严重度。反控：`§1063` 内同时有被作废旧值 `108/82/4/33` 与「不得引用」；自造串 `ZZZ_NOT_IN_LEDGER_QQQ` 在同一节必须 0 命中。

### 二 · F23 仍是全表唯一零存活项

同口径统计「第 4 列一项都不存在」的行：全表恰 1 行 = F23，grade 仍 `[已证]`。它两项都属乙类真失 ⇒ 第一节的减负**不适用于 F23**。

### 三 · R90 的「档 2（可重算）」判据被证伪

R90 七式（`BOARD_ARCHIVE.md:4915`）**逐位全部为真**，但无一具鉴别力：`458+1196=1654` 是 A+非A 恒真（换 A=300/400/500/600/900 并令 none=1654−A 全部成立）；`863+791=1654` 同理；四个百分数是计数的函数，属循环。⇒ **「可重算」需要一条能否决候选值的约束，七式里没有。** R90 把「算术自洽」当成了「独立复现」。

### 四 · 1654 的来源清楚，但计数本身不可重数

`1,654+5,875+10,969=18,498` 整除全表行数 ⇒ 1,654 是 grade 列 `[已证]` 的计数，不是从 18,498 筛出来的（审计「缺筛选规则」的措辞不成立）。增量链逐卡可查：`1,481+8→1,489`（M58）、`1,643+7→1,650`（M76）、`1,650+4→1,654`（M77），台账明写「不自行补算该 +173」；coverage 快照 sha 记 `0046BAD9…`。**真正缺口只有一个：计数本身在现盘不可重数**（`coverage.tsv` basename 全库 0 命中、按 4,147,334 B 精确反查 0 命中）。

### 五 · 两个「16 条」不同集

`R14_COMMON` §2.92 的「去重 16 条」含 `COVERAGE/coverage.tsv`；FACT_INDEX 第 4 列口径不含（无一行把 coverage.tsv 写进第 4 列）。数值同、集合不同 ⇒ 凡写「16 条」必须带口径。

### 六 · F08 锚点粒度（登记不改）

F08 第二项证据写 `R17_LEDGER_1064/SECTION.md(事项4)`，但台账 §1064 事项 4 是「§2.10 已成文」的文档动作；a–e 细目实在 `R14_COMMON` §2.9 一（逐字含 `0x47C3D0`/`0x6F322F`/`0x6F2B40`/`1 写 / 0 非栈`/`8 / 0`）。F08 第一项证据正是 `R14_COMMON.md(§2.9一/§2.10一/二)` ⇒ 内容可核，错的是第二项锚点粒度。只登记，改 evidence_paths 须单独一卡 + 门禁回归。

### 七 · 未取得

① F23 的 458/291/293/1,196/12/2/9 与 1,654 仍不可重数；② 乙类 11 条只判「不在盘」，未判可否二手替代；③ F23 grade 本轮未改；④ 甲类锚点命中的是台账并入版，不等于 `SECTION.md` 原文逐字等价。

### 八 · 下一轮前置条件

改 F23 的 grade 前必须二选一，且不得用「算术自洽」作答：(甲) 补出在盘证据（现零存活）；(乙) 按零存活降级 —— 须**先撤 R90 档 2 定性**，再单独一卡 + 门禁回归。
"""
append(P2, SEC1204, 337)

json=None
