# -*- coding: utf-8 -*-
"""R126i: 门禁回归反控 —— 本轮改了 check_disc.py（C16 重钉 + GATE_VER 升版），
必须证明这些改动不是「把门禁改松」。

关键约束（第一版踩到）：check_disc.py 读文档用的是写死的绝对路径
（R14 = .../lead/next_re_20261117_r14），所以在临时目录里拷一份门禁脚本
再跑，它会去读原目录的文档 —— 反控根本没生效（S-161）。
故本脚本的做法是：先把正本改名藏起来（只保留 .r126i_hold 后缀，不回退内容），
再把「改过的副本」放到正本路径上跑，跑完无论成败都在 finally 里恢复。

三条可失败的检验：

  R1  把 2.130 节正文清空到只剩标题，必须 FAIL（C16 hollow）。
  R2  只把 check_disc.py 里的 GATE_VER 改成一个别的值、不动第 20 行，必须 FAIL（C10）。
  R3  把 C16_FLOORS 里一个数改小、不改摘要常量，必须 FAIL（C16d）。
  R4  正控：不做任何修改时必须 PASS（否则前面三条 FAIL 是假的）。
"""
import io, os, re, shutil, subprocess, sys, hashlib

R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
HOLD = '.r126i_hold'
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

def sha16(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]

TARGETS = {'check_disc.py': None, 'DISC_RECHECK.tsv': None, 'R14_COMMON.md': None}
for t in TARGETS:
    TARGETS[t] = sha16(os.path.join(R14, t))

def run_gate():
    p = subprocess.run([sys.executable, 'check_disc.py'], cwd=R14,
                       capture_output=True, text=True, timeout=300)
    return p.returncode, (p.stdout or '') + (p.stderr or '')

def with_patched(fname, transform):
    """把 fname 改过的副本放到正本路径上跑一次门禁，然后恢复。"""
    live = os.path.join(R14, fname)
    hold = live + HOLD
    if os.path.exists(hold):
        os.remove(hold)
    os.rename(live, hold)
    try:
        data = io.open(hold, encoding='utf-8', newline='').read()
        new = transform(data)
        assert new != data, 'transform 未改动 %s' % fname
        io.open(live, 'w', encoding='utf-8', newline='').write(new)
        return run_gate()
    finally:
        if os.path.exists(live):
            os.remove(live)
        os.rename(hold, live)
        assert sha16(live) == TARGETS[fname], '%s 恢复后 sha 不符' % fname

# ---- R4 正控 ----
rc0, out0 = run_gate()
add('R4 正控：不做任何修改时必须 PASS（否则后面三条 FAIL 无意义）',
    rc0 == 0 and 'PASS  structure/paths/sections/self all ok' in out0,
    'exit=%d' % rc0)

# ---- R1 清空 2.130 正文 ----
def wipe_130(txt):
    lines = txt.split('\n')
    start = None
    for i, l in enumerate(lines):
        if re.match(r'^##\s+2\.130\b', l):
            start = i
            break
    assert start is not None, 'R14_COMMON 里没有 2.130'
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r'^##\s+2\.\d+\b', lines[j]):
            end = j
            break
    assert end - start > 5, '2.130 段太短，无法做清空实验'
    return '\n'.join(lines[:start + 1] + lines[end:])

rc1, out1 = with_patched('R14_COMMON.md', wipe_130)
add('R1 把 2.130 正文清空后门禁必须 FAIL（C16 逐节下界在起约束）',
    rc1 != 0 and 'C16' in out1, 'exit=%d ; 命中 C16=%s' % (rc1, 'C16' in out1))

# ---- R2 只改 GATE_VER ----
rc2, out2 = with_patched(
    'check_disc.py', lambda s: s.replace("GATE_VER = 'R126'", "GATE_VER = 'R999'"))
add('R2 只改 GATE_VER 而不同步第 20 行时必须 FAIL（C10 门自检）',
    rc2 != 0 and 'C10' in out2, 'exit=%d ; 命中 C10=%s' % (rc2, 'C10' in out2))

# ---- R3 改表不改摘要 ----
rc3, out3 = with_patched(
    'check_disc.py', lambda s: s.replace('130: 3722', '130: 3700'))
add('R3 改 C16_FLOORS 一个数而不改摘要常量时必须 FAIL（C16d sha 钉）',
    rc3 != 0 and 'C16d' in out3, 'exit=%d ; 命中 C16d=%s' % (rc3, 'C16d' in out3))

# ---- 收尾：确认三个正本字节未变 ----
for t in TARGETS:
    add('R5 收尾：%s 字节与开工时一致（%s）' % (t, TARGETS[t]),
        sha16(os.path.join(R14, t)) == TARGETS[t])

bad = [c for c in ck if not c['ok']]
print('R126i %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
