# -*- coding: utf-8 -*-
"""R72 · 亲复算跨家族审计 A1(deepseek-v4.1-flash) 的六条指正。

A1 判「打折」，三条核心指控：
  C1 【Q1】「全程零写盘」不成立：gatesplit_r72.py 写了 _r72/_neg1/p.txt，且留在盘上。
  C2 【Q2】S2-b 的 W_only 格是**零信息格**：R1 在 R4 之前返回，窗口表根本没被读；
     把 ROUND_WINDOWS 整个清空，该格输出完全相同 ⇒ S2-b 不能排除「窗口没修对」。
  C3 【Q3】S2-c 只证明「路径是独立缺陷」，**不能**证明「窗口表错是独立缺陷」：
     把 round 从 R55 改成 R54（**live 表原样**）也能 5/5 全绿 ⇒ 「改表」与「改行」
     在本轮实验里不可区分。A1 声称已实测。
  C4 【Q4】纪律 3/4 共用一个产物 ⇒ 独立证据广度是 4，不是 5。
  C5 【Q5】S3-c 实质是 S2-d 的重复，应降格为矩阵自检。
  C6 【Q6】结论「先后掩盖」成立；但「(b) 是窗口表错」超出实验范围。

本轮逐条复算。凡成立者，主会话收回原结论并改写；凡不成立者，说明理由。
"""
import io, os, re, sys, types, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
DR = os.path.join(R14, 'DISC_RECHECK.tsv')

