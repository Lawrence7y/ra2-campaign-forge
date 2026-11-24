# -*- coding: utf-8 -*-
"""R72 · 门禁 5 条 C11 FAIL 的根因分离实测（只读 live，全部改动在内存/sandbox）。

R71 §CY10⑤ 声称根因是「两件事」：(a) live recheck_verify.py 在 Linux 上
rel.replace('/','\\\\') 反向；(b) 窗口应取修正口径。但没验证：
  Q1 live 到底死在哪一条前置检查上？（若 R1 先死，R4 的窗口对错根本测不到 ⇒ 两者有掩盖顺序）
  Q2 两处都修后，5 条是否真的全过？（counterfactual，不落地）
  Q3 单修 (b) 不修 (a) 会怎样？单修 (a) 不修 (b) 会怎样？（2x2 矩阵，分离贡献）
  Q4 变绿是否等价于「判据对」？（R71 T4 已证 selftest 是自证循环 ⇒ 须显式声明边界）

纪律：不写 live 任何文件。recheck_verify.py / check_disc.py 均以源码替换后在内存 exec。

【R72 审计后修订 · 由跨家族审计 A1(deepseek-v4.1-flash) 判「打折」，主会话逐条复算全部成立】
  A1-C1「全程零写盘」不成立：本脚本曾把 _r72/_neg1/p.txt 留在盘上（含一条 DISC_RECHECK 行）。
         已改为 finally 清理；对 live 的「一字未改」仍成立（两个 live 脚本 mtime 早于运行）。
  A1-C2 S2-b 的 W_only 格是**零信息格**：R1 在 R4 之前返回，窗口表未被读；
         把 ROUND_WINDOWS 整个清空，该格输出逐条相同（复算见 recheckA1_r72.py C2）。
         ⇒ S2-b **不能**排除「窗口没修对」。
  A1-C3 S2-c 只证「路径是独立缺陷」，**不证**「窗口表错是独立缺陷」：
         只把 round 从 R55 改成 R54、live 表原样，同样 5/5 全绿（复算 C3）。
         ⇒ 「改表」与「改行」在本轮实验里**不可区分**。
  ⇒ 因此本轮**收回**「(b) 是窗口表错」「(a)(b) 是两件独立缺陷」。
    保留：路径缺陷使 R4 不可达（C2 零信息格佐证）、修好路径后前移到 R4、两处都需修、
          修好后 5/5（counterfactual）。「第二个不一致的修复方向」本轮**未裁**。
"""
import io, os, re, sys, types, hashlib, tempfile, shutil, atexit

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

DR = os.path.join(R14, 'DISC_RECHECK.tsv')
TARGETS = ('3', '4', '22', '27', '28')

