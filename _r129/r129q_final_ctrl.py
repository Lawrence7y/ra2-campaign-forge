# -*- coding: utf-8 -*-
"""R129q：收尾反控 —— C16 重钉与本轮全部门禁改动都必须能 FAIL。

六条：
  Q1 正控：exit 0；C10 ok(R129)；C16 pinned 127 / unpinned 0；C16d d7d41af1
  Q2 把 133 的下界改回 1000 而不改摘要 ⇒ exit 1 命中 C16d TAMPERED
  Q3 清空 2.133 正文只剩标题 ⇒ exit 1 命中 C16 hollowed
  Q4 GATE_VER 改回 R128 ⇒ exit 1 命中 C10
  Q5 只改 DISC_RECHECK 第 20 行登记式 ⇒ exit 1 命中 C7 id 20
  Q6 收尾断言三份正本字节回到基线
"""
import io, os, sys, hashlib, subprocess, json, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
RC = os.path.join(R14, 'R14_COMMON.md')
FILES = (GATE, DR, RC)
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

base = {p: io.open(p, 'rb').read() for p in FILES}
def run():
    r = subprocess.run([sys.executable, 'check_disc.py'], cwd=R14, capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr

code, out = run()
add('Q1 正控：exit 0；C10 ok(R129)；C16 pinned 127 / unpinned 0；C16d d7d41af1',
    code == 0 and 'C10 self-check: ok(R129)' in out
    and '(pinned 127)' in out and 'unpinned 0' in out
    and 'C16d floor-table pin: d7d41af1' in out,
    {'code': code, 'grep': [l for l in out.splitlines() if 'C16' in l or 'C10' in l]})

def with_file(path, pairs):
    try:
        raw = base[path].decode('utf-8')
        for o, nw in pairs:
            assert raw.count(o) == 1, '目标串不是恰好一处：%r (%d)' % (o[:40], raw.count(o))
            raw = raw.replace(o, nw)
        with io.open(path, 'wb') as f: f.write(raw.encode('utf-8'))
        return run()
    finally:
        with io.open(path, 'wb') as f: f.write(base[path])

# Q2
code, out = with_file(GATE, [('133: 4747', '133: 1000')])
add('Q2 把 133 下界改成 1000 而不改摘要 ⇒ exit 1 命中 C16d TAMPERED',
    code == 1 and 'C16d floor table TAMPERED' in out, {'code': code})

# Q3：清空 2.133 正文
raw = base[RC].decode('utf-8')
m = re.search(r'(?m)^## 2\.133\b.*$(?=\n)', raw)
start = m.end()
nxt = re.search(r'(?m)^## 2\.\d+\b', raw[start:])
seg = raw[start:start + nxt.start()] if nxt else raw[start:]
code, out = with_file(RC, [(seg, '\n\n')])
add('Q3 把 2.133 正文清成只剩标题行 ⇒ exit 1 命中 C16 hollowed',
    code == 1 and 'hollowed' in out, {'code': code, 'hit': [l for l in out.splitlines() if 'C16' in l][:3]})

# Q4
code, out = with_file(GATE, [("GATE_VER = 'R129'", "GATE_VER = 'R128'")])
add('Q4 GATE_VER 改回 R128（登记行仍 R129）⇒ exit 1 命中 C10',
    code == 1 and 'C10' in out, {'code': code})

# Q5 只改登记行
code, out = with_file(DR, [("grep=(?m)^GATE_VER = 'R129'", "grep=(?m)^GATE_VER = 'R128'")])
add('Q5 只改 DISC_RECHECK 第 20 行登记式 ⇒ exit 1 命中 C7 id 20 与 C10',
    code == 1 and 'C7 id 20' in out, {'code': code, 'hit': [l for l in out.splitlines() if 'id 20' in l][:2]})

# Q6
for p in FILES:
    add('Q6 收尾断言 %s 字节回到基线（%s）' % (os.path.basename(p), hashlib.sha256(base[p]).hexdigest()[:16]),
        io.open(p, 'rb').read() == base[p])

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck)},
          open(os.path.join(ROOT, '_r129', 'r129q_final_ctrl.json'), 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
sys.exit(0 if ok == len(ck) else 1)
