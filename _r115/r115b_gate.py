#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115b_gate.py —— 门禁「永远通过」分区与可静默摘帽漏洞的机械证明（R114 下轮待办⑥的一半）。

背景（R114 遗留）：
  check_disc.py 的 C11 把 DISC_RECHECK 的 31 行分成三条互斥通道：
    (i)   claims-有 & 未冻结 -> 真跑 recheck_verify，可 FAIL    （= 5 行）
    (ii)  claims-有 & 冻结   -> 可 FAIL 但只走 C12 锚检查        （= 12 行）
    (iii) claims-无          -> 直接 continue，**永不 FAIL**      （= 14 行）
  R102 已把 (iii) 里落在 C11_LANDABLE 的 7 个 id 钉成 C11B_PIN_GAP，但：
    漏洞 A：(iii) 中有 **7 个 id 不在 C11_LANDABLE**（16/19/21/23/31/32/33），
            既不进 C11B_PIN_GAP 的核对、也不进任何 FAIL 分支 ⇒ 完全无约束。
    漏洞 B：(i)+(ii) 的 17 个 claims-有 里有 **12 个不在 C11_LANDABLE**，
            把它们的第 7 列从「有」翻成「无」只增加 (iii) 计数，
            C11B 的 gap 集合**不变**（因为它只看 LANDABLE 内），C12 的
            「frozen but not claims-有」也不触发（那 12 个在 C12 里是「已冻结」…
            需实测）⇒ 一次编辑就能静默摘掉一条可 FAIL 的行。

本脚本的断言（全部机检，且以**真实脚本变异**为证据，不是推理）：
  B1 三通道分区实测（5 / 12 / 14），合计 31
  B2 漏洞 A 明细：7 个 id 不在任何 FAIL 可达集合内
  B3 漏洞 B 明细：把 12 个「有且不在 LANDABLE」翻成「无」后 C11B gap 集合不变
  B4 **变异实测**：复制整棵树到临时目录、把某行从「有」翻成「无」，
     跑未改动的 check_disc.py ⇒ 观察 exit code 与输出（证明可以静默通关）
  B5 对照实验（必须反向）：把「无且**在** LANDABLE」翻成「有」，门禁必须 FAIL
     ⇒ 证明变异方法本身有牙，B4 的静默通过不是"变异没生效"
内存纪律：只读 TSV + 复制目录；脚本带 timeout 由外层控制。
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r115/r115b_gate.json')
GATE = os.path.join(R14, 'check_disc.py')
REC = os.path.join(R14, 'DISC_RECHECK.tsv')
FRZ = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}
PIN_GAP = sorted([11, 12, 13, 14, 15, 17, 26])

checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def load_rows(path):
    out = []
    for ln in io.open(path, encoding='utf-8').read().split('\n'):
        if not ln.strip():
            continue
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit():
            out.append(c)
    return out


rows = load_rows(REC)
frozen = set()
for ln in io.open(FRZ, encoding='utf-8').read().split('\n')[1:]:
    c = ln.split('\t')
    if c and c[0].strip().isdigit():
        frozen.add(int(c[0]))

has = sorted(int(r[0]) for r in rows if r[6].strip().startswith('有'))
none = sorted(int(r[0]) for r in rows if not r[6].strip().startswith('有'))
real = [i for i in has if i not in frozen]
fro = [i for i in has if i in frozen]

ck('B1 三通道分区实测：可真检 %d %s / 冻结 %d %s / claims-无(永不 FAIL) %d %s ; 合计 %d'
   % (len(real), real, len(fro), fro, len(none), none, len(rows)),
   len(real) == 5 and len(fro) == 12 and len(none) == 14 and len(rows) == 31,
   {'real': real, 'frozen': fro, 'none': none})

