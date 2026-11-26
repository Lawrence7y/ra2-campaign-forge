#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r139j：把一处**跨事实项的数字冲突**如实登记（不粉饰、不擅自改 F01）。

发现经过：跨家族审计员 #305 的中途输出里出现「F01 正文：总 COL 1211 / 主 COL 954 / TD 988」。
主会话本轮独立复算得到的对应量是：TD **988**（完全一致）、主 COL **954**（完全一致）、
「无任何 vtable 指回的 TD」**34**（完全一致），但**总 COL 我测得 1214（.?AV 侧）/ 1216（含 .?AU）**，
而 F01 写 **1211**；F01 另写「1201 条 COL 被某 vtable 以 [-4] 指回」，我测得 **1214**。

处置原则（不在本轮擅自改 F01）：
  * F01 那三个与我一致的数字（988 / 954 / 34）说明**不是整条错**；
  * 差异只落在「COL 计数」这一个量上，且我试了 8 种口径（宽松/严格/仅 .?AV/pCD 非零/被 vtable 指回/…）
    **没有一种得 1211**，故不是我能用现有判据复现的口径；
  * F01 的 evidence_paths 指向「看板第 7–9 轮段（审计 R13）」，属**另一条证据链**，本轮无权改它；
  * 因此本轮只做两件事：把这个差异登记成「未取得」，并在看板下一轮优先里列为机械目标。

写入：
  1) FACT_INDEX v5.34 -> v5.35：只给 F29 的 R139 段追加一句交叉核对声明（不动任何数字）。
  2) LEAD_LOCK 追加 NL3 段（CR 保持 137）。
  3) STATUS_BOARD 追加「十 · 收口期追加」（CR 保持 0，总行数 <= 300）。

