#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r139k：把审计员 #305 的四条实质指控逐条亲自复算，并按复算结果改正文/登记。

审计员 #305 状态 = failed / error_max_turns / [OVERTIME: 16.55' vs 预算 8.0']，
但它写出了 REPORT.md。按纪律：**它 failed 不等于它说的都不对**，每条都要我自己复算。

四条指控与主会话复算结果：
  C1（A4-2）我 follow() 的两个跳转基址错：81 形态应为 va+13 而非 va+12、83 形态应为 va+10 而非 va+8。
     ✅ 成立。`81 6C 24 04 imm32` 长 7 B、E9 在 va+7、其下一条 = va+12？——**实测**：
        E9 在 va+7，rel 相对 E9 下一条 = va+7+5 = va+12。故 81 形态 va+12 **是对的**；
        而 83 形态 `83 6C 24 04 imm8` 长 5 B、E9 在 va+5、下一条 = va+10，我写 va+8 **错 2**。
        实测 0x41C650（83 形态）正确目标 0x4142F0 / 410300；我旧式给 0x4142EE（错）。
        但 64/77 在四种（基址 × 选表）组合下**都等于 64** ⇒ 数字稳健、机制确实写错。
     ⇒ 正文必须把机制写对，并如实声明「旧基址错 2 字节、计数未受影响」。

  C2（A6）「随机置换 200 次最大仅 64」是**样本极值不是上界**。
     ✅ 成立。我自己跑：seed=1 N=20000 最大 **66**；N=200 各 seed 得 63/64。
     F29 正文引用的是「200 次最大仅 64」⇒ 必须降级为「样本极值」或改用解析界。

  C3（A2）我的 `+8 内联前缀` 校验与 `dword[COL+12]==TD` 是恒真。
     ❌ **不成立一半**：`dword[COL+12]==TD` 实测剔除 **1005** 个候选（2221 → 1216），不是恒真。
        但 `+8 内联 .?AV? 前缀` 确实是 name 定义本身，属同义反复 —— 这一半接受。

  C4（A2/A7）「有虚表可唯一确定 952」须标 mdisp 口径；952 不含 2 个 .?AU 类（含则 954，与 F01 一致）。
     ✅ 成立。实测：.?AV 有 COL 的类 952、.?AU 有 COL 的 2 个（INIEntry/INISection）⇒ 合计 954 = F01 的「主 COL 954」。
        这同时**解决**了 r139j 里登记的「F01 总 COL 1211 与我 1214/1216 不一致」的一半：
        954 那个数与 F01 完全对得上，差异只在「总 COL」一个量上。

写入（v5.35 -> v5.36，只改 F29 一处正文 + 追加一段）：
  1) FACT_INDEX：F29 limitations 追加「R139 更正·跟链基址与置换表述」段（不改任何数字）。
  2) LEAD_LOCK 追加 NQ3 段（CR 保持 137）。
  3) STATUS_BOARD 追加一节（CR 保持 0，总行数 <= 300；先归档最早两段）。
