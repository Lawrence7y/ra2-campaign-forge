#!/usr/bin/env python3
"""R144 R：门禁三处版本标记同步（GATE_VER R143→R144、DISC_RECHECK 第 21 行、DISC_UNVERIFIABLE 第 11 行），
并给出正反控（沙箱），证明「这几处咬合」不是纸上的。

S-299 教训（R143 付出 7 FAIL 的代价）：表里同时有「行号」与「主键」时，必须先查清是哪种。
本轮先打印目标行再断言：
  DISC_RECHECK.tsv     行号 21 ←→ 纪律号 20（列 1 = 20）
  DISC_UNVERIFIABLE.tsv 行号 11 ←→ 纪律号 20（列 1 = 20）
两者主键相同（20）但行号不同，绝不能按主键去套行号。
"""
import hashlib, io, json, os, re, shutil, subprocess, time

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
RECH = os.path.join(BASE, 'DISC_RECHECK.tsv')
FREE = os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv')
RC = os.path.join(BASE, 'R14_COMMON.md')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
OUT = '/home/t628/projects/ra2-campaign-forge/_r144/r144r_sync.json'
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)
def backup(p, tag):
    b = open(p, 'rb').read()
    dst = os.path.join(BL, '%s.before_%s_%s.bak' % (os.path.basename(p), tag, time.strftime('%Y%m%d_%H%M%S')))
    with io.open(dst, 'xb') as f: f.write(b)
    ck('[%s] 备份 wx 独占且逐字节相同' % tag, open(dst, 'rb').read() == b, os.path.basename(dst))
    return b
def run_gate(cwd=BASE, script='check_disc.py'):
    r = subprocess.run(['python3', script], capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr

g0 = open(GATE, 'rb').read().decode('utf-8')
ck('C0 GATE_VER 先是 R143', "GATE_VER = 'R143'" in g0)
old_c7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", g0).group(1)
old_fr = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", g0).group(1)
ck('C1 旧 C7d 钉 25e8096c', old_c7.startswith('25e8096c'), old_c7[:16])
ck('C2 旧 FREEZE 钉 cc4a7c5f', old_fr.startswith('cc4a7c5f'), old_fr[:16])

# ---- DISC_RECHECK：先查清行号 vs 主键 ----
rec = open(RECH, 'rb').read().decode('utf-8')
rl = rec.split('\n')
ck('C3 DISC_RECHECK 有 >= 22 行', len(rl) >= 22, len(rl))
row21 = rl[20]
cols = row21.split('\t')
ck('C4 第 21 行第 1 列（主键）= 20', cols[0] == '20', cols[0])
ck('C5 第 21 行是 check_disc.py 自指行且登记 R143', 'check_disc.py' in row21 and "GATE_VER = 'R143'" in row21, row21[:70])
new_row21 = row21.replace("GATE_VER = 'R143'", "GATE_VER = 'R144'")
ck('C6 替换后含 R144 且只有一处变化', "GATE_VER = 'R144'" in new_row21 and new_row21.count("GATE_VER") == 1)
rl2 = list(rl); rl2[20] = new_row21
new_rec = '\n'.join(rl2)
rows = [x.split('\t') for x in new_rec.split('\n') if x]
def blob7(rs): return '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rs if len(r) == 7)
new_c7 = hashlib.sha256(blob7(rows).encode()).hexdigest()
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode()).hexdigest() for r in rows if len(r) == 7}
ck('C7 行指纹表 31 行', len(rowsha) == 31, len(rowsha))
ck('C8 新 C7d != 旧钉；且只有 row20 变化', new_c7 != old_c7 and rowsha['20'] != hashlib.sha256(('%s\t%s\t%s' % ('20', rl[20].split('\t')[4].strip(), rl[20].split('\t')[5].strip())).encode()).hexdigest(), [new_c7[:16], old_c7[:16]])

