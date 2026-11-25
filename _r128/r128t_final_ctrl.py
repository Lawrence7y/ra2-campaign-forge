# -*- coding: utf-8 -*-
"""R128t：本轮三处门禁改动（C11 claims-none 真修、GATE_VER 升级、C16 重钉）的收尾反控。

沿用 r128k 的做法：正本改名藏起 -> 改过的副本放到正本路径 -> finally 恢复并断言 sha。
四条：
  正控   现状 exit 0、C10 ok(R128)、C16 unpinned=0
  反控一 清空 2.132 正文 -> 必须 exit 1 命中 C16（报 132 的 floor）
  反控二 只改 GATE_VER 不改第 20 行 -> 必须 exit 1 命中 C10
  反控三 改 132 的 floor 下界不改摘要 -> 必须 exit 1 命中 C16d
"""
import io, os, sys, json, hashlib, shutil, subprocess
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
RC = os.path.join(R14, 'R14_COMMON.md')
TB = os.path.join(ROOT, '_r128', 'tmp')
os.makedirs(TB, exist_ok=True)
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})
def sha(p): return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]
def run():
    r = subprocess.run([sys.executable, GATE], capture_output=True, text=True, timeout=900)
    return r.returncode, (r.stdout or '') + (r.stderr or '')

G0 = sha(GATE)
add('T0 开工 sha', True, {'gate': G0})

rc, out = run()
add('T1 正控：exit 0、C10 ok(R128)、C16 unpinned 0 且 pinned 126',
    rc == 0 and 'ok(R128)' in out and 'unpinned 0' in out and 'pinned 126' in out,
    {'rc': rc})

def variant(gate_mutate):
    mut = gate_mutate()
    tmp = os.path.join(TB, 'gate_variant.py')
    io.open(tmp, 'w', encoding='utf-8', newline='').write(mut)
    hid = GATE + '.hidden_r128t'
    shutil.move(GATE, hid)
    try:
        shutil.copyfile(tmp, GATE)
        return run()
    finally:
        if os.path.exists(GATE): os.remove(GATE)
        shutil.move(hid, GATE)
        assert sha(GATE) == G0, 'restore failed'

# 反控二：GATE_VER 改回 R127
src = io.open(GATE, encoding='utf-8').read()
rc2, out2 = variant(lambda: src.replace("GATE_VER = 'R128'", "GATE_VER = 'R127'", 1))
add('T2 反控一：GATE_VER 改回 R127 而第 20 行仍登记 R128 -> exit 1 命中 C10',
    rc2 == 1 and 'C10 self GATE_VER registered R128 != actual R127' in out2,
    {'rc': rc2, 'hit': [l.strip() for l in out2.splitlines() if 'C10' in l and 'FAIL' in l]})

# 反控三：改 132 的 floor 不改摘要
def mut_floor():
    return src.replace('    132: 5998', '    132: 1000', 1)
rc3, out3 = variant(mut_floor)
add('T3 反控二：把 132 的下界改成 1000 而不改摘要 -> exit 1 命中 C16d（表被篡改）',
    rc3 == 1 and 'C16d' in out3 and 'TAMPERED' in out3,
    {'rc': rc3, 'hit': [l.strip() for l in out3.splitlines() if 'C16d' in l]})

# 反控四：清空 2.132 正文（保留标题）
rc_old = io.open(RC, 'rb').read()
RC_H = sha(RC)
txt = rc_old.decode('utf-8')
i = txt.index('## 2.132')
j = txt.find('\n## 2.', i + 5)
stub = txt[:i] + txt[i:txt.index('\n', i)] + '\n' + txt[j:]
hid = RC + '.hidden_r128t'
shutil.move(RC, hid)
try:
    io.open(RC, 'w', encoding='utf-8', newline='').write(stub)
    rc4, out4 = run()
finally:
    if os.path.exists(RC): os.remove(RC)
    shutil.move(hid, RC)
    assert sha(RC) == RC_H, 'R14_COMMON restore failed'
add('T4 反控三：把 2.132 正文清成只剩标题行 -> exit 1 命中 C16 并报 132 的下界',
    rc4 == 1 and '(132,' in out4,
    {'rc': rc4, 'hit': [l.strip()[:150] for l in out4.splitlines() if 'hollowed' in l]})

add('T5 收尾：check_disc.py 与 R14_COMMON.md 的 sha 都回到本轮写入完成时的值',
    sha(GATE) == G0 and sha(RC) == RC_H, {'gate': sha(GATE), 'rc': sha(RC)})

json.dump({'checks': ck}, open(os.path.join(ROOT, '_r128', 'r128t_final_ctrl.json'), 'w'),
          ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128t: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:400])
sys.exit(0 if n == len(ck) else 1)
