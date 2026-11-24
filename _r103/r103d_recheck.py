#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r103d_recheck.py —— §2.12 规则 D：主会话亲自复算执行员 hy4 #160 的结论

复算对象是执行员写在 VERDICT103.md 里的可判定的数字断言，不是它的推理。
**不读、不 import、不复制它的任何脚本**（r103_probe.py 一眼未看）。

复算项（逐项独立实现，用 r103a/r103c 的沙箱库，不共用它的实现）：
  D1 第 3 列全改 x ⇒ exit 0（它报 0）
  D2 第 3 列改 TBD ⇒ exit 1 且 31 条 C9（它报 1 / 31）
  D3 第 4 列全改 ANCHOR-X ⇒ FAIL 集合恰为 {3,4,22,27,28}（它报 5 条，id 与它逐项一致）
  D4 第 2 列全改 §2.14 ⇒ exit 0；全改 §2.999 ⇒ exit 1 且 31 条 C8（它报同）
  D5 (a) 17 个「有」行逐行改「无」⇒ 每行都 exit 1（它报 17/17）
  D6 (b) 14 个「无」行逐行改「有」⇒ 每行都 exit 1（它报 14/14）
  D7 (c) 14 个「无」行逐行改成另一个同以「无」开头的串 ⇒ 每行 exit 0（它报 14/14 不可见）
  D8 读第 7 列的代码点全部是 startswith 前缀判断、无整串相等（它报 Q5 结论）
  D9 它报的基线 md5 与现状是否一致（它写 check_disc.py md5 9f64f5b3.. / DR md5 114ee019..）
