# -*- coding: utf-8 -*-
"""r135c_controls.py -- R135 门禁改动的正反控（C11 frozen 分支真修 + C12b 冻结档镜像判据）

沙箱：symlink 真树，只把 4 个文件做成可写副本：
      check_disc.py / recheck_verify.py / DISC_RECHECK.tsv / DISC_UNVERIFIABLE.tsv
清场一律走 _safe_rmtree（R134 S-233：沙箱里有指向真树的软链时，不能用任何递归删除原语）。
复原一律从内存基线写回（R130 S-203）。

正控（P）：修法不得误伤
  P1 未改副本 exit 0
  P2 C11 仍报 ok=0 fail=0 frozen-unverifiable=12
  P3 C12b 打印 12/12 镜像一致

负控（N）：每一处都必须被抓，且必须报出对应的检查名
  N1 冻结产物里出现**一条半截**自述行（discipline=N garbage）
     -> R58 的旧语义会把它记成 declared（豁免）；R135 必须 FAIL 并点名「理由不是 no-line」
  N1b 对照：同一把产品换成「什么都没有」的空文件 -> 必须仍然 exit 0（豁免不能被误伤）
  N2 改 live 表某冻结行的第 6 列 -> C12b FAIL
  N2b 关键一条：连 C7d 的常量与行指纹一起重钉（模拟伪造者），C7d 放行而 C12b 仍 FAIL
      —— 证明 C12b 与 sha 钉是两个独立条件
  N3 改冻结档第 4 列 -> C12b FAIL（镜像断裂的两个方向都要被抓）
"""
import io
import os
import re
import sys
import copy
import shutil
import subprocess
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
REAL = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SB = os.path.join(ROOT, '_r135', 'sb')
GATE = 'check_disc.py'
VERIF = 'recheck_verify.py'
ROWS = 'DISC_RECHECK.tsv'
FREEZE = 'DISC_UNVERIFIABLE.tsv'
WRITABLE = (GATE, VERIF, ROWS, FREEZE)
res = []
OUT = {}


def _safe_rmtree(path):
    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.islink(fp):
                os.unlink(fp)
            else:
                os.remove(fp)
        for d in dirs:
            dp = os.path.join(root, d)
            if os.path.islink(dp):
                os.unlink(dp)
            else:
                try:
                    os.rmdir(dp)
                except OSError:
                    pass
    try:
        os.rmdir(path)
    except OSError:
        pass


