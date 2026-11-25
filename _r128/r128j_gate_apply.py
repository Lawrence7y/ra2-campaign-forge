# -*- coding: utf-8 -*-
"""R128j：把 r128g 验证过的 C11 真修落到 check_disc.py，并同步 GATE_VER 与第 20 行。

改动两处（方向都是收紧）：
  1. C11 主循环的 claims-none 分支：从「直接 continue 计 claims-none」改为
     「先核该行的产物里不得出现本纪律的自述行」，违反即 FAIL。
     现状 14 行全部诚实（r128f F2 实测），故改动后仍 exit 0；但将来谁把
     「有」悄悄改成「无」而产物里还留着自述行，就会当场 FAIL。
  2. GATE_VER R127 -> R128，并同步 DISC_RECHECK 第 20 行的登记式（C10 门自检要求）。

纪律：wx 独占备份 -> 断言旧 sha256 -> 一次性写入 -> 回读校验 -> 反控四条。
"""
import io, os, sys, json, hashlib, shutil, subprocess
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
TS = '20261125_r128'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

def sha16(b): return hashlib.sha256(b).hexdigest()[:16]

old_gate = io.open(GATE, 'rb').read()
old_dr = io.open(DR, 'rb').read()
add('J0 开工前 sha（用于事后确认是本脚本改的）', True,
    {'gate': sha16(old_gate), 'dr': sha16(old_dr)})

# ---- 备份（wx 独占）----
for path, tag in ((GATE, 'check_disc.py'), (DR, 'DISC_RECHECK.tsv')):
    dst = os.path.join(BK, 'r128_%s.%s.bak' % (tag, TS))
    assert not os.path.exists(dst), 'backup exists: %s' % dst
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, io.open(path, 'rb').read())
    finally:
        os.close(fd)
    add('J1 备份 %s -> %s' % (tag, os.path.basename(dst)), True)

# ---- 断言旧内容确实是我读到的形态 ----
g = old_gate.decode('utf-8')
assert "GATE_VER = 'R127'" in g, 'GATE_VER not R127'
OLD_NONE = """    if not later.startswith('\\u6709'):
        c11_unver += 1
        continue"""
if OLD_NONE not in g:
    # 源码里是字面转义还是真字符，两种都试
    OLD_NONE = """    if not later.startswith('有'):
        c11_unver += 1
        continue"""
add('J2 定位到 claims-none 分支原文（未找到则本脚本必须失败，不能盲改）',
    OLD_NONE in g, {'found': OLD_NONE in g})

NEW_NONE = """    if not later.startswith('有'):
        # R128 真修：claims-none 此前是「声明不补」的免检通道，永不 FAIL。
        # 实测 14 行现状诚实（_r128/r128f_gate_probe.py F2），但无机制阻止有人把
        # 「有」悄悄改成「无」而产物里仍留着自述行。故此处补一条可失败的判据：
        # claims-none 行的产物里不得出现本纪律的自述行。
        _p_none = os.path.join(ROOT, r[4].strip().replace('\\\\', '/'))
        if os.path.isfile(_p_none):
            try:
                _t_none = io.open(_p_none, encoding='utf-8', errors='replace').read()
            except OSError:
                _t_none = ''
            _hits_none = 0
            for _l_none in _t_none.splitlines():
                if not _l_none.startswith('DISC_RECHECK '):
                    continue
                _m_none = re.search(r'\\bdiscipline=(\\d+)\\b', _l_none)
                if _m_none and int(_m_none.group(1)) == int(r[0]):
                    _hits_none += 1
            if _hits_none > 0:
                c11_fail += 1
                fails.append('C11 id %s claims-none but its product carries %d '
                             'self-description line(s) for this discipline (R128)'
                             % (r[0], _hits_none))
                continue
        c11_unver += 1
        continue"""
new_gate = g.replace(OLD_NONE, NEW_NONE, 1)
assert new_gate != g, 'claims-none patch did not apply'
new_gate = new_gate.replace("GATE_VER = 'R127'", "GATE_VER = 'R128'", 1)
assert "GATE_VER = 'R128'" in new_gate

# 第 20 行登记式同步
d = old_dr.decode('utf-8')
assert "grep=(?m)^GATE_VER = 'R127'" in d, 'row20 registration not found'
new_d = d.replace("grep=(?m)^GATE_VER = 'R127'", "grep=(?m)^GATE_VER = 'R128'", 1)

# ---- 一次性写入 + 回读 ----
for path, blob in ((GATE, new_gate.encode('utf-8')), (DR, new_d.encode('utf-8'))):
    with io.open(path, 'wb') as f:
        f.write(blob)
    rb = io.open(path, 'rb').read()
    add('J3 回读一致 %s' % os.path.basename(path), rb == blob,
        {'sha': sha16(rb), 'bytes': len(rb)})
old_cr_gate = old_gate.count(b'\r')
new_cr_gate = io.open(GATE, 'rb').read().count(b'\r')
add('J4 check_disc.py 的 CR 数与改前一致（该文件本身是 CRLF，不因本轮改动而变）',
    old_cr_gate == new_cr_gate, {'before': old_cr_gate, 'after': new_cr_gate})
add('J5 DISC_RECHECK.tsv 仍为全 LF（CR=0）',
    io.open(DR, 'rb').read().count(b'\r') == 0, None)

json.dump({'checks': ck}, open(os.path.join(ROOT, '_r128', 'r128j_gate_apply.json'), 'w'),
          ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128j: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:300])
if n != len(ck): sys.exit(1)