"""
import hashlib, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbxlib as S

# 量测对象声明（R103 落盘后补记）：本脚本复算的是执行员 #160 在**R103 落盘前**（GATE_VER=R102）
# 量到的那些数，故用 prepare(gate='unpatched')。落盘 C13/C14 之后同一批变异已会被抓住，
# 那份复核放在 r103a 的 PAT 组里，不在这里。

OUT = os.path.join(S.REAL, '_r103')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

S.prepare(gate='unpatched')
G = S.p(S.SBX, 'check_disc.py')
D = S.p(S.SBX, 'DISC_RECHECK.tsv')
G0 = io.open(G, encoding='utf-8', newline='').read()
D0 = io.open(D, encoding='utf-8', newline='').read()
R, _t = S.rows(S.SBX)
RES = {}

def setcol(col, fn):
    out = []
    for r in R:
        c = list(r)
        c[col] = fn(c)
        out.append(c)
    return out

def trial(rows):
    S.write_rows(rows, D0, S.SBX)
    rc, f, _ = S.run()
    S.write_rows(R, D0, S.SBX)
    return rc, f

# D9 基线指纹
md5 = lambda b: hashlib.md5(b).hexdigest()
RES['D9'] = {'gate_md5': md5(G0.encode('utf-8')), 'dr_md5': md5(D0.encode('utf-8'))}
ck('D9 被测对象确为执行员报的那一份（check_disc.py 9f64f5b3.. / DISC_RECHECK 114ee019..）',
   RES['D9']['gate_md5'].startswith('9f64f5b3') and RES['D9']['dr_md5'].startswith('114ee019'),
   RES['D9'])
_now = io.open(os.path.join(S.REAL, S.R14REL, 'check_disc.py'), 'rb').read()
RES['D9b'] = {'gate_md5_now': md5(_now)}
ck('D9b 盘上门禁已与执行员当时量的那一份不同（GATE_VER 已抬到 R103）—— 这不是矛盾，是量测对象变了；'
   '本脚本所有期望值因此都钉在备份门禁上',
   RES['D9b']['gate_md5_now'] != RES['D9']['gate_md5'], RES['D9b'])

# D1 / D2 第 3 列
rc, f = trial(setcol(2, lambda c: 'x'))
RES['D1'] = {'exit': rc, 'fails': f}
ck('D1 第 3 列全改 x ⇒ exit 0', rc == 0 and f == [], 'exit=%d' % rc)
rc, f = trial(setcol(2, lambda c: 'TBD'))
RES['D2'] = {'exit': rc, 'n_c9': sum(1 for x in f if x.startswith('C9')), 'fails': f}
ck('D2 第 3 列全改 TBD ⇒ exit 1 且 31 条 C9', rc == 1 and RES['D2']['n_c9'] == 31,
   'exit=%d C9=%d' % (rc, RES['D2']['n_c9']))

# D3 第 4 列
rc, f = trial(setcol(3, lambda c: 'ANCHOR-X'))
ids = sorted(int(x.split()[2]) for x in f if x.startswith('C11'))
RES['D3'] = {'exit': rc, 'ids': ids, 'fails': f}
ck('D3 第 4 列全改 ANCHOR-X ⇒ FAIL 集合恰为 {3,4,22,27,28}（与执行员逐项一致）',
   rc == 1 and ids == [3, 4, 22, 27, 28], 'ids=%s' % ids)

# D4 第 2 列
rc, f = trial(setcol(1, lambda c: '§2.14'))
RES['D4a'] = {'exit': rc, 'fails': f}
ck('D4a 第 2 列全改 §2.14 ⇒ exit 0', rc == 0, 'exit=%d' % rc)
rc, f = trial(setcol(1, lambda c: '§2.999'))
n8 = sum(1 for x in f if x.startswith('C8'))
RES['D4b'] = {'exit': rc, 'n_c8': n8, 'fails': f}
ck('D4b 第 2 列全改 §2.999 ⇒ exit 1 且 31 条 C8', rc == 1 and n8 == 31, 'exit=%d C8=%d' % (rc, n8))

# D5 / D6 / D7 逐行翻转
def flip(idx, val):
    out = [list(r) for r in R]
    out[idx][6] = val
    return out
res5, res6, res7 = [], [], []
for i, r in enumerate(R):
    if r[6].strip().startswith('有'):
        rc, f = trial(flip(i, '无（复算探针）'))
        res5.append((int(r[0]), rc))
    else:
        rc, f = trial(flip(i, '有（复算探针）'))
        res6.append((int(r[0]), rc))
        rc, f = trial(flip(i, '无（复算探针：措辞不同）'))
        res7.append((int(r[0]), rc))
RES['D5'] = res5; RES['D6'] = res6; RES['D7'] = res7
ck('D5 (a) 17 个「有」行逐行改「无」⇒ 17/17 exit 1', len(res5) == 17 and all(x[1] == 1 for x in res5),
   'n=%d nonzero=%d' % (len(res5), sum(1 for x in res5 if x[1] == 1)))
ck('D6 (b) 14 个「无」行逐行改「有」⇒ 14/14 exit 1', len(res6) == 14 and all(x[1] == 1 for x in res6),
   'n=%d nonzero=%d' % (len(res6), sum(1 for x in res6 if x[1] == 1)))
ck('D7 (c) 14 个「无」行改成措辞不同的「无」⇒ 14/14 exit 0（第 7 列措辞对门禁完全不可见）',
   len(res7) == 14 and all(x[1] == 0 for x in res7),
   'n=%d zero=%d' % (len(res7), sum(1 for x in res7 if x[1] == 0)))

# D8 读第 7 列的全部代码点
lines = G0.replace('\r\n', '\n').split('\n')
reads = [(i + 1, l.strip()) for i, l in enumerate(lines) if 'r[6]' in l or "_r[6]" in l]
exact = [x for x in reads if re.search(r"r\[6\]\.strip\(\)\s*==", x[1])]
RES['D8'] = {'reads': reads, 'exact_equality': exact}
ck('D8 读第 7 列共 %d 处，全部为 startswith/前缀式，无一处整串相等' % len(reads),
   len(reads) >= 4 and exact == [], 'reads=%d exact=%d' % (len(reads), len(exact)))
for i, l in reads:
    print('    :%d  %s' % (i, l[:110]))

json.dump({'checks': checks, 'results': RES},
          io.open(os.path.join(OUT, 'r103d_recheck.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n%d checks, %d FAIL' % (len(checks), nf))
sys.exit(1 if nf else 0)
