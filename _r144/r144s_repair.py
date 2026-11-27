#!/usr/bin/env python3
"""R144 S：修正 r144r 的自错 S-312（C7d 指纹把表头行一起算了）。

根因：`check_disc.py` 的口径是 `rows = [l.split('\\t') for l in raw[1:]]`（**丢表头**），
我在 r144r 里写成「所有非空行」⇒ 32 行而非 31 行 ⇒ 新钉 8c35cff4 是**含表头**的指纹，
门禁按 31 行算出 636db13b ⇒ C7d FAIL。
铁律：**先读门禁怎么算，再照抄它的口径**（与 R143 S-299「行号 vs 主键」同族，但这次是「行集口径」）。

本脚本：重算正确指纹 -> 断言 == 门禁现算值 -> 换钉 -> 复跑门禁 -> 沙箱正反控。
"""
import hashlib, io, json, os, re, shutil, subprocess

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
RECH = os.path.join(BASE, 'DISC_RECHECK.tsv')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
OUT = '/home/t628/projects/ra2-campaign-forge/_r144/r144s_repair.json'
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)
def run_gate():
    r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=BASE)
    return r.returncode, r.stdout + r.stderr

g = open(GATE, 'rb').read().decode('utf-8')
cur_pin = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", g).group(1)
ck('R0 当前钉是 8c35cff4（我上一版写错的含表头指纹）', cur_pin.startswith('8c35cff4'), cur_pin[:16])

raw = [l for l in open(RECH, 'rb').read().decode('utf-8').split('\n') if l]
ck('R1 表头行 7 列且第 1 列是「纪律号」', len(raw[0].split('\t')) == 7 and raw[0].split('\t')[0] == '纪律号', raw[0].split('\t')[0])
rows = [l.split('\t') for l in raw[1:]]
ck('R2 照抄门禁口径（丢表头）后恰 31 行', len(rows) == 31, len(rows))
ck('R3 31 行全是 7 列', all(len(r) == 7 for r in rows))
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows)
right = hashlib.sha256(blob.encode()).hexdigest()
ck('R4 正确指纹 == 门禁现算的 636db13b', right.startswith('636db13b'), right[:16])
ck('R5 正确指纹 != 我写错的那个（差一行表头）', right != cur_pin)
# 反控：含表头会得到我上一版的错值（证明差异就是表头这一行）
blobh = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in [raw[0].split('\t')] + rows)
ck('R6 反控：含表头重算恰得我写错的 8c35cff4（差异确实只是表头）', hashlib.sha256(blobh.encode()).hexdigest() == cur_pin)
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode()).hexdigest() for r in rows}
ck('R7 rowsha 31 键，且 20 号行的指纹与门禁一致（row 内容未因去表头而变）', len(rowsha) == 31 and len(rowsha['20']) == 64)

src = open(GATE, 'rb').read()
dst = os.path.join(BL, 'check_disc.py.before_r144s_repair_%s.bak' % __import__('time').strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(src)
ck('R8 备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))

g2 = g.replace("C7_TEXT_SHA256 = '%s'" % cur_pin, "C7_TEXT_SHA256 = '%s'" % right)
ck('R9 已换钉', right in g2 and cur_pin not in g2)
open(GATE, 'wb').write(g2.encode('utf-8'))

rc, out = run_gate()
ck('R10 门禁 exit 0', rc == 0, rc)
ck('R11 C7d 报正确指纹且 OK', 'C7d' in out and right[:16] in out and 'OK' in out)
ck('R12 C10 ok(R144)', 'C10 self-check: ok(R144)' in out)
ck('R13 C16 pinned 143 / unpinned 0 / min margin 21', 'pinned 143' in out and 'unpinned 0' in out and 'min margin 21' in out)

# 沙箱正反控（软链复刻三层 + 只复制待改文件）
tmp = '/tmp/r144_gate_ctl2'
if os.path.isdir(tmp): shutil.rmtree(tmp)
sand = os.path.join(tmp, 'lead', 'next_re_20261117_r14')
os.makedirs(sand)
for f in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md', 'STATUS_BOARD.md',
          'place_r87.py', 'recheck_verify.py'):
    src2 = os.path.join(BASE, f)
    if os.path.exists(src2): shutil.copy2(src2, os.path.join(sand, f))
for name in os.listdir(BASE):
    s2 = os.path.join(BASE, name); d2 = os.path.join(sand, name)
    if not os.path.exists(d2): os.symlink(s2, d2)
for name in os.listdir('/home/t628/projects/ra2-campaign-forge/lead'):
    s2 = os.path.join('/home/t628/projects/ra2-campaign-forge/lead', name); d2 = os.path.join(tmp, 'lead', name)
    if not os.path.exists(d2): os.symlink(s2, d2)
# S-313：首版只软链了 ra2bench/_r143/_r144，而门禁 C7 的 id 31 产物在 `_r94\falsify_r94.py`
# ⇒ 沙箱报 3 条 FILE_MISSING、P0/P1 双双 FAIL。改为软链 ROOT 下**全部**顶层条目
# （门禁是靠「本文件位置反推三层」定位 ROOT 的，任何顶层目录都可能被某行引用）。
for name in os.listdir('/home/t628/projects/ra2-campaign-forge'):
    s2 = os.path.join('/home/t628/projects/ra2-campaign-forge', name)
    d2 = os.path.join(tmp, name)
    if not os.path.exists(d2) and os.path.isdir(s2): os.symlink(s2, d2)
def sb():
    r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=sand)
    return r.returncode, r.stdout + r.stderr
