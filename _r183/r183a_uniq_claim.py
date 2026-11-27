# -*- coding: utf-8 -*-
"""R183 取证 A：全表「唯一性断言」与第 4 列实测项数的冲突普查。
判据（三分类，互斥）：
  CONFLICT  该出现所在句既无版本限定、又断言项数==1，而该行第 4 列实测项数 != 1
  QUALIFIED 同一断言但在句内含版本限定（真值只在那几个版本成立）
  OTHER_SEM 形近但不同义（唯一 + evidence_path 单数 + 后接「为」= 讲某行证据形态，不是本条项数）
"""
import csv, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
LED = os.environ.get('R183_LEDGER') or os.path.join(R, 'lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv')
FAIL = []; N = [0]
def ck(c, m):
    N[0] += 1
    if not c: FAIL.append(m)

def load(p):
    rows = list(csv.reader(open(p, encoding='utf-8'), delimiter='\t'))
    return rows[0], rows[1:]

def norm(e):
    return re.sub(r'\(.*?\)\s*$', '', e.replace('\\', '/').strip()).strip()

# 精确模式：断言「本行 evidence_paths 只有一项」
STRICT = ['唯一一项', '只有一项', '仅一项']
# 版本限定词（句内出现即判 QUALIFIED）
QUAL = ['及以前', 'v5.30', 'v5.33', 'V530', 'V533']

def sent_of(cell, i):
    L = max(cell.rfind('。', 0, i), cell.rfind('；', 0, i), cell.rfind('【', 0, i))
    rc = [x for x in (cell.find('。', i), cell.find('；', i)) if x >= 0]
    Rr = min(rc) if rc else len(cell)
    return cell[L+1:Rr]

def hits_of(cell, n):
    out = []
    for p in STRICT:
        st = 0
        while True:
            i = cell.find(p, st)
            if i < 0: break
            s = sent_of(cell, i)
            if any(q in s for q in QUAL): k = 'QUALIFIED'
            elif n == 1:                  k = 'CONSISTENT'
            else:                         k = 'CONFLICT'
            out.append((p, i, k, n, s)); st = i + len(p)
    # 广义形近（不同义），单独记
    for m in re.finditer(r'唯一\s*evidence_path(?![s])', cell):
        out.append(('唯一 evidence_path(单数)', m.start(), 'OTHER_SEM', n, sent_of(cell, m.start())))
    return sorted(out, key=lambda t: t[1])

def scan(p):
    _, rows = load(p)
    res = []
    for r in rows:
        items = [x for x in r[3].split(';') if x.strip()]
        for col, cn in ((1, 'statement'), (4, 'limitations')):
            for h in hits_of(r[col], len(items)):
                res.append(dict(fid=r[0], col=cn, pat=h[0], at=h[1], kind=h[2], n=h[3], sent=h[4]))
    return res

H = scan(LED)
print('== A. V563 全表（54 行 x 2 列）唯一性断言普查 ==')
print('命中处数 =', len(H))
for h in H:
    print('  %-4s %-11s %-22s %-10s n=%d  句=[%s]' % (h['fid'], h['col'], h['pat'], h['kind'], h['n'], h['sent'][:110]))

conf = [h for h in H if h['kind'] == 'CONFLICT']
qual = [h for h in H if h['kind'] == 'QUALIFIED']
other = [h for h in H if h['kind'] == 'OTHER_SEM']
print('\n  CONFLICT=%d  QUALIFIED=%d  OTHER_SEM=%d' % (len(conf), len(qual), len(other)))

# ---- A 段断言（双模：V563 基线 / 修后版本）----
POSTFIX = bool(os.environ.get('R183_POSTFIX'))
ck(len(H) >= 1, 'A0 判据不能空转：全表至少命中 1 处')
if POSTFIX:
    ck(len(conf) == 0, 'A1p 修后版本真冲突必须为 0，实测 %d' % len(conf))
    ck(len(qual) == 3, 'A4p 修后版本「已限定」应为 3 处（原 2 + 就地限定 1），实测 %d' % len(qual))
    ck(any(h['sent'].startswith('在 v5.33 及以前口径下，本条 evidence_paths') for h in qual),
       'A4q 就地限定句必须以版本限定词开头（改法本身就是负控验证过的那种）')
    ck(all(h['fid'] == 'F35' for h in qual), 'A5p 已限定处全在 F35')
    ck(len(other) == 1 and other[0]['fid'] == 'F22', 'A6p 不同义形近仍恰 1 处且在 F22')
else:
    ck(len(conf) == 1, 'A1 真冲突恰 1 处，实测 %d' % len(conf))
if not POSTFIX:
    ck(conf and conf[0]['fid'] == 'F35' and conf[0]['col'] == 'limitations' and conf[0]['n'] == 5,
       'A2 真冲突落在 F35.limitations 且该行第 4 列项数==5，实测 %r' % ([ (h['fid'],h['col'],h['n']) for h in conf ],))
    ck(conf and conf[0]['sent'].startswith('本条 evidence_paths 唯一一项即该已失文件'),
       'A3 冲突句首即该断言（不是被引文包住的形态）')
    ck(len(qual) == 2, 'A4 引文自指形态恰 2 处（R152 限定段 + 其后自述句），实测 %d' % len(qual))
    ck(all(h['fid'] == 'F35' for h in qual), 'A5 引文自指形态全在 F35')
    ck(len(other) == 1 and other[0]['fid'] == 'F22', 'A6 不同义形近恰 1 处且在 F22（唯一 evidence_path 单数），实测 %r'
       % ([ (h['fid'],h['pat']) for h in other ],))