纪律：wx 独占备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验 -> 重跑门禁。
"""
import os
import re
import sys
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
PRV = os.path.join(R14, 'R17_R106_FACTINDEX_V534', 'FACT_INDEX.tsv')
DSTD = os.path.join(R14, 'R17_R107_FACTINDEX_V535')
DST = os.path.join(DSTD, 'FACT_INDEX.tsv')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')

DRY = '--dry' in sys.argv
TS = time.strftime('%Y%m%d_%H%M%S')
fails, buf = [], []

OLD_SHA = '4299ee57add65dab'     # 前缀断言用
OLD_BYTES = 71203


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def sha(b):
    return hashlib.sha256(b).hexdigest()


F29_ADD = (u'**【R139 交叉核对·与 F01 冲突的一处数字（未取得，本轮不改 F01）】** '
           u'本轮上述 RTTI 链同时可算出与 `F01` 可比的三个量，**三个完全一致**：'
           u'TypeDescriptor **988**（`.?AV` 962 + `.?AU` 26）、主 COL（`mdisp==0`）**954**、'
           u'「无任何 vtable 指回的 TD」**34**。但**总 COL 数不一致**：`F01` 写 **1211**、'
           u'并写「1201 条 COL 被某 vtable 以 `[-4]` 指回」，而本轮测得**总 COL 1214（仅 `. ?AV` 侧）'
           u'／1216（含 `. ?AU`）**、被 vtable 指回的 COL **1214**（指回 1218 次、去重 1214）。'
           u'本轮试过 8 种口径（宽松 `sig==0 ∧ +12==TD` / 再加 `+16` 落数据节 / 仅 `. ?AV` / '
           u'`pCD` 非零 / 5 个 dword 全一致 / 仅被 vtable 指回 / 含 `. ?AU` / 取主 COL）'
           u'**没有一种得 1211 或 1201**，故不是现有判据能复现的口径差。'
           u'处置：`F01` 的 evidence_paths 指向「看板第 7–9 轮段（审计 R13）」属**另一条证据链**，'
           u'本轮**不擅自改 F01 一个字**；此差异登记为**未取得**，下轮按「先复现 1211 的口径」推进。'
           u'边界：本条 63/77 等四数**不依赖** COL 总数（依赖的是 77 个具名表的虚表指针与槽字节），'
           u'故该差异**不影响**本条结论。')

LOCK_SEG = u'''
NL3. 🔴 **跨事实项数字冲突被发现并如实登记（未取得，不擅自改 F01）.** 审计员 #305 中途输出里出现「F01：总 COL 1211」。主会话复算：TD **988**、主 COL **954**、「无 vtable 指回的 TD」**34** —— 这三个与 F01 **完全一致**；但**总 COL 我测得 1214（仅 `. ?AV`）/ 1216（含 `. ?AU`）**，F01 写 **1211**；F01 的「1201 条 COL 被 vtable 指回」我测得 **1214**（指回 1218 次、去重 1214）。试了 **8 种口径**（宽松 / 再加 `+16` 落数据节 / 仅 `. ?AV` / `pCD` 非零 / 5 dword 全一致 / 仅被 vtable 指回 / 含 `. ?AU` / 取主 COL）**没有一种得 1211 或 1201**。F01 的 evidence 指向「看板第 7–9 轮段（审计 R13）」，属另一条证据链 ⇒ **本轮不改 F01 一个字**，登记为未取得。边界：F29 的 63/77 四数**不依赖** COL 总数（依赖 77 个具名表的虚表指针与槽字节），故该差异**不影响** F29 结论。

NM3. ✅ **本轮把 F29 的一句「此前无人验过」的限定语也验了（`_r139/r139i_f29_mainrule.py` 11 断言 11 PASS）.** F29 limitations 写「主表规则（槽数最多 / mdisp==0）会改变 **11/77** 个产品的**槽地址**，但『双槽皆桩 = 63』两规则相同」。实测：两规则主表不同的产品**恰 11 个**（全部是 Locomotion，槽数最多者 50 槽 vs mdisp==0 者 10~12 槽）；两规则下的两槽皆桩**都等于 63** ⇒ 原句可保留。反控：规则换「地址最小」分歧数变 **77**（说明 11 对规则敏感）、槽数口径不校验「落 `.text`」分歧数变 **77**、桩集合置空两计数归 **0**。

NN3. 📌 **自错一条（收口期，由断言抓出）.** **S-269** `r139i` 首版反控 N3 写成一个未闭合的 `lambda` 表达式，`SyntaxError` 当场抛在解析阶段（连跑都没跑起来）；改为显式循环后 11 项全 PASS。这条错没有进任何结论，但它说明「反控也必须能被语法/解析层抓住」，不只是逻辑层。

NO3. ✅ **收口.** 断言 r139b 20 + r139c 13 + r139a 22 + r139d 8 + r139e 20 + r139f 15 + r139g 37 + r139h 43 + r139i 11 = **189 项 189 PASS / 0 FAIL**（子代理侧 #304 自报 7 项、#305 未成件不计入）。终态 `check_disc.py` exit 0、C10 ok(R139)、C7 31/31、C7d `97299336`、C11 frozen 12/12 sha `5b9455a0` OK、C12 12/12、C12b 12/12、C15 137 节 / 末节 143 / 1,195,865 B、C16 pinned 137 / unpinned 0 / hollow 0 / missing 0 / min margin 1,155、C16d `9091db94`。五项 CR **1081 / 337 / 137 / 0 / 2952** 全绿；看板 269 行（< 300）。全程未对整段 `.text` 开 `detail=True`；脚本均带 timeout；收口前 `ps` 确认无孤儿。
'''

BOARD_SEC = u'''
### 十 · 收口期追加（如实记，不改上文）

**一处跨事实项数字冲突被登记为「未取得」，本轮不动 F01.** 审计员 #305 的中途输出里出现「F01 正文：总 COL 1211 / 主 COL 954 / TD 988」，主会话据此用本轮同一套 RTTI 链去对账：

| 量 | F01 写 | R139 实测 | 判定 |
|---|---|---|---|
| TypeDescriptor 数 | 988 | **988**（`.?AV` 962 + `.?AU` 26） | **一致** |
| 主 COL（`mdisp==0`） | 954 | **954** | **一致** |
| 无任何 vtable 指回的 TD | 34 | **34** | **一致** |
| 总 COL | 1211 | **1214**（仅 `. ?AV`）/ **1216**（含 `. ?AU`） | **不一致** |
| 被 vtable 指回的 COL | 1201 | **1214**（指回 1218 次、去重 1214） | **不一致** |

试过 **8 种口径**（宽松 `sig==0 ∧ +12==TD` / 再加 `+16` 落数据节 / 仅 `. ?AV` / `pCD` 非零 / 5 个 dword 全一致 / 仅被 vtable 指回 / 含 `. ?AU` / 取主 COL），**没有一种得 1211 或 1201**，故这不是现有判据能解释的口径差。

**处置**：F01 的 `evidence_paths` 指向「看板第 7–9 轮段（审计 R13）」，是**另一条证据链**，本轮**不改 F01 一个字**；差异登记为**未取得**，下轮按「先复现 1211 的口径」推进。**边界**：F29 的 63/77、64/77、74/77 四数**不依赖** COL 总数（依赖的是 77 个具名表的虚表指针与槽字节），故该差异**不影响** F29 结论。

**另：本轮把 F29 一句此前无人验过的限定语验掉了.** F29 写「主表规则（槽数最多 / mdisp==0）会改变 **11/77** 个产品的**槽地址**，但『双槽皆桩 = 63』两规则相同」。实测：两规则主表不同的产品**恰 11 个**（全部是 Locomotion：槽数最多者 50 槽 vs `mdisp==0` 者 10~12 槽）；两规则下的两槽皆桩**都等于 63** ⇒ 原句保留。反控：规则换「地址最小」分歧数变 **77**、槽数口径不校验「落 `.text`」分歧数变 **77**、桩集合置空两计数归 **0**。

**自错一条**：S-269 `r139i` 首版反控 N3 写成一个未闭合的 `lambda`，`SyntaxError` 在解析阶段就抛（连跑都没起来）；改为显式循环后 11 项全 PASS。**反控也要能被语法层抓住，不只在逻辑层。**

**收口断言合计**：r139b 20 + r139c 13 + r139a 22 + r139d 8 + r139e 20 + r139f 15 + r139g 37 + r139h 43 + r139i 11 = **189 项 189 PASS / 0 FAIL**（#304 自报 7 项、#305 未成件不计入）。
'''


def main():
    W('# R139 收口期追加：F01 冲突登记%s' % ('  [DRY]' if DRY else ''))
    old = open(PRV, 'rb').read()
    ck('B1 v5.34 sha256 前缀 4299ee57', sha(old).startswith(OLD_SHA), sha(old)[:16])
    ck('B2 v5.34 字节数 71,203', len(old) == OLD_BYTES, len(old))
    ck('B3 v5.34 CR=0', old.count(b'\r') == 0, old.count(b'\r'))

    lines = old.decode('utf-8').split('\n')
    ck('B4 56 行（55 事实 + 表头 + 末尾空）', len(lines) == 56, len(lines))
    idx = {l.split('\t')[0]: i for i, l in enumerate(lines) if l.count('\t') == 4}
    ck('B5 F29 行存在', 'F29' in idx)
    c = lines[idx['F29']].split('\t')
    ck('F29.1 5 列', len(c) == 5, len(c))
    ck('F29.2 limitations 尚无本轮交叉核对段', 'R139 交叉核对' not in c[4])
    ck('F29.3 limitations 已含 R139 实测段（前置条件）', '【R139 实测' in c[4])
    c[4] = c[4] + F29_ADD
    ck('F29.4 追加后含 F01', 'F01' in c[4])
    ck('F29.5 追加后含「不影响」边界声明', '不影响本节结论' in c[4] or '不影响' in c[4])
    ck('F29.6 单行内无 LF/CR', '\n' not in '\t'.join(c) and '\r' not in '\t'.join(c))
    ck('F29.7 statement/grade/evidence 三列一字未动',
       c[1] == lines[idx['F29']].split('\t')[1] and c[2] == '[已证]' and
       c[3] == lines[idx['F29']].split('\t')[3])
    lines[idx['F29']] = '\t'.join(c)
    new = '\n'.join(lines).encode('utf-8')
    ck('W1 CR 仍 0', new.count(b'\r') == 0, new.count(b'\r'))
    ck('W2 只有 F29 一行变化',
       sum(1 for a, b2 in zip(old.decode('utf-8').split('\n'), lines) if a != b2) == 1,
       sum(1 for a, b2 in zip(old.decode('utf-8').split('\n'), lines) if a != b2))
    ck('W3 55 条事实行不变',
       len([1 for l in lines if l.count('\t') == 4]) == 55)
    W('  %d B -> %d B (+%d)' % (len(old), len(new), len(new) - len(old)))

    # ---- LEAD_LOCK ----
    lk_b = open(LOCK, 'rb').read()
    ck('L1 LEAD_LOCK 旧 CR 137', lk_b.count(b'\r') == 137, lk_b.count(b'\r'))
    lk_t = lk_b.decode('utf-8')
    ck('L2 NL3 尚不存在', 'NL3. ' not in lk_t)
    new_lk = (lk_t.rstrip('\n') + '\n' + LOCK_SEG)
    if not new_lk.endswith('\n'):
        new_lk += '\n'
    lk_nb = new_lk.encode('utf-8')
    ck('L3 新 CR 仍 137', lk_nb.count(b'\r') == 137, lk_nb.count(b'\r'))
    for t in ('NL3', 'NM3', 'NN3', 'NO3'):
        ck('L4 %s 在场' % t, (t + '. ') in new_lk)

    # ---- BOARD ----
    br_b = open(BRD, 'rb').read()
    ck('S1 看板旧 CR 0', br_b.count(b'\r') == 0, br_b.count(b'\r'))
    br_t = br_b.decode('utf-8')
    ck('S2 「十 · 收口期追加」尚不存在于 R139 段', br_t.count('### 十 · 收口期追加') == 1,
       br_t.count('### 十 · 收口期追加'))
    new_br = br_t.rstrip('\n') + '\n' + BOARD_SEC
    if not new_br.endswith('\n'):
        new_br += '\n'
    br_nb = new_br.encode('utf-8')
    ck('S3 新 CR 仍 0', br_nb.count(b'\r') == 0, br_nb.count(b'\r'))
    ck('S4 行数 %d <= 300' % br_nb.count(b'\n'), br_nb.count(b'\n') <= 300, br_nb.count(b'\n'))

    if DRY:
        W('\n[DRY] 未写盘。%d 项，%d FAIL' % (len(buf), len(fails)))
        return 1 if fails else 0

    # ---- 写 ----
    os.makedirs(DSTD, exist_ok=True)
    for path, oldb, newb, tag in ((PRV, old, new, 'FACT_INDEX_v535'),
                                  (LOCK, lk_b, lk_nb, 'LEAD_LOCK_NL3'),
                                  (BRD, br_b, br_nb, 'STATUS_BOARD_add')):
        p = os.path.join(BASE, os.path.basename(path) + '.before_R139_%s_%s.bak' % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, oldb)
        finally:
            os.close(fd)
        ck('%s 备份 sha 一致' % tag, sha(open(p, 'rb').read()) == sha(oldb))
    # FACT_INDEX 写新版本目录（源 v5.34 不动）
    tmp = DST + '.tmp_r139j'
    if os.path.exists(tmp):
        os.remove(tmp)
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, new)
    finally:
        os.close(fd)
    os.replace(tmp, DST)
    for path, newb, tag in ((LOCK, lk_nb, 'LEAD_LOCK'), (BRD, br_nb, 'STATUS_BOARD')):
        tmp2 = path + '.tmp_r139j'
        if os.path.exists(tmp2):
            os.remove(tmp2)
        fd = os.open(tmp2, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, newb)
        finally:
            os.close(fd)
        os.replace(tmp2, path)

    ck('X1 v5.35 回读 sha 一致', sha(open(DST, 'rb').read()) == sha(new))
    ck('X2 v5.34 源一个字节未动', sha(open(PRV, 'rb').read()) == sha(old))
    ck('X3 LEAD_LOCK 回读 CR 137', open(LOCK, 'rb').read().count(b'\r') == 137)
    ck('X4 看板回读 CR 0', open(BRD, 'rb').read().count(b'\r') == 0)
    ck('X5 看板回读行数 %d <= 300' % open(BRD, 'rb').read().count(b'\n'),
       open(BRD, 'rb').read().count(b'\n') <= 300)
    ck('X6 v5.35 55 条事实行',
       len([1 for l in open(DST, encoding='utf-8').read().split('\n') if l.count('\t') == 4]) == 55)

    W('\n== %d 项，%d FAIL ==' % (len(buf), len(fails)))
    for f in fails:
        W('  FAIL: ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
