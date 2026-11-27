#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 C：规则 D —— 主会话亲自复算两个子代理的关键结论（不采信其自报）。
逐条复算：
  X1 执行员 #331 的 5 个文件 sha256
  X2 strict_panel.py 内 [未证] 出现 2 次（第 14 行散文 + 第 78 行代码）；代码形态恰 1 次
  X3 三条 M59 脚本的判据行号原文：precheck.py:60 sem / simulate.py:72 r[3] / verify.py:83 r[3]
  X4 merge_panel.py 不含判据（反控）
  X5 F23 evidence_paths 两项是否都在盘（审计员称两项全失联）
  X6 F35 evidence_paths 五项存在性
  X7 4,147,334 在现盘台账的逐字佐证（审计员称 42 行 + sha 钉）
  X8 审计员批评「两个父目录都不在」为伪 —— 复算我自己的 A3h 到底测了哪两个目录
"""
import hashlib, io, json, os, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI = os.path.join(R14, 'R17_R111_FACTINDEX_V539', 'FACT_INDEX.tsv')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()


# ---------- X1 sha256 ----------
EXPECT = {
    'RULING_R15_20261119/work/strict_panel.py': '731c98ea4910f5e910ce95ae2ae14e471af98d4d0a9d0051a32c9968e65e5f86',
    '_cards/M59-MERGE/precheck.py': 'bd0a3ff023bf76bbc6584866352171d0220dec6ac5c7a5e54f1bb22d6f2ef70d',
    '_cards/M59-MERGE/simulate.py': 'fb325686be0ec68f2ec3928bbadf6a2332f4d87757809e912e9814f2961fa0df',
    '_cards/M59-MERGE/verify.py': '98ea5d6032bf75442d7a52741c4bf3fdfa7f0b6cc49b6c24ee6156643dd8f2a6',
    '_cards/M59-MERGE/merge_panel.py': 'ac7e04a7fb11ce944c7c5bdbf19e3ac6a6e417e992bde2278415aea5a9bee76e',
}
for rel, want in EXPECT.items():
    p = os.path.join(R14, rel)
    got = hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else 'MISSING'
    ck('X1 执行员 sha256 逐字节一致 %s' % rel.split('/')[-1], got == want, got[:16])

# ---------- X2 ----------
sp = os.path.join(R14, 'RULING_R15_20261119', 'work', 'strict_panel.py')
t = rd(sp)
L = t.split('\n')
ck('X2a [未证] 全文恰 2 次（14 行散文 + 78 行代码）', t.count('[未证]') == 2, t.count('[未证]'))
ck('X2b 裸子串 未证 亦恰 2 次', t.count('未证') == 2, t.count('未证'))
ck('X2c 代码形态 [未证]" not in sem 恰 1 次', t.count('[未证]" not in sem') == 1,
   t.count('[未证]" not in sem'))
ck('X2d 第 78 行正是指标行', L[77].strip() == 'if "[未证]" not in sem:', L[77].strip())
ck('X2e 第 78 行嵌套在 grade == "[已证]" 之下（76 行）',
   L[75].strip() == 'if grade == "[已证]":', L[75].strip())
ck('X2f 第 14 行散文含 不含 [未证]', '不含 [未证]' in L[13], L[13].strip()[:50])

# ---------- X3 ----------
exp3 = {'_cards/M59-MERGE/precheck.py': (60, 'if "[未证]" not in sem:'),
        '_cards/M59-MERGE/simulate.py': (72, None),
        '_cards/M59-MERGE/verify.py': (83, None)}
for rel, (ln, exact) in exp3.items():
    LL = rd(os.path.join(R14, rel)).split('\n')
    line = LL[ln - 1].strip()
    ok = exact is None
    if exact is not None:
        ok = (line == exact)
    else:
        ok = ('[未证]" not in r[3]' in line) and line.startswith('if ')
    ck('X3 判据行号与形态 %s:%d' % (rel.split('/')[-1], ln), ok, line[:60])

# ---------- X4 反控 ----------
mp = rd(os.path.join(R14, '_cards/M59-MERGE/merge_panel.py'))
ck('X4 反控 merge_panel.py 全无 未证 字面', '未证' not in mp, mp.count('未证'))

# ---------- X5/X6 evidence_paths 存在性 ----------
rows = {}
for l in rd(FI).split('\n')[1:]:
    if l.strip():
        c = l.split('\t')
        rows[c[0]] = c


def check_ev(fid):
    pats = [p for p in rows[fid][3].split(';') if p.strip()]
    res = []
    for p in pats:
        q = p.split('(')[0].strip().replace('\\', '/')
        full = q if q.startswith('_') else os.path.join(ROOT, q)
        if not q.startswith('_'):
            full = os.path.join(ROOT, q)
        else:
            full = os.path.join(ROOT, q)
        res.append((q, os.path.exists(full)))
    return res


for fid in ('F23', 'F35'):
    r = check_ev(fid)
    miss = [q for q, ok in r if not ok]
    print('  [%s] evidence %d 项，缺失 %d 项: %s' % (fid, len(r), len(miss), miss))
    if fid == 'F23':
        ck('X5 F23 两项 evidence 全部失联（审计员主张）', len(r) == 2 and len(miss) == 2, r)
        ck('X5b F23 失联的两项恰是 R17_DELIVERY/DELIVERY_SUMMARY.md 与 COVERAGE/PANEL.md',
           sorted(q.replace('lead/next_re_20261117_r14/', '') for q in miss) ==
           ['COVERAGE/PANEL.md', 'R17_DELIVERY/DELIVERY_SUMMARY.md'], miss)
    if fid == 'F35':
        ck('X6 F35 5 项 evidence 里只 COVERAGE/PANEL.md 失联', len(r) == 5 and len(miss) == 1,
           (len(r), miss))
        ck('X6b F35 失联项恰为 COVERAGE/PANEL.md', miss == ['lead/next_re_20261117_r14/COVERAGE/PANEL.md'], miss)

# ---------- X7 4,147,334 台账 ----------
hits = []
for dp, dns, fns in os.walk(R14):
    dns[:] = [d for d in dns if d != '__pycache__']
    for fn in fns:
        if not fn.endswith(('.tsv', '.txt', '.md', '.json', '.py')):
            continue
        p = os.path.join(dp, fn)
        try:
            s = io.open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        if '4,147,334' in s or '4147334' in s:
            hits.append(os.path.relpath(p, R14))
print('  [X7] 含 4,147,334 的文件 %d 个: %s' % (len(hits), hits[:12]))
ck('X7a 有现盘台账逐字记 4,147,334（不是完全不可复核）', len(hits) >= 1, len(hits))
uc = os.path.join(R14, '_r67', 'unique_content_4417.tsv')
if os.path.exists(uc):
    txt = rd(uc).split('\n')
    ln = [i + 1 for i, l in enumerate(txt) if 'coverage.tsv' in l]
    ck('X7b _r67/unique_content_4417.tsv 命中 coverage.tsv 行号 == [1022]', ln == [1022], ln)
    if ln:
        ck('X7c 该行含 sha256 c2ee063f', 'c2ee063f' in txt[ln[0] - 1], txt[ln[0] - 1][:120])
else:
    ck('X7b _r67/unique_content_4417.tsv 在盘', False, uc)
tf = os.path.join(R14, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
tl = rd(tf).split('\n')
cov = [i + 1 for i, l in enumerate(tl) if 'coverage.tsv' in l]
print('  [X7] tier_final_4417 里 coverage.tsv 行号: %s' % cov)
ck('X7d tier_final_4417 里 coverage.tsv 命中 4 行（主份 + 3 备份）', len(cov) == 4, cov)
szs = [int(tl[i - 1].split('\t')[1]) for i in cov] if cov else []
print('  [X7] 四行字节: %s' % szs)
ck('X7e 四行里恰 1 行 == 4,147,334（主份），其余 3 行为不同世代备份',
   szs.count(4147334) == 1 and len(set(szs)) == 4, szs)

# ---------- X8 我自己 A3h 的措辞 ----------
ck('X8a r14 目录本身存在（审计员称「两个父目录都不在」为伪的根据）',
   os.path.isdir(R14), R14)
ck('X8b 我 A3h 实测的两个目录是 COVERAGE/ 与 lead/next_re_20261112_r10（均为 F35 输入侧，非 F23）',
   (not os.path.isdir(os.path.join(R14, 'COVERAGE')))
   and (not os.path.isdir(os.path.join(ROOT, 'lead', 'next_re_20261112_r10'))), '')
ck('X8c F23 limitations 原文点名的三目录亦均不存在',
   all(not os.path.isdir(os.path.join(R14, d)) for d in ('COVERAGE', 'R17_DELIVERY', 'R17_R41_RECOMPUTE')),
   '')

json.dump(dict(fails=fails), open(os.path.join(ROOT, '_r148', 'r148c_recompute_sub.json'), 'w',
                                  encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
