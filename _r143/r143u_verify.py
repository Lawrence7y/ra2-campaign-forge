#!/usr/bin/env python3
"""R143 U：门禁终态校验 + 四个反控（对当前真树做，沙箱副本，不碰真树）。

背景：r143t_gate.py 那次跑出 7 FAIL，根因是我把「第 21 行」当成 id 21，
而 check_disc.py 自指行的 id 是 20（行号 21）——两条都叫「21」，我按行号取了行、
按 id 写了 C7_ROW_SHA['21']，于是真正变化的 id 20 没被重钉。
已就地修正（重钉 C7_TEXT_SHA256 + C7_ROW_SHA['20']，'21' 恢复原值）。本脚本做终态校验与反控，
并把那次自错记为 S-299。
"""
import hashlib, io, json, os, re, shutil, subprocess
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
OUT = '/home/t628/projects/ra2-campaign-forge/_r143/r143u_verify.json'
cc, cc_n = [], 0
def ck(n, c, d=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

def run(cwd):
    r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr

rc, out = run(BASE)
ck('E1 真树 exit 0', rc == 0, rc)
ck('E2 GATE_VER 已升到 R143', 'C10 self-check: ok(R143)' in out and "GATE_VER = 'R143'" in open(GATE).read())
ck('E3 C7d 钉一致（ok）', 'C7d product/expression fingerprint ok' in out)
ck('E4 C11 冻结档一致（OK）', re.search(r'frozen-class registry loaded.*sha256=[0-9a-f]{16} OK', out) is not None)
ck('E5 C16 pinned 142 / unpinned 0 / min margin 21',
   'pinned 142' in out and 'unpinned 0' in out and 'min margin 21' in out)
ck('E6 C15 末节 148 / bytes 1,227,758', 'last 148' in out and 'bytes 1227758' in out)

# 独立复算三个钉
g = open(GATE).read()
c7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", g).group(1)
fr = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", g).group(1)
c16 = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]+)'", g).group(1)
txt = io.open(os.path.join(BASE, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read()
rows = [l.split('\t') for l in txt.split('\n') if l][1:]
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
ck('E7 C7d 钉 = 独立重算', hashlib.sha256(blob.encode()).hexdigest() == c7, c7[:16])
fre = io.open(os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv'), encoding='utf-8', newline='')
freeb = open(os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv'), 'rb').read()
ck('E8 FREEZE 钉 = 独立重算（字节级）', hashlib.sha256(freeb).hexdigest() == fr, fr[:16])
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', g, re.S)
d = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
ck('E9 C16 表 142 条、148 项在表', len(d) == 142 and 148 in d, len(d))
ck('E10 C16 钉 = 独立重算', hashlib.sha256('\n'.join('%d:%d' % (k, d[k]) for k in sorted(d)).encode()).hexdigest() == c16, c16[:16])

# ---- 反控（沙箱）----
# 沙箱必须复刻 check_disc.py 反推的三层目录结构 <sbx>/lead/next_re_20261117_r14/。
# lead/ 有 975 MB，不能复制：改用「逐项软链 + 只复制要改的 4 个文件」。
SBX = '/tmp/r143_gate_sbx'
shutil.rmtree(SBX, ignore_errors=True)
L1 = os.path.join(SBX, 'lead')
tmp = os.path.join(L1, 'next_re_20261117_r14')
os.makedirs(tmp)
ROOT = os.path.dirname(os.path.dirname(BASE))  # ra2-campaign-forge
MUT = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md'}
for f in os.listdir(ROOT):
    if f == 'lead': continue
    os.symlink(os.path.join(ROOT, f), os.path.join(SBX, f))
for f in os.listdir(os.path.join(ROOT, 'lead')):
    if f == 'next_re_20261117_r14': continue
    os.symlink(os.path.join(ROOT, 'lead', f), os.path.join(L1, f))
for f in os.listdir(BASE):
    src = os.path.join(BASE, f)
    if f in MUT:
        shutil.copy2(src, os.path.join(tmp, f))
    else:
        os.symlink(src, os.path.join(tmp, f))
rcP, outP = run(tmp)
ck('N0 沙箱基线 exit 0（控制脚本自身前提）', rcP == 0, rcP)

def ctl(tag, fname, old, new, must):
    shutil.copy2(os.path.join(BASE, fname), os.path.join(tmp, fname))
    p = os.path.join(tmp, fname)
    s = io.open(p, encoding='utf-8', newline='').read()
    assert old in s, (tag, 'anchor missing')
    io.open(p, 'w', encoding='utf-8', newline='').write(s.replace(old, new, 1))
    rc, out = run(tmp)
    hit = must in out
    ck('N-%s 改 %s（不重钉）=> exit != 0 且点名 %s' % (tag, fname, must), rc != 0 and hit, rc)
    shutil.copy2(os.path.join(BASE, fname), os.path.join(tmp, fname))

ctl('1', 'check_disc.py', "GATE_VER = 'R143'", "GATE_VER = 'R140'", 'C10')
ctl('2', 'DISC_UNVERIFIABLE.tsv', 'structurally_unverifiable', 'structurally_unverifiableX', 'C11')
ctl('3', 'DISC_RECHECK.tsv', "GATE_VER = 'R143'", "GATE_VER = 'R143b'", 'C7d')
# N4：删掉 R14_COMMON 里 §2.148 的一个小节正文（C16 单节下界应抓）
s = io.open(os.path.join(tmp, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
i = s.rindex('## 2.148')
io.open(os.path.join(tmp, 'R14_COMMON.md'), 'w', encoding='utf-8', newline='').write(s[:i] + '## 2.148 R143\n')
rc, out = run(tmp)
ck('N-4 把 §2.148 掏空 => exit != 0 且点名 C16', rc != 0 and 'C16' in out, rc)
shutil.copy2(os.path.join(BASE, 'R14_COMMON.md'), os.path.join(tmp, 'R14_COMMON.md'))

rcP2, _ = run(tmp)
ck('P1 全部复原 => 沙箱 exit 0', rcP2 == 0, rcP2)
rcT, _ = run(BASE)
ck('P2 真树仍 exit 0（控制脚本未污染真树）', rcT == 0, rcT)

json.dump(dict(checks=cc_n, fails=cc, c7d=c7, freeze=fr, c16=c16), io.open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n=== 校验+反控：%d 项 / FAIL %d ===' % (cc_n, len(cc)))
if cc: print('FAILS:', cc)