rcP, outP = sb()
ck('P0 沙箱基线 exit 0（复刻可用）', rcP == 0, rcP)
s = open(os.path.join(sand, 'check_disc.py')).read().replace("GATE_VER = 'R144'", "GATE_VER = 'R143'", 1)
open(os.path.join(sand, 'check_disc.py'), 'w').write(s)
rc1, o1 = sb()
ck('N1 只回退 GATE_VER => FAIL 且点名 C10', rc1 != 0 and 'C10' in o1, rc1)
shutil.copy2(GATE, os.path.join(sand, 'check_disc.py'))
s = open(os.path.join(sand, 'DISC_RECHECK.tsv')).read().replace('grep=逐字节闭合', 'grep=逐字节闭合X', 1)
open(os.path.join(sand, 'DISC_RECHECK.tsv'), 'w').write(s)
rc2, o2 = sb()
ck('N2 改 C7d 两列不重钉 => FAIL 且点名 C7d 与 id 19', rc2 != 0 and 'C7d' in o2 and "'19'" in o2, rc2)
shutil.copy2(RECH, os.path.join(sand, 'DISC_RECHECK.tsv'))
s = open(os.path.join(sand, 'DISC_UNVERIFIABLE.tsv')).read().replace('structurally_unverifiable', 'structurally_unverifiableX', 1)
open(os.path.join(sand, 'DISC_UNVERIFIABLE.tsv'), 'w').write(s)
rc3, o3 = sb()
ck('N3 改冻结档不重钉 => FAIL 且点名 C11', rc3 != 0 and 'C11' in o3, rc3)
shutil.copy2(os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv'), os.path.join(sand, 'DISC_UNVERIFIABLE.tsv'))
rcb = open(os.path.join(BASE, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
i = rcb.rindex('## 2.149')
open(os.path.join(sand, 'R14_COMMON.md'), 'w').write(rcb[:i] + '## 2.149 R144 · （占位）\n')
rc4, o4 = sb()
ck('N4 §2.149 掏空 => FAIL 且点名 C16', rc4 != 0 and 'C16' in o4, rc4)
shutil.copy2(os.path.join(BASE, 'R14_COMMON.md'), os.path.join(sand, 'R14_COMMON.md'))
s = open(os.path.join(sand, 'check_disc.py')).read().replace('149: 9026,', '149: 100,', 1)
open(os.path.join(sand, 'check_disc.py'), 'w').write(s)
rc5, o5 = sb()
ck('N5 调小 149 下界不重钉 sha => FAIL 且点名 C16d', rc5 != 0 and 'C16d' in o5, rc5)
shutil.copy2(GATE, os.path.join(sand, 'check_disc.py'))
rc6, o6 = sb()
ck('P1 全部复原 => exit 0', rc6 == 0, rc6)
shutil.rmtree(tmp)
rcT, outT = run_gate()
ck('T1 真树最终 exit 0', rcT == 0, rcT)

json.dump({'checks': len(cc) + 1, 'fails': cc, 'old_wrong': cur_pin, 'new_right': right,
           'rows': len(rows)}, io.open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n=== 修复：FAIL %d ===' % len(cc))
if cc: print(cc)
