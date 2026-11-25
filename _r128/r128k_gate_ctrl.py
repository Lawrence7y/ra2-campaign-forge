# -*- coding: utf-8 -*-
"""R128k：C11 真修的四条反控 —— 必须证明新判据真能 FAIL，而不是又一个永远通过分支。

做法（R126 的 S-161 教训：不能把脚本拷到临时目录跑，它读死绝对路径）：
  把正本改名藏起 -> 把改过的副本放到正本路径 -> 跑 -> finally 恢复并断言字节。

四条：
  反控一 清空某 claims-none 行的产物并用一个含自述行的文件顶上 -> 必须 FAIL（命中 C11 新判据）
  反控二 把 GATE_VER 改回 R127 而不改第 20 行 -> 必须 FAIL（命中 C10）
  反控三 只改第 20 行不改 GATE_VER -> 必须 FAIL（命中 C7 id 20）
  正控   不改任何东西 -> exit 0
"""
import io, os, sys, json, hashlib, shutil, subprocess
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
TB = os.path.join(ROOT, '_r128', 'tmp')
os.makedirs(TB, exist_ok=True)

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

def sha(p): return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]

def run_gate():
    r = subprocess.run([sys.executable, GATE], capture_output=True, text=True, timeout=900)
    return r.returncode, (r.stdout or '') + (r.stderr or '')

G0, D0 = sha(GATE), sha(os.path.join(R14, 'DISC_RECHECK.tsv'))
add('K0 开工 sha（收尾必须回落）', True, {'gate': G0})

# ---- 正控 ----
rc, out = run_gate()
add('K1 正控：不改任何东西，exit 0 且 C10 显示 ok(R128)', rc == 0 and 'ok(R128)' in out,
    {'rc': rc, 'c10': 'ok(R128)' in out})

g_src = io.open(GATE, encoding='utf-8').read()

def with_variant(mutate, label):
    """在正本路径上放一个改过的副本，跑完恢复。"""
    mut = mutate(g_src)
    tmp = os.path.join(TB, 'check_disc_variant.py')
    io.open(tmp, 'w', encoding='utf-8', newline='').write(mut)
    hid = GATE + '.hidden_r128'
    shutil.move(GATE, hid)
    try:
        shutil.copyfile(tmp, GATE)
        return run_gate()
    finally:
        if os.path.exists(GATE): os.remove(GATE)
        shutil.move(hid, GATE)
        assert sha(GATE) == G0, '%s 恢复失败' % label

# 反控二：GATE_VER 改回 R127，第 20 行不动
def m2(s):
    return s.replace("GATE_VER = 'R128'", "GATE_VER = 'R127'", 1)
rc2, out2 = with_variant(m2, 'K2')
add('K2 反控二：GATE_VER 改回 R127 而第 20 行仍登记 R128 -> exit 1，命中 C10',
    rc2 == 1 and 'C10 self GATE_VER registered R128 != actual R127' in out2,
    {'rc': rc2, 'hit': [l for l in out2.splitlines() if 'C10' in l and 'FAIL' in l]})

# 反控三：第 20 行改成 R127，GATE_VER 不动 —— 通过临时改 DISC_RECHECK 副本
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
d_src = io.open(DR, encoding='utf-8').read()
d_mut = d_src.replace("grep=(?m)^GATE_VER = 'R128'", "grep=(?m)^GATE_VER = 'R127'", 1)
D1 = sha(DR)
io.open(DR, 'w', encoding='utf-8', newline='').write(d_mut)
try:
    rc3, out3 = run_gate()
finally:
    io.open(DR, 'w', encoding='utf-8', newline='').write(d_src)
    assert sha(DR) == D0, 'DISC_RECHECK 恢复失败'
add('K3 反控三：只改第 20 行不改 GATE_VER -> exit 1，命中 C7 id 20 的 grep 不匹配',
    rc3 == 1 and 'C7 id 20' in out3,
    {'rc': rc3, 'hit': [l for l in out3.splitlines() if 'C7 id 20' in l]})

# 反控一：新判据本身 —— 把一条 claims-none 行的产物换成含自述行的文件
rows = [x.split('\t') for x in d_src.split('\n')[1:] if x]
r11 = [r for r in rows if r[0].strip() == '11'][0]
prod = os.path.join(ROOT, r11[4].strip().replace('\\', '/'))
P0 = sha(prod)
bak = prod + '.r128_bak'
shutil.move(prod, bak)
try:
    io.open(prod, 'w', encoding='utf-8').write(
        'probe\nDISC_RECHECK discipline=11 round=R128 at=2026-11-25T09:00:00+08:00 '
        'anchors=sha256:' + 'a' * 64 + ' conclusion=PASS\n')
    rc4, out4 = run_gate()
finally:
    if os.path.exists(prod): os.remove(prod)
    shutil.move(bak, prod)
    assert sha(prod) == P0, '产物恢复失败'
add('K4 反控一：给 id 11（claims-none）的产物塞一条自己的自述行 -> exit 1，'
    '命中 C11 新判据「claims-none but its product carries 1 self-description line」',
    rc4 == 1 and 'claims-none but its product carries' in out4,
    {'rc': rc4, 'hit': [l.strip() for l in out4.splitlines() if 'claims-none but' in l]})

# 收尾：三份正本字节回到开工时
add('K5 收尾：check_disc.py 与 DISC_RECHECK.tsv 的 sha 与开工时一致',
    sha(GATE) == G0 and sha(DR) == D0, {'gate': sha(GATE), 'dr': sha(DR)})

json.dump({'checks': ck}, open(os.path.join(ROOT, '_r128', 'r128k_gate_ctrl.json'), 'w'),
          ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128k: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:400])
sys.exit(0 if n == len(ck) else 1)
