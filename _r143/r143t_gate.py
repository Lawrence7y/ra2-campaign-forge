#!/usr/bin/env python3
"""R143 C：门禁四处同步（全部为「容纳新节 / 同步版本标记」性质，不改任何判据语义）。
  1) GATE_VER R140 -> R143（C10 自检要求登记行版本标记与脚本一致）
  2) DISC_UNVERIFIABLE.tsv 第 20 行（check_disc.py 自指行）的 grep 串同步到 R143，重钉 FREEZE_SHA256
  3) DISC_RECHECK.tsv 第 21 行的 grep 串同步到 R143，重钉 C7_TEXT_SHA256 / C7_ROW_SHA[21]
正反控：① 不回退版本标记会 FAIL 且点名 C10；② 回退版本标记但不同步登记行仍 FAIL；
        ③ 冻结档改内容不重钉必须 FAIL 且点名 C11；④ 复原后 exit 0。
"""
import hashlib, io, json, os, re, time
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
RECH = os.path.join(BASE, 'DISC_RECHECK.tsv')
FREE = os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
OUT = '/home/t628/projects/ra2-campaign-forge/_r143/r143t_gate.json'
cc, cc_n = [], 0
def ck(n, c, d=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

def backup(p, tag):
    b = open(p, 'rb').read()
    dst = os.path.join(BL, '%s.before_%s_%s.bak' % (os.path.basename(p), tag, time.strftime('%Y%m%d_%H%M%S')))
    with io.open(dst, 'xb') as f: f.write(b)
    ck('[%s] 备份 wx 独占且逐字节相同' % tag, open(dst, 'rb').read() == b, os.path.basename(dst))
    return b

def run_gate():
    import subprocess
    r = subprocess.run(['python3', GATE], capture_output=True, text=True, cwd=BASE)
    return r.returncode, r.stdout + r.stderr

g0 = open(GATE, 'rb').read().decode('utf-8')
ck('C0 GATE_VER 先是 R140', "GATE_VER = 'R140'" in g0)
old_c7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", g0).group(1)
old_fr = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", g0).group(1)
ck('C1 旧 C7d 钉 a582d592', old_c7.startswith('a582d592'), old_c7[:16])
ck('C2 旧 FREEZE 钉 ce735a99', old_fr.startswith('ce735a99'), old_fr[:16])

# ---- 1) DISC_RECHECK 第 21 行（check_disc.py 自指行）----
rec = open(RECH, 'rb').read().decode('utf-8')
rl = rec.split('\n')
ck('C3 DISC_RECHECK 有 21 行以上', len(rl) >= 22, len(rl))
row21 = rl[20]
ck('C4 第 21 行是 check_disc.py 自指行', 'check_disc.py' in row21 and "GATE_VER = 'R140'" in row21, row21[:80])
new_row21 = row21.replace("GATE_VER = 'R140'", "GATE_VER = 'R143'")
ck('C5 第 21 行已换成 R143', "GATE_VER = 'R143'" in new_row21)
rl2 = list(rl); rl2[20] = new_row21
new_rec = '\n'.join(rl2)

# 计算新 C7d 指纹（必须在写盘前用新行算）
rows = [x.split('\t') for x in new_rec.split('\n') if x]
def blob7(rs): return '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rs if len(r) == 7)
new_c7 = hashlib.sha256(blob7(rows).encode()).hexdigest()
ck('C6 新 C7d 钉 != 旧钉', new_c7 != old_c7)
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode()).hexdigest()
          for r in rows if len(r) == 7}
ck('C7 行指纹表 31 行', len(rowsha) == 31, len(rowsha))

# ---- 2) DISC_UNVERIFIABLE 第 20 行 ----
fre = open(FREE, 'rb').read().decode('utf-8')
fl = fre.split('\n')
idx = [i for i, l in enumerate(fl) if l.startswith('20\t')]
ck('C8 冻结档有第 20 行', len(idx) == 1, idx)
fl2 = list(fl)
fl2[idx[0]] = fl2[idx[0]].replace("GATE_VER = 'R140'", "GATE_VER = 'R143'")
ck('C9 冻结档第 20 行已换成 R143', "GATE_VER = 'R143'" in fl2[idx[0]])
new_fre = '\n'.join(fl2)
new_fr = hashlib.sha256(new_fre.encode()).hexdigest()
ck('C10 新 FREEZE 钉 != 旧钉', new_fr != old_fr)
# 冻结档的「冻结时刻」列必须保持原值（不许悄悄改时刻）
ck('C11 冻结时刻列未被改动', fl2[idx[0]].split('\t')[6] == fl[idx[0]].split('\t')[6])

