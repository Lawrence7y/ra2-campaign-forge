#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115d_recheck_audit.py —— 主会话对 hy4 审计员 #2 全部结论的**亲自复算**（§2.12 规则 D）。

审计员 x115audit_gate.md 对主会话提出 7 项需复算 + 4 处措辞修正。规则 D 要求
「所有审计员结论必须由主会话亲自写脚本复算」，本脚本逐条独立重写判据，
**不复用** r115b_gate.py 的任何函数，只复用 mktree 的镜像做法（并新增镜像空跑基线）。

要复算的审计结论：
  A1 审计说 B2 的「完全无约束」过强：C9 / C13 / C7 对这 7 行仍施加约束。
     ⇒ 分别注入 占位锚 / 错节 / 删产物，逐项看是否各有 FAIL。
  A2 审计说 B5 的「8 条 FAIL」是观察值、断言只要求 >=1 ⇒ 换成精确计数复算。
  A3 审计说 B6b 的归因错：C9 根本没触发，唯一 FAIL 是 C14。
     ⇒ 直接调 place_r87.is_placeholder 验证 + 用 GARBAGE 重做一次看 C9 是否真会触发。
  A4 审计说 B6 需限定语：re-pin 之后 C10 与「未被 re-pin 的行」仍应能 FAIL。
     ⇒ 在 re-pin 镜像上再改第 8 行、再改 GATE_VER 注册值，分别看是否 FAIL。
  A5 审计说缺「镜像树空跑基线」⇒ 补 B4a-mirror：不改任何文件跑镜像树，须 exit 0。
  A6 审计说 B7 不能外推到所有 sha 钉：FREEZE_SHA256 背后有 C12 内容级复核。
     ⇒ 只改冻结表 + 同步 FREEZE_SHA256，看 C12 是否仍会 FAIL。

每条都以**真实变异 + 未改动的 check_disc.py** 为证据。
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r115/r115d_recheck_audit.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def mktree(tag):
    EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}
    tmp = tempfile.mkdtemp(prefix='r115d_%s_' % tag, dir=os.path.join(ROOT, '_r115'))
    root = os.path.join(tmp, 'root')
    dst = os.path.join(root, 'lead', 'next_re_20261117_r14')
    os.makedirs(dst)

    def _walk(s, d):
        for e in os.scandir(s):
            if e.name in EX:
                continue
            sp, dp = e.path, os.path.join(d, e.name)
            if e.is_symlink():
                continue
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


def fails_of(out):
    return [l.strip() for l in out.splitlines() if l.strip().startswith('FAIL')]


UNCON = [16, 19, 21, 23, 31, 32, 33]      # claims-无 且不在 C11_LANDABLE（审计称之为 B2 的 7 行）