def build():
    if os.path.isdir(SB):
        _safe_rmtree(SB)
    r14 = os.path.join(SB, 'lead', 'next_re_20261117_r14')
    os.makedirs(r14)
    for name in os.listdir(REAL):
        if name in WRITABLE:
            continue
        try:
            os.symlink(os.path.join(REAL, name), os.path.join(r14, name))
        except OSError:
            pass
    os.symlink(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(SB, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    if os.path.isdir(os.path.join(ROOT, '_r94')):
        os.symlink(os.path.join(ROOT, '_r94'), os.path.join(SB, '_r94'))
    for n in WRITABLE:
        dst = os.path.join(r14, n)
        if os.path.lexists(dst):
            os.remove(dst)
        shutil.copy2(os.path.join(REAL, n), dst)
    return r14


def gate(r14):
    p = subprocess.run([sys.executable, os.path.join(r14, GATE)],
                       capture_output=True, text=True, timeout=600)
    fails = [l.strip() for l in p.stdout.split('\n') if l.strip().startswith('FAIL')]
    return p.returncode, fails, p.stdout


def rd(p):
    t = io.open(p, encoding='utf-8', newline='').read()
    assert '\r' not in t
    ls = [l for l in t.split('\n') if l]
    return ls[0], [l.split('\t') for l in ls[1:]]


def wr(p, hdr, rows):
    io.open(p, 'w', encoding='utf-8', newline='').write(
        hdr + '\n' + '\n'.join('\t'.join(r) for r in rows) + '\n')


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-62s %s' % ('PASS' if cond else 'FAIL', name, detail))


r14 = build()
pROWS = os.path.join(r14, ROWS)
pFREEZE = os.path.join(r14, FREEZE)
pGATE = os.path.join(r14, GATE)

hdrR, rowsR = rd(pROWS)
hdrF, rowsF = rd(pFREEZE)
BASE_R = copy.deepcopy(rowsR)
BASE_F = copy.deepcopy(rowsF)
HDR_R, HDR_F = hdrR, hdrF


def restore():
    wr(pROWS, HDR_R, copy.deepcopy(BASE_R))
    wr(pFREEZE, HDR_F, copy.deepcopy(BASE_F))
    gate_patched_reset()
    # 自错 S-239：第一版 restore() 只复位两张表与门禁，没复位 N1 改过的产物副本，
    # 于是 P4「复原后 exit 0」实测 exit=1 —— 那次失败暴露的是我的处置不完整，
    # 不是判据有问题。这里补上产物复位（prod_restore 在 N1 段定义，故按名查）。
    _pr = globals().get('prod_restore')
    if _pr is not None:
        _pr()


def gate_patched_reset():
    shutil.copy2(os.path.join(REAL, GATE), pGATE)


# ---------- 正控 ----------
rc0, f0, o0 = gate(r14)
chk('P1 unmodified copy exit 0', rc0 == 0, 'exit=%d fails=%s' % (rc0, f0[:2]))
chk('P2 C11 still reports ok=0 fail=0 frozen-unverifiable=12',
    bool(re.search(r'C11 col7 machine-check: ok=0 fail=0 frozen-unverifiable=12 claims-none=19', o0)),
    'C11 note')
chk('P3 C12b reports 12/12 mirror-identical',
    bool(re.search(r'C12b frozen registry mirrors the live table: 12/12 rows identical', o0)),
    'C12b note')

# ---------- N1 / N1b：冻结产物里出现半截自述行 ----------
# 选 id 24：产物是 REPORT.md、校验式是 grep=（追加一行不会让 C7 失效），且该文件在沙箱里
# 默认是软链 —— 故先把它换成真副本，再往副本追加，绝不写穿到真树。
# （自错 S-236：我第一次想让这条半截行落进 check_disc.py，那是 Python 源码，追加即 SyntaxError，
#   门禁连跑都跑不起来，于是 N1 的 exit=1 与冻结分支毫无关系 —— 零信息反控。）
NID = 24
_hdrR0, _rowsR0 = rd(pROWS)
_prod_rel = [r for r in _rowsR0 if r[0] == str(NID)][0][4].strip()
# 产物路径相对的是 ROOT（沙箱根 SB），不是 lead/next_re_.../ —— 自错 S-237：
# 第一版把 r14 当根拼路径，得到双层错路。
# 且该产物所在的**目录**在沙箱里是软链（沙箱只对 r14 顶层的条目建软链），故
# os.path.islink(文件) 为 False、而往里写会写穿到真树 —— 自错 S-238。
# 正确做法：把该目录软链换成真目录，内部逐项建软链，只把目标文件做成真副本。
_prod_abs = os.path.join(SB, _prod_rel.replace('\\', '/'))
_real_prod = os.path.join(ROOT, _prod_rel.replace('\\', '/'))
_dir_abs = os.path.dirname(_prod_abs)
_dir_real = os.path.dirname(_real_prod)
if os.path.islink(_dir_abs):
    os.unlink(_dir_abs)
    os.makedirs(_dir_abs)
    for nm in os.listdir(_dir_real):
        src = os.path.join(_dir_real, nm)
        dst = os.path.join(_dir_abs, nm)
        if nm == os.path.basename(_real_prod):
            shutil.copy2(src, dst)
        else:
            os.symlink(src, dst)
elif not os.path.isdir(_dir_abs):
    # 目录在沙箱里既不软链也不存在 —— 这种状态下写文件等于在沙箱里凭空造目录，如实断言失败。
    raise AssertionError('sandbox product dir neither symlink nor dir: %s' % _dir_abs)
assert not os.path.islink(_prod_abs), 'product must be a real copy in the sandbox'
assert os.path.realpath(_prod_abs) != os.path.realpath(_real_prod), \
    'sandbox product must not resolve to the real tree'
_orig_prod = io.open(_prod_abs, encoding='utf-8', newline='').read()
# 完整性自检：副本与原文件字节相同（否则后面的「破坏」测的不是同一对象）
assert _orig_prod == io.open(_real_prod, encoding='utf-8', newline='').read()


def prod_append_bad(tail):
    io.open(_prod_abs, 'w', encoding='utf-8', newline='').write(_orig_prod + tail)


def prod_restore():
    io.open(_prod_abs, 'w', encoding='utf-8', newline='').write(_orig_prod)


rc1, f1, o1 = gate(r14)
m1 = re.search(r'C11 col7 machine-check: ok=(\d+) fail=(\d+) frozen-unverifiable=(\d+)', o1)
chk('N1b 基线：无自述行 -> frozen-unverifiable=12 / fail=0（豁免成立且计数可见）',
    rc1 == 0 and m1 and m1.group(1) == '0' and m1.group(2) == '0' and m1.group(3) == '12',
    'exit=%d %s' % (rc1, m1.group(0) if m1 else 'no-note'))

prod_append_bad('\nDISC_RECHECK discipline=%d garbage\n' % NID)
rc2, f2, o2 = gate(r14)
hit = [x for x in f2 if 'frozen-class row failed verification for a reason' in x]
m2 = re.search(r'C11 col7 machine-check: ok=(\d+) fail=(\d+) frozen-unverifiable=(\d+)', o2)
chk('N1 半截自述行 -> exit 1，点名 id %d，且 frozen 12->11 / fail 0->1' % NID,
    rc2 == 1 and len(hit) == 1 and ('id %d ' % NID) in hit[0]
    and m2 and m2.group(2) == '1' and m2.group(3) == '11',
    'exit=%d hits=%d %s' % (rc2, len(hit), (m2.group(0) if m2 else 'no-note')))
OUT['N1'] = {'exit': rc2, 'hits': len(hit), 'c11': (m2.group(0) if m2 else None)}

# N1c：成对反控 —— 同一个破坏，只把冻结分支换回 R58 的旧语义（入档即 declared），必须 exit 0。
# 用 R134 的整份快照做对照是不成立的：那份快照里 GATE_VER='R134'，与当前第 20 行（R135）冲突，
# 会先被 C10/C7d 抓住，测到的就不是冻结分支了（自错 S-236 记的就是这个：我第一次就是这么写的，
# N1c 报 exit=1 而失败项是 C7 id 1/2，与冻结分支无关 —— 那是一条零信息的反控）。
# 正确做法：只改一处语义，其余字节相同。
_hdrR, _rowsR = rd(pROWS)
_src = io.open(pGATE, encoding='utf-8', newline='').read()
_OLD_BRANCH = """        if _absent:
            c11_declared += 1
        else:"""
_NEW_BRANCH = """        if True:            # N1c 旧语义注入：入档即豁免，不看失败理由
            c11_declared += 1
        else:"""
_src_old = _src.replace(_OLD_BRANCH, _NEW_BRANCH)
assert _src_old != _src
io.open(pGATE, 'w', encoding='utf-8', newline='').write(_src_old)
rc2b, f2b, o2b = gate(r14)
m2b = re.search(r'C11 col7 machine-check: ok=(\d+) fail=(\d+) frozen-unverifiable=(\d+)', o2b)
chk('N1c 成对反控：同一破坏 + 旧分支语义 -> exit 0（修正方向可分辨，唯一变量是那一行）',
    rc2b == 0 and m2b and m2b.group(3) == '12',
    'exit=%d %s' % (rc2b, m2b.group(0) if m2b else 'no-note'))
OUT['N1c'] = {'exit_old_semantics': rc2b, 'c11': (m2b.group(0) if m2b else None)}
gate_patched_reset()
restore()

# ---------- N2：改 live 表第 6 列 ----------
hdrR, rowsR = rd(pROWS)
tgt = None
for rr in rowsR:
    if rr[0] == '1':
        rr[5] = rr[5].rstrip() + '|(?m:^)'
        tgt = rr[0]
        break
wr(pROWS, hdrR, rowsR)
rc3, f3, o3 = gate(r14)
hit3 = [x for x in f3 if 'C12b' in x]
chk('N2 改 live 第 6 列 -> exit 1 且报 C12b',
    rc3 == 1 and len(hit3) == 1, 'id=%s exit=%d C12b=%s' % (tgt, rc3, bool(hit3)))
OUT['N2'] = {'exit': rc3}
restore()

# ---------- N3：改冻结档第 4 列 ----------
hdrF, rowsF = rd(pFREEZE)
for ff in rowsF:
    if ff[0] == '1':
        ff[3] = 'grep=(?m)^\\*\\*\\u7eaa\\u5f8b'
        break
wr(pFREEZE, hdrF, rowsF)
rc4, f4, o4 = gate(r14)
hit4 = [x for x in f4 if 'C12b' in x]
chk('N3 改冻结档第 4 列 -> exit 1 且报 C12b（镜像另一方向）',
    rc4 == 1 and len(hit4) == 1, 'exit=%d C12b=%s' % (rc4, bool(hit4)))
OUT['N3'] = {'exit': rc4}
restore()

# ---------- N2b：连 C7d 常量与行指纹一起重钉，C12b 仍应 FAIL ----------
hdrR, rowsR = rd(pROWS)
for rr in rowsR:
    if rr[0] == '1':
        rr[5] = rr[5].rstrip() + '|(?m:^)'
        break
wr(pROWS, hdrR, rowsR)
# 重钉 C7d：常量 + 该行指纹
hdrR2, rowsR2 = rd(pROWS)
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rowsR2)
newsha = hashlib.sha256(blob.encode('utf-8')).hexdigest()
row1 = [r for r in rowsR2 if r[0] == '1'][0]
rowsha = hashlib.sha256(('%s\t%s\t%s' % (row1[0], row1[4].strip(), row1[5].strip()))
                        .encode('utf-8')).hexdigest()
src = io.open(pGATE, encoding='utf-8', newline='').read()
m = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", src)
oldsha = m.group(1)
m2 = re.search(r"'1': '([0-9a-f]{64})'", src)
oldrow = m2.group(1)
src2 = src.replace(oldsha, newsha).replace(oldrow, rowsha)
assert src2 != src and newsha in src2 and rowsha in src2
io.open(pGATE, 'w', encoding='utf-8', newline='').write(src2)
rc5, f5, o5 = gate(r14)
c7d_ok = bool(re.search(r'C7d product/expression fingerprint ok', o5))
hit5 = [x for x in f5 if 'C12b' in x]
chk('N2b 重钉 C7d 后：C7d 放行而 C12b 仍 FAIL（两个独立条件）',
    c7d_ok and len(hit5) == 1,
    'C7d_ok=%s C12b_hits=%d exit=%d' % (c7d_ok, len(hit5), rc5))
OUT['N2b'] = {'c7d_ok': c7d_ok, 'c12b_hits': len(hit5), 'exit': rc5}
gate_patched_reset()
restore()

# ---------- 复原后回到绿 ----------
rc6, f6, _ = gate(r14)
chk('P4 复原后 exit 0（沙箱无残留污染）', rc6 == 0, 'exit=%d fails=%s' % (rc6, f6[:2]))

_safe_rmtree(SB)
npass = sum(1 for _, c, _ in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
io.open(os.path.join(ROOT, '_r135', 'r135c_controls.json'), 'w', encoding='utf-8').write(
    __import__('json').dumps({'asserts': [{'name': n, 'ok': c, 'detail': d} for n, c, d in res],
                              'out': {k: str(v) for k, v in OUT.items()}},
                             ensure_ascii=False, indent=1))
sys.exit(0 if npass == len(res) else 1)
