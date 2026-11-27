# -*- coding: utf-8 -*-
"""R172 K：C16 反控**重做**（S-592：J 的 N4/N5 用的是深度不对的副本 ⇒ 假反控）。

check_disc.py 的 ROOT 由「本文件位置反推三层」得出，放在 _r172/ 下的副本会反推到 /home/t628/projects
⇒ N4「未改副本 exit 0」FAIL 且 N5「改大 1 必 FAIL」是**因为找不到文件才 FAIL**，对该断言毫无判别力。
本脚本把副本放在 **lead/next_re_20261117_r14/** 下（与生产同深度），再做正反控。
"""
import hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
CD = os.path.join(TIER, 'check_disc.py')
PROBE = os.path.join(TIER, '_r172_cd_probe.py')     # 与生产同深度（lead/next_re_20261117_r14/）

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

def run(p, t=900):
    r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=t)
    return r.returncode, r.stdout + r.stderr

text = io.open(CD, encoding='utf-8').read()
m = re.search(r'^C16_FLOORS = \{(.*?)^\}', text, re.S | re.M)
tbl = dict((int(a), int(b)) for a, b in re.findall(r'^\s{4}(\d+): (\d+),', m.group(1), re.M))
FLOOR = tbl[177]
print('  现盘 C16_FLOORS %d 条，177 的 floor = %d' % (len(tbl), FLOOR))

# 深度自证：副本的反推 ROOT 必须等于生产 ROOT
ck('K0 副本位置与生产同深度（三层反推得同一 ROOT）',
   os.path.dirname(os.path.dirname(os.path.dirname(PROBE))) == ROOT, os.path.dirname(os.path.dirname(os.path.dirname(PROBE))))

io.open(PROBE, 'w', encoding='utf-8').write(text)
rc0, o0 = run(PROBE)
ck('K1 正控：未改副本 exit 0（真跑，不是「找不到文件」）', rc0 == 0, o0[-400:])
ck('K1b 未改副本 NOTE 逐字 171 节 pinned 171 / unpinned 0',
   '171 sections measured (pinned 171), hollow/deficient 0, missing 0, unpinned 0' in o0,
   [l for l in o0.split('\n') if 'C16 per-section' in l])

# 反控 A：177 的 floor 调大 1 ⇒ 该节变 deficient ⇒ 必 FAIL
mutA = text.replace('    177: %d,\n}' % FLOOR, '    177: %d,\n}' % (FLOOR + 1), 1)
ck('K2 反控构造 A：只改 177 的 floor（+1）', mutA != text)
io.open(PROBE, 'w', encoding='utf-8').write(mutA)
rcA, oA = run(PROBE)
ck('K2b 反控 A 必 FAIL 且失败理由与 C16 有关（不是 FileNotFoundError）',
   rcA == 1 and 'FileNotFoundError' not in oA and ('C16' in oA or 'deficient' in oA or 'TAMPERED' in oA), oA[-400:])

# 反控 B：把 177 整行删掉 ⇒ unpinned 1 ⇒ 必 FAIL
mutB = text.replace('    177: %d,\n}' % FLOOR, '}', 1)
ck('K3 反控构造 B：删掉 177 整行', mutB != text)
io.open(PROBE, 'w', encoding='utf-8').write(mutB)
rcB, oB = run(PROBE)
ck('K3b 反控 B 必 FAIL 且理由含 unpinned（不是 FileNotFoundError）',
   rcB == 1 and 'FileNotFoundError' not in oB and 'unpinned' in oB, oB[-400:])

os.remove(PROBE)
ck('K4 探针已清除', not os.path.exists(PROBE))
rcP, oP = run(CD)
ck('K5 生产 check_disc 仍 exit 0（反控未污染生产）', rcP == 0, oP[-300:])

io.open(os.path.join(HERE, 'r172k_c16_control.json'), 'w', encoding='utf-8').write(json.dumps(
    {'probe_depth_ok': True, 'floor177': FLOOR, 'entries': len(tbl),
     'rc_clean': rc0, 'rc_mutA': rcA, 'rc_mutB': rcB, 'rc_prod': rcP}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
