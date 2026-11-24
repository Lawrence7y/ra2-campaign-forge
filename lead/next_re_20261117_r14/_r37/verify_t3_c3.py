# -*- coding: utf-8 -*-
"""复核 T3 关于 C3 的指控：锚解析失败时 C3 是否 fail-open（空池 ⇒ 整行全报）。
不复用 checkC.py 的代码，按其判据重写一遍，并单独打印剥离括号后的路径。
"""
import io, os, re, csv

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI   = os.path.join(R14, 'R17_R69_FACTINDEX_V513', 'FACT_INDEX.tsv')

lines = io.open(FI, encoding='utf-8', newline='').read().split('\n')
h = lines[0].split('\t')
rows = [dict(zip(h, l.split('\t'))) for l in lines[1:] if l.strip()]
d = {r['fact_id']: r for r in rows}

ANCHOR_TAIL = re.compile(r'\([^()]*\)$')

def split_items(ev):
    out, depth, cur = [], 0, ''
    for ch in ev:
        if ch in '（(': depth += 1
        elif ch in '）)': depth = max(0, depth - 1)
        if ch == ';' and depth == 0:
            out.append(cur); cur = ''; continue
        cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]

print('=== F17 / F21 的锚逐项剥离与解析 ===')
for fid in ('F17', 'F21', 'F06', 'F07'):
    r = d[fid]
    print('-- %s  %s' % (fid, r['evidence_paths']))
    for it in split_items(r['evidence_paths']):
        f = ANCHOR_TAIL.sub('', it).strip()
        ap = os.path.join(ROOT, f.replace('\\', '/'))
        ok = os.path.isfile(ap)
        print('   item=%-60s -> file=%-58s isfile=%s' % (it[:60], f[:58], ok))
    print()

print('=== C3 判据重跑（含 fail-open 观测）===')
def c3(row, verbose=False):
    pool = []
    loaded, missing = [], []
    for it in split_items(row['evidence_paths']):
        f = ANCHOR_TAIL.sub('', it).strip()
        ap = os.path.join(ROOT, f.replace('\\', '/'))
        if os.path.isfile(ap):
            pool.append(io.open(ap, encoding='utf-8', errors='replace').read().lower())
            loaded.append(f)
        else:
            missing.append(f)
    blob = '\n'.join(pool)
    miss = []
    for m in re.finditer(r'0x([0-9A-Fa-f]{4,8})', row['statement']):
        hx = m.group(1).lower()
        cands = {hx, hx.lstrip('0'), hx.zfill(8), hx.zfill(6), str(int(hx, 16))}
        if not any(c in blob for c in cands):
            miss.append('0x' + m.group(1))
    return sorted(set(miss)), loaded, missing, len(blob)

for fid in ('F17', 'F21', 'F06', 'F07', 'F50'):
    miss, loaded, missing, bloblen = c3(d[fid])
    print('  %-4s 报出地址数=%-3d 已载锚=%d 解析失败锚=%d pool字符=%d' %
          (fid, len(miss), len(loaded), len(missing), bloblen))
    if missing:
        print('        解析失败的锚: %s' % missing)
    if miss:
        print('        报出: %s' % miss[:8])

print()
print('=== 结论性观测：解析失败锚是否导致整行全报 ===')
for fid in ('F17', 'F21'):
    r = d[fid]
    n_addr = len(set(re.findall(r'0x([0-9A-Fa-f]{4,8})', r['statement'])))
    miss, loaded, missing, bloblen = c3(r)
    print('  %-4s 正文地址总数=%-3d 报出=%-3d ⇒ 全报? %s' % (fid, n_addr, len(miss), len(miss) == n_addr and n_addr > 0))
