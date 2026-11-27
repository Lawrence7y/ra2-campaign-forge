#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159e_fact_revision.py — FACT_INDEX 正文修订（目标①）：F23 与 F35 两块**追加式**修订。

只追加，不改任何既有字符：
  F23 追加两段：
    【R159 补·12 行分解的缺口是 1 行，且该分解只在 v5.40 起存在】
    【R159 补·计数依赖的 coverage.tsv 已失，但它的内容指纹在盘】
  F35 追加一段：
    【R159 补·「proved_strict 定义缺一手权威」的自指闭环】
随后 F08：
    【R159 补·evidence_paths 的第二项指向一个从未落盘的台账目录】

写入纪律：wx 独占备份 + 断言旧 sha256 + 一次性写 + 回读逐字校验 + 幂等。
本脚本只改 R17_R114_FACTINDEX_V542/FACT_INDEX.tsv 这一个文件（+ 一份新版本副本）。
"""
import hashlib
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
OLD = D + '/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
NEWDIR = D + '/R17_R115_FACTINDEX_V543'
NEW = NEWDIR + '/FACT_INDEX.tsv'
BD = D + '/R17_LEAD_BASELINE'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def rb(p):
    with open(p, 'rb') as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

print('== 0 · 旧态 ==')
src = rd(OLD)
sha_old = sha(src.encode())
print('  V542 FACT_INDEX.tsv  sha256=%s  bytes=%d' % (sha_old, len(rb(OLD))))
raw = src.split('\n')
if raw and raw[-1] == '':
    raw = raw[:-1]
hdr = raw[0].split('\t')
ck('0.1 表头 5 列且为预期字段',
   hdr == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'], hdr)
rows = [l.split('\t') for l in raw[1:]]
ck('0.2 54 数据行、每行 5 列', len(rows) == 54 and all(len(r) == 5 for r in rows),
   (len(rows), sorted({len(r) for r in rows})))

# ---------- 1 · 事实先复算（改正文前必须先拿到数）----------
print('\n== 1 · 追加内容里每个数字的实测依据 ==')
import glob, subprocess

# 1a F23：12/6/2/3 与版本首现
f23 = {r[0]: r for r in rows}['F23']
blob23 = f23[1] + '\n' + f23[4]
m = re.search(r'(\d+)\s*行分解', blob23)
m2 = re.search(r'(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*之和为?\s*\*{0,2}(\d+)\*{0,2}', blob23)
ck('1.1 F23 正文含 12 行分解与 6+2+3 算式', m is not None and m2 is not None, None)
tot23 = int(m.group(1)); a, b, c = (int(m2.group(i)) for i in (1, 2, 3)); claimed = int(m2.group(4))
ck('1.2 三项和 11 == 自报、差 1 到 12', a + b + c == claimed == 11 and tot23 == 12
   and tot23 - (a + b + c) == 1, (a + b + c, claimed, tot23))

vers = sorted(glob.glob(D + '/R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv'))
found = []
for p in vers:
    tag = re.search(r'(V5\d+)', p).group(1)
    rws = [l.split('\t') for l in rd(p).split('\n') if l.strip()][1:]
    dd = {r[0]: r for r in rws}
    if 'F23' not in dd:
        continue
    bb = dd['F23'][1] + '\n' + dd['F23'][4]
    if re.search(r'(\d+)\s*行分解', bb) and re.search(r'\d+\s*\+\s*\d+\s*\+\s*\d+\s*之和为', bb):
        found.append(tag)
print('  含「12 行分解」的版本 =', found)
# 断言必须对「本轮之后又多了 V543」保持成立：写死 == ['V540','V541','V542'] 会在
# 幂等复跑时假 FAIL（S-432 同族：把某时刻的集合当不变式）。正确判据是两条结构性命题：
#   ① 首现版本是 V540；② 从首现到最后一版每一版都含（无中途消失）。
ck('1.3 该分解首现于 V540（扫描 %d 版）' % len(vers),
   bool(found) and found[0] == 'V540' and 'V539' not in found, found)
ck('1.3b 从首现版本到最后一版逐版连续含该分解（中途无消失）',
   found == ['V%d' % (540 + i) for i in range(len(found))], found)
ck('1.4 反控：V539 及以前 0 版含该分解', 'V539' not in found and 'V530' not in found, found)

# 1b F23：coverage.tsv 的指纹出处（两份独立清单）
def grab_cov_sha(path):
    for line in io.open(path, encoding='utf-8'):
        cc = line.rstrip('\n').split('\t')
        if cc and cc[0].endswith('next_re_20261117_r14/COVERAGE/coverage.tsv'):
            return cc
    return None
u = grab_cov_sha(D + '/_r67/unique_content_4417.tsv')
ck('1.5 unique_content_4417.tsv 有 coverage.tsv 行', u is not None, None)
cov_bytes = int(u[1]); cov_sha = u[3]
print('  coverage.tsv  bytes=%d  sha256=%s' % (cov_bytes, cov_sha))
ck('1.6 字节数 == 4,147,334（正文引用的那个数）', cov_bytes == 4147334, cov_bytes)
ck('1.7 sha256 是 64 位十六进制且以 c2ee063f 开头',
   len(cov_sha) == 64 and cov_sha.startswith('c2ee063f'), cov_sha[:16])
tier = [l.rstrip('\n').split('\t') for l in io.open(
    D + '/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv', encoding='utf-8')
    if 'COVERAGE/coverage.tsv' in l]
ck('1.8 第二份独立清单里也恰 1 条是 4,147,334 B（两份互证）',
   sum(1 for x in tier if int(x[1]) == 4147334) == 1,
   [x[1] for x in tier])
ck('1.9 4 条记录的字节各不相同 ⇒ 该 4,147,334 在清单内唯一（反控）',
   len({x[1] for x in tier}) == len(tier) == 4, [x[1] for x in tier])

# 1c 全库 coverage.tsv 精确名命中 0（find 口径，S-427 教训：不用 os.walk 全库）
p = subprocess.run(['find', R, '-name', '.git', '-prune', '-o', '-name', '__pycache__',
                    '-prune', '-o', '-name', 'coverage.tsv', '-print'],
                   capture_output=True, text=True, timeout=180)
hits = [x for x in p.stdout.split('\n') if x.strip()]
ck('1.10 全库按精确名 coverage.tsv 命中 0 件（「已失」实测）', hits == [], hits[:3])

# 1d F35：strict_panel.py 的行号与 [未证] 次数
sp = D + '/RULING_R15_20261119/work/strict_panel.py'
lines35 = rd(sp).split('\n')
ck('1.11 第 14 行是散文措辞', 'proved_strict' in lines35[13] and '[未证]' in lines35[13], lines35[13][:70])
ck('1.12 第 76 行是 grade 判定、第 78 行是 sem 判定（嵌套）',
   'grade == "[已证]"' in lines35[75] and '"[未证]" not in sem' in lines35[77],
   (lines35[75].strip()[:40], lines35[77].strip()[:40]))
n_weizheng = rd(sp).count('[未证]')
ck('1.13 [未证] 全文恰 2 次', n_weizheng == 2, n_weizheng)

# 1e F08：台账目录
dirs = sorted(os.path.basename(x) for x in glob.glob(D + '/R17_LEDGER_*'))
print('  盘上 R17_LEDGER_* 目录 =', dirs)
ck('1.14 盘上只有 R17_LEDGER_1063，无 R17_LEDGER_1064', dirs == ['R17_LEDGER_1063'], dirs)
ck('1.15 F08 第二项证据路径指向 R17_LEDGER_1064（正是缺的那个）',
   'R17_LEDGER_1064' in {r[0]: r for r in rows}['F08'][3], None)

# 1f F35 证据链在盘性（反控：不是所有都失联）
def evid_state(r):
    out = []
    for seg in r[3].split(';'):
        seg = seg.strip()
        if not seg:
            continue
        q = seg.replace('\\', '/').split('(')[0]
        out.append((seg, os.path.exists(os.path.join(R, q))))
    return out
live35 = sum(1 for _, e in evid_state({r[0]: r for r in rows}['F35']) if e)
ck('1.16 F35 五项证据 4 活 1 失', live35 == 4, live35)

# ---------- 2 · 组装追加文本 ----------
print('\n== 2 · 组装追加文本（只追加，不改既有字符）==')
ADD23 = (
    ' **【R159 补·12 行分解的缺口与作用域】** 上句「12 行分解」的三个分项 6 + 2 + 3 '
    '与 total = 12 **确实出自同一段正文**（不是跨行拼凑）：正文自报之和 11，与 12 差 '
    '**1 行无归属**；第二读法 6 + 2 + 3 + 3 = 14 > 12，多 **2** 行。两读法都不闭合 ⇒ '
    '缺口**对读法不敏感**（R148 A1a–A1c 只证了「两读法都不等于 12」的算术，未证三个分项与 '
    'total 同源；本轮补证同源：`_r159/r159d_f23_gap.py` 0.3/0.5/0.6/0.9/1.0 与三条反控）。'
    '**这句话有版本作用域，引用必须带**：逐版扫 13 版（V530–V542），「N 行分解 + 三项算式」'
    '在 **V539 及以前共 0 版命中**，**首现于 V540**，V541/V542 逐字延续（同脚本 1.3/1.4）。'
    '脱作用域引用会把一个 v5.40 起才写下的表述当成「本条一直如此」。'
)
ADD23B = (
    ' **【R159 补·丢失件有内容指纹，不是无名失联】** 上句「该文件已失」说的是**现盘不可读**；'
    '它的**内容指纹仍在盘**，可机械反查：字节数 **4,147,334**、sha256 '
    '**c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a**，出处为两份'
    '**互不相同**的清单——`lead/next_re_20261117_r14/_r67/unique_content_4417.tsv` 第 1022 行与 '
    '`lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv` 第 1022 行；后者按路径串 '
    '`COVERAGE/coverage.tsv` 共 **4** 条记录（主份 1 + `_hygiene` 备份 3），其中字节数恰为 '
    '4,147,334 的**只有 1 条**，且四条字节互不相同 ⇒ 该摘要无歧义（`_r159/r159d_f23_gap.py` '
    '1.5–1.9；全库按精确名命中 0 件 = 1.10）。⇒ 正确措辞是「**内容指纹在盘、文件本体不在**」，'
    '而**不是**「什么都查不到」；但**指纹能核身份、不能恢复内容**，故 458/291/293/1,196 与分母 '
    '1,654 **仍不可重数**，结论不变。'
)
ADD35 = (
    ' **【R159 补·「缺一手权威」这个说法本身的自指闭环】** R138 那句「`proved_strict` 定义'
    '缺一手权威」已由上文明文撤回；本轮补它的**残余效力边界**：该定义的一手代码权威是 '
    '`RULING_R15_20261119/work/strict_panel.py` 第 78 行（`if "[未证]" not in sem:`，嵌套在'
    '第 76 行 `if grade == "[已证]":` 内），散文措辞在第 14 行，全文 `[未证]` 恰 **2 次**'
    '（`_r159/r159e_fact_revision.py` 1.11–1.13）。**但这条权威本身是流程产物、不是外部规范**'
    '：它由本项目的裁定目录定义，没有任何外部标准或原厂文档为它背书。⇒ 准确表述是'
    '「**定义有代码权威、无外部规范权威**」，一句「缺一手权威」与一句「已有一手权威」'
    '**都过强**。另：`COVERAGE/PANEL.md` 那一项**仍失联**（本条 5 项证据 4 活 1 失，同脚本 '
    '1.16），故「严格口径双列表」的**具体数值**仍不可重数——定义可引、数不可引。'
)
ADD08 = (
    ' **【R159 补·第二项证据路径指向一个从未落盘的目录】** `evidence_paths` 第二项指向 '
    '`R17_LEDGER_1064/SECTION.md`，但现盘 `lead/next_re_20261117_r14/` 下 `R17_LEDGER_*` '
    '目录**只有 `R17_LEDGER_1063` 一个**，**1064 从未落盘**（`_r159/r159e_fact_revision.py` '
    '1.14；反控 1.15 确认该路径正是 F08 写的那个）。⇒ 本项的 a–e 三个地址 '
    '`0x47C3D0` / `0x6F322F` / `0x6F2B40` 只能从 `R14_COMMON` §2.9 一 取，**不能**从台账取；'
    '任何「已在台账 §1064 见证」的措辞都是**引用了一个不存在的文档**。该项的 grade '
    '仍为 [静态推断]，本条不构成升档授权。'
)

# ---------- 3 · 幂等应用 ----------
print('\n== 3 · 应用（幂等）==')
targets = {'F23': (ADD23 + ADD23B, 'R159 补·12 行分解的缺口与作用域'),
           'F35': (ADD35, 'R159 补·「缺一手权威」这个说法本身的自指闭环'),
           'F08': (ADD08, 'R159 补·第二项证据路径指向一个从未落盘的目录')}

out_rows = []
applied = {'F23': 0, 'F35': 0, 'F08': 0}
for r in rows:
    fid = r[0]
    if fid in targets and targets[fid][1] not in r[4]:
        newlim = r[4] + targets[fid][0]
        ck('3.x %s 追加后长度增加' % fid, len(newlim) > len(r[4]), (len(r[4]), len(newlim)))
        ck('3.y %s 追加是纯后缀（原字符逐字保留）' % fid, newlim.startswith(r[4]), None)
        out_rows.append([r[0], r[1], r[2], r[3], newlim])
        applied[fid] = 1
    else:
        out_rows.append(list(r))

print('  本轮实际写入的 fact =', {k: v for k, v in applied.items() if v})

newtxt = '\n'.join(['\t'.join(hdr)] + ['\t'.join(r) for r in out_rows]) + '\n'
sha_new = sha(newtxt.encode())
print('  新文件 bytes=%d sha256=%s' % (len(newtxt.encode()), sha_new))

# ---------- 4 · 写盘（先备份，再写新版目录）----------
print('\n== 4 · 写盘 ==')
os.makedirs(NEWDIR, exist_ok=True)
stamp = time.strftime('%Y%m%d_%H%M%S')
bak = os.path.join(BD, 'FACT_INDEX.tsv.V542.before_r159_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(rb(OLD))
ck('4.1 备份已建（wx 独占）', os.path.exists(bak), os.path.basename(bak))
ck('4.2 备份字节 == 写前实读 sha', sha(rb(bak)) == sha_old, None)
ck('4.3 写前断言：源文件未被别人改过', sha(rb(OLD)) == sha_old, sha(rb(OLD))[:16])

if os.path.exists(NEW) and sha(rb(NEW)) == sha_new:
    print('  [idempotent] V543 已是本轮内容')
else:
    with io.open(NEW, 'w', encoding='utf-8', newline='') as f:
        f.write(newtxt)

back = rd(NEW)
ck('4.4 回读：V543 与内存中构造的文本逐字相同', sha(back.encode()) == sha_new, None)
ck('4.5 回读：V543 无 CR（全 LF）', back.count('\r') == 0, back.count('\r'))
ck('4.6 回读：V543 仍是 54 数据行 5 列',
   len([l for l in back.split('\n') if l.strip()]) == 55, None)
ck('4.7 原 V542 文件一字未改（本轮不覆盖历史版本）', sha(rb(OLD)) == sha_old, None)

# ---------- 5 · 内容校验 ----------
print('\n== 5 · 回读内容校验 ==')
nrows = [l.split('\t') for l in back.split('\n') if l.strip()][1:]
nd = {r[0]: r for r in nrows}
for fid in ('F23', 'F35', 'F08'):
    old_r = {r[0]: r for r in rows}[fid]
    ck('5.%s %s limitations 是旧值严格后缀' % (fid, fid), nd[fid][4].startswith(old_r[4]), None)
    ck('5.%s %s statement/grade/evidence 三列逐字未改' % (fid, fid),
       nd[fid][1] == old_r[1] and nd[fid][2] == old_r[2] and nd[fid][3] == old_r[3], None)
# 反控：其余 51 条一行未动
untouched = [r[0] for r in nrows if r[0] not in ('F23', 'F35', 'F08')]
oldmap = {r[0]: r for r in rows}
ck('5.9 其余 %d 条逐字未改（反控：改动面精确可控）' % len(untouched),
   all(nd[k] == oldmap[k] for k in untouched), len(untouched))
# 关键数字必须真的写进去了
ck('5.10 F23 新文本含 4,147,334 的 sha256', 'c2ee063f' in nd['F23'][4], None)
ck('5.11 F23 新文本含 V540 作用域标注', 'V540' in nd['F23'][4], None)
ck('5.12 F35 新文本含「无外部规范权威」', '无外部规范权威' in nd['F35'][4], None)
ck('5.13 F08 新文本含 R17_LEDGER_1064 与 1063 的对照',
   'R17_LEDGER_1064' in nd['F08'][4] and 'R17_LEDGER_1063' in nd['F08'][4], None)

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