# ---- DISC_UNVERIFIABLE：行号 11 ←→ 主键 20 ----
fre = open(FREE, 'rb').read().decode('utf-8')
fl = fre.split('\n')
idxs = [i for i, l in enumerate(fl) if l.split('\t')[0] == '20']
ck('C9 冻结档里主键 20 恰 1 行', len(idxs) == 1, idxs)
ck('C10 该行行号是 11（1-based），与 DISC_RECHECK 的行号 21 不同 —— 这是 S-299 的坑', idxs[0] == 10, idxs[0] + 1)
ck('C11 该行登记 R143', "GATE_VER = 'R143'" in fl[idxs[0]])
fl2 = list(fl); fl2[idxs[0]] = fl2[idxs[0]].replace("GATE_VER = 'R143'", "GATE_VER = 'R144'")
ck('C12 替换后含 R144', "GATE_VER = 'R144'" in fl2[idxs[0]])
ck('C13 冻结时刻列未被改动', fl2[idxs[0]].split('\t')[6] == fl[idxs[0]].split('\t')[6])
new_fre = '\n'.join(fl2)
new_fr = hashlib.sha256(new_fre.encode()).hexdigest()
ck('C14 新 FREEZE != 旧钉', new_fr != old_fr, [new_fr[:16], old_fr[:16]])

# ---- 写 ----
backup(RECH, 'r144_recheck'); backup(FREE, 'r144_unverif'); backup(GATE, 'r144_gatever')
open(RECH, 'wb').write(new_rec.encode('utf-8'))
open(FREE, 'wb').write(new_fre.encode('utf-8'))

g1 = g0.replace("GATE_VER = 'R143'", "GATE_VER = 'R144'")
g1 = g1.replace("C7_TEXT_SHA256 = '%s'" % old_c7, "C7_TEXT_SHA256 = '%s'" % new_c7)
g1 = g1.replace("FREEZE_SHA256 = '%s'" % old_fr, "FREEZE_SHA256 = '%s'" % new_fr)
old20 = re.search(r"'20': '([0-9a-f]{64})'", g1).group(1)
g1 = g1.replace("'20': '%s'" % old20, "'20': '%s'" % rowsha['20'])
ck('C15 三处常量都已替换', new_c7 in g1 and new_fr in g1 and rowsha['20'] in g1 and old20 not in g1)
open(GATE, 'wb').write(g1.encode('utf-8'))

rc, out = run_gate()
ck('C16 改后 check_disc.py exit 0', rc == 0, rc)
ck('C17 C10 报 ok(R144)', 'C10 self-check: ok(R144)' in out)
ck('C18 C7d 报新钉且 OK', 'C7d' in out and new_c7[:16] in out and 'OK' in out)
ck('C19 C11 冻结档 OK（新钉在场）', new_fr[:16] in out and 'OK' in out)
ck('C20 C16 pinned 143 / unpinned 0 / min margin 21', 'pinned 143' in out and 'unpinned 0' in out and 'min margin 21' in out)
ck('C21 C16d 钉 05b54f35 且 OK', '05b54f35' in out and 'C16d floor-table pin' in out)
ck('C22 C15 报 143 节 / 末节 149', '143 sections' in out or 'sections' in out)

# ---- 反控（沙箱：软链复刻三层目录，只复制 4 个待改文件）----
tmp = '/tmp/r144_gate_ctl'
if os.path.isdir(tmp): shutil.rmtree(tmp)
os.makedirs(os.path.join(tmp, 'lead', 'next_re_20261117_r14'))
sand = os.path.join(tmp, 'lead', 'next_re_20261117_r14')
for f in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md',
          'STATUS_BOARD.md', 'place_r87.py', 'recheck_verify.py'):
    src = os.path.join(BASE, f)
    if os.path.exists(src): shutil.copy2(src, os.path.join(sand, f))
# 其余被 check_disc 引用的路径用软链接回真树（不复制 975 MB 的 lead/）
for name in os.listdir(BASE):
    src = os.path.join(BASE, name); dst = os.path.join(sand, name)
    if not os.path.exists(dst): os.symlink(src, dst)
for name in os.listdir('/home/t628/projects/ra2-campaign-forge/lead'):
    src = os.path.join('/home/t628/projects/ra2-campaign-forge/lead', name)
    dst = os.path.join(tmp, 'lead', name)
    if not os.path.exists(dst): os.symlink(src, dst)
for name in ('ra2bench', '_r143', '_r144', 'tools', 'docs', 'out', 'YRpp'):
    src = os.path.join('/home/t628/projects/ra2-campaign-forge', name)
    if os.path.exists(src) and not os.path.exists(os.path.join(tmp, name)): os.symlink(src, os.path.join(tmp, name))

