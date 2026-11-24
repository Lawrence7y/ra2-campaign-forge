# -*- coding: utf-8 -*-
"""R37 Check C 探针：先看「limitations 说某 token 是推断/未证」与「statement 怎么用这个 token」的形态分布，
用于设计可机械判的判据。不做判定，只列候选。"""
import io, os, re

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')

def load(p):
    raw = io.open(p, encoding='utf-8', newline='').read()
    lines = raw.split('\n')
    h = lines[0].split('\t')
    return [dict(zip(h, l.split('\t'))) for l in lines[1:] if l.strip()]

v510 = load(os.path.join(R14, 'R17_R65_FACTINDEX_V510', 'FACT_INDEX.tsv'))
v512 = load(os.path.join(R14, 'R17_R67_FACTINDEX_V512', 'FACT_INDEX.tsv'))
print('v5.10 rows', len(v510), ' v5.12 rows', len(v512))

# limitations 里「把某个 token 标为推断/未证」的句式
HEDGE_DECL = [
    r'的「([^」]{2,40})」是[^。；]{0,10}推断措辞',
    r'「([^」]{2,40})」[是为][^。；]{0,6}推断措辞',
    r'的「([^」]{2,40})」[^。；]{0,10}未经字节证实',
    r'「([^」]{2,40})」[^。；]{0,6}未经[^。；]{0,6}证实',
    r'「([^」]{2,40})」属[^。；]{0,10}推断',
    r'不得写成[「]?([^，。；」]{2,30})',
]

def extract_hedged(lim):
    out = []
    for pat in HEDGE_DECL:
        for m in re.finditer(pat, lim):
            t = m.group(1).strip()
            if len(t) >= 2:
                out.append(t)
    return sorted(set(out))

print()
print('=== A. limitations 中「标为推断/未证」的 token（v5.12）===')
for r in v512:
    hs = extract_hedged(r['limitations'])
    if hs:
        print('  %s  -> %s' % (r['fact_id'], ' | '.join(hs)))

print()
print('=== B. 这些 token 在 statement 里的出现情况（v5.12 现在的写法）===')
HEDGE_WORDS = ['推断', '未证', '未经', '存疑', '不能排除', '仅', '疑似', '不稳定', '待核']
for r in v512:
    for t in extract_hedged(r['limitations']):
        if t in r['statement']:
            i = r['statement'].index(t)
            ctx = r['statement'][max(0, i - 40):i + len(t) + 40]
            hedged = any(w in ctx for w in HEDGE_WORDS)
            print('  %-4s token=%-12s hedged_in_stmt=%-5s  ctx…%s…' % (r['fact_id'], t, hedged, ctx.replace('\n', ' ')))

print()
print('=== C. 同一探针跑 v5.10（已知含 F24/F29 两处未修文本，应能看出差别）===')
for r in v510:
    if r['fact_id'] in ('F24', 'F29'):
        print('  %s statement: %s' % (r['fact_id'], r['statement'][:150]))
        print('  %s limitations(末120字): %s' % (r['fact_id'], r['limitations'][-120:]))
        print()
