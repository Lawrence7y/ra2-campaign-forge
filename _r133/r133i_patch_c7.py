#!/usr/bin/env python3
# R133 r133i: apply the C7 fix under the write discipline.
#   exclusive-create backup (wx) -> assert old sha256 -> single write -> readback verify
# Two independent changes, both verification-free of each other, so they are done in ONE
# pass and verified AFTER both (lesson S-217: verifying between two interdependent edits
# is how the R132 GATE_VER incident happened).
import hashlib, io, os, time

GATE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py'
BAK  = '/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE/check_disc.py.before_R133_%s.bak' % time.strftime('%H%M%S')

old = io.open(GATE, encoding='utf-8').read()
h_old = hashlib.sha256(old.encode('utf-8')).hexdigest()
print('old sha256:', h_old, 'bytes', len(old.encode('utf-8')))

# ---------- edit 1: pin the C7 shape census ----------
anchor1 = """# ---- C8 节号存在性 ----"""
new1 = """# ---- C7b 【R133 新增】形态覆盖普查：31/31 passed 不等于「所有分支形态都被走过了」----
# R132 测得 C7 的 exists / bytes= / none 三个分支在 31 行里各覆盖 0 行；R133 r133g 复测
# 仍是 0/0/0（8/8 PASS），r133h 证明注入一行对应形态会把计数从 0 推到 1（钉有分辨力）。
# 修法不用「为不可达形态硬造产物」——那会制造一条只为过门禁而存在的行。改为把普查本身
# 显式钉住：形态计数一旦漂移就 FAIL，逼下一个人先做裁定再改数据。
C7_SHAPE_PIN = {'grep=': 24, 'grepcount=': 3, 'rows=': 4,
                'exists': 0, 'bytes=': 0, 'none': 0}
c7_shape = {}
for _r in rows:
    if len(_r) != 7:
        continue
    _h = _r[5].strip().split(' ')[0]
    _k = ('none' if _h in ('none', '') else
          'bytes=' if _h.startswith('bytes=') else
          'rows=' if _h.startswith('rows=') else
          'grepcount=' if _h.startswith('grepcount=') else
          'grep=' if _h.startswith('grep=') else
          'exists' if _h == 'exists' else 'BAD:' + _h)
    c7_shape[_k] = c7_shape.get(_k, 0) + 1
c7_shape_pin_ok = True
for _k, _v in sorted(c7_shape.items()):
    if C7_SHAPE_PIN.get(_k) != _v:
        c7_shape_pin_ok = False
        fails.append('C7b shape census drifted: %s=%d but pinned %s '
                     '(a new shape needs a deliberate decision, not a silent addition)'
                     % (_k, _v, C7_SHAPE_PIN.get(_k)))
for _k, _v in sorted(C7_SHAPE_PIN.items()):
    if _k not in c7_shape:
        c7_shape_pin_ok = False
        fails.append('C7b pinned shape %s=%d vanished from the table entirely' % (_k, _v))
notes.append('C7b shape census: %s ; three of six shapes have ZERO rows '
             '(exists/bytes=/none are live code with no data behind them -- 31/31 passed '
             'MUST NOT be read as all shapes exercised)%s'
             % (', '.join('%s=%d' % (k, v) for k, v in sorted(c7_shape.items())),
                '' if c7_shape_pin_ok else ' [DRIFTED]'))

# ---- C8 节号存在性 ----"""
assert old.count(anchor1) == 1, old.count(anchor1)
s = old.replace(anchor1, new1)

# ---------- edit 2: report the census on the C7 result line ----------
anchor2 = """print('C7 live-checks passed %d ; none-skipped %d' % (c7_ok, c7_none))"""
new2 = """print('C7 live-checks passed %d ; none-skipped %d ; shape census %s'
      % (c7_ok, c7_none, ', '.join('%s=%d' % (k, v) for k, v in sorted(c7_shape.items()))))"""
assert s.count(anchor2) == 1, s.count(anchor2)
s = s.replace(anchor2, new2)

# ---------- backup with exclusive create, then single write ----------
fd = os.open(BAK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(old)
print('backup written:', BAK, os.path.getsize(BAK), 'bytes')

assert hashlib.sha256(io.open(BAK, encoding='utf-8').read().encode('utf-8')).hexdigest() == h_old, 'backup content mismatch'

io.open(GATE, 'w', encoding='utf-8', newline='\n').write(s)
h_new = hashlib.sha256(io.open(GATE, encoding='utf-8').read().encode('utf-8')).hexdigest()
print('new sha256:', h_new, 'bytes', os.path.getsize(GATE))
print('C7b present:', 'C7b shape census' in io.open(GATE, encoding='utf-8').read())