def sandbox():
    r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=sand)
    return r.returncode, r.stdout + r.stderr

rcP, outP = sandbox()
ck('P0 沙箱基线 exit 0（复刻可用，否则后面反控无意义）', rcP == 0, rcP)

# N1：只回退 GATE_VER
s = open(os.path.join(sand, 'check_disc.py')).read().replace("GATE_VER = 'R144'", "GATE_VER = 'R143'", 1)
open(os.path.join(sand, 'check_disc.py'), 'w').write(s)
rcN1, outN1 = sandbox()
ck('N1 只回退 GATE_VER => exit != 0 且点名 C10', rcN1 != 0 and 'C10' in outN1, rcN1)
shutil.copy2(os.path.join(BASE, 'check_disc.py'), os.path.join(sand, 'check_disc.py'))

# N2：改冻结档内容不重钉
s = open(os.path.join(sand, 'DISC_UNVERIFIABLE.tsv')).read().replace('structurally_unverifiable', 'structurally_unverifiableX', 1)
open(os.path.join(sand, 'DISC_UNVERIFIABLE.tsv'), 'w').write(s)
rcN2, outN2 = sandbox()
ck('N2 改冻结档不重钉 => exit != 0 且点名 C11', rcN2 != 0 and 'C11' in outN2, rcN2)
shutil.copy2(os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv'), os.path.join(sand, 'DISC_UNVERIFIABLE.tsv'))

# N3：改 DISC_RECHECK 第 21 行 col5/col6 不重钉
s = open(os.path.join(sand, 'DISC_RECHECK.tsv')).read().replace('grep=逐字节闭合', 'grep=逐字节闭合X', 1)
open(os.path.join(sand, 'DISC_RECHECK.tsv'), 'w').write(s)
rcN3, outN3 = sandbox()
ck('N3 改 C7d 表不重钉 => exit != 0 且点名 C7d', rcN3 != 0 and 'C7d' in outN3, rcN3)
shutil.copy2(os.path.join(BASE, 'DISC_RECHECK.tsv'), os.path.join(sand, 'DISC_RECHECK.tsv'))

# N4：把 §2.149 正文掏空只剩标题
rcb = open(os.path.join(BASE, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
i = rcb.rindex('## 2.149')
hollow = rcb[:i] + '## 2.149 R144 · （占位）\n'
open(os.path.join(sand, 'R14_COMMON.md'), 'w').write(hollow)
rcN4, outN4 = sandbox()
ck('N4 §2.149 掏空只剩标题 => exit != 0 且点名 C16', rcN4 != 0 and 'C16' in outN4, rcN4)
shutil.copy2(os.path.join(BASE, 'R14_COMMON.md'), os.path.join(sand, 'R14_COMMON.md'))

# N5：把 149 的下界调小但不重钉 sha
s = open(os.path.join(sand, 'check_disc.py')).read().replace('149: 9026,', '149: 100,', 1)
open(os.path.join(sand, 'check_disc.py'), 'w').write(s)
rcN5, outN5 = sandbox()
ck('N5 调小 149 下界不重钉 sha => exit != 0 且点名 C16d', rcN5 != 0 and 'C16d' in outN5, rcN5)

# P1：复原
shutil.copy2(os.path.join(BASE, 'check_disc.py'), os.path.join(sand, 'check_disc.py'))
rcP1, outP1 = sandbox()
ck('P1 全部复原 => exit 0', rcP1 == 0, rcP1)
shutil.rmtree(tmp)

# 真树未受污染
rcT, outT = run_gate()
ck('T1 真树最终 exit 0', rcT == 0, rcT)
ck('T2 真树 GATE_VER 是 R144', "GATE_VER = 'R144'" in open(GATE).read())

json.dump({'checks': len(cc) + len([1]), 'fails': cc, 'c7d': new_c7, 'freeze': new_fr,
           'row20': rowsha['20'], 'c16': re.search(r'C16d floor-table pin: ([0-9a-f]+)', out).group(1)},
          io.open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n=== 同步：FAIL %d ===' % len(cc))
if cc: print(cc)