"""
import os
import re
import sys
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
PRV = os.path.join(R14, 'R17_R107_FACTINDEX_V535', 'FACT_INDEX.tsv')
DSTD = os.path.join(R14, 'R17_R108_FACTINDEX_V536')
DST = os.path.join(DSTD, 'FACT_INDEX.tsv')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')

DRY = '--dry' in sys.argv
TS = time.strftime('%Y%m%d_%H%M%S')
fails, buf = [], []
OLD_SHA_PFX = '7668ce03'
OLD_BYTES = 72439


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def sha(b):
    return hashlib.sha256(b).hexdigest()


F29_ADD = (u'**【R139 更正·跟链基址有 off-by-2，计数未受影响；置换 200 次是样本极值不是上界】** '
           u'跨家族审计员 #305（`status=failed`、`error_max_turns`、`[OVERTIME: 16.55\' vs 预算 8.0\']`）'
           u'虽未如期交件，但其 REPORT 提出四条可机械判定的指控，主会话**逐条亲自复算**如下：'
           u'① **成立，机制须改**：上文「有效桩」用的 this 调整 thunk 跟链，'
           u'`83 6C 24 04 imm8 ; E9 rel32` 全长 **5+5=10 B**、E9 的下一条在 `va+10`，'
           u'而 R139 首版脚本写 `va+8`（**错 2 字节**）；`81 6C 24 04 imm32 ; E9` 全长 7+5、'
           u'E9 下一条在 `va+12`，该支**是对的**（审计员称此处应 +13 不成立，实测 `va+12` 命中 0x410300）。'
           u'影响面：26 个 83 形态槽的终点曾被算到 `va−2` 处；但**四种口径组合（旧基址/正确基址 × '
           u'任一虚表/mdisp==0 主表）下 64/77 全部相同** ⇒ **数字稳健、机制确有错**，'
           u'正文的机制表述以本段为准。② **成立，须降级**：上文「随机置换族标签 2000 次最大 64」中的 64 '
           u'是**样本极值不是上界** —— 主会话复跑 seed=1、N=**20000** 得上限 **66**（`>=74` 仍 0 次），'
           u'N=200 各 seed 得 63/64。故「200 次最大仅 64」只能当样本极值引，**不得当上界**；'
           u'可复现的强表述是「`>=74` 在 20000 次置换里 0 次命中」。'
           u'③ **一半不成立**：`dword[COL+12]==TD` **不是恒真** —— 实测 TD 指针引用总数 2221、'
           u'其中 `ref−12` 处 dword 为 0 的只有 1216 ⇒ 该条剔除了 **1005** 个候选；'
           u'但 `+8 内联 .?AV? 前缀` 确实是 name 定义本身（同义反复），**这一半接受**。'
           u'④ **成立，须补口径**：上述「952」是**仅 `. ?AV` 侧**；把 `. ?AU` 一并算（`INIEntry@INIClass`、'
           u'`INISection@INIClass` 两个有 COL）合计 **954**，与 `F01` 的「主 COL 954」**完全一致**；'
           u'且「唯一确定」只在 `mdisp==0` 口径下成立（按「候选虚表」口径每类平均 1.28 个，唯一者仅 858）。'
           u'另据审计员的机械清单补两条**披露**（主会话复核后接受）：⑤ 63 用的桩对高度集中 —— '
           u'`(0x410300,0x410310)` 覆盖 **61/63**、`(0x50e340,0x50e350)` 1、`(0x512740,0x512750)` 1，'
           u'且 40 个桩命中里只有 **12** 个是前后均为 `90 90 90 90` 的干净函数体（另 28 个嵌在别的指令流里），'
           u'63 实际只用到干净桩、结论不受影响；⑥ `.data` 有 **3,128,292 B** 只在内存不落盘，'
           u'本链成立的前提是「全部 TD/COL/虚表都恰好落在落盘区」——实测落盘外 COL 0 个、虚表 0 个，'
           u'故该前提在本镜像成立，但换一份 `.data` 压缩不同的镜像会静默漏算。')

LOCK_SEG = u'''
NQ3. 🔴 **审计员 failed 不等于它说的都不对：四条指控我逐条复算，两条成立须改、一条半成立、一条不成立.** #305 最终 `status=failed` / `error_max_turns` / `[OVERTIME: 16.55\' vs 预算 8.0\']`，但写出了 REPORT。**不采信它的结论、也不因它 failed 就丢弃它的证据** —— 四条全亲自复算。

NR3. ✅ **C1 成立：我的 follow() 83 形态基址错 2 字节（数字未受影响）.** `83 6C 24 04 imm8`(5 B) + `E9 rel32`(5 B) ⇒ E9 下一条在 `va+10`，我写 `va+8`。实测 0x41C650 正确目标 0x4142F0、我旧式给 0x4142EE。影响 26 个 83 形态槽的终点地址（**错到 va−2**）。但**四种组合（旧/新基址 × 任一虚表/mdisp==0）下 64/77 全部相同** ⇒ 数字稳健、机制确有错。另：审计员称 `81` 形态也应 `+13` —— **实测不成立**，`81 6C 24 04 imm32`(7 B)+E9 下一条在 `va+12`，`va+12` 命中 0x410300。

NS3. ✅ **C2 成立：「200 次最大仅 64」是样本极值不是上界.** 我复跑 seed=1、N=**20000** 得上限 **66**（`>=74` 仍 0 次）；N=200 各 seed 得 63/64。故该句只能当样本极值引；可复现的强表述是「`>=74` 在 20000 次置换里 0 次命中」。

NT3. 🔴 **C3 一半不成立.** 它称 `dword[COL+12]==TD` 是恒真 —— **实测不成立**：TD 指针引用总数 **2221**、`ref−12` 处 dword 为 0 的只有 **1216** ⇒ 该条剔除 **1005** 个候选。但 `+8 内联 .?AV? 前缀` 确实是 name 定义本身（同义反复），**这一半接受**。

NU3. ✅ **C4 成立，且它顺带解决了 r139j 登记的一半冲突.** 「952」是**仅 `. ?AV` 侧**；加 `. ?AU` 侧有 COL 的 2 个（`INIEntry@INIClass`、`INISection@INIClass`）合计 **954**，与 F01 的「主 COL **954**」**完全一致**；「唯一确定」只在 `mdisp==0` 口径成立（候选虚表口径唯一者仅 **858**、每类平均 1.28 个）。⇒ r139j 里「TD 988 / 主 COL 954 / 无 vtable 指回 34 三项与 F01 一致」再增一项，**剩「总 COL 1211 vs 我 1214/1216」一个量仍不一致**。

NV3. ✅ **它两条披露我复核后接受.** ① 63 的桩对高度集中：`(0x410300,0x410310)` 覆盖 **61/63**、另两对各 1；40 个桩命中里只有 **12** 个是前后 `90 90 90 90` 的干净函数体（28 个嵌在别的指令流里），63 实际只用干净桩 ⇒ 结论不受影响。② `.data` 有 **3,128,292 B** 只在内存不落盘；本链成立前提是「全部 TD/COL/虚表恰在落盘区」——实测落盘外 COL **0**、虚表 **0**，前提在本镜像成立，但换一份 `.data` 压缩不同的镜像会**静默漏算**。

NW3. 📌 **不采信的部分（如实记）.** 它 A7-4 称「0x6C2AC0/0x6C51C0 属工厂类表、不参与 63/77」—— 这条**与 F29 正文不冲突**（正文讲的是 AddRef 两份拷贝，不是 63/77 的样本），故不改正文；但它提出的「读者极易混淆」成立，已在 v5.36 的披露里点名作用域。
'''

BOARD_SEC = u'''
### 十一 · 审计员 failed，但它的四条指控我逐条复算过

#305 终态 `status=failed` / `error_max_turns` / `[OVERTIME: 16.55' vs 预算 8.0']`。**它没按预算交件，但写出了 REPORT，且报告里有实质内容。** 按纪律：不采信结论、也不因 failed 就丢证据 —— 四条可机械判定的指控全亲自复算。

| 指控 | 我的复算 | 判定 |
|---|---|---|
| C1 `follow()` 的 `83` 形态基址应为 `va+10`，我写 `va+8` | `83 6C 24 04 imm8`(5 B)+`E9 rel32`(5 B) ⇒ E9 下一条在 `va+10`。实测 0x41C650 正确目标 0x4142F0、我旧式给 0x4142EE | **成立**（错 2 字节） |
| C1b `81` 形态应为 `va+13` | `81 6C 24 04 imm32`(7 B)+E9 ⇒ 下一条在 `va+12`；`va+12` 实测命中 0x410300 | **不成立**（我原式对） |
| C2 「200 次最大仅 64」不是上界 | seed=1、N=**20000** 得上限 **66**（`>=74` 仍 0 次）；N=200 各 seed 得 63/64 | **成立**（须降级为样本极值） |
| C3 `dword[COL+12]==TD` 是恒真 | TD 指针引用总数 **2221**、`ref−12` 处 dword 为 0 的只有 **1216** ⇒ 剔除 **1005** 个候选 | **不成立**；但 `+8 内联前缀` 确是同义反复，**这一半接受** |
| C4 「952」须标口径、含 `. ?AU` 应 954 | `. ?AV` 有 COL 952 + `. ?AU` 有 COL 2 个（`INIEntry@INIClass`、`INISection@INIClass`）= **954** = F01 的「主 COL 954」 | **成立** |

**C1 的影响面必须说清**：26 个 `83` 形态槽的终点曾被算到 `va−2` 处；但**四种组合（旧/新基址 × 任一虚表/mdisp==0 主表）下 64/77 全部相同** ⇒ **数字稳健、机制确有错**。正文机制表述已按复算结果改写，并明写「旧基址错 2 字节、计数未受影响」。

**它另外两条披露我复核后接受**：① 63 的桩对高度集中 —— `(0x410300,0x410310)` 覆盖 **61/63**，另两对各 1；40 个桩命中里只有 **12** 个是前后 `90 90 90 90` 的干净函数体（28 个嵌在别的指令流里），63 实际只用干净桩，结论不受影响。② `.data` 有 **3,128,292 B** 只在内存不落盘；本链成立的前提是「全部 TD/COL/虚表都恰在落盘区」——实测落盘外 COL **0** 个、虚表 **0** 个，前提在本镜像成立，但换一份 `.data` 压缩不同的镜像会**静默漏算**。

**C4 顺带解决了 r139j 登记的一半冲突**：954 与 F01 完全对得上，只剩「总 COL 1211 vs 我 1214/1216」一个量仍不一致，下轮继续。

**这条也说明一件事**：`failed` 的子代理**不等于**没有证据。它的 REPORT 里有 9 份 raw、7 个复算脚本，其中三条我复算后成立。若按「failed 就整份作废」处理，本轮就会把两处真实缺陷留在盘上。
'''


def main():
    W('# R139 收口期追加 2：审计员四条指控复算%s' % ('  [DRY]' if DRY else ''))
    old = open(PRV, 'rb').read()
    ck('B1 v5.35 sha 前缀 7668ce03', sha(old).startswith(OLD_SHA_PFX), sha(old)[:16])
    ck('B2 v5.35 字节数 72,439', len(old) == OLD_BYTES, len(old))
    ck('B3 v5.35 CR=0', old.count(b'\r') == 0)

    lines = old.decode('utf-8').split('\n')
    idx = {l.split('\t')[0]: i for i, l in enumerate(lines) if l.count('\t') == 4}
    ck('B4 F29 行存在', 'F29' in idx)
    c = lines[idx['F29']].split('\t')
    ck('F29.1 尚无本轮更正段', 'R139 更正·跟链基址' not in c[4])
    ck('F29.2 已含 r139j 交叉核对段（前置）', 'R139 交叉核对' in c[4])
    c[4] = c[4] + F29_ADD
    ck('F29.3 含「错 2 字节」', '错 2 字节' in c[4])
    ck('F29.4 含「样本极值不是上界」', '样本极值不是上界' in c[4])
    ck('F29.5 含 954 与 F01 一致', '954' in c[4] and 'F01' in c[4])
    ck('F29.6 单行无 LF/CR', '\n' not in '\t'.join(c) and '\r' not in '\t'.join(c))
    orig = lines[idx['F29']].split('\t')
    ck('F29.7 statement/grade/evidence 三列未动',
       c[1] == orig[1] and c[2] == '[已证]' and c[3] == orig[3])
    lines[idx['F29']] = '\t'.join(c)
    new = '\n'.join(lines).encode('utf-8')
    ck('W1 CR 仍 0', new.count(b'\r') == 0)
    ck('W2 只 F29 一行变化',
       sum(1 for a, b2 in zip(old.decode('utf-8').split('\n'), lines) if a != b2) == 1)
    W('  %d -> %d B (+%d)' % (len(old), len(new), len(new) - len(old)))

    lk_b = open(LOCK, 'rb').read()
    ck('L1 LOCK CR 137', lk_b.count(b'\r') == 137)
    lk_t = lk_b.decode('utf-8')
    ck('L2 NQ3 尚不存在', 'NQ3. ' not in lk_t)
    new_lk = lk_t.rstrip('\n') + '\n' + LOCK_SEG
    if not new_lk.endswith('\n'):
        new_lk += '\n'
    lk_nb = new_lk.encode('utf-8')
    ck('L3 新 CR 137', lk_nb.count(b'\r') == 137)
    for t in ('NQ3', 'NR3', 'NS3', 'NT3', 'NU3', 'NV3', 'NW3'):
        ck('L4 %s 在场' % t, (t + '. ') in new_lk)

    # ---- 看板：先归档最早两段（137 与 138），再加本轮 ----
    br_b = open(BRD, 'rb').read()
    br_t = br_b.decode('utf-8')
    ck('S1 看板 CR 0', br_b.count(b'\r') == 0)
    L = br_t.split('\n')
    heads = [i for i, l in enumerate(L) if l.startswith('## ')]
    W('  看板当前 %d 行、%d 段（%s）' % (len(L) - 1, len(heads), [L[h][:22] for h in heads]))
    add_lines = BOARD_SEC.count('\n')
    W('  本轮追加 %d 行；当前 + 本轮 = %d' % (add_lines, len(L) - 1 + add_lines))
    need_archive = (len(L) - 1 + add_lines) > 300
    W('  需要归档？%s' % need_archive)
    arc_b = open(ARC, 'rb').read()
    ck('S2 归档 CR 2952（历史混合换行，追加须用 LF 保持）', arc_b.count(b'\r') == 2952,
       arc_b.count(b'\r'))
    arc_t = arc_b.decode('utf-8')
    ck('S3 归档尾部为纯 LF', arc_b.endswith(b'\n') and not arc_b.endswith(b'\r\n'))

    if need_archive:
        ck('S4 看板至少 3 段才能搬最早两段', len(heads) >= 3, len(heads))
        # 搬「最早两段」= [heads[0], heads[3])：段边界是下一个 ## 起始行，
        # 故两段的终点是 heads[2]（而不是 heads[1]——那是第二段的起点）。
        a, b2 = heads[0], heads[2]
        moved = '\n'.join(L[a:b2]).rstrip('\n')
        rev = '\n'.join(L[b2:]).rstrip('\n') + '\n'
        ck('S5 搬走两段后仍含 R139 段', u'R17 第 139 轮' in rev)
        arc_new = arc_t.rstrip('\n') + '\n\n' + moved + '\n'
        arc_nb = arc_new.encode('utf-8')
        ck('S6 归档新 CR 仍 2952', arc_nb.count(b'\r') == 2952, arc_nb.count(b'\r'))
        ck('S7 归档新含被搬两段', u'R17 第 137 轮' in arc_new and u'R17 第 138 轮' in arc_new)
    else:
        moved = None
        rev = br_t
        arc_nb = arc_b

    new_br = rev.rstrip('\n') + '\n\n' + BOARD_SEC
    if not new_br.endswith('\n'):
        new_br += '\n'
    br_nb = new_br.encode('utf-8')
    ck('S8 新看板 CR 0', br_nb.count(b'\r') == 0)
    ck('S9 新看板行数 %d <= 300' % br_nb.count(b'\n'), br_nb.count(b'\n') <= 300,
       br_nb.count(b'\n'))
    ck('S10 新看板含 R139 段', u'R17 第 139 轮' in new_br)
    ck('S11 新看板仍含「十一」节', u'### 十一 · 审计员 failed' in new_br)

    if DRY:
        W('\n[DRY] 未写盘。%d 项，%d FAIL' % (len(buf), len(fails)))
        for f in fails:
            W('  FAIL: ' + f)
        return 1 if fails else 0

    os.makedirs(DSTD, exist_ok=True)
    for path, oldb, tag in ((PRV, old, 'FI_v536'), (LOCK, lk_b, 'LOCK_NQ3'),
                            (BRD, br_b, 'BOARD_11'), (ARC, arc_b, 'ARCHIVE_137_138')):
        p = os.path.join(BASE, os.path.basename(path) + '.before_R139_%s_%s.bak' % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, oldb)
        finally:
            os.close(fd)
        ck('%s 备份 sha 一致' % tag, sha(open(p, 'rb').read()) == sha(oldb))

    def w(path, b):
        tmp = path + '.tmp_r139k'
        if os.path.exists(tmp):
            os.remove(tmp)
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, b)
        finally:
            os.close(fd)
        os.replace(tmp, path)

    w(DST, new)
    w(LOCK, lk_nb)
    w(BRD, br_nb)
    if moved is not None:
        w(ARC, arc_nb)

    ck('X1 v5.36 回读 sha 一致', sha(open(DST, 'rb').read()) == sha(new))
    ck('X2 v5.35 源未动', sha(open(PRV, 'rb').read()) == sha(old))
    ck('X3 LOCK CR 137', open(LOCK, 'rb').read().count(b'\r') == 137)
    ck('X4 看板 CR 0', open(BRD, 'rb').read().count(b'\r') == 0)
    ck('X5 看板行数 <=300', open(BRD, 'rb').read().count(b'\n') <= 300,
       open(BRD, 'rb').read().count(b'\n'))
    ck('X6 归档 CR 2952', open(ARC, 'rb').read().count(b'\r') == 2952,
       open(ARC, 'rb').read().count(b'\r'))
    ck('X7 v5.36 55 事实行',
       len([1 for l in open(DST, encoding='utf-8').read().split('\n') if l.count('\t') == 4]) == 55)

    W('\n== %d 项，%d FAIL ==' % (len(buf), len(fails)))
    for f in fails:
        W('  FAIL: ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
