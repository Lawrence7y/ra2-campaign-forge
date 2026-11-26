#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话交付：FACT_INDEX v5.33 -> v5.34（两处正文修订，均由本轮实测驱动）

修订一 · F35：撤下 R138 的「定义只有二手转述」
----------------------------------------------
R138 写「proved_strict 的定义只有二手转述，一手 PANEL.md M52 不在现盘」。
本轮实测该句为伪：现盘 RULING_R15_20261119/work/strict_panel.py 第 78 行
  if "[未证]" not in sem:
就是该判据的**代码级一手实现**，且 LEAD_LOCK 的「Lead 错误 #14」段明确把它
当权威定义（"权威定义是 ... strict_panel.py 第 78 行"）。另有 3 个独立脚本同判据。
真事实是两个**分开**的：① 定义在盘（有代码权威）；② 该脚本的两个输入
coverage.tsv / function_atlas.tsv 不在盘。R138 把这两条合成一句，方向错了。
处置：撤下原句、换成实测句；evidence_paths 补上这个在盘的一手实现（原先只有一条已失文件）。

修订二 · F29：把 63/77、64/77、74/77 从「二手转述」升级为「盘上字节可复算」
--------------------------------------------------------------------------
R135..R138 一直只引 PANEL.md（已失）与 R14_COMMON。本轮首次用盘上字节独立复算：
  RTTI(.?AVA<Name>@@ 串内联, TD = str-8) -> COL(sig==0 且 +12==TD) -> 主虚表(vt-4==COL)
  -> slot1/slot2 -> 是否落在 40 个 8 字节桩的起始 VA 集合
得到 63/77、64/77（跟 this 调整 thunk 到终点）、74/77（族内多数派），与正文四数逐项相同。
并新测得一条正文未写的边界：slot1 单判 = slot2 单判 = 63，故「两槽皆桩」的合取
在 77 张表上不增加判别力（如实登记，不掩饰）。