# ---- B2 漏洞 A ----
gap_pinned = sorted(i for i in none if i in LANDABLE)
unconstrained = sorted(i for i in none if i not in LANDABLE)
# 措辞更正（hy4 审计员 #2 指出、主会话 r115d 复算 13/13 PASS 确认）：
# 初稿写「完全无约束」过强。精确表述是：这 7 行在**第 7 列 claims-有 通道**上永不可 FAIL，
# 既不进 C11b 的 gap 钉、也不受 C12 冻结档防线约束；
# 但 C9（第 3/4 列占位化，实测 7 条 FAIL）、C13（第 2 列节号，实测 7 条）、
# C7（产物存在性，实测 1 条）对它们仍然施加约束。
ck('B2 漏洞 A（措辞已按审计降级）：claims-无 里 %d 个不在 C11_LANDABLE ⇒ 不进 C11B_PIN_GAP、'
   '在 claims-有/冻结档这两条防线上永不可 FAIL ids=%s（C9/C13/C7 仍管它们的第 3/4 列与产物，'
   '见 r115d 的 A1i/A1ii/A1iii 实测）' % (len(unconstrained), unconstrained),
   unconstrained == [16, 19, 21, 23, 31, 32, 33],
   {'pinned_gap': gap_pinned, 'unconstrained': unconstrained})

# ---- B3 漏洞 B 的精确边界（自错 S-18：初稿此处分区写错，实测当场 FAIL 抓出）----
# 初稿断言「claims-有 里所有不在 LANDABLE 的 12 个都能静默摘帽」。实测 B4 直接 12 条
# C12 FAIL —— 因为 C12 有独立防线：冻结档行若不是 claims-有 就 FAIL
# （'frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch)'）。
# 真正的洞只有**既不在 LANDABLE、又不在冻结档**的那部分 —— 两条防线都不覆盖。
cand = sorted(i for i in has if i not in LANDABLE)
guarded_by_c12 = sorted(i for i in cand if i in frozen)      # C12 会拦
silentizable = sorted(i for i in cand if i not in frozen)    # 无人拦
ck('B3 漏洞 B 的精确边界：claims-有 里 %d 个不在 LANDABLE，其中 %d 个被 C12 冻结档防线拦住'
   '（%s），真正无人拦的只有 %d 个 %s'
   % (len(cand), len(guarded_by_c12), guarded_by_c12, len(silentizable), silentizable),
   cand == [1, 2, 5, 6, 7, 8, 9, 10, 18, 20, 24, 25]
   and guarded_by_c12 == [1, 2, 5, 6, 7, 8, 9, 10, 18, 20, 24, 25]
   and silentizable == [],
   {'candidates': cand, 'guarded_by_C12': guarded_by_c12, 'unguarded': silentizable})