# ---- 与同行 statement ④ 的正面对撞 ----
_, rows = load(LED); d = {r[0]: r for r in rows}
ck('5 项里只有' in d['F35'][1] and '其余 4 项在盘' in d['F35'][1], 'A7 statement ④ 的 5 项/4 项在盘 在场')
ck('整行证据链失联' in d['F35'][4], 'A8 limitations 仍带「整行证据链失联」字样')
f23n = len([x for x in d['F23'][3].split(';') if x.strip()])
f23p = sum(1 for x in d['F23'][3].split(';') if x.strip() and os.path.exists(os.path.join(R, norm(x))))
ck((f23n, f23p) == (2, 0), 'A9 F23 实测 (2,0) 全失联，实际 %r' % ((f23n, f23p),))
f35i = [x for x in d['F35'][3].split(';') if x.strip()]
f35p = sum(1 for x in f35i if os.path.exists(os.path.join(R, norm(x))))
ck((len(f35i), f35p) == (5, 4), 'A10 F35 实测 (5,4)，实际 %r' % ((len(f35i), f35p),))

# ---- 正反控 ----
tmp = '/tmp/r183a'; os.makedirs(tmp, exist_ok=True)
def mk(path, mut):
    hdr, rows = load(LED); rows = [list(r) for r in rows]
    mut({r[0]: r for r in rows}, rows)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(hdr); w.writerows(rows)

def kindc(hs): 
    return (len([x for x in hs if x['kind']=='CONFLICT']),
            len([x for x in hs if x['kind']=='QUALIFIED']),
            len([x for x in hs if x['kind']=='OTHER_SEM']))

# 反控1：F35 第 4 列砍到 1 项 => 该行断言变「一致」，CONFLICT 归 0，CONSISTENT 出现 3
def m1(dd, _): dd['F35'][3] = dd['F35'][3].split(';')[0]
mk(tmp+'/ctrl1_one_item.tsv', m1)
h1 = scan(tmp+'/ctrl1_one_item.tsv')
c1 = kindc(h1); cons1 = len([x for x in h1 if x['kind']=='CONSISTENT'])
print('\n  反控1（F35 砍到 1 项）：C/Q/O = %r, CONSISTENT=%d' % (c1, cons1))
ck(c1[0] == 0, 'B1 反控1：CONFLICT 必须归 0，实测 %d' % c1[0])
# S-183a1：初版写 cons1==3（把版本限定段也算成会翻转），而分类器先判 QUAL 再看 n
# => 那 2 处仍为 QUALIFIED，只有真冲突那 1 处转 CONSISTENT。按实测口径改。
# B2 的期望值随台账版本走（S-183b2：初版把 V563 的 (1,2) 写死，在 V564 上假 FAIL）
_exp_c1 = (0, 3) if POSTFIX else (1, 2)
ck((cons1, c1[1]) == _exp_c1, 'B2 反控1：CONSISTENT=%d / QUALIFIED=%d，期望 %r（POSTFIX=%s）' % (cons1, c1[1], _exp_c1, POSTFIX))

# 反控2：在冲突句里插入版本限定 => 该处转 QUALIFIED
def m2(dd, _):
    dd['F35'][4] = dd['F35'][4].replace('本条 evidence_paths 唯一一项即该已失文件',
                                       '在 v5.33 及以前口径下，本条 evidence_paths 唯一一项即该已失文件')
mk(tmp+'/ctrl2_qualified.tsv', m2)
h2 = scan(tmp+'/ctrl2_qualified.tsv'); c2 = kindc(h2)
print('  反控2（冲突句加版本限定）：C/Q/O = %r' % (c2,))
ck(c2[0] == 0 and c2[1] == 3, 'B3 反控2：CONFLICT 归 0 且 QUALIFIED 变 3，实测 %r' % (c2,))

# 反控3：删掉该句 => 该处消失
def m3(dd, _):
    dd['F35'][4] = dd['F35'][4].replace('本条 evidence_paths 唯一一项即该已失文件，故 F35 是本表里与 F23 并列的**两条整行证据链失联项**之一', '')
mk(tmp+'/ctrl3_deleted.tsv', m3)
h3 = scan(tmp+'/ctrl3_deleted.tsv'); c3 = kindc(h3)
print('  反控3（删掉冲突句）：C/Q/O = %r 总数 %d' % (c3, len(h3)))
ck(c3[0] == 0 and len(h3) == 3, 'B4 反控3：CONFLICT 归 0 且总数降为 3，实测 C=%d total=%d' % (c3[0], len(h3)))

# 反控4：把别行（F29，项数8）注入同一断言 => 判据必须抓到第 4 列项数 != 1 的新冲突
def m4(dd, _): dd['F29'][4] = dd['F29'][4] + '另：本条 evidence_paths 唯一一项即该已失文件。'
mk(tmp+'/ctrl4_inject.tsv', m4)
h4 = scan(tmp+'/ctrl4_inject.tsv')
f29c = [x for x in h4 if x['fid']=='F29']
print('  反控4（F29 注入）：F29 命中 %r' % ([ (x['kind'],x['n']) for x in f29c ],))
ck(len(f29c)==1 and f29c[0]['kind']=='CONFLICT' and f29c[0]['n']==8,
   'B5 反控4：F29 应得 1 处 CONFLICT 且 n==8，实测 %r' % ([ (x['kind'],x['n']) for x in f29c ],))

print('\n断言 %d 条，FAIL %d 条' % (N[0], len(FAIL)))
for f in FAIL: print('  FAIL', f)
sys.exit(1 if FAIL else 0)