P = print
FAILS = []
def ck(name, cond, detail=''):
    P('  %s %s  %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond: FAILS.append(name)
    return cond

def load(src_path, subs, name):
    s = io.open(src_path, encoding='utf-8').read()
    for a, b in subs:
        if a not in s:
            raise AssertionError('PATCH ANCHOR MISSING in %s: %r' % (name, a))
        s = s.replace(a, b)
    m = types.ModuleType(name); m.__file__ = src_path
    exec(compile(s, src_path, 'exec'), m.__dict__)
    return m

# ---- live 基线：原样加载，必须复现 R71 记的失败形态 ----
P('=== S0 · live 原样（不修任何东西）===')
rv_live = load(os.path.join(R14, 'recheck_verify.py'), [], 'rv_live')
rows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n')[1:] if l]
tgt = [r for r in rows if len(r) == 7 and r[0] in TARGETS]
ck('S0-a 命中 5 条目标行', len(tgt) == 5, 'got %d' % len(tgt))

base = {}
for r in tgt:
    ok, d = rv_live.verify_recheck_line(ROOT, r)
    base[r[0]] = (ok, d)
    P('    id=%-3s ok=%-5s %s' % (r[0], ok, d[:95]))

# Q1：live 死在哪一条？必须全部死在 R1（路径），且 reason 文本可枚举
all_r1 = all((not ok) and d.startswith('R1 product file missing') for ok, d in base.values())
ck('S0-b live 5/5 全部死在 R1（路径），不是 R4（窗口）', all_r1,
   '首个 reason=%s' % base['3'][1][:45])
ck('S0-c 反控 · live 的失败 reason 里不含 R4/window（证 R4 分支未被触达）',
   all('R4' not in d and 'window' not in d for _, d in base.values()),
   'reasons=%s' % set(d.split(':')[0] for _, d in base.values()))

# ---- 四种组合 ----
FIX_PATH = ("ap = rel.replace('/', '\\\\')", "ap = rel.replace('\\\\', '/')")
# 修窗口：把 _ROUND_ROWS 里 r56/r57 的来源列与端点改成 R71 算出的修正值（D5 建议值）
CUR_ROWS_SRC = None
def fix_window(mod):
    """按 R71 D5 建议值重写 ROUND_WINDOWS：row N 窗口 = [before_r(N-1), before_rN)。"""
    import datetime
    D = os.path.join(R14, 'R17_LEAD_BASELINE')
    pat = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
    snap = {}
    for f in os.listdir(D):
        m = pat.match(f)
        if m: snap.setdefault(int(m.group(1)), []).append(m.group(2))
    # 同轮多份取最晚（R71 默认口径）
    snap = {k: max(v) for k, v in snap.items()}
    new = {}
    for n in sorted(snap):
        if (n - 1) in snap:
            new[n] = (mod._hhmmss(snap[n - 1]), mod._hhmmss(snap[n]), 'fix', 'fix')
    mod.ROUND_WINDOWS.clear()
    mod.ROUND_WINDOWS.update(new)
    return new

def run_matrix(fix_p, fix_w, tag):
    subs = [FIX_PATH] if fix_p else []
    mod = load(os.path.join(R14, 'recheck_verify.py'), subs, 'rv_%s' % tag)
    nwin = None
    if fix_w:
        nwin = fix_window(mod)
    out = {}
    for r in tgt:
        ok, d = mod.verify_recheck_line(ROOT, r)
        out[r[0]] = (ok, d)
    return out, nwin

P('')
P('=== S1 · 2x2 分离矩阵（只读 counterfactual，不落地）===')
matrix = {}
for fix_p, fix_w, tag in ((False, True, 'W_only'), (True, False, 'P_only'), (True, True, 'P_and_W')):
    out, nwin = run_matrix(fix_p, fix_w, tag)
    npass = sum(1 for ok, _ in out.values() if ok)
    matrix[tag] = (out, nwin, npass)
    P('  -- %-8s fix_path=%-5s fix_window=%-5s  pass=%d/5' % (tag, fix_p, fix_w, npass))
    for k in TARGETS:
        ok, d = out[k]
        P('       id=%-3s ok=%-5s %s' % (k, ok, d[:88]))

P('')
P('=== S2 · 分离结论（每处修法各自的贡献）===')
n_base = sum(1 for ok, _ in base.values() if ok)
ck('S2-a 基线 pass=0/5', n_base == 0, '0/5')
ck('S2-b 只修窗口不修路径 ⇒ 仍 0/5（窗口修了也测不到，因为死在路径）',
   matrix['W_only'][2] == 0, '%d/5' % matrix['W_only'][2])
# 只修路径：必须仍 5 FAIL，但失败点必须前移到 R4
p_only = matrix['P_only'][0]
p_only_r4 = all((not ok) and d.startswith('R4 at outside') for ok, d in p_only.values())
ck('S2-c 只修路径 ⇒ 仍 0/5，但失败点前移到 R4（证明 (a)(b) 确为两件独立缺陷）',
   matrix['P_only'][2] == 0 and p_only_r4,
   '%d/5, all_R4=%s' % (matrix['P_only'][2], p_only_r4))
ck('S2-d 两处都修 ⇒ 5/5（counterfactual，未落地）',
   matrix['P_and_W'][2] == 5, '%d/5' % matrix['P_and_W'][2])
P('  ⚠ 审计后修订：S2-b 是**零信息格**（R1 先于 R4 返回，窗口未被读），')
P('    因此它**不能**证明「窗口没修对」；S2-c 只证「路径是独立缺陷」，')
P('    不证「窗口表错是独立缺陷」—— 只改 round R55->R54、live 表原样同样 5/5（见 recheckA1_r72 C3）。')

P('')
P('=== S3 · 反控（防「恒真」与「测了个错的」）===')
# 反控 1：只修路径时，把 at 改成**晚于立条但在 R55 窗口外**的时刻 ⇒ 必须 FAIL 在 R4
# （R72 自错修正：初版取 03:00:00，先死在 R3 而非 R4 —— 与 R71 §CY9② 同族的「反控设计错」，
#  取时刻必须同时满足「晚于 establish」与「落在标称 round 窗口外」，只满足后者测不到 R4 分支。）
mod = load(os.path.join(R14, 'recheck_verify.py'), [FIX_PATH], 'rv_neg1')
r0 = list(tgt[0])
tmpdir = tempfile.mkdtemp(prefix='_r72neg_')      # 本轮修：改到系统临时目录
prodfile = os.path.join(tmpdir, 'p.txt')
atexit.register(lambda d=tmpdir: shutil.rmtree(d, ignore_errors=True))   # 真清理（A1-C1 整改）
with io.open(prodfile, 'w', encoding='utf-8') as f:
    f.write('DISC_RECHECK discipline=3 round=R55 at=2026-11-22T17:50:00+08:00 '
            'anchors=sha256:%s conclusion=PASS\n'
            % hashlib.sha256(r0[3].encode('utf-8')).hexdigest())
rneg = list(r0); rneg[4] = os.path.relpath(prodfile, ROOT)
ok, d = mod.verify_recheck_line(ROOT, rneg)
ck('S3-a 反控 · 17:50:00 标 R55（晚于立条、在 R55 窗口外）⇒ 必须 FAIL 在 R4',
   (not ok) and d.startswith('R4'), '%s' % d[:70])
# S3-a2 对照：取一个**确实落在 CUR 表 r56 窗口内**的时刻（CUR r56 = [174645,174854) =
# 17:46:45..17:48:54，故取 17:47:30 —— 不可取 17:50:00，那在 CUR 下同样落在窗口外，
# 会把「对照」写成恒 FAIL。这是本轮我第二次犯「期望值写坏」，如实记入日志。）
with io.open(prodfile, 'w', encoding='utf-8') as f:
    f.write('DISC_RECHECK discipline=3 round=R56 at=2026-11-22T17:47:30+08:00 '
            'anchors=sha256:%s conclusion=PASS\n'
            % hashlib.sha256(r0[3].encode('utf-8')).hexdigest())
ok2, d2 = mod.verify_recheck_line(ROOT, rneg)
ck('S3-a2 对照 · 17:47:30 标 R56（该时刻确实在 CUR r56 窗口内）⇒ 必须 PASS（证 S3-a 非恒 FAIL）',
   ok2, '%s' % d2[:80])

# 反控 2：两处都修时，round 标 R54（at 落在 R55 窗口）⇒ 必须 FAIL
mod2 = load(os.path.join(R14, 'recheck_verify.py'), [FIX_PATH], 'rv_neg2')
fix_window(mod2)
with io.open(prodfile, 'w', encoding='utf-8') as f:
    f.write('DISC_RECHECK discipline=3 round=R54 at=2026-11-22T17:39:19+08:00 '
            'anchors=sha256:%s conclusion=PASS\n'
            % hashlib.sha256(r0[3].encode('utf-8')).hexdigest())
ok, d = mod2.verify_recheck_line(ROOT, rneg)
ck('S3-b 反控 · FIX 口径下 round 标 R54 而 at 在 R55 ⇒ 必须 FAIL',
   (not ok) and d.startswith('R4'), '%s' % d[:70])

# 反控 3：EXACT 对照 —— 同一产物、同一行，只把 round 从 R55 换成 R55（原样）在两口径下结果必须不同
mod3 = load(os.path.join(R14, 'recheck_verify.py'), [FIX_PATH], 'rv_neg3')
cur_ok, _ = mod3.verify_recheck_line(ROOT, tgt[0])
fix_window(mod3)
fix_ok, _ = mod3.verify_recheck_line(ROOT, tgt[0])
ck('S3-c 关键对照 · 同一条行，CUR 判 FAIL / FIX 判 PASS（两表必须不同，证非恒真）',
   cur_ok != fix_ok, 'cur=%s fix=%s' % (cur_ok, fix_ok))

P('')
P('=== S4 · 边界声明（必须写进结论）===')
P('  * 本轮 S1/S2 是内存 counterfactual：live 的 recheck_verify.py 与 _ROUND_ROWS 一个字节未改。')
P('    但「全程零写盘」**不成立** —— 本脚本写过临时产物（现已改到系统 temp 并在 finally 清理）。')
P('  * 「两处都修 ⇒ 5/5」只证明这 5 条在两种修法下都能变绿；')
P('    它不能区分是「改表」还是「改行」。要裁这一条需要不依赖快照的时刻材料，')
P('    而本轮已查实 R71 那支时钟的 mtime 全部是搬入继承的（见 clockindep_r72），同样不足以裁决。')
P('  * 因此：不改表、不改 live、不改 DISC_RECHECK.tsv。这一条属判据变更，须单独一卡。')

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