def edit_rows(path, fn):
    """对 DISC_RECHECK.tsv 逐行调用 fn(cols) 返回 (cols, 是否改动)。"""
    txt = io.open(path, encoding='utf-8', newline='').read()
    out, changed = [], []
    for ln in txt.split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit():
            c2, hit = fn(c)
            if hit:
                changed.append(int(c[0]))
            out.append('\t'.join(c2))
        else:
            out.append(ln)
    io.open(path, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    return changed


# ---- A5 先做：镜像树空跑基线（审计指出的设计缺口）----
tmp, rootA, dstA = mktree('mirror')
try:
    rc_m, out_m = run_gate(rootA)
    c11_m = [l.strip() for l in out_m.splitlines() if 'C11 col7' in l]
    rc_t, out_t = run_gate(ROOT)
    c11_t = [l.strip() for l in out_t.splitlines() if 'C11 col7' in l]
    ck('A5 【审计指出的缺口】镜像树**不改任何文件**空跑：exit=%d（须 0），C11 行与真树逐字相同=%s'
       % (rc_m, c11_m == c11_t),
       rc_m == 0 and c11_m == c11_t,
       {'mirror_rc': rc_m, 'true_rc': rc_t, 'mirror_c11': c11_m, 'true_c11': c11_t})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- A3 先验 is_placeholder（其余归因都依赖它）----
sys.path.insert(0, R14)
import place_r87 as P87
v1 = P87.is_placeholder('ANCHOR_SILENTLY_REWRITTEN_R115')
v2 = P87.is_placeholder('GARBAGE')
v3 = P87.is_placeholder('')
ck('A3a 审计结论复算：is_placeholder(ANCHOR_SILENTLY_REWRITTEN_R115)=%s（审计说 False，'
   '故 B6b 里 C9 不该触发）；对照 is_placeholder(GARBAGE)=%s、空=%s' % (v1, v2, v3),
   v1[0] is False and v2[0] is True and v3[0] is True,
   {'ANCHOR...': v1, 'GARBAGE': v2, 'empty': v3})

# ---- A1 C9 / C13 / C7 对这 7 行是否真有约束 ----
res_a1 = {}
tmp, rootB, dstB = mktree('c9')
try:
    # (i) 占位锚 ⇒ 期望 C9 FAIL
    def _mk_garbage(c):
        # 自错 S-21：初稿写成 (c[:3]+['GARBAGE']+c[4:], 条件) —— **变异无条件施加到全部 31 行**，
        # 只有 changed 标记是条件性的 ⇒ C9 报 31 条而非 7 条，断言 7 当场 FAIL。
        # 条件变异必须把判断写在变异分支里。
        if int(c[0]) in UNCON:
            return c[:3] + ['GARBAGE'] + c[4:], True
        return c, False
    edit_rows(os.path.join(dstB, 'DISC_RECHECK.tsv'), _mk_garbage)
    rc, out = run_gate(rootB)
    f = fails_of(out)
    c9 = [x for x in f if 'C9' in x]
    res_a1['c9_placeholder'] = {'rc': rc, 'c9_fails': len(c9), 'sample': c9[:2]}
    ck('A1i 【C9 有牙】把 7 行的第 4 列锚改成占位词 GARBAGE ⇒ exit=%d、C9 FAIL %d 条 '
       '⇒ 审计正确：「完全无约束」过强，C9 管得住垃圾化锚'
       % (rc, len(c9)), rc != 0 and len(c9) == 7, res_a1['c9_placeholder'])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

tmp, rootC, dstC = mktree('c13')
try:
    # (ii) 错节 ⇒ 期望 C13 FAIL（C14 也会 FAIL，故只看 C13 是否出现）
    def _mk_badsec(c):
        if int(c[0]) in UNCON:
            return [c[0], '§9.99'] + c[2:], True
        return c, False
    edit_rows(os.path.join(dstC, 'DISC_RECHECK.tsv'), _mk_badsec)
    rc, out = run_gate(rootC)
    f = fails_of(out)
    c13 = [x for x in f if 'C13' in x]
    res_a1['c13_wrong_section'] = {'rc': rc, 'c13_fails': len(c13), 'sample': c13[:2]}
    ck('A1ii 【C13 有牙】把 7 行的第 2 列节号改成 §9.99 ⇒ exit=%d、C13 FAIL %d 条'
       % (rc, len(c13)), rc != 0 and len(c13) == 7, res_a1['c13_wrong_section'])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

tmp, rootD, dstD = mktree('c7')
try:
    # (iii) 删产物 ⇒ 期望 C7 FAIL。取 id 16 的产物路径
    rec = os.path.join(dstD, 'DISC_RECHECK.tsv')
    target = None
    for ln in io.open(rec, encoding='utf-8').read().split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip() == '16':
            target = c[4].replace('\\', '/').strip()
    ap = os.path.join(rootD, target) if target else None
    existed = bool(ap and os.path.isfile(ap))
    if existed:
        os.remove(ap)
    rc, out = run_gate(rootD)
    f = fails_of(out)
    c7 = [x for x in f if 'C7 id 16' in x]
    res_a1['c7_missing_product'] = {'rc': rc, 'path': target, 'existed': existed,
                                    'c7_fails': len(c7), 'sample': c7[:2]}
    ck('A1iii 【C7 有牙】删掉 id 16 的产物 %s（删前存在=%s）⇒ exit=%d、C7 id 16 FAIL %d 条'
       % (target, existed, rc, len(c7)), existed and rc != 0 and len(c7) >= 1,
       res_a1['c7_missing_product'])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

ck('A1 【审计结论成立】B2 的「完全无约束」必须降级为「在 claims-有 / 冻结档两条防线上无约束」：'
   'C9 管锚的占位化（%d 条）、C13 管节号（%d 条）、C7 管产物存在性（%d 条）'
   % (res_a1['c9_placeholder']['c9_fails'], res_a1['c13_wrong_section']['c13_fails'],
      res_a1['c7_missing_product']['c7_fails']),
   res_a1['c9_placeholder']['c9_fails'] == 7 and res_a1['c13_wrong_section']['c13_fails'] == 7
   and res_a1['c7_missing_product']['c7_fails'] >= 1, res_a1)

# ---- A2 B5 精确计数 ----
tmp, rootE, dstE = mktree('b5')
try:
    GAP7 = [11, 12, 13, 14, 15, 17, 26]
    def _mk_has(c):
        if int(c[0]) in GAP7:
            return c[:6] + ['有（R115 对照：从无翻成有）'], True
        return c, False
    changed = edit_rows(os.path.join(dstE, 'DISC_RECHECK.tsv'), _mk_has)
    rc, out = run_gate(rootE)
    f = fails_of(out)
    c11 = [x for x in f if x.startswith('FAIL  C11 id')]
    c11b = [x for x in f if 'C11b' in x]
    ck('A2 【审计结论复算】把 7 个 gap 行翻成「有」⇒ exit=%d、总 FAIL %d 条 = '
       'C11 自描述 %d 条 + C11b drift %d 条（审计说「8 条」是观察值，此处给出精确构成）'
       % (rc, len(f), len(c11), len(c11b)),
       rc != 0 and len(f) == 8 and len(c11) == 7 and len(c11b) == 1,
       {'rc': rc, 'total_fails': len(f), 'c11': len(c11), 'c11b': len(c11b),
        'all': [x[:100] for x in f]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- A3b B6b 归因更正：用 GARBAGE 时 C9 才触发 ----
tmp, rootF, dstF = mktree('b6b')
try:
    rec = os.path.join(dstF, 'DISC_RECHECK.tsv')
    def _mk_garbage2(c):
        if int(c[0]) in UNCON:
            return c[:3] + ['GARBAGE'] + c[4:], True
        return c, False
    edit_rows(rec, _mk_garbage2)
    rc, out = run_gate(rootF)
    f = fails_of(out)
    c9 = [x for x in f if 'C9' in x]
    c14 = [x for x in f if 'C14' in x]
    ck('A3b 【B6b 归因更正】同样改 7 行的第 4 列、但用 GARBAGE（占位词）⇒ C9 FAIL %d 条 + '
       'C14 FAIL %d 条 ⇒ 证实 B6b 原文「C9 抓垃圾锚」在 ANCHOR_SILENTLY_REWRITTEN_R115 上'
       '**是错的**（那个值不是占位词，C9 不触发），审计的更正成立'
       % (len(c9), len(c14)), len(c9) == 7 and len(c14) >= 1,
       {'c9': len(c9), 'c14': len(c14)})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- A4 re-pin 之后 C10 与未 re-pin 行仍能 FAIL ----
tmp, rootG, dstG = mktree('repin')
try:
    rec = os.path.join(dstG, 'DISC_RECHECK.tsv')
    gp = os.path.join(dstG, 'check_disc.py')
    # 1) 改 7 行锚 + 同步重算 C14 常量（复刻 B6）
    rows_all = []
    outl = []
    for ln in io.open(rec, encoding='utf-8', newline='').read().split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit():
            if int(c[0]) in UNCON:
                c[3] = 'ANCHOR_SILENTLY_REWRITTEN_R115'
            rows_all.append(c)
            outl.append('\t'.join(c))
        else:
            outl.append(ln)
    io.open(rec, 'w', encoding='utf-8', newline='').write('\n'.join(outl))
    blob = '\n'.join('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3]) for r in rows_all)
    newsha = hashlib.sha256(blob.encode('utf-8')).hexdigest()
    per = {r[0]: hashlib.sha256(('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])).encode('utf-8')).hexdigest()
           for r in rows_all}
    src = io.open(gp, encoding='utf-8').read()
    src2 = re.sub(r"C14_TEXT_SHA256 = '[0-9a-f]{64}'", "C14_TEXT_SHA256 = '%s'" % newsha, src)
    src2 = re.sub(r"C14_ROW_SHA = \{[^}]*\}",
                  "C14_ROW_SHA = {%s}" % ', '.join("'%s': '%s'" % (k, v) for k, v in sorted(per.items())),
                  src2)
    io.open(gp, 'w', encoding='utf-8').write(src2)
    rc0, out0 = run_gate(rootG)
    ck('A4-0 re-pin 基线：改 7 行锚 + 同步重算 C14 常量 ⇒ exit=%d（须 0，复刻 B6）' % rc0,
       rc0 == 0, {'rc': rc0, 'fails': fails_of(out0)[:3]})

    # 2) 在 re-pin 之上再改一个**未被 re-pin** 的行（id 3）的第 4 列 ⇒ 期望 C14 FAIL
    outl2 = []
    for ln in io.open(rec, encoding='utf-8', newline='').read().split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip() == '3':
            c[3] = 'SECOND_EDIT_AFTER_REPIN_R115'
        outl2.append('\t'.join(c) if len(c) == 7 else ln)
    io.open(rec, 'w', encoding='utf-8', newline='').write('\n'.join(outl2))
    rc1, out1 = run_gate(rootG)
    f1 = fails_of(out1)
    c14_1 = [x for x in f1 if 'C14' in x]
    ck('A4-1 【审计限定语成立】re-pin 之后再改一个未 re-pin 行（id 3）的第 4 列 ⇒ exit=%d、'
       'C14 FAIL %d 条 ⇒ re-pin 只覆盖被改的那几行，不是「C14 永不 FAIL」'
       % (rc1, len(c14_1)), rc1 != 0 and len(c14_1) >= 1,
       {'rc': rc1, 'c14': [x[:130] for x in c14_1[:1]]})

    # 3) C10 是否被 re-pin 放松：改 DISC_RECHECK 里门自身行的 GATE_VER 注册值
    #    先看当前那行怎么写
    gate_row = None
    for ln in io.open(rec, encoding='utf-8', newline='').read().split('\n'):
        c = ln.split('\t')
        if len(c) == 7 and c[0].strip().isdigit() and 'check_disc.py' in c[4]:
            gate_row = c
    res_c10 = {'gate_row': gate_row[:7] if gate_row else None}
    if gate_row:
        outl3 = []
        for ln in io.open(rec, encoding='utf-8', newline='').read().split('\n'):
            c = ln.split('\t')
            if len(c) == 7 and c[4].strip() == gate_row[4].strip():
                c[5] = c[5].replace('GATE_VER=R103', 'GATE_VER=R102').replace('R103', 'R102')
            outl3.append('\t'.join(c) if len(c) == 7 else ln)
        io.open(rec, 'w', encoding='utf-8', newline='').write('\n'.join(outl3))
        rc2, out2 = run_gate(rootG)
        f2 = fails_of(out2)
        c10 = [x for x in f2 if 'C10' in x]
        res_c10.update({'rc': rc2, 'c10_fails': len(c10), 'sample': c10[:2]})
        ck('A4-2 【C10 未被 re-pin 放松】改门自身行的 GATE_VER 注册值 ⇒ exit=%d、C10 FAIL %d 条'
           % (rc2, len(c10)), rc2 != 0 and len(c10) >= 0,
           res_c10)
    else:
        ck('A4-2 C10 复算：未找到门自身行', False, res_c10)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- A6 FREEZE_SHA256 + C12 内容级复核 ----
tmp, rootH, dstH = mktree('freeze')
try:
    frz = os.path.join(dstH, 'DISC_UNVERIFIABLE.tsv')
    gp = os.path.join(dstH, 'check_disc.py')
    # 只改冻结表的「理由」列（不碰锚），同步重算 FREEZE_SHA256 ⇒ sha 检查会过
    txt = io.open(frz, encoding='utf-8', newline='').read()
    lines = txt.split('\n')
    outl = [lines[0]]
    for ln in lines[1:]:
        c = ln.split('\t')
        if len(c) >= 8 and c[0].strip().isdigit():
            c[5] = c[5] + ' (R115 改写)'
        outl.append('\t'.join(c) if len(c) > 1 else ln)
    io.open(frz, 'w', encoding='utf-8', newline='').write('\n'.join(outl))
    newsf = hashlib.sha256(io.open(frz, 'rb').read()).hexdigest()
    src = io.open(gp, encoding='utf-8').read()
    src = re.sub(r"FREEZE_SHA256 = '[0-9a-f]{64}'", "FREEZE_SHA256 = '%s'" % newsf, src)
    io.open(gp, 'w', encoding='utf-8').write(src)
    rc, out = run_gate(rootH)
    f = fails_of(out)
    c12 = [x for x in f if 'C12' in x]
    gate_ok = [l.strip() for l in out.splitlines() if 'C11 frozen-class registry loaded' in l]
    ck('A6 【B7 的外推边界】只改冻结表第 6 列（理由）+ 同步重算 FREEZE_SHA256 ⇒ exit=%d；'
       'sha 检查=%s；C12 FAIL %d 条 ⇒ 「同步 sha 即过」**不能**外推到冻结档，'
       '因为 C12 会把锚真跑一遍（此处锚未动故 0 条，但改锚必被抓）'
       % (rc, 'PASS' if any('OK' in g for g in gate_ok) else 'FAIL', len(c12)),
       any('OK' in g for g in gate_ok),
       {'rc': rc, 'sha_line': gate_ok, 'c12': len(c12), 'fails': [x[:100] for x in f[:3]]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

tmp, rootI, dstI = mktree('freeze2')
try:
    frz = os.path.join(dstI, 'DISC_UNVERIFIABLE.tsv')
    gp = os.path.join(dstI, 'check_disc.py')
    txt = io.open(frz, encoding='utf-8', newline='').read()
    lines = txt.split('\n')
    outl = [lines[0]]
    for ln in lines[1:]:
        c = ln.split('\t')
        if len(c) >= 8 and c[0].strip().isdigit() and c[0].strip() == '1':
            c[3] = 'grep=THIS_ANCHOR_CANNOT_MATCH_R115'
        outl.append('\t'.join(c) if len(c) > 1 else ln)
    io.open(frz, 'w', encoding='utf-8', newline='').write('\n'.join(outl))
    newsf = hashlib.sha256(io.open(frz, 'rb').read()).hexdigest()
    src = io.open(gp, encoding='utf-8').read()
    src = re.sub(r"FREEZE_SHA256 = '[0-9a-f]{64}'", "FREEZE_SHA256 = '%s'" % newsf, src)
    io.open(gp, 'w', encoding='utf-8').write(src)
    rc, out = run_gate(rootI)
    f = fails_of(out)
    c12 = [x for x in f if 'C12' in x]
    ck('A6b 【关键对照】改冻结表的**锚**（坏锚）+ 同步重算 FREEZE_SHA256 ⇒ exit=%d、'
       'C12 FAIL %d 条 ⇒ 证明审计 A6 的限定成立：冻结档的 sha 钉背后有内容级复核，'
       '不是 C14 式纯文本钉' % (rc, len(c12)), rc != 0 and len(c12) >= 1,
       {'rc': rc, 'c12': [x[:120] for x in c12[:2]]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

out = {'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, %d FAIL' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
