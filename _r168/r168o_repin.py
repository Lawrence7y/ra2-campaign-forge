#!/usr/bin/env python3
"""R168 O：门禁重钉（facts_floors.py 五点 + gate_runner.py 五处 V547→V548）。

纪律（R160 S-531 / R167 S-541 同族错的防范）：
  ① 常量一律 ast.literal_eval 从源码取真值，不用正则抓 dict；
  ② MASTER_SHA256 由门禁自己的 canon 五函数 + 源码里的 11 项拼接顺序重算，
     并**先用旧常量复算一次命中旧值**自证同法；
  ③ 改写后必须 compile + 常量读回；
  ④ 幂等：已是新值则跳过、并断言新值一致。
"""
import ast, hashlib, json, re, os, py_compile
ROOT = '/home/t628/projects/ra2-campaign-forge'
FF = ROOT + '/_r160/facts_floors.py'
GR = ROOT + '/_r161/gate_runner.py'
V548 = ROOT + '/lead/next_re_20261117_r14/R17_R120_FACTINDEX_V548/FACT_INDEX.tsv'
V547 = ROOT + '/lead/next_re_20261117_r14/R17_R119_FACTINDEX_V547/FACT_INDEX.tsv'

raw548 = open(V548, 'rb').read()
sha548 = hashlib.sha256(raw548).hexdigest()
B548 = len(raw548)
assert sha548.startswith('ef1716cf') and B548 == 113574, (sha548, B548)

src = open(FF, encoding='utf-8').read()

_tree = ast.parse(open(FF, encoding='utf-8').read())
_TOPS = {}
for _n in _tree.body:
    if isinstance(_n, ast.Assign) and len(_n.targets) == 1 and isinstance(_n.targets[0], ast.Name):
        try:
            _TOPS[_n.targets[0].id] = ast.literal_eval(_n.value)
        except Exception:
            pass

def const(name, text=None):
    assert name in _TOPS, name
    return _TOPS[name]

