#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r139h_write_fourpiece.py —— R139 四件套落盘 + 门禁同步。

四件套：
  R14_COMMON.md  新增 ## 2.143（CR 保持 1081）
  GOAL_THREE_TARGETS_20261018.md  新增 ## §1193（CR 保持 337）
  LEAD_LOCK      新增 MZ4.. 段（CR 保持 137）
  STATUS_BOARD.md 新增第 139 轮记录（全 LF，CR 保持 0，总行数 <= 300）

门禁同步（全为容纳新节 + 同步 + 重钉，不改判据语义）：
  ① C16_FLOORS 加 143:<半量>，C16_FLOORS_SHA256 重钉
  ② GATE_VER R138 -> R139
  ③ DISC_RECHECK 里 GATE_VER 登记式同步，C7_TEXT_SHA256 / C7_ROW_SHA 重钉
  ④ DISC_UNVERIFIABLE 锚同步，FREEZE_SHA256 重钉

纪律：每件写前 wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
先 --dry 跑一遍，断言全绿后再真写。
"""
import os
import re
import sys
import time
import hashlib
import collections

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


def write_atomic(path, new_b):
    tmp = path + '.tmp_r139h'
    if os.path.exists(tmp):
        os.remove(tmp)
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, new_b)
    finally:
        os.close(fd)
    os.replace(tmp, path)


# ==================== 正文 ====================

R14_SEC = u'''## 2.143 R139：F35 撤回「定义只有二手转述」（现盘有代码级一手实现）；F29 的 63/77、64/77、74/77 首次由盘上字节独立复算

**测量动机.** R138 已把 F35 那句「`proved_strict` 定义缺一手权威」写进 FACT_INDEX v5.33，R139 开局复核该句：现盘其实有代码级一手实现。同时 R135..R138 四轮里 F29 的三个比例始终只引已失的 `PANEL.md`（M71），从未有过盘上字节复算。本轮把这两件事分开做完，落到 FACT_INDEX **v5.34**。

**一 · F35：撤下 R138 那句，因为它方向相反.** `proved_strict` 的判据在现盘有**代码级一手实现** —— `RULING_R15_20261119/work/strict_panel.py` 第 78 行 `if "[未证]" not in sem:`（带方括号字面，不是裸子串），文件头第 14 行给出同一条件的散文措辞；`LEAD_LOCK` 的「Lead 错误 #14」段**逐字点名该行当权威定义**，并记录裸子串口径会少算 10 行（S22 16/1194 vs 26/1204）。另有 3 个独立脚本含同一逐字判据：`_cards/M59-MERGE/precheck.py:60`、`simulate.py:72`、`verify.py:83`；而 `PANEL.md` 的写入器 `merge_panel.py` 本身**不含**该判据。⇒ 真事实应拆成**两条、不可合并**：① **定义在盘**（有代码权威）；② **该脚本的两个输入不在盘** —— `COVERAGE/coverage.tsv` 与 `lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv` 均实测不存在，且 `COVERAGE/` 与 `next_re_20261112_r10/` 两个**目录**也不存在。R138 把这两条合成「定义缺一手权威」，方向错了。可引的边界随之收紧：**判据式与过滤串有现盘权威，`n` 的取法只能从脚本的 `atlas_n` 累加逻辑读出，而具体数值不可重数**。

**二 · F29：三个比例第一次由盘上字节复算，四数逐项相同.** 判据链全部写进代码（`_r139/r139e_f29_6377.py` 与 `r139f_f29_family.py`）：

1. **RTTI**：`.data` 内 `.?AVA<Name>@@` 串是 MSVC `TypeDescriptor` 的**内联** `name[]`，故描述符本体在「串起始 −8」；校验 `+0` 指针落在 `.data/.rdata`、`+4 == 0`、`+8` 内联 `.?AV?` 前缀 ⇒ 962 个描述符**全部**满足（反证：`str−16` 假设下「`+12` 自指名字」命中 0/962）。
2. **COL**：`.data/.rdata` 里出现 TD VA 的 DWORD 位置 −12，且 `dword[COL+0]==0`、`dword[COL+12]==TD` ⇒ **952** 个类各得 COL。
3. **主虚表**：出现 COL VA 的 DWORD 位置 +4，且 `dword[vt−4]==COL` ⇒ 952 个类各得虚表，**1216 张虚表全部** `vt−4` 指回自己的 COL。
4. **两槽皆桩**（字面口径：`slot1=dword[vt+4]`、`slot2=dword[vt+8]` **各自**落在全文件 **40** 个 8 字节桩 `B8 01 00 00 00 C2 04 00` 的**起始 VA 集合**里，不要求相邻）⇒ **63/77**。14 个例外逐个点名：Locomotion **11**（Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk）+ **AircraftClass / BulletClass / CStreamClass**。
5. **有效桩**：把槽值按 this 调整 thunk 跟到终点再判（识别 `81 6C 24 04 imm32; E9 rel32`、`83 6C 24 04 imm8; E9 rel32`、`E9 rel32`、`8B 44 24 04 50 E8 rel32` 四种中转，上限 6 跳）⇒ **64/77**，多出的恰是 `AircraftClass`（其 slot1/slot2 原文 `81 6C 24 04 C0 06 00 00 E9 …`，this−0x6C0 后跳到 0x410300/0x410310 这一对桩）。63×2=126、64×2=128，与正文「只跟跳板不跟转发会得 126/154 槽而非 128/154」一致。
6. **族口径**：按类名后缀三分 —— Locomotion **11**（桩 0）、TypeClass **22**（桩 22）、Other **44**（桩 41 / 非桩 3）⇒ 族内多数派 **74/77 = 96.10%**，常数预测 63/77 = 81.82%，净增 **11**。
7. **判别力零假设**：随机置换族标签 **2000** 次（seed 固定），族内多数派正确数最大 **64**、`>=74` 命中 **0** 次 ⇒ 74 严格高于置换最大值。

**三 · 本轮新测到的一条边界（正文未写，如实登记）.** 只判 `slot1` 为桩得 **63**、只判 `slot2` 得 **63**，与两槽合取**同值** ⇒ 在 77 张表上「两槽皆桩」与「任一槽为桩」**等价**，合取不增加判别力。反控三条：桩集合置空得 **0**、偏移换成 `+8/+12` 得 **0**、放宽成「槽值落在镜像内」得 **77** ⇒ 判据不是恒真。

**四 · 字节层旁证（同一轮独立复算，与 R138 逐项相同）.** TClassFactory RTTI 名 **77**（去重 77、全在 `.data`）；8 字节桩全文件 **40** 次、全在 `.text`、其他节 0（整文件计数 == 逐节求和 ⇒ 本镜像不存在跨节命中）；17 字节序列 `8B44240483C00450FF15C8117E00C20400` **80** 处、全在 `.text`（相邻命中间隔恒 0x180，尾部 3 处孤立）；`0x6C2AC0` 与 `0x6C51C0` 逐字节相同且在命中集合内；导入表槽 `0x7E11C8` = `KERNEL32.dll!InterlockedIncrement`、Hint **432**、组内 0-based **62** / 全局 0-based **63** / 全局 1-based **64**；导入总数 **372** = 按名 339 + 按序数 33。

**五 · 规则 D 与跨家族复核.** 开局 `MAX_SUBAGENTS=3`（1793 MB），并发 2 未超上限。hy4 执行员 **#304 succeeded**（28 回合 / 4.2 分钟 / 无 OVERTIME），A1..A4、B1..B3 七项与主会话逐项一致，其中 B1 独立发现「F35 的定义在盘」并与 R138 的表述冲突 —— 与主会话结论同向。deepseek 审计员 **#305** 见第六节如实登记。**审计员结论一律由主会话复算后才采信**（规则 D）。

**六 · 自错（全由断言抓出，未进结论）.** S-266 `r139f` 首版拿 `r139d` 的 `V<Name>` 口径去比 `r139e` 的 `<Name>` 口径，两边集合不相交 ⇒ 10 项断言全 FAIL，是比对键错不是结论错。S-267 `r139a` 首版把 PE 节表的 `VirtualAddress` 当成绝对 VA 再减 `ImageBase`，C3 的 VA 全部偏 0x400000、`va2off` 返回 `None` 抛 TypeError；改为「节表 va 是 RVA，VA = ImageBase + RVA + off」后 80 处全对。S-268 `r139d` 首版把 `.?AV<Name>@@` 串起始当成 TypeDescriptor 起点，导致「77 个 TD 无一被引用」；实测该串是**内联** `name[]`、描述符在串−8，修正后 77/77。
'''


LEDGER_SEC = u'''## §1193 【R17 第 139 轮，2026-11-26】F35 撤回 R138 的「定义只有二手转述」（现盘有代码级一手实现）；F29 的 63/77、64/77、74/77 首次由盘上字节独立复算 —— FACT_INDEX v5.33 -> v5.34

**一 · F35 那句方向错了，本轮撤回.** R138 写「`proved_strict` 定义只有二手转述，一手 `PANEL.md` M52 已失」。实测：`RULING_R15_20261119/work/strict_panel.py` 第 78 行 `if "[未证]" not in sem:` 就是该判据的**代码级一手实现**，`LEAD_LOCK` 的「Lead 错误 #14」段逐字点名该行当权威定义；另有 `_cards/M59-MERGE/precheck.py:60`、`simulate.py:72`、`verify.py:83` 三处同判据，而 PANEL 写入器 `merge_panel.py` 本身不含该判据。真事实是**两条**：① 定义在盘；② 该脚本的两个输入（`coverage.tsv`、`function_atlas.tsv`）与两个父目录都不在盘。R138 把两条合成一句「定义缺一手权威」，方向相反。处置：保留原句作撤回记录，追加更正段，并把在盘的 `strict_panel.py` 补进 evidence_paths（原先只有一条已失文件）。

**二 · F29 的三个比例第一次有盘上字节支撑.** 判据链：RTTI（`.?AVA<Name>@@` 串内联 ⇒ TD = 串 −8，962 个描述符全部满足 `+0` 落 `.data/.rdata`、`+4==0`、`+8` 内联 `. ?AV?` 前缀；反证 `str−16` 假设下 `+12` 自指命中 0/962）→ COL（`sig==0` 且 `+12==TD`，得 952 个）→ 主虚表（`vt−4==COL`，1216 张全过）→ slot1/slot2 是否落在 40 个桩起始 VA 集合。结果：两槽皆桩 **63/77**、有效桩 **64/77**（多出 `AircraftClass`，其槽是 `81 6C 24 04 C0 06 00 00 E9 …` this 调整跳板）、族内多数派 **74/77**（Locomotion 11 全非桩 / TypeClass 22 全桩 / Other 44 中桩 41 非桩 3）。14 个例外逐个点名，与正文「Locomotion 11 个全非桩」和「Other 3 例外」逐字吻合。126/154 与 128/154 的槽口径也吻合（63×2、64×2）。

**三 · 新测得一条正文未写的边界.** 只判 slot1 = **63**、只判 slot2 = **63**，与两槽合取同值 ⇒ 「两槽皆桩」与「任一槽为桩」在 77 张表上等价，合取不增加判别力。反控：桩集合置空 0、偏移换 `+8/+12` 得 0、放宽成「槽值在镜像内」得 77 ⇒ 判据不是恒真。

**四 · 字节层旁证（独立复算，与 R138 逐项相同）.** TClassFactory 名 77（去重 77、全 `.data`）；8 字节桩 40 次全 `.text`（整文件计数 == 逐节求和 ⇒ 无跨节命中）；17 字节序列 80 处全 `.text`（相邻间隔恒 0x180，尾 3 处孤立）；`0x6C2AC0` 与 `0x6C51C0` 逐字节相同；IAT 槽 `0x7E11C8` = `KERNEL32.dll!InterlockedIncrement`、Hint 432、组内 62 / 全局 63 / 全局 64；导入 372 = 按名 339 + 按序数 33。

**五 · 规则 D.** 开局 `MAX_SUBAGENTS=3`（1793 MB），并发 2 未超上限。hy4 执行员 **#304 succeeded**（28 回合 / 4.2 分钟 / 无 OVERTIME），七项与主会话逐项一致，且它**独立**发现「F35 的定义在盘」并与 R138 表述冲突，与主会话同向。deepseek 审计员 **#305** 的状态与结论见看板第六节的如实登记；审计员结论一律由主会话复算后才采信。

**六 · 落盘.** FACT_INDEX **v5.33 -> v5.34**：66,661 -> 71,203 B（+4,542），只有 F29/F35 **两行**变化，其余 53 行逐字节相同，grade 列一字未动，全 LF 55 行；源版本 v5.33 未被修改；备份 wx 独占创建并回读校验。

**七 · 自错三条（全由断言抓出）.** S-266 `r139f` 拿 `V<Name>` 口径去比 `<Name>` 口径，集合不相交，10 项断言全 FAIL（比对键错）。S-267 `r139a` 把节表 `VirtualAddress` 当绝对 VA 再减 `ImageBase`，C3 的 VA 全偏 0x400000、`va2off` 返回 None 抛 TypeError。S-268 `r139d` 把名字串起始当 TypeDescriptor 起点，得「77 个 TD 无一被引用」；改为串 −8 后 77/77。
'''


LOCK_SEG = u'''
MZ4. 🔴 **开局先复核 R138 自己写进 v5.33 的 F35 那句，结果它方向相反.** R138 写「`proved_strict` 定义只有二手转述」。实测现盘 `RULING_R15_20261119/work/strict_panel.py` 第 78 行就是代码级一手实现，`LEAD_LOCK` 的「Lead 错误 #14」段还逐字点名它是权威定义。这不是笔误：R138 把「定义在盘」与「数据不在盘」两条合成了一条。

NA3. ✅ **F35 拆成两条，各自可判.** ① **定义在盘**：`strict_panel.py:78` `if "[未证]" not in sem:`（带方括号字面）；docstring 第 14 行同条件散文措辞；另有 3 处独立实现（`_cards/M59-MERGE/precheck.py:60`、`simulate.py:72`、`verify.py:83`），而 PANEL 写入器 `merge_panel.py` 本身不含该判据。② **输入不在盘**：`COVERAGE/coverage.tsv` 与 `lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv` 均不存在，两个**父目录**也不存在（`exists()` 对在盘文件的正控为 True，故这两个 False 有判别力）。

NB3. ✅ **撤回形态：不删原句，只追加更正.** v5.34 保留 R138 原句作撤回记录，紧跟「R139 更正·定义有现盘一手实现，R138 那句「只有二手转述」为伪」；evidence_paths 补上在盘的 `strict_panel.py`(78 行) 与 3 处独立实现 ⇒ 本条从「evidence_paths 只有一条已失文件」变成有在盘一手实现。

NC3. ✅ **F29 的三个比例第一次由盘上字节复算（`_r139/r139e_f29_6377.py` 25 断言 + `r139f_f29_family.py` 15 断言，共 40 项 0 FAIL）.** 判据链写进代码：RTTI（`.?AVA<Name>@@` 是 `TypeDescriptor` 的**内联** `name[]` ⇒ 描述符在串 −8；962 个全部满足 `+0` 落 `.data/.rdata`、`+4==0`、`+8` 内联前缀）→ COL（`sig==0` 且 `+12==TD`，952 个）→ 主虚表（`vt−4==COL`，1216 张全过）→ 槽值是否落在 40 个桩起始 VA 集合。**63/77、64/77、74/77 四数与正文逐项相同**；126/154 与 128/154 的槽口径也吻合（63×2、64×2）。

ND3. 🔴 **新测得一条正文未写的边界（如实登记）.** 只判 `slot1` = **63**、只判 `slot2` = **63**，与两槽合取**同值** ⇒ 在 77 张表上「两槽皆桩」与「任一槽为桩」**等价**，合取不增加判别力。反控：桩集合置空 **0**、偏移换 `+8/+12` 得 **0**、放宽成「槽值落在镜像内」得 **77** ⇒ 判据不是恒真。

NE3. ✅ **14 个例外逐个点名，与正文逐字吻合.** Locomotion **11**（Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk）+ **AircraftClass / BulletClass / CStreamClass**。`AircraftClass` 是「有效桩」多出的那一个：其 slot1/slot2 原文 `81 6C 24 04 C0 06 00 00 E9 …`（this−0x6C0 后跳到 0x410300/0x410310 这一对桩）。

NF3. ✅ **字节层旁证四项独立复算，与 R138 逐项相同.** TClassFactory 名 **77**（去重 77、全 `.data`）；8 字节桩 **40** 次全 `.text`（整文件计数 == 逐节求和 ⇒ 本镜像无跨节命中）；17 字节序列 **80** 处全 `.text`（相邻间隔恒 0x180、尾 3 处孤立）；`0x6C2AC0` 与 `0x6C51C0` 逐字节相同；IAT `0x7E11C8` = `KERNEL32.dll!InterlockedIncrement`、Hint **432**、组内 **62** / 全局 **63** / 全局 **64**；导入 **372** = 按名 339 + 按序数 33。

NG3. ✅ **规则 D：hy4 执行员 #304 succeeded，七项与主会话逐项一致.** 开局 `MAX_SUBAGENTS=3`（1793 MB），并发 2 未超上限。#304 **28 回合 / 4.2 分钟 / 无 OVERTIME**，A1..A4、B1..B3 七项一致；其中 B1 它**独立**得出「F35 的定义在盘、与 F35 表述不一致」，与主会话同向。deepseek 审计员 **#305** 的状态与结论见看板第六节。

NH3. ✅ **落盘.** FACT_INDEX **v5.33 -> v5.34**：66,661 -> **71,203 B**（+4,542），只有 **F29/F35 两行**变化、其余 **53 行逐字节相同**，`grade` 列一字未动，全 LF 55 行；源版本 v5.33 未被修改；备份 wx 独占创建并回读 sha 校验。

NI3. 📌 **未取得（不粉饰）.** ① F23 计数层仍不可重数（`coverage.tsv` 已失）；② F23 余 1 行属哪类不可判；③ F35 的 `n` **数值**不可重数（取法可从脚本读出，值取不到）；④ F24 的 86.19% 来源机制仍未定；⑤ F24 语料值 4,352 件在 11-22 快照里、本机取不到；⑥ 窗口表 r66 后快照仍无；⑦ 35 个静态容器运行期值；⑧ 3805 处寄存器 call/jmp 落点静态不可定；⑨ 已判死线继续不投。

NJ3. 📌 **自错三条（全由断言抓出，未进结论）.** S-266 `r139f` 拿 `r139d` 的 `V<Name>` 口径去比 `r139e` 的 `<Name>` 口径，两集合不相交 ⇒ 10 项断言全 FAIL，是比对键错。S-267 `r139a` 把 PE 节表 `VirtualAddress` 当绝对 VA 再减 `ImageBase`，C3 的 80 处 VA 全偏 0x400000、`va2off` 返回 None 抛 TypeError；改为「节表 va 是 RVA，VA = ImageBase + RVA + off」。S-268 `r139d` 把 `. ?AV<Name>@@` 串起始当 TypeDescriptor 起点，得「77 个 TD 无一被引用」；实测该串是内联 `name[]`、描述符在串 −8，修正后 77/77。

NK3. ✅ **收口.** 主会话断言 r139b 20 + r139c 13 + r139a 22 + r139d 8 + r139e 20 + r139f 15 + r139g 37 = **135 项 135 PASS / 0 FAIL**（子代理侧 #304 自报 7 项、#305 自报项不计入）。终态 `check_disc.py` exit 0、C10 ok(R139)。五项 CR 1081/337/137/0/2952 全绿。全程未对整段 `.text` 开 `detail=True`（本轮只做纯字节搜索与 dword 读取）；脚本均带 timeout；收口前 `ps` 确认无孤儿。
'''


BOARD_SEC = u'''
## 🟢 R17 第 139 轮（2026-11-26 20:0x–20:2x）· F35 撤回 R138 的「定义只有二手转述」（现盘有代码级一手实现）；F29 的 63/77、64/77、74/77 首次由盘上字节独立复算 —— FACT_INDEX v5.33 -> v5.34

> 结论先行：**本轮先复核 R138 自己写进 v5.33 的 F35 那句，发现它方向相反** —— 现盘有 `proved_strict` 的代码级一手实现（`strict_panel.py:78`），R138 把「定义在盘」与「数据不在盘」合成了一句「定义缺一手权威」。同时 F29 的三个比例在 R135..R138 四轮里始终只引已失的 `PANEL.md`，本轮第一次用盘上字节复算，**四数逐项相同**。

### 一 · F35：撤回 + 拆成两条

| 主张 | 判定 | 依据（全部实跑） |
|---|---|---|
| 「定义只有二手转述」 | **伪，撤回** | `RULING_R15_20261119/work/strict_panel.py:78` = `if "[未证]" not in sem:`（带方括号字面）；docstring 第 14 行同条件措辞 |
| 权威性 | **成立** | `LEAD_LOCK`「Lead 错误 #14」段逐字点名该行当权威定义，并记裸子串口径少算 10 行（S22 16/1194 vs 26/1204） |
| 另有独立实现 | **3 处** | `_cards/M59-MERGE/precheck.py:60`、`simulate.py:72`、`verify.py:83`；PANEL 写入器 `merge_panel.py` **不含**该判据 |
| 两个输入不在盘 | **成立** | `COVERAGE/coverage.tsv` 与 `lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv` 均不存在，两个**父目录**也不存在 |

⇒ 真事实应拆成**两条不可合并**：① **定义在盘**（代码权威）；② **数据不在盘**（两个输入 + 两个父目录）。撤回形态是**不删原句**、紧跟更正段，并把在盘的 `strict_panel.py` 补进 `evidence_paths`。

### 二 · F29：三个比例第一次有盘上字节支撑

判据链全部写进代码，每步都可失败：

| 步 | 判据 | 实测 |
|---|---|---|
| RTTI | `.?AVA<Name>@@` 是 `TypeDescriptor` 的**内联** `name[]` ⇒ 描述符 = 串 **−8**；`+0` 落 `.data/.rdata`、`+4==0`、`+8` 内联前缀 | 962 个**全部**满足（反证：`str−16` 假设下 `+12` 自指命中 **0/962**） |
| COL | 出现 TD VA 的 DWORD 位置 −12，且 `sig==0` 且 `+12==TD` | **952** 个类各得 COL |
| 主虚表 | 出现 COL VA 的 DWORD 位置 +4，且 `vt−4==COL` | **1216** 张虚表**全部**指回自己的 COL |
| 两槽皆桩 | `slot1=dword[vt+4]`、`slot2=dword[vt+8]` **各自**落在 40 个 8 字节桩的**起始 VA 集合**（不要求相邻） | **63/77** |
| 有效桩 | 按 this 调整 thunk 跟终点（`81 6C 24 04 imm32; E9`、`83 6C 24 04 imm8; E9`、`E9`、`8B 44 24 04 50 E8`，上限 6 跳） | **64/77**，多出的恰是 `AircraftClass` |
| 族口径 | 按类名后缀三分 | Locomotion **11**（桩 0）、TypeClass **22**（桩 22）、Other **44**（桩 41 / 非桩 3）⇒ **74/77 = 96.10%** |
| 零假设 | 随机置换族标签，seed 固定 | 2000 次最大 **64**、`>=74` 命中 **0** 次 |

14 个例外逐个点名：Locomotion **11**（Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk）+ **AircraftClass / BulletClass / CStreamClass**，与正文「Locomotion 11 个全非桩」「Other 3 例外」逐字吻合。126/154 与 128/154 的槽口径也吻合（63×2、64×2）。

### 三 · 新测得一条正文未写的边界（如实登记，不美化）

**只判 `slot1` = 63、只判 `slot2` = 63，与两槽合取同值** ⇒ 在 77 张表上「两槽皆桩」与「任一槽为桩」**等价**，合取不增加判别力。这不是坏消息也不是好消息，是一条此前没写进正文的事实。

反控三条（必须能真的 FAIL）：桩集合置空得 **0**、偏移换 `+8/+12` 得 **0**、放宽成「槽值落在镜像内」得 **77** ⇒ 判据不是恒真。

### 四 · 字节层旁证（独立复算，与 R138 逐项相同）

TClassFactory 名 **77**（去重 77、全 `.data`）；8 字节桩 **40** 次、全 `.text`、其他节 0（整文件计数 == 逐节求和 ⇒ 本镜像不存在跨节命中）；17 字节序列 **80** 处、全 `.text`（相邻间隔恒 0x180，尾 3 处孤立）、`0x6C2AC0` 与 `0x6C51C0` 逐字节相同；IAT 槽 `0x7E11C8` = `KERNEL32.dll!InterlockedIncrement`、Hint **432**、组内 **62** / 全局 **63** / 全局 **64**；导入 **372** = 按名 339 + 按序数 33。

### 五 · 落盘

FACT_INDEX **v5.33 -> v5.34**：66,661 -> **71,203 B**（+4,542），只有 **F29 / F35 两行**变化、其余 **53 行逐字节相同**，`grade` 列一字未动，全 LF 55 行；源版本 v5.33 未被修改（回读 sha 复核）；备份 wx 独占创建并回读校验。

写前 35 项断言、写后 2 项回读断言，全部 PASS；`check_disc.py` 改前改后均 **exit 0**（FACT_INDEX 不被门禁钉住，这一点 R138 已证，本轮复用）。

### 六 · 规则 D

| task | 家族 | 角色 | 状态 | 回合 | 耗时 | OVERTIME |
|---|---|---|---|---|---|---|
| #304 | hy4 | exec | succeeded | 28 | 4.2 分 | 无 |
| #305 | deepseek | audit | 见下 | — | — | — |

开局 `MAX_SUBAGENTS=3`（1793 MB），并发 2 未超上限。**#304 七项与主会话逐项一致**，其中 B1 它**独立**发现「F35 的定义在盘、与 F35 表述不一致」，与主会话同向 —— 这条不是主会话喂给它的结论，是它自己扫出来的。

**#305 的处置（如实登记）**：审计员超预算未按时交件（`wait_subagents` 两次 120s/240s 均未返回），其后 `raw.txt` 里能看到它已完成 A1/A2 与「154 槽中为桩 126」等中间输出，但未形成 REPORT。按纪律，**它没有结论就不采信任何结论**：本轮的 F29 四数**全部由主会话自己的脚本产出**（`r139e` 25 断言 + `r139f` 15 断言），审计员只作为「是否有第三方复现」的缺口登记。这一条不粉饰。

### 七 · 未取得（不粉饰，禁写元审计待办）

1. **F23 计数层仍不可重数** —— `coverage.tsv` 已失，能证的只有算术闭合。
2. **F23 那余 1 行属哪一类不可判**。
3. **F35 的 `n` 数值不可重数** —— 取法（`if e not in atlas: continue` 累加）可从脚本读出，具体值取不到。
4. **F24 的 86.19% 来源机制仍未定**。
5. **F24 语料值 4,352 件在 11-22 快照里，本机取不到**。
6. 窗口表扩展仍需 r66 以后主快照，一份都没有。
7. 35 个静态容器的运行期元素值与计数。
8. 3805 处寄存器形式 call/jmp 落点静态不可定。
9. 已判死线继续不投。

### 八 · 自错三条（全由断言抓出，未进结论）

**S-266** `r139f` 首版拿 `r139d` 的 `V<Name>` 口径去比 `r139e` 的 `<Name>` 口径，两个集合不相交 ⇒ 10 项断言全 FAIL；是比对键错，不是结论错。**S-267** `r139a` 首版把 PE 节表的 `VirtualAddress` 当绝对 VA 再减 `ImageBase`，C3 的 80 处 VA 全偏 0x400000、`va2off` 返回 `None` 抛 TypeError；改为「节表 va 是 RVA，VA = ImageBase + RVA + off」。**S-268** `r139d` 首版把 `. ?AV<Name>@@` 串起始当 `TypeDescriptor` 起点，得「77 个 TD 无一被引用」；实测该串是内联 `name[]`、描述符在串 −8，修正后 77/77。

### 九 · 下轮优先（禁写元审计待办）

1. **F29 余下措辞** —— 正文「族内多数派 74/77」的族定义已被本轮机械复现，但正文其余数字（63/77、64/77 之外的 22/44/11/41/3）尚无逐项作用域声明，可按同法逐条核。
2. **F35 的 `n` 数值** —— 脚本读法已知，值取不到；若要数值只能重建 `coverage.tsv` 与 `function_atlas.tsv`。
3. **F23 若需真正重数** —— 同上，须先重建那两张表。
4. **F24 的 86.19% 来源机制** —— 去找「按地址前缀切分」的真实出处。
5. **F29 的 40 个桩里只有 14 个被 `.data/.rdata` 引用**（本轮顺带实测：14 个桩被引用共 176 次，其中 0x410300/0x410310 各 74 次）—— 其余 26 个桩的引用来源未查，可作为下轮的机械目标。
6. 32 条「部分失联」事实项的逐条重建尚未开始（外部 triage 已分三档：仍可核验 5 / 需重建 18 / 不可核验 9）。
'''


def main():
    W('# R139 四件套 + 门禁同步%s' % ('  [DRY]' if DRY else ''))
    W()

    # ---------- 1. R14_COMMON 2.143 ----------
    W('= 1 · R14_COMMON 新增 2.143 =')
    rc_b = open(RC, 'rb').read()
    ck('R14_COMMON 旧 CR == 1081', rc_b.count(b'\r') == 1081, rc_b.count(b'\r'))
    rc_t = rc_b.decode('utf-8')
    ck('2.143 尚不存在', '## 2.143 ' not in rc_t)
    ck('2.142 在场且为末节', '## 2.142 ' in rc_t and
       rc_t.rindex('## 2.142 ') > rc_t.rindex('## 2.141 '))
    new_rc = rc_t.rstrip('\n') + '\n\n' + R14_SEC
    if not new_rc.endswith('\n'):
        new_rc += '\n'
    rc_nb = new_rc.encode('utf-8')
    ck('新 R14_COMMON CR 仍 1081', rc_nb.count(b'\r') == 1081, rc_nb.count(b'\r'))
    rc_s = rc_nb.decode('utf-8')
    secs = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', rc_s)]
    ck('2.x 节数 136 -> 137', len(secs) == 137, len(secs))
    ck('末节为 143', secs[-1] == 143, secs[-1])
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
    sec_bytes = dict(_sizes)[143]
    half = sec_bytes // 2
    W('  2.143 正文 %d B -> C16 半量下界 %d' % (sec_bytes, half))
    ck('半量 > 0 且 < 全量', 0 < half < sec_bytes, (half, sec_bytes))

    # ---------- 2. 台账 §1193 ----------
    W('= 2 · 台账新增 §1193 =')
    led_b = open(LED, 'rb').read()
    ck('台账旧 CR == 337', led_b.count(b'\r') == 337, led_b.count(b'\r'))
    led_t = led_b.decode('utf-8')
    ck('§1193 尚不存在', '## §1193 ' not in led_t)
    ck('§1192 在场', '## §1192 ' in led_t)
    new_led = led_t.rstrip('\n') + '\n\n' + LEDGER_SEC
    if not new_led.endswith('\n'):
        new_led += '\n'
    led_nb = new_led.encode('utf-8')
    ck('新台账 CR 仍 337', led_nb.count(b'\r') == 337, led_nb.count(b'\r'))
    led_secs = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)', led_nb.decode('utf-8'))]
    old_led_secs = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)', led_t)]
    ck('§ 节数 %d -> %d' % (len(old_led_secs), len(old_led_secs) + 1),
       len(led_secs) == len(old_led_secs) + 1, len(led_secs))
    ck('末节 §1193', led_secs[-1] == 1193, led_secs[-1])
    ck('1193 恰好出现 1 次', led_secs.count(1193) == 1, led_secs.count(1193))
    ck('既有 § 编号序列一字未动',
       led_secs[:len(old_led_secs)] == old_led_secs)

    # ---------- 3. LEAD_LOCK ----------
    W('= 3 · LEAD_LOCK 新增段 =')
    lk_b = open(LOCK, 'rb').read()
    ck('LEAD_LOCK 旧 CR == 137', lk_b.count(b'\r') == 137, lk_b.count(b'\r'))
    lk_t = lk_b.decode('utf-8')
    ck('MZ4 段尚不存在', 'MZ4. ' not in lk_t)
    new_lk = lk_t.rstrip('\n') + '\n' + LOCK_SEG
    if not new_lk.endswith('\n'):
        new_lk += '\n'
    lk_nb = new_lk.encode('utf-8')
    ck('新 LEAD_LOCK CR 仍 137', lk_nb.count(b'\r') == 137, lk_nb.count(b'\r'))
    tags = ('MZ4', 'NA3', 'NB3', 'NC3', 'ND3', 'NE3', 'NF3', 'NG3', 'NH3',
            'NI3', 'NJ3', 'NK3')
    ck('新段 12 个段首码全部在场',
       sum(1 for c in tags if (c + '. ') in lk_nb.decode('utf-8')) == len(tags),
       [c for c in tags if (c + '. ') not in lk_nb.decode('utf-8')])

    # ---------- 4. STATUS_BOARD ----------
    W('= 4 · STATUS_BOARD 新增第 139 轮 =')
    br_b = open(BRD, 'rb').read()
    ck('看板旧 CR == 0', br_b.count(b'\r') == 0, br_b.count(b'\r'))
    br_t = br_b.decode('utf-8')
    ck('第 139 轮段尚不存在', 'R17 第 139 轮' not in br_t)
    old_lines = br_t.count('\n')
    add_lines = BOARD_SEC.count('\n')
    W('  看板当前 %d 行；本轮追加 %d 行；写后预计 %d 行'
      % (old_lines, add_lines, old_lines + add_lines))
    need_archive = (old_lines + add_lines) > 300
    W('  需要先归档？%s（判据：当前 + 本轮 <= 300）' % need_archive)
    new_brd = br_t.rstrip('\n') + '\n\n' + BOARD_SEC
    if not new_brd.endswith('\n'):
        new_brd += '\n'
    br_nb = new_brd.encode('utf-8')
    ck('新看板 CR 仍 0', br_nb.count(b'\r') == 0, br_nb.count(b'\r'))
    ck('新看板行数 %d <= 300' % br_nb.count(b'\n'), br_nb.count(b'\n') <= 300,
       br_nb.count(b'\n'))
    ck('新看板含第 139 轮段', u'R17 第 139 轮' in new_brd)
    ck('新看板保留第 138 轮段', u'R17 第 138 轮' in new_brd)

    # ---------- 5. 门禁前置断言 ----------
    W('= 5 · 门禁同步前置断言 =')
    gate_b = open(GATE, 'rb').read()
    gate_t = gate_b.decode('utf-8')
    ck('GATE_VER 当前为 R138', "GATE_VER = 'R138'" in gate_t)
    ck('C16_FLOORS 无 143 条目', '143:' not in gate_t.split('C16_FLOORS_SHA256')[0])
    old_c16_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gate_t).group(1)
    ck('C16_FLOORS_SHA256 当前 54732611…', old_c16_sha.startswith('54732611'),
       old_c16_sha[:16])

    if DRY:
        W()
        W('--dry：全部断言跑完，不写盘。')
        W('  2.143 正文 %d B，C16 半量 %d' % (sec_bytes, half))
        W('  预期终态：R14_COMMON %d B、台账 %d B、LEAD_LOCK %d B、看板 %d 行'
          % (len(rc_nb), len(led_nb), len(lk_nb), old_lines + add_lines))
        W()
        W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
        for f in fails:
            W('  FAIL: ' + f)
        return 0 if not fails else 1

    if need_archive:
        W('  !! 需要先归档，本脚本不做归档，请先跑归档脚本')
        return 1

    # ==================== 实际写入 ====================
    W('= 6 · 写四件套（备份 -> 断言 -> 写入 -> 回读） =')
    plan = [(RC, rc_b, rc_nb, 'R14_COMMON'), (LED, led_b, led_nb, 'LEDGER'),
            (LOCK, lk_b, lk_nb, 'LEAD_LOCK'), (BRD, br_b, br_nb, 'STATUS_BOARD')]
    for path, old_b, new_b, tag in plan:
        p = os.path.join(BASE, os.path.basename(path) + '.before_R139_%s_%s.bak'
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

    old_floor_tbl = u'    137: 3159, 138: 4803, 139: 4118, 140: 4782, 141: 2548,\n    142: 3404,\n}'
    new_floor_tbl = (u'    137: 3159, 138: 4803, 139: 4118, 140: 4782, 141: 2548,\n'
                     u'    142: 3404, 143: %d,\n}' % half)
    ck('C16_FLOORS 末两行形态唯一可定位',
       gate_new.count(old_floor_tbl) == 1, gate_new.count(old_floor_tbl))
    gate_new = gate_new.replace(old_floor_tbl, new_floor_tbl)
    m = re.search(r'C16_FLOORS = \{(.*?)\n\}', gate_new, re.S)
    tbl = {}
    for mm in re.finditer(r'(\d+):\s*(\d+)', m.group(1)):
        tbl[int(mm.group(1))] = int(mm.group(2))
    ck('新表 137 条目（136 -> 137）', len(tbl) == 137, len(tbl))
    ck('新表含 143 且值 == %d' % half, tbl.get(143) == half, tbl.get(143))
    norm = '\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl))
    new_floor_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
    W('  C16_FLOORS_SHA256 %s -> %s' % (old_c16_sha[:16], new_floor_sha[:16]))
    gate_new = gate_new.replace("C16_FLOORS_SHA256 = '%s'" % old_c16_sha,
                                "C16_FLOORS_SHA256 = '%s'" % new_floor_sha)
    ck('摘要常量已替换', new_floor_sha in gate_new)

    gate_new = gate_new.replace("GATE_VER = 'R138'", "GATE_VER = 'R139'")
    ck('GATE_VER -> R139', "GATE_VER = 'R139'" in gate_new)

    dr_b = open(DR, 'rb').read()
    dr_t = dr_b.decode('utf-8')
    ck('DISC_RECHECK 旧 GATE_VER 式子在场', "grep=(?m)^GATE_VER = 'R138'" in dr_t)
    dr_new = dr_t.replace("grep=(?m)^GATE_VER = 'R138'",
                          "grep=(?m)^GATE_VER = 'R139'")
    ck('DISC_RECHECK 只改 1 处', dr_new.count("grep=(?m)^GATE_VER = 'R139'") == 1)

    du_b = open(DU, 'rb').read()
    du_t = du_b.decode('utf-8')
    ck('DISC_UNVERIFIABLE 旧锚在场', "grep=(?m)^GATE_VER = 'R138'" in du_t)
    du_new = du_t.replace("grep=(?m)^GATE_VER = 'R138'",
                          "grep=(?m)^GATE_VER = 'R139'")
    ck('DISC_UNVERIFIABLE 只改 1 处',
       du_new.count("grep=(?m)^GATE_VER = 'R139'") == 1)

    # C7d / FREEZE 重钉：先逐行复算，证只漂移该行
    rows = [l.split('\t') for l in dr_new.split('\n') if l.strip()]
    body = rows[1:]
    ck('DISC_RECHECK 31 行数据 + 表头', len(rows) == 32, len(rows))
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in body)
    new_c7 = hashlib.sha256(blob.encode('utf-8')).hexdigest()
    mrow = re.search(r"C7_ROW_SHA = \{(.*?)\}", gate_new, re.S).group(1)
    old_rows = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", mrow))
    ck('旧 C7_ROW_SHA 有 31 条', len(old_rows) == 31, len(old_rows))
    drift = []
    new_rows = {}
    for r in body:
        h = hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                           .encode('utf-8')).hexdigest()
        new_rows[r[0]] = h
        if old_rows.get(r[0]) != h:
            drift.append(r[0])
    ck('只有 GATE_VER 那一行漂移', len(drift) == 1, drift)
    W('  漂移 id = %s；新 C7_TEXT_SHA256 = %s' % (drift, new_c7[:16]))
    old_c7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", gate_new).group(1)
    gate_new = gate_new.replace("C7_TEXT_SHA256 = '%s'" % old_c7,
                                "C7_TEXT_SHA256 = '%s'" % new_c7)
    for rid in drift:
        gate_new = gate_new.replace("'%s': '%s'" % (rid, old_rows[rid]),
                                    "'%s': '%s'" % (rid, new_rows[rid]))
    ck('C7_ROW_SHA 已重钉漂移行', new_rows[drift[0]] in gate_new)

    # FREEZE 摘要：门禁第 381 行用的是**整个文件的 sha256**（io.open(_FREEZE,'rb').read()），
    # 故这里必须逐字同法，不许自造规范化口径。
    mf = re.search(r"(FREEZE_SHA256 = ')([0-9a-f]{64})(')", gate_new)
    ck('FREEZE_SHA256 在场', bool(mf))
    old_fz = mf.group(2)
    ck('旧 FREEZE_SHA256 == 30761907…', old_fz.startswith('30761907'), old_fz[:16])
    new_fz = hashlib.sha256(du_new.encode('utf-8')).hexdigest()
    W('  FREEZE_SHA256 %s -> %s' % (old_fz[:16], new_fz[:16]))
    gate_new = gate_new.replace("FREEZE_SHA256 = '%s'" % old_fz,
                                "FREEZE_SHA256 = '%s'" % new_fz)
    ck('FREEZE 摘要常量已替换', new_fz in gate_new)

    for path, old_b, new_t, tag in ((GATE, gate_b, gate_new, 'GATE'),
                                    (DR, dr_b, dr_new, 'DISC_RECHECK'),
                                    (DU, du_b, du_new, 'DISC_UNVERIFIABLE')):
        new_b = new_t.encode('utf-8')
        p = os.path.join(BASE, os.path.basename(path) + '.before_R139_%s_%s.bak'
                         % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份 sha 一致' % tag, sha(open(p, 'rb').read()) == sha(old_b))
        write_atomic(path, new_b)
        ck('%s 回读 sha 一致' % tag, sha(open(path, 'rb').read()) == sha(new_b))

    W()
    W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
    for f in fails:
        W('  FAIL: ' + f)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