# ---- 写 ----
backup(RECH, 'r143_recheck'); backup(FREE, 'r143_unverif'); backup(GATE, 'r143_gatever')
open(RECH, 'wb').write(new_rec.encode('utf-8'))
open(FREE, 'wb').write(new_fre.encode('utf-8'))

g1 = g0.replace("GATE_VER = 'R140'", "GATE_VER = 'R143'")
g1 = g1.replace("C7_TEXT_SHA256 = '%s'" % old_c7, "C7_TEXT_SHA256 = '%s'" % new_c7)
g1 = g1.replace("FREEZE_SHA256 = '%s'" % old_fr, "FREEZE_SHA256 = '%s'" % new_fr)
# C7_ROW_SHA['21'] 同步
old21 = re.search(r"'21': '([0-9a-f]{64})'", g1).group(1)
g1 = g1.replace("'21': '%s'" % old21, "'21': '%s'" % rowsha['21'])
ck('C12 三处常量都已替换', new_c7 in g1 and new_fr in g1 and rowsha['21'] in g1)
open(GATE, 'wb').write(g1.encode('utf-8'))

rc, out = run_gate()
ck('C13 改后 check_disc.py exit 0', rc == 0, rc)
ck('C14 C10 报 ok(R143)', 'C10 self-check: ok(R143)' in out)
ck('C15 C7d 报新钉且 OK', ('C7d' in out and new_c7[:16] in out and 'OK' in out))
ck('C16 C11 冻结档 OK', 'sha256=%s OK' % new_fr[:16] in out)
ck('C17 C16 pinned 142 / unpinned 0', 'pinned 142' in out and 'unpinned 0' in out)

# ---- 反控 ----
import shutil
tmp = '/tmp/r143_gate_ctl'
os.makedirs(tmp, exist_ok=True)
for f in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'):
    shutil.copy2(os.path.join(BASE, f), os.path.join(tmp, f))
# 沙箱需要 R14_COMMON.md（C15/C16 读它）
shutil.copy2(os.path.join(BASE, 'R14_COMMON.md'), os.path.join(tmp, 'R14_COMMON.md'))
def sandbox_gate():
    import subprocess
    r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=tmp)
    return r.returncode, r.stdout + r.stderr
# N1 把 GATE_VER 回退成 R140，登记行仍是 R143
s = open(os.path.join(tmp, 'check_disc.py')).read().replace("GATE_VER = 'R143'", "GATE_VER = 'R140'")
open(os.path.join(tmp, 'check_disc.py'), 'w').write(s)
rcN1, outN1 = sandbox_gate()
ck('N1 只回退 GATE_VER => exit != 0 且点名 C10', rcN1 != 0 and 'C10' in outN1, rcN1)
# N2 复原，再改冻结档内容不重钉
shutil.copy2(os.path.join(BASE, 'check_disc.py'), os.path.join(tmp, 'check_disc.py'))
s = open(os.path.join(tmp, 'DISC_UNVERIFIABLE.tsv')).read().replace('structurally_unverifiable', 'structurally_unverifiableX', 1)
open(os.path.join(tmp, 'DISC_UNVERIFIABLE.tsv'), 'w').write(s)
rcN2, outN2 = sandbox_gate()
ck('N2 改冻结档不重钉 => exit != 0 且点名 C11', rcN2 != 0 and 'C11' in outN2, rcN2)
# N3 复原，再改 C7d 表不重钉
shutil.copy2(os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv'), os.path.join(tmp, 'DISC_UNVERIFIABLE.tsv'))
s = open(os.path.join(tmp, 'DISC_RECHECK.tsv')).read().replace("GATE_VER = 'R143'", "GATE_VER = 'R143b'", 1)
open(os.path.join(tmp, 'DISC_RECHECK.tsv'), 'w').write(s)
rcN3, outN3 = sandbox_gate()
ck('N3 改 col5/col6 不重钉 => exit != 0 且点名 C7d', rcN3 != 0 and 'C7d' in outN3, rcN3)
# P1 复原 => exit 0
for f in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md'):
    shutil.copy2(os.path.join(BASE, f), os.path.join(tmp, f))
rcP, outP = sandbox_gate()
ck('P1 复原 => exit 0', rcP == 0, rcP)
# 真树未被沙箱影响
rcT, outT = run_gate()
ck('P2 真树仍 exit 0', rcT == 0, rcT)

json.dump(dict(checks=cc_n, fails=cc, c7dh=new_c7, c7do=old_c7, freezeh=new_fr, freezeo=old_fr,
               row21=rowsha['21']), io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 门禁同步：%d 项 / FAIL %d ===' % (cc_n, len(cc)))
if cc: print('FAILS:', cc)