NAMES = ['CUR_SHA256', 'TOTAL_BYTES', 'GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST',
         'MASTER_SHA256', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ']
C = {n: const(n, src) for n in NAMES}
# canon 五函数：直接取源码定义，保证同法
ns = {}
for fn in ('canon_g', 'canon_f', 'canon_e', 'canon_eb', 'canon_l'):
    m = re.search(r'^def %s\(.*?$' % fn, src, re.M)
    exec(m.group(0), ns)

def master_of(cur_sha, total, grades, floors, evid, evidb, lost, items, uniq, li, lu):
    blob = '\n'.join([cur_sha, str(total), ns['canon_g'](grades), ns['canon_f'](floors),
                      ns['canon_e'](evid), ns['canon_eb'](evidb), ns['canon_l'](lost),
                      str(items), str(uniq), str(li), str(lu)])
    return hashlib.sha256(blob.encode()).hexdigest()

# ② 先用**旧常量**复算，必须命中旧 MASTER（同法自证）
old_master = C['MASTER_SHA256']
recomputed_old = master_of(C['CUR_SHA256'], C['TOTAL_BYTES'], C['GRADES'], C['FLOORS'],
                           C['EVID'], C['EVIDB'], C['LOST'], C['ITEMS'], C['UNIQ'],
                           C['LOST_ITEMS'], C['LOST_UNIQ'])
print('old master from source :', old_master[:16])
print('old master recomputed  :', recomputed_old[:16])

# 新 FLOORS：只改 F24 的两界
FLOORS = dict(C['FLOORS'])
old_f24 = FLOORS['F24']
import csv, io
rows = list(csv.reader(io.StringIO(raw548.decode('utf-8')), delimiter='\t'))
data = rows[1:]
f24 = [r for r in data if r[0] == 'F24'][0]
new_f24 = (len(f24[1].encode('utf-8')), len(f24[4].encode('utf-8')))
FLOORS['F24'] = new_f24
new_master = master_of(sha548, B548, C['GRADES'], FLOORS, C['EVID'], C['EVIDB'], C['LOST'],
                       C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ'])
print('old F24 floor', old_f24, '-> new', new_f24)
print('new master    :', new_master[:16])

# 改写 facts_floors.py
src2 = src
src2 = re.sub(r'^CUR_SHA256 = \'.*\'$', "CUR_SHA256 = '%s'" % sha548, src2, count=1, flags=re.M)
src2 = re.sub(r'^TOTAL_BYTES = \d+$', 'TOTAL_BYTES = %d' % B548, src2, count=1, flags=re.M)
src2 = re.sub(r'^MASTER_SHA256 = \'.*\'$', "MASTER_SHA256 = '%s'" % new_master, src2, count=1, flags=re.M)
src2 = re.sub(r"R17_R119_FACTINDEX_V547", "R17_R120_FACTINDEX_V548", src2, count=1)
src2 = re.sub(r"'F24': \(\d+, \d+\),", "'F24': (%d, %d)," % new_f24, src2, count=1)
open(FF, 'w', encoding='utf-8', newline='').write(src2)
py_compile.compile(FF, doraise=True)
src3 = open(FF, encoding='utf-8').read()
def _tops_of(text):
    out = {}
    for _n in ast.parse(text).body:
        if isinstance(_n, ast.Assign) and len(_n.targets) == 1 and isinstance(_n.targets[0], ast.Name):
            try: out[_n.targets[0].id] = ast.literal_eval(_n.value)
            except Exception: pass
    return out
_T3 = _tops_of(src3)
back = {n: _T3[n] for n in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'FLOORS')}

# gate_runner.py：LEDGER + 4 处 V547 -> 共 5 处 V548
gr = open(GR, encoding='utf-8').read()
gr2 = gr.replace('V547', 'V548')
open(GR, 'w', encoding='utf-8', newline='').write(gr2)
py_compile.compile(GR, doraise=True)

A = []
A.append({'id': 'O0 旧常量复算 MASTER 命中旧值（同法自证）', 'ok': recomputed_old == old_master,
          'detail': recomputed_old[:16]})
# S-553 登记：首版把「新 != 旧」写成硬断言 ⇒ 二次运行必假 FAIL（与 S-543/S-525 同族）。
# 正确判据：两态并存 —— 首次运行要求不等；已是新值的重跑要求等值且 O0 仍命中。
_first = (old_master != new_master)
A.append({'id': 'O1 幂等感知：首次应有变化，重跑应已稳定（两态并存）',
          'ok': _first or (old_master == new_master and recomputed_old == new_master),
          'detail': 'first_run_changed=%s' % _first})
A.append({'id': 'O2 常量读回：CUR_SHA256 / TOTAL_BYTES / FLOORS[F24] / MASTER 均为新值',
          'ok': back['CUR_SHA256'] == sha548 and back['TOTAL_BYTES'] == B548
          and back['FLOORS']['F24'] == new_f24 and back['MASTER_SHA256'] == new_master})
A.append({'id': 'O3 其余 53 条 FLOORS 逐条不变',
          'ok': all(back['FLOORS'][k] == C['FLOORS'][k] for k in C['FLOORS'] if k != 'F24'),
          'detail': '%d 条' % (len(C['FLOORS']) - 1)})
A.append({'id': 'O4 新 F24 界等于 V548 实测字节（等值 pin）',
          'ok': new_f24 == (len(f24[1].encode('utf-8')), len(f24[4].encode('utf-8'))),
          'detail': repr(new_f24)})
A.append({'id': 'O5 gate_runner 里 V547 归零、V548 恰 5 处（幂等：重跑 was 可为 0）',
          'ok': gr2.count('V548') == 5 and gr2.count('V547') == 0 and gr.count('V547') in (0, 5),
          'detail': 'was %d -> now %d' % (gr.count('V547'), gr2.count('V548'))})
A.append({'id': 'O6 反控：gate_runner 仍无行首 GATE_VER 赋值',
          'ok': not re.search(r'^GATE_VER\s*=', gr2, re.M)})
A.append({'id': 'O7 facts_floors 里 V547 归零',
          'ok': 'V547' not in src3, 'detail': str(src3.count('V547'))})
out = {'old_master': old_master, 'recomputed_old': recomputed_old, 'new_master': new_master,
       'old_f24': old_f24, 'new_f24': new_f24, 'sha548': sha548, 'bytes548': B548,
       'ff_sha': hashlib.sha256(open(FF, 'rb').read()).hexdigest(),
       'gr_sha': hashlib.sha256(open(GR, 'rb').read()).hexdigest(),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r168/r168o_repin.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'assertions'}, ensure_ascii=False, indent=1))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
