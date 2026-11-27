#!/usr/bin/env python3
"""R170 A：基线实测（只读）。
① V549 身份；② F23/F35/F24/F29 grade 与目标措辞在场计数；
③ grade 词表定义是否在盘（多模式全库检索）；④ R90 七式复算 + 鉴别力反控。
"""
import hashlib, os, re, subprocess, json
ROOT = '/home/t628/projects/ra2-campaign-forge'
L = ROOT + '/lead/next_re_20261117_r14'
V549 = L + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
OUT = {}
def ck(name, got, want, tol=None):
    ok = (got == want) if tol is None else (abs(got - want) <= tol)
    print(('PASS' if ok else 'FAIL'), name, '=', got, 'want', want)
    assert ok, (name, got, want)

raw = open(V549, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()
ck('V549.bytes', len(raw), 117545); ck('V549.sha16', sha[:8], 'f1d32127'); ck('V549.CR', raw.count(b'\r'), 0)
txt = raw.decode('utf-8')
parts = txt.split('\n')
ck('V549.parts', len(parts), 56)          # 55 lines + trailing
ck('V549.rows', len([p for p in parts[1:] if p.strip()]), 54)
rows = {}
for p in parts[1:]:
    if not p.strip(): continue
    f = p.split('\t'); ck('cols.' + f[0], len(f), 5); rows[f[0]] = f

# ② grade 现状
for fid, g in (('F23', '[已证]'), ('F35', '[流程]'), ('F24', '[已证]'), ('F29', '[已证]')):
    ck('grade.' + fid, rows[fid][2], g)

# 目标措辞在场（statement + limitations 合并；并以分段计数留口径）
def cnt(s, pat): return s.count(pat)
for fid in ('F23', 'F35'):
    s, lim = rows[fid][1], rows[fid][4]
    both = s + '\n' + lim
    print('--', fid, 'stmt', len(s), 'lim', len(lim))
    OUT[fid + '.len'] = [len(s), len(lim)]
    for pat in ('差 **1 行无归属**', '没有归属', '4,147,334', '不可重数', '缺一手权威',
                '已撤回', '无外部规范权威', 'coverage.tsv', 'proved_strict'):
        print('   pat %-24r stmt=%d lim=%d both=%d' % (pat, cnt(s, pat), cnt(lim, pat), cnt(both, pat)))

# ③ grade 词表定义在盘？多模式全库（只搜文本件，限大小）
pats = ['grade 四档', '分级口径', 'grade 取值', 'grade 语义', '四个 grade', 'grade 列定义',
        '已证\\]=\\[', '\\[已证\\]=', 'grade: \\[已证\\]']
hits = {}
for pat in pats:
    r = subprocess.run(['grep', '-rIl', '--include=*.md', '--include=*.tsv', '--include=*.txt',
                        '-e', pat, ROOT + '/lead'], capture_output=True, text=True)
    files = [x for x in r.stdout.split('\n') if x]
    hits[pat] = len(files)
    if files: print('   defpat %-18r files=%d first=%s' % (pat, len(files), files[0].replace(ROOT + '/', '')))
OUT['defpatterns'] = hits
print('DEFPAT total-files-with-any:', sum(1 for v in hits.values() if v))

# ④ R90 七式复算（F23 正文数字）+ 鉴别力反控
n_all = 18498
ck('R90.1654+5875+10969', 1654 + 5875 + 10969, n_all)
ck('R90.458+1196', 458 + 1196, 1654)
ck('R90.863+791', 863 + 791, 1654)
for num, den, pct in ((458, 1654, 27.69), (291, 1654, 17.59), (293, 1654, 17.71), (863, 1654, 52.18)):
    ck('R90.pct.%d' % num, round(num / den * 100, 2), pct)
# 鉴别力：把 A 换成任意值，七式是否全存活（恒真）
alive = []
for A in (300, 400, 500, 600, 900, 1200):
    none_ = 1654 - A
    okA = (A + none_ == 1654) and (458 + 1196 == 1654) and (863 + 791 == 1654) and (1654 + 5875 + 10969 == 18498)
    alive.append((A, okA))
print('R90 鉴别力反控 (A, 七式仍全真):', alive)
ck('R90.no-discrim', [x[1] for x in alive], [True] * 6)

json.dump(OUT, open(ROOT + '/_r170/r170a_baseline.json', 'w'), ensure_ascii=False, indent=1)
print('ALL PASS')