写入纪律：R17_LEAD_BASELINE 下 wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写 -> 回读校验。
源版本 v5.33 目录一个字节不动；v5.34 落到新目录。
"""
import os
import sys
import json
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
PRV = os.path.join(R14, 'R17_R105_FACTINDEX_V533', 'FACT_INDEX.tsv')
DSTD = os.path.join(R14, 'R17_R106_FACTINDEX_V534')
DST = os.path.join(DSTD, 'FACT_INDEX.tsv')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
DRY = '--dry' in sys.argv

OLD_SHA = 'a6e7a8d9af95d1296714f36bf567e91264e2b05945fbeac41425e43eba600de0'
OLD_BYTES = 66661
OLD_CR = 0
OLD_ROWS = 55

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


# ==================== 新文本 ====================

# ---- F35 limitations 追加（撤回 + 实测）----
F35_ADD = (u'**【R139 更正·定义有现盘一手实现，R138 那句「只有二手转述」为伪】** '
           u'`proved_strict` 的判据在现盘有**代码级一手实现**：'
           u'`RULING_R15_20261119\\\\work\\\\strict_panel.py` 第 78 行 `if "[未证]" not in sem:`'
           u'（带方括号字面，不是裸子串），文件头第 14 行给出同一条件的散文措辞；'
           u'`lead/LEAD_LOCK` 的「Lead 错误 #14」段逐字点名该行当**权威定义**'
           u'（并记录裸子串口径会少算 10 行：S22 16/1194 vs 26/1204）。'
           u'另有 3 个独立脚本含同一逐字判据（`_cards/M59-MERGE/precheck.py:60`、'
           u'`simulate.py:72`、`verify.py:83`），而 PANEL.md 的写入器 `merge_panel.py` 本身**不含**该判据。'
           u'⇒ 真事实应拆成**两条**，不可合并：① **定义在盘**（有代码权威，原 R138 表述方向相反，本轮撤回）；'
           u'② **该脚本的两个输入不在盘** —— `COVERAGE/coverage.tsv` 与 '
           u'`lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv` 均实测不存在，'
           u'`COVERAGE/` 与 `next_re_20261112_r10/` 两个目录亦不存在。'
           u'故本文可引的是：判据式与过滤串**有现盘权威**，`n`（atlas 内分母）的**取法**只能从该脚本的'
           u'`atlas_n` 累加逻辑读出（`if e not in atlas: continue`），而**具体数值不可重数**。')

# ---- F29 limitations 追加（盘上字节复算）----
F29_ADD = (u'**【R139 实测·四个数首次由盘上字节独立复算】** 此前本条三比例只引已失的 `PANEL.md`（M71）'
           u'与 `R14_COMMON §13.3`，属二手转述。R139 主会话按以下判据从 `ra2bench/gamemd.exe` '
           u'（4,825,360 B、sha256 前缀 `73201cc0`）独立复算，正文四数**逐项相同**：'
           u'① **RTTI 链**：`.data` 内 `.?AVA<Name>@@` 串是 MSVC `TypeDescriptor` 的**内联** `name[]`，'
           u'故描述符本体在「串起始 −8」；校验 `+0` 指针落在 `.data/.rdata`、`+4==0`、`+8` 内联 `.?AV?` 前缀。'
           u'`.data` 内共 **962** 个 TypeDescriptor。'
           u'② **COL**：`.data/.rdata` 里出现 TD VA 的 DWORD 位置 −12，且 `dword[COL+0]==0`（signature）、'
           u'`dword[COL+12]==TD` ⇒ **952** 个类各得 COL。'
           u'③ **主虚表**：出现 COL VA 的 DWORD 位置 +4，且 `dword[vt−4]==COL` ⇒ **952** 个类各得虚表，'
           u'全部 1216 张虚表的 `vt−4` 都指回自己的 COL。'
           u'④ **两槽皆桩**（字面口径：`slot1=dword[vt+4]`、`slot2=dword[vt+8]` **各自**落在全文件 '
           u'**40** 个 8 字节桩 `B8 01 00 00 00 C2 04 00` 的**起始 VA 集合**里，不要求两槽相邻）'
           u'⇒ **63/77**。14 个例外逐个点名：Locomotion **11** 个（Drive/DropPod/Fly/Hover/Jumpjet/'
           u'Mech/Rocket/Ship/Teleport/Tunnel/Walk）＋ **AircraftClass / BulletClass / CStreamClass**，'
           u'与正文「Locomotion 11 个全非桩」「Other 3 例外」逐字吻合。'
           u'⑤ **有效桩**：把槽值按 this 调整 thunk 跟到终点再判（识别 `81 6C 24 04 imm32; E9 rel32`、'
           u'`83 6C 24 04 imm8; E9 rel32`、`E9 rel32`、`8B 44 24 04 50 E8 rel32` 四种中转，上限 6 跳）'
           u'⇒ **64/77**，多出的恰是 `AircraftClass`（其 slot1/slot2 原文 `81 6C 24 04 C0 06 00 00 E9 …`，'
           u'this−0x6C0 后跳到 0x410300/0x410310 这一对桩）。与正文「只跟跳板不跟转发会得 126/154 槽而非 '
           u'128/154」一致（63×2=126、64×2=128）。'
           u'⑥ **族口径**：按类名后缀三分 —— Locomotion **11**（桩 0）、TypeClass **22**（桩 22）、'
           u'Other **44**（桩 41 / 非桩 3 = AircraftClass/BulletClass/CStreamClass）；族内多数派 **74/77**'
           u' = 96.10%，常数预测（全判桩）63/77 = 81.82%，净增 **11**。'
           u'⑦ **判别力零假设**：随机置换族标签 **2000** 次（seed 固定），族内多数派正确数最大 **64**、'
           u'`>=74` 命中 **0** 次 ⇒ 74 严格高于置换最大值，正文「200 次最大仅 64」方向一致且更严。'
           u'**⑧ 本轮新测得的一条边界（正文未写，如实登记）**：只判 `slot1` 为桩得 **63**、只判 `slot2` 得 **63**，'
           u'与两槽合取同值 ⇒ 在 77 张表上「两槽皆桩」与「任一槽为桩」**等价**，合取不增加判别力；'
           u'反控：把桩集合置空得 0、把偏移换成 `+8/+12` 得 0、放宽成「槽值落在镜像内」得 77 ⇒ 判据不是恒真。')

F35_EV_ADD = r';lead\next_re_20261117_r14\RULING_R15_20261119\work\strict_panel.py(78 行判据 + 14 行散文措辞)'
F35_EV_ADD2 = (r';lead\next_re_20261117_r14\_cards\M59-MERGE\precheck.py(60)'
               r';lead\next_re_20261117_r14\_cards\M59-MERGE\simulate.py(72)'
               r';lead\next_re_20261117_r14\_cards\M59-MERGE\verify.py(83)')
F29_EV_ADD = (r';_r139\r139e_f29_6377.py(63/77 与 64/77 复算 25 断言)'
              r';_r139\r139f_f29_family.py(74/77 与置换零假设 15 断言)'
              r';_r139\r139a_f29_bytes.py(RTTI 77/桩 40/序列 80/IAT idx 三口径)')


def main():
    old = open(PRV, 'rb').read()
    W('=== 写前断言 ===')
    ck('B1 源版本 v5.33 sha256 与开局实测一致', sha(old) == OLD_SHA, sha(old)[:16])
    ck('B2 源版本字节数 66,661', len(old) == OLD_BYTES, len(old))
    ck('B3 源版本 CR=0（全 LF）', old.count(b'\r') == OLD_CR, old.count(b'\r'))
    ck('B4 源版本 55 条事实行', len([1 for l in old.decode('utf-8').split('\n') if l.count('\t') == 4]) == OLD_ROWS)

    lines = old.decode('utf-8').split('\n')
    ck('B5 末元素为空串（文件以 LF 结尾）', lines[-1] == '', repr(lines[-1]))

    idx = {}
    for i, l in enumerate(lines):
        if l.count('\t') == 4:
            idx[l.split('\t')[0]] = i
    ck('B6 F29 行存在', 'F29' in idx, 'F29' in idx)
    ck('B7 F35 行存在', 'F35' in idx, 'F35' in idx)

    # ---------- F35 ----------
    c35 = lines[idx['F35']].split('\t')
    ck('F35.1 5 列', len(c35) == 5, len(c35))
    old_lim35 = c35[4]
    ck('F35.2 旧 limitations 含 R138 那句「只有二手转述」', '定义**只有二手转述**' in old_lim35)
    new_lim35 = old_lim35 + F35_ADD
    ck('F35.3 追加后仍含原句（保留撤回记录形态，不删原文）', '定义**只有二手转述**' in new_lim35)
    ck('F35.4 追加段含「R138 那句为伪」的撤下声明', 'R138 那句「只有二手转述」为伪' in F35_ADD)
    ck('F35.5 追加段含「撤回」字样', '本轮撤回' in F35_ADD)
    c35[4] = new_lim35
    old_ev35 = c35[3]
    ck('F35.6 旧 evidence_paths 只一条（无分号）', ';' not in old_ev35, old_ev35)
    c35[3] = old_ev35 + F35_EV_ADD + F35_EV_ADD2
    ck('F35.7 新 evidence_paths 含在盘 strict_panel.py', 'strict_panel.py' in c35[3])
    ck('F35.8 新 evidence_paths 含 3 个独立实现', c35[3].count('M59-MERGE') == 3)
    ck('F35.9 grade 一字未动', c35[2] == '[流程]', c35[2])
    oneline35 = '\t'.join(c35)
    ck('F35.10 单行内无 LF（不会破坏 55 行结构）', '\n' not in oneline35 and '\r' not in oneline35)

    # ---------- F29 ----------
    c29 = lines[idx['F29']].split('\t')
    ck('F29.1 5 列', len(c29) == 5, len(c29))
    ck('F29.2 旧 limitations 不含本轮追加段', '【R139 实测·四个数首次由盘上字节独立复算】' not in c29[4])
    c29[4] = c29[4] + F29_ADD
    c29[3] = c29[3] + F29_EV_ADD
    ck('F29.3 新 limitations 含 63/77', '**63/77**' in c29[4])
    ck('F29.4 新 limitations 含 64/77', '**64/77**' in c29[4])
    ck('F29.5 新 limitations 含 74/77', '**74/77**' in c29[4])
    ck('F29.6 新 limitations 含合取不加判别力这条边界', '合取不增加判别力' in c29[4])
    ck('F29.7 grade 一字未动', c29[2] == '[已证]', c29[2])
    ck('F29.8 新 evidence_paths 含复算脚本', 'r139e_f29_6377.py' in c29[3])
    oneline29 = '\t'.join(c29)
    ck('F29.9 单行内无 LF/CR', '\n' not in oneline29 and '\r' not in oneline29)

    lines[idx['F35']] = oneline35
    lines[idx['F29']] = oneline29
    new = '\n'.join(lines).encode('utf-8')

    W('')
    W('=== 写入前后结构断言 ===')
    ck('W1 行数不变（55 事实行 + 表头 + 末尾空）', len(lines) == len(old.decode('utf-8').split('\n')),
       len(lines))
    ck('W2 CR 仍为 0', new.count(b'\r') == 0, new.count(b'\r'))
    ck('W3 只有 F29/F35 两行变化（逐行比对）',
       sum(1 for a, b2 in zip(old.decode('utf-8').split('\n'), lines) if a != b2) == 2,
       sum(1 for a, b2 in zip(old.decode('utf-8').split('\n'), lines) if a != b2))
    chg = [l.split('\t')[0] for a, l in zip(old.decode('utf-8').split('\n'), lines) if a != l and l.count('\t') == 4]
    ck('W4 变化的正是 F29 与 F35', sorted(chg) == ['F29', 'F35'], chg)
    ck('W5 新增字节 = F35 两条 + F29 两条之和', len(new) - len(old) > 1000, len(new) - len(old))

    W('  旧 %d B -> 新 %d B（+%d）' % (len(old), len(new), len(new) - len(old)))

    if DRY:
        W('\n[DRY] 未写盘。断言 %d 项，%d FAIL' % (len(buf), len(fails)))
        return 1 if fails else 0

    # ---------- 备份（wx 独占）----------
    ts = time.strftime('%Y%m%d_%H%M%S')
    bpath = os.path.join(BASE, 'FACT_INDEX.tsv.before_R139_v534_%s.bak' % ts)
    fd = os.open(bpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    ck('X1 备份回读 sha256 == 源', sha(open(bpath, 'rb').read()) == OLD_SHA, bpath)

    # ---------- 写 ----------
    os.makedirs(DSTD, exist_ok=True)
    tmp = DST + '.tmp_r139'
    if os.path.exists(tmp):
        os.remove(tmp)
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, new)
    finally:
        os.close(fd)
    os.replace(tmp, DST)
    back = open(DST, 'rb').read()
    ck('X2 回读字节数一致', len(back) == len(new), (len(back), len(new)))
    ck('X3 回读 sha256 一致', sha(back) == sha(new), sha(back)[:16])
    ck('X4 回读 CR=0', back.count(b'\r') == 0)
    ck('X5 源版本 v5.33 一个字节未动', sha(open(PRV, 'rb').read()) == OLD_SHA)
    ck('X6 回读 55 条事实行', len([1 for l in back.decode('utf-8').split('\n') if l.count('\t') == 4]) == 55)

    res = dict(old_bytes=len(old), new_bytes=len(new), delta=len(new) - len(old),
               new_sha=sha(new), backup=bpath, fails=fails,
               assertions=len([l for l in buf if l.strip().startswith(('PASS', 'FAIL'))]))
    open(os.path.join(ROOT, '_r139', 'r139g_write_v534.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    W('\n落盘完成：%s' % DST)
    W('断言 %d 项，%d FAIL' % (res['assertions'], len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