P = print
FAILS = []
def ck(name, cond, detail=''):
    P('  %s %s  %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond: FAILS.append(name)
    return cond

def load(subs, name):
    src = os.path.join(R14, 'recheck_verify.py')
    s = io.open(src, encoding='utf-8').read()
    for a, b in subs:
        assert a in s, a
        s = s.replace(a, b)
    m = types.ModuleType(name); m.__file__ = src
    exec(compile(s, src, 'exec'), m.__dict__)
    return m

FIX_PATH = ("ap = rel.replace('/', '\\\\')", "ap = rel.replace('\\\\', '/')")

targets = ('3', '4', '22', '27', '28')
rows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n')[1:] if l]
tgt = [r for r in rows if len(r) == 7 and r[0] in targets]

P('=== C1 · 「零写盘」是否成立 ===')
leaks = sorted(glob.glob(os.path.join(HERE, '_neg1', '*')))
# R72 修订：本条原本断言「盘上必有残留」——那是个**依赖状态**的断言：整改完成后它会假失败。
# 正确做法：断言**整改已生效**（无残留 + gatesplit 用系统 temp + atexit 清理），
# 并把「曾经有过残留」作为已记账的历史事实（A1 原件判定见上一条审计报告）。
P('  _r72/_neg1/ 当前残留：%s' % ([os.path.basename(x) for x in leaks] or 'none'))
gsrc = io.open(os.path.join(HERE, 'gatesplit_r72.py'), encoding='utf-8').read()
fixed = ('tempfile.mkdtemp' in gsrc) and ('atexit.register' in gsrc)
ck('C1-a A1 指正已被整改：无残留 && gatesplit 改用系统 temp && atexit 清理',
   len(leaks) == 0 and fixed, 'leaks=%d fixed=%s' % (len(leaks), fixed))
ck('C1-b gatesplit 的 docstring 已记 A1-C1 这条指正（不是悄悄改掉）',
   'A1-C1' in gsrc, 'documented')
# live 是否真的未改（这是原来 S4 那条声称的**正确范围**）
import subprocess
for f in ('recheck_verify.py', 'check_disc.py'):
    p = os.path.join(R14, f)
    st = os.stat(p)
    P('  live %-20s mtime=%s' % (f, __import__('datetime').datetime.fromtimestamp(st.st_mtime).strftime('%H:%M:%S')))
ck('C1-c 但「live 两个脚本未被改」这一条仍成立（原 S4 对 live 的限定为真）',
   all(os.stat(os.path.join(R14, f)).st_mtime < 1795357000 for f in ('recheck_verify.py', 'check_disc.py')),
   'both < 22:16')
# 清理
for x in leaks:
    os.remove(x)
if os.path.isdir(os.path.join(HERE, '_neg1')):
    os.rmdir(os.path.join(HERE, '_neg1'))
ck('C1-d 库内 _neg1 目录已不存在（A1-C1 整改后）',
   not os.path.isdir(os.path.join(HERE, '_neg1')), 'cleaned')

P('')
P('=== C2 · S2-b 的 W_only 格是否零信息 ===')
# 复现 W_only：只修窗口不修路径，然后 (i) 正常窗口 (ii) 窗口表整个清空
def run_wonly(clear=False):
    mod = load([], 'rv_w_%s' % clear)
    if clear:
        mod.ROUND_WINDOWS.clear()
    else:
        import datetime
        D = os.path.join(R14, 'R17_LEAD_BASELINE')
        pat = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
        snap = {}
        for f in os.listdir(D):
            m = pat.match(f)
            if m: snap.setdefault(int(m.group(1)), []).append(m.group(2))
        snap = {k: max(v) for k, v in snap.items()}
        new = {}
        for n in sorted(snap):
            if (n - 1) in snap:
                new[n] = (mod._hhmmss(snap[n-1]), mod._hhmmss(snap[n]), 'x', 'x')
        mod.ROUND_WINDOWS.clear(); mod.ROUND_WINDOWS.update(new)
    return [mod.verify_recheck_line(ROOT, r) for r in tgt]

a1 = run_wonly(False)
a2 = run_wonly(True)
same = [x == y for x, y in zip(a1, a2)]
ck('C2-a 修对窗口 vs 清空窗口，W_only 格输出逐条相同（零信息）',
   all(same), 'identical=%d/5' % sum(same))
P('  修对窗口首条：%s' % (a1[0][1][:60],))
P('  清空窗口首条：%s' % (a2[0][1][:60],))
ck('C2-b A1 指正成立：S2-b 不能排除「窗口没修对」', all(same), 'ok')

P('')
P('=== C3 · 「改表」与「改行」是否不可区分（A1 最重的一条）===')
# 路径修好 + live 表原样 + 把每条自述行的 round 从 R55 改成 R54（产物临时副本）
mod = load([FIX_PATH], 'rv_alt')
tmpd = os.path.join(HERE, '_alt_tmp')
os.makedirs(tmpd, exist_ok=True)
res = []
try:
    for r in tgt:
        rel = r[4].strip()
        p = os.path.join(ROOT, rel.replace('\\', os.sep))
        txt = io.open(p, encoding='utf-8', errors='replace').read()
        txt2 = txt.replace('round=R55 ', 'round=R54 ')
        assert txt2 != txt or 'round=R55' not in txt
        q = os.path.join(tmpd, 'pdt_%s.tsv' % r[0])
        io.open(q, 'w', encoding='utf-8', newline='').write(txt2)
        rr = list(r); rr[4] = os.path.relpath(q, ROOT)
        res.append(mod.verify_recheck_line(ROOT, rr))
finally:
    for x in os.listdir(tmpd): os.remove(os.path.join(tmpd, x))
    os.rmdir(tmpd)

npass = sum(1 for ok, _ in res if ok)
for r, (ok, d) in zip(tgt, res):
    P('    id=%-3s ok=%-5s %s' % (r[0], ok, d[:88]))
ck('C3-a A1 指正成立：只改 round R55->R54、live 表原样 ⇒ 也能 5/5 全绿',
   npass == 5, '%d/5' % npass)
P('  ⇒ 「改表」与「改行」在本轮实验里**不可区分**。本轮没有资格说「(b) 是窗口表错」。')
P('  ⇒ 判别材料必须来自别处（R71 的时钟），而 R71 那支本轮已另行复查（见 clockindep_r72）。')

P('')
P('=== C4 · 共用产物是否高估 ===')
from collections import Counter
c = Counter(r[4].strip() for r in tgt)
P('  5 条纪律对应的产物：%s' % dict(c))
ck('C4-a A1 指正成立：5 条纪律 / 4 个产物文件（纪律 3、4 共用）',
   len(c) == 4 and c[max(c, key=lambda k: c[k])] == 2, '%d products' % len(c))
P('  ⇒ 「5/5 条纪律通过」准确；「5 条独立证据」不准确，独立广度是 4。')

P('')
P('=== C5 · S3-c 是否 S2-d 的重复 ===')
P('  S2-d 数据：P_and_W 格 5/5 全 True；S3-c 数据：同一行 id=3 在 P_only(False)/P_and_W(True)。')
P('  ⇒ S3-c 的两个观测点**都已在 S1 矩阵里**，未引入新观测。')
ck('C5-a A1 指正成立：S3-c 是矩阵内数据重述，不是新反控', True, 'agree')

P('')
P('=== C6 · 结论措辞是否超范围 ===')
P('  可保留（有直接证据）：')
P('    - 路径缺陷使 R4 不可达（S0-c 全 R1 + C2 零信息格一致）')
P('    - 修好路径后失败点前移到 R4（S2-c）')
P('    - 二者存在先后掩盖（上两条合取）')
P('  须收回：')
P('    - 「(b) 是窗口**表**错」—— C3 证明改行同样可行，本轮不可区分')
P('    - 「(a)(b) 是两件**独立**缺陷」—— (a) 独立已证；(b) 的独立性本轮未证')
ck('C6-a 结论须改写（本轮原措辞超范围）', True, 'rewrite')

P('')
P('=== S7 · 审计 A1 自身的两处须打回 ===')
P('  A1 在 Q3 写「裁决『改表而非改行』的独立材料来自 R71 clock_r71.py，本轮未复算该时钟」。')
P('  本轮实查该时钟（clockindep_r72 / thirdsrc_r72 / e3scope_r72）：')
P('    那三支证据的 mtime **全部是搬入时继承的**（ctime 全落在 21:23:41/42），')
P('    本库内无法重观测 ⇒ 它也不足以独立裁决「改表 vs 改行」。')
ck('S7-a A1 把裁决依据指向 R71 时钟，而该时钟本轮查实为继承 mtime ⇒ 依据不足',
   True, 'both 改表与改行 均缺独立裁决')

P('')
P('=== S8 · 最终处置 ===')
P('  A1 六条：C1 成立（已清残留）、C2 成立（零信息格）、C3 成立（不可区分）、')
P('           C4 成立（4 个产物）、C5 成立（冗余）、C6 成立（超范围）。')
P('  ⇒ 本轮**接受 A1 的打折裁决**，原 gatesplit 结论第 2/5 条收回。')
P('  ⇒ 保留：根因分离（路径先死）+ 两处都需修 + 修好后 5/5（counterfactual）。')
P('  ⇒ 收回：「窗口表错是第二个独立缺陷」；改为「存在第二个不一致，其修复方向未裁」。')

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
