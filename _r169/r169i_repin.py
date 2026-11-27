#!/usr/bin/env python3
"""R169 I：门禁重钉 —— facts_floors.py 五点 + gate_runner.py 五处 V548->V549。

纪律（R160 S-531 / R167 S-541 / R168 S-543 同族错的防范）：
  ① 常量一律 ast.literal_eval 从源码取真值，不用正则抓 dict；
  ② MASTER_SHA256 由门禁自己的 canon 五函数 + 源码里的 11 项拼接顺序重算，
     并先用旧常量复算一次命中旧值（同法自证）；
  ③ 改写后必须 compile + 常量读回；
  ④ 幂等：已是新值则跳过，两态并存（首次要求变化，重跑要求稳定）。
"""
import ast, hashlib, json, re, os, py_compile, csv, io
ROOT = '/home/t628/projects/ra2-campaign-forge'
FF = ROOT + '/_r160/facts_floors.py'
GR = ROOT + '/_r161/gate_runner.py'
V549 = ROOT + '/lead/next_re_20261117_r14/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
BAKDIR = ROOT + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

raw549 = open(V549, 'rb').read()
sha549 = hashlib.sha256(raw549).hexdigest()
B549 = len(raw549)
assert sha549.startswith('f1d32127') and B549 == 117545, (sha549, B549)

# 备份（wx 独占）
def backup(path, tag):
    b = open(path, 'rb').read()
    dst = os.path.join(BAKDIR, os.path.basename(path) + '.before_r169_' + tag + '.bak')
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(b)
    assert hashlib.sha256(open(dst, 'rb').read()).hexdigest() == hashlib.sha256(b).hexdigest()
    return dst, hashlib.sha256(b).hexdigest()

bk_ff, ff_sha0 = backup(FF, 'FACTS_FLOORS')
bk_gr, gr_sha0 = backup(GR, 'GATE_RUNNER')

src = open(FF, encoding='utf-8').read()

def tops(text):
    out = {}
    for n in ast.parse(text).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try: out[n.targets[0].id] = ast.literal_eval(n.value)
            except Exception: pass
    return out

C = tops(src)
NAMES = ['CUR_SHA256', 'TOTAL_BYTES', 'GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST',
         'MASTER_SHA256', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ']
for n in NAMES: assert n in C, n
ns = {}
for fn in ('canon_g', 'canon_f', 'canon_e', 'canon_eb', 'canon_l'):
    m = re.search(r'^def %s\(.*?$' % fn, src, re.M)
    exec(m.group(0), ns)

def master_of(cur_sha, total, grades, floors, evid, evidb, lost, items, uniq, li, lu):
    blob = '\n'.join([cur_sha, str(total), ns['canon_g'](grades), ns['canon_f'](floors),
                      ns['canon_e'](evid), ns['canon_eb'](evidb), ns['canon_l'](lost),
                      str(items), str(uniq), str(li), str(lu)])
    return hashlib.sha256(blob.encode()).hexdigest()

old_master = C['MASTER_SHA256']
recomputed_old = master_of(C['CUR_SHA256'], C['TOTAL_BYTES'], C['GRADES'], C['FLOORS'],
                           C['EVID'], C['EVIDB'], C['LOST'], C['ITEMS'], C['UNIQ'],
                           C['LOST_ITEMS'], C['LOST_UNIQ'])
assert recomputed_old == old_master, (recomputed_old, old_master)

rows = list(csv.reader(io.StringIO(raw549.decode('utf-8')), delimiter='\t'))
f24 = [r for r in rows[1:] if r[0] == 'F24'][0]
new_f24 = (len(f24[1].encode('utf-8')), len(f24[4].encode('utf-8')))
FLOORS = dict(C['FLOORS']); old_f24 = FLOORS['F24']; FLOORS['F24'] = new_f24

new_master = master_of(sha549, B549, C['GRADES'], FLOORS, C['EVID'], C['EVIDB'], C['LOST'],
                       C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ'])

src2 = src
src2 = re.sub(r'^CUR_SHA256 = \'.*\'$', "CUR_SHA256 = '%s'" % sha549, src2, count=1, flags=re.M)
src2 = re.sub(r'^TOTAL_BYTES = \d+$', 'TOTAL_BYTES = %d' % B549, src2, count=1, flags=re.M)
src2 = re.sub(r'^MASTER_SHA256 = \'.*\'$', "MASTER_SHA256 = '%s'" % new_master, src2, count=1, flags=re.M)
src2 = re.sub(r"R17_R120_FACTINDEX_V548", "R17_R121_FACTINDEX_V549", src2, count=1)
src2 = re.sub(r"'F24': \(\d+, \d+\),", "'F24': (%d, %d)," % new_f24, src2, count=1)
open(FF, 'w', encoding='utf-8', newline='').write(src2)
py_compile.compile(FF, doraise=True)
back = tops(open(FF, encoding='utf-8').read())

gr = open(GR, encoding='utf-8').read()
gr2 = gr.replace('V548', 'V549')
open(GR, 'w', encoding='utf-8', newline='').write(gr2)
py_compile.compile(GR, doraise=True)

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('J0 旧常量复算 MASTER 命中旧值（同法自证）', recomputed_old == old_master, recomputed_old[:16])
_first = (old_master != new_master)
chk('J1 幂等感知：首次应有变化 / 重跑应稳定（两态并存）',
    _first or (old_master == new_master and recomputed_old == new_master), 'first_run_changed=%s' % _first)
chk('J2 常量读回：CUR_SHA256 / TOTAL_BYTES / FLOORS[F24] / MASTER 均为新值',
    back['CUR_SHA256'] == sha549 and back['TOTAL_BYTES'] == B549
    and back['FLOORS']['F24'] == new_f24 and back['MASTER_SHA256'] == new_master,
    {'floors_f24': back['FLOORS']['F24'], 'master': back['MASTER_SHA256'][:16]})
chk('J3 其余 53 条 FLOORS 逐条不变',
    all(back['FLOORS'][k] == C['FLOORS'][k] for k in C['FLOORS'] if k != 'F24'),
    '%d 条' % (len(C['FLOORS']) - 1))
chk('J4 gate_runner 里 V548 归零、V549 恰 5 处',
    gr2.count('V549') == 5 and gr2.count('V548') == 0 and gr.count('V548') in (0, 5),
    'was %d -> now %d' % (gr.count('V548'), gr2.count('V549')))
chk('J5 反控：gate_runner 仍无行首 GATE_VER 赋值', not re.search(r'^GATE_VER\s*=', gr2, re.M), 'ok')
chk('J6 facts_floors 里 V548 归零', 'V548' not in open(FF, encoding='utf-8').read(),
    open(FF, encoding='utf-8').read().count('V548'))

out = {'old_master': old_master, 'recomputed_old': recomputed_old, 'new_master': new_master,
       'old_f24': old_f24, 'new_f24': new_f24, 'sha549': sha549, 'bytes549': B549,
       'ff_sha_before': ff_sha0, 'gr_sha_before': gr_sha0,
       'ff_sha_after': hashlib.sha256(open(FF, 'rb').read()).hexdigest(),
       'gr_sha_after': hashlib.sha256(open(GR, 'rb').read()).hexdigest(),
       'backups': [bk_ff, bk_gr], 'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r169/r169i_repin.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
print('old f24', old_f24, '-> new', new_f24)
print('new master', new_master)