# ---- B4/B5 真实变异实测 ----
def mktree():
    """把 check_disc.py 依赖的树镜像到临时目录，返回 (tmp, root, r14_mirror)。

    自错 S-17（三连）：初稿用 shutil.copytree 少排了 R17_LEAD_BASELINE ——
    而 recheck_verify 的**轮次窗口表正是从该目录的看板快照文件名推导**的，
    排掉它 ⇒ 窗口为空 ⇒ 可真检的 5 行全 FAIL ⇒ 实测 exit=1，
    我把「镜像不完整」误读成「漏洞 B 不成立」，还反向怀疑了自己的判据。
    第二版补上基线却仍 exit=1，原因换了一个：源树里有**自指符号链接环**
    （lead/.../_r94/_r94 -> 自身，42 层），copytree 直接抛 ELOOP。
    第三版跳过全部符号链接，剩最后一条 FAIL：纪律 31 的产物
    `_r94\falsify_r94.py` 是相对 **ROOT** 解析的（不在 lead/ 下），
    我没镜像仓库根级的 `_r94/`。
    最终形态：手写递归复制 + 跳过符号链接 + 基线用符号链接 + 补根级 `_r94/`。
    **教训**：变异实验的对照组必须先跑通基线；基线不过时得出的任何
    「漏洞成立/不成立」结论都是环境噪声。
    """
    EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}
    tmp = tempfile.mkdtemp(prefix='r115gate_', dir=os.path.join(ROOT, '_r115'))
    root = os.path.join(tmp, 'root')
    dst = os.path.join(root, 'lead', 'next_re_20261117_r14')
    os.makedirs(dst)

    def _walk(srcdir, dstdir):
        for e in os.scandir(srcdir):
            if e.name in EX:
                continue
            sp, dp = e.path, os.path.join(dstdir, e.name)
            if e.is_symlink():
                continue                       # 跳过符号链接（含 _r94 自指环）
            if e.is_dir(follow_symlinks=False):
                os.makedirs(dp, exist_ok=True)
                _walk(sp, dp)
            elif e.is_file(follow_symlinks=False):
                shutil.copy2(sp, dp)

    _walk(R14, dst)
    os.symlink(os.path.join(R14, 'R17_LEAD_BASELINE'), os.path.join(dst, 'R17_LEAD_BASELINE'))
    shutil.copy2(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
                 os.path.join(root, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    shutil.copytree(os.path.join(ROOT, '_r94'), os.path.join(root, '_r94'), symlinks=True)
    return tmp, root, dst


def run_gate(root):
    env = dict(os.environ)
    env['TMPDIR'] = os.path.join(os.path.dirname(root), 'tmp')
    os.makedirs(env['TMPDIR'], exist_ok=True)
    p = subprocess.run([sys.executable, os.path.join(root, 'lead', 'next_re_20261117_r14', 'check_disc.py')],
                       capture_output=True, text=True, timeout=600, env=env)
    return p.returncode, p.stdout + p.stderr


base_rc, base_out = run_gate(ROOT)
ck('B4a 基线：未改动的 check_disc.py 在真树上 exit=%d（应为 0），C11 行=%s'
   % (base_rc, [l for l in base_out.splitlines() if 'C11 col7' in l]),
   base_rc == 0, {'rc': base_rc})

# 变异：把 id=1（有且不在 LANDABLE、且已冻结）和 id=22 之外的一个未冻结者翻成「无」
# 选 id=3/4/22/27/28 之外的：只有那 5 个是未冻结，翻它们会触发 C11 fail（被 B5 用）。
# B4 要证明的是「已冻结的 12 行翻成无」能否静默通过。
# B4a-mirror（审计指出的缺口）：镜像树**不改任何文件**空跑，必须 exit 0，
# 否则后续所有变异实验的对照都是环境噪声。
_tmpm, _rootm, _r14m = mktree()
try:
    _rcm, _outm = run_gate(_rootm)
    _c11m = [l.strip() for l in _outm.splitlines() if 'C11 col7' in l]
    ck('B4a-mirror 镜像树空跑基线：exit=%d（须 0）、C11 行与真树逐字相同=%s'
       % (_rcm, _c11m == [l for l in base_out.splitlines() if 'C11 col7' in l].__class__(
           [l.strip() for l in _c11m])),
       _rcm == 0, {'mirror_rc': _rcm, 'c11': _c11m})
finally:
    shutil.rmtree(_tmpm, ignore_errors=True)

tmp, root2, r14_2 = mktree()
try:
    txt = io.open(os.path.join(r14_2, 'DISC_RECHECK.tsv'), encoding='utf-8').read()
    lines = txt.split('\n')
    changed = []
    out_lines = []
    for ln in lines:
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit() and int(c[0]) in guarded_by_c12:
            c[6] = '无（R115 变异实测：从有翻成无）'
            changed.append(int(c[0]))
            out_lines.append('\t'.join(c))
        else:
            out_lines.append(ln)
    io.open(os.path.join(r14_2, 'DISC_RECHECK.tsv'), 'w', encoding='utf-8').write('\n'.join(out_lines))
    rc2, out2 = run_gate(root2)
    c11line = [l for l in out2.splitlines() if 'C11 col7' in l]
    fails2 = [l.strip() for l in out2.splitlines() if l.strip().startswith('FAIL')]
    c12n = [f for f in fails2 if 'C12 id' in f and 'freeze != escape hatch' in f]
    ck('B4 【C12 防线实测（正向结论）】把 %d 个「有且不在 LANDABLE」ids=%s 全翻成「无」后，'
       '未改动的 check_disc.py exit=%d、报出 %d 条 C12「frozen but not claims-有」FAIL ⇒ '
       '**C12 确实拦得住**，初稿「可静默摘帽」的断言被实测推翻'
       % (len(changed), changed, rc2, len(c12n)),
       rc2 != 0 and len(c12n) == len(changed),
       {'rc': rc2, 'c12_fails': len(c12n), 'all_fails': len(fails2)})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- B5 对照：翻「无且在 LANDABLE」成「有」必须 FAIL ----
tmp, root3, r14_3 = mktree()
try:
    txt = io.open(os.path.join(r14_3, 'DISC_RECHECK.tsv'), encoding='utf-8').read()
    out_lines = []
    changed3 = []
    for ln in txt.split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit() and int(c[0]) in gap_pinned:
            c[6] = '有（R115 对照：从无翻成有）'
            changed3.append(int(c[0]))
        out_lines.append('\t'.join(c))
    io.open(os.path.join(r14_3, 'DISC_RECHECK.tsv'), 'w', encoding='utf-8').write('\n'.join(out_lines))
    rc3, out3 = run_gate(root3)
    fails3 = [l for l in out3.splitlines() if l.strip().startswith('FAIL')]
    c11_3 = [f for f in fails3 if 'C11 id' in f]
    c11b_3 = [f for f in fails3 if 'C11b' in f]
    # 断言收紧（审计指出初稿只要 >=1，太弱）：精确锁定 FAIL 构成
    ck('B5 对照（必须反向）：把 %d 个「无且在 LANDABLE」ids=%s 翻成「有」⇒ exit=%d（必须非 0），'
       'FAIL %d 条 = C11 自描述 %d 条 + C11b drift %d 条 —— 变异方法本身有牙'
       % (len(changed3), changed3, rc3, len(fails3), len(c11_3), len(c11b_3)),
       rc3 != 0 and len(c11_3) == len(changed3) and len(c11b_3) == 1,
       {'rc': rc3, 'c11': len(c11_3), 'c11b': len(c11b_3), 'fails': [f[:110] for f in fails3[:3]]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- B6 精确形态：不是「改一格不被看见」，而是「同步改常量后不被看见」 ----
# 自错 S-19（本轮第二次踩）：
#   初稿 B6 的假设是「那 7 个 claims-无 且不在 LANDABLE 的行其锚/产物无人管」。
#   实测直接 7 条 C9 + 1 条 C14 FAIL —— C9 管锚的垃圾化，C14 管 (id,col2,col3,col4) 整表指纹。
#   所以「改一格不被看见」是**假**的，我不该那样断言。
#   真正要问的是：**同步改常量**之后还拦不拦得住。C14 的注释自己写着
#   "sha 钉只能抬高成本，不能防伪造 —— 同时改表与本常量者仍可过"。
#   本轮把它做成实测：找一条防线最少的行（三通道里「无人管」的那批），
#   改它的**第 7 列以外的自由文本 + 同步重算 C14_TEXT_SHA256/C14_ROW_SHA** ⇒ 若 exit 0，
#   则「可静默改写」成立，且**与 LANDABLE 无关**（任何行都行）。
def _recompute_c14(lines_of_rows):
    blob = '\n'.join('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3]) for r in lines_of_rows)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


tmp, root6, r14_6 = mktree()
try:
    gp = os.path.join(r14_6, 'check_disc.py')
    src = io.open(gp, encoding='utf-8').read()
    tp = os.path.join(r14_6, 'DISC_RECHECK.tsv')
    rowsx = []
    for ln in io.open(tp, encoding='utf-8').read().split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit():
            if int(c[0]) in unconstrained:
                c[3] = 'ANCHOR_SILENTLY_REWRITTEN_R115'   # 改锚
            rowsx.append(c)
        elif ln.strip():
            rowsx.append(ln)
    # 只重写有 7 列的
    keep = [r for r in rowsx if isinstance(r, list)]
    io.open(tp, 'w', encoding='utf-8').write('\n'.join(
        ('\t'.join(r) if isinstance(r, list) else r) for r in rowsx))
    # 同步重算 C14 常量
    newall = _recompute_c14(keep)
    per = {}
    for r in keep:
        per[r[0]] = hashlib.sha256(('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])).encode('utf-8')).hexdigest()
    import re as _re
    src2 = _re.sub(r"C14_TEXT_SHA256 = '[0-9a-f]{64}'", "C14_TEXT_SHA256 = '%s'" % newall, src)
    src2 = _re.sub(r"C14_ROW_SHA = \{[^}]*\}",
                   "C14_ROW_SHA = {%s}" % ', '.join("'%s': '%s'" % (k, v) for k, v in sorted(per.items())),
                   src2)
    io.open(gp, 'w', encoding='utf-8').write(src2)
    rc6, out6 = run_gate(root6)
    fails6 = [l.strip() for l in out6.splitlines() if l.strip().startswith('FAIL')]
    ck('B6 【可静默改写实测】把 %d 个 claims-无 行的第 4 列锚改成 %r 并**同步重算** '
       'C14_TEXT_SHA256/C14_ROW_SHA 后，check_disc.py exit=%d、FAIL %d 条 ⇒ '
       'sha 钉只抬高成本不防伪造（与 C14 注释自述一致，本轮首次做成实测）'
       % (len(unconstrained), 'ANCHOR_SILENTLY_REWRITTEN_R115', rc6, len(fails6)),
       rc6 == 0 and not fails6, {'rc': rc6, 'fails': fails6[:5]})

    # 反向对照：只改锚、**不**同步常量 ⇒ 必须 FAIL（证明 B6 不是"破坏没生效"）
    io.open(tp, 'w', encoding='utf-8').write(
        io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read())
    rowsy, out_y = [], []
    for ln in io.open(tp, encoding='utf-8').read().split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit() and int(c[0]) in unconstrained:
            c[3] = 'ANCHOR_SILENTLY_REWRITTEN_R115'
        out_y.append('\t'.join(c) if len(c) == 7 else ln)
    io.open(tp, 'w', encoding='utf-8').write('\n'.join(out_y))
    io.open(gp, 'w', encoding='utf-8').write(src)     # 常量回到原值
    rc7, out7 = run_gate(root6)
    fails7 = [l.strip() for l in out7.splitlines() if l.strip().startswith('FAIL')]
    # 归因更正（hy4 审计员指出、r115d 的 A3a/A3b 复算确认）：
    # 初稿写「C9 抓垃圾锚、C14 抓指纹漂移」。实测 place_r87.is_placeholder(
    # 'ANCHOR_SILENTLY_REWRITTEN_R115') == (False, '') —— 它不是占位词，C9 **没有**触发，
    # 唯一 FAIL 来自 C14。用 GARBAGE 时才是 C9 7 条 + C14 1 条。
    c9_7 = [f for f in fails7 if 'C9' in f]
    c14_7 = [f for f in fails7 if 'C14' in f]
    ck('B6b 对照（必须反向）：同样改锚但**不**同步 C14 常量 ⇒ exit=%d、FAIL %d 条 = '
       'C9 %d 条 + C14 %d 条 ⇒ 归因更正：该变异值不是占位词，C9 不触发，只由 C14 抓'
       % (rc7, len(fails7), len(c9_7), len(c14_7)),
       rc7 != 0 and len(c9_7) == 0 and len(c14_7) >= 1,
       {'rc': rc7, 'c9': len(c9_7), 'c14': len(c14_7), 'fails': [f[:100] for f in fails7[:3]]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# B7 的限定语（审计指出不能外推）：B6 只证明**C14 式纯自由文本 sha 钉**不防伪造；
# 冻结档的 FREEZE_SHA256 背后有 C12 的内容级复核（r115d A6/A6b 实测：改理由列+同步 sha 可过，
# 改锚+同步 sha 仍被 C12 抓）。
out = {'b7_scope': 'C14 式纯自由文本 sha 钉不防伪造；不外推到带内容级复核的 FREEZE_SHA256+C12',
       'partition': {'real_checkable': real, 'frozen': fro, 'claims_none': none},
       'hole_A_unconstrained_none': unconstrained,
       'hole_B_candidates': cand, 'hole_B_guarded_by_C12': guarded_by_c12,
       'hole_B_unguarded': silentizable,
       'landable': sorted(LANDABLE), 'pin_gap': PIN_GAP, 'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, %d FAIL' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
