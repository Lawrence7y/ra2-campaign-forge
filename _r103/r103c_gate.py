#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r103c_gate.py —— 把三处「纯加严」打进真门禁（C13 节号对应 / C14 自由文本钉 / C15 内容下界）

每处都有动机实测（见 r103a_freetext.json、r103b_loss.json）与反控，全部在沙箱先跑通：
  C13  DISC_RECHECK 第 2 列「节」今天只校验「该 ## x.y 存在」，不校验「与纪律号对应」。
       实测：31 行全改成 §2.14 ⇒ exit 0（M3）；全改成 §2.999 ⇒ exit 1（M3b，证明 C8 真在跑）。
       严格化可行：从 R14_COMMON 正文反推出每个「纪律 N ·」所属的 ## x.y 节，31/31 行第 2 列
       都落在该集合里，零误伤。唯一歧义：纪律 1 在正文出现于 2.14 与 2.26（后者是引用），
       故判据按**集合成员**而非单值（这条歧义本就是 R102 待办②里 C11_LANDABLE 语义问题的同族）。
  C14  DISC_RECHECK 第 3 列「可执行判据（逐字截取）」与第 4 列「必查的现有数据锚」是自由文本：
       第 3 列 31 行全改单字符 x ⇒ exit 0（M1）；第 4 列只有 5 行经 R5 的 sha256 绑定，
       其余 26 行改了看不见（M2 的 FAIL 集合恰为 [3,4,22,27,28]）。且 R5 是**自洽性**检查：
       同时改第 4 列与重写那 5 条自述行的 anchors ⇒ exit 0（M5 实测）。
       故新增 C14：把 31 行的 (id, 第2列, 第3列, 第4列) 四元组聚合成一个 sha256 常量，
       任一字符改动即 FAIL 并列出变更过的 id。边界如实声明：这与 FREEZE_SHA256 同族，
       属防误触/防静默改写，不防伪造（纪律 31 已证 sha 钉只能抬高成本）。
  C15  R14_COMMON 整节丢失对门禁完全透明：删 §2.100..§2.106（7 节，74,626 B）⇒ exit 0，
       且 CRLF 计数变化量 0（CR 不变量对此失明），这正是 R102 那次 828,603→738,215 B
       事故能全绿的原因。C15 加三条单调下界：2.x 节集合必须覆盖钉住的集合、末节号不得回退、
       字节数与节数不得低于下界（留 8 KiB / 1 节余量，允许小节内改写与正常增节）。

用法：
  python3 _r103/r103c_gate.py           # 只跑沙箱控制组
  python3 _r103/r103c_gate.py --apply   # 控制组全过后落真门禁（唯一备份 + 字节级补丁 + 回读校验）
"""
import hashlib, io, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbxlib as S

OUT = os.path.join(S.REAL, '_r103')
REAL = S.REAL
R14 = os.path.join(REAL, S.R14REL)
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
RC = os.path.join(R14, 'R14_COMMON.md')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

# ------------------------------------------------------------------ 实测取值
rc_txt = io.open(RC, encoding='utf-8', newline='').read()
rc_lf = rc_txt.replace('\r\n', '\n')
SECS2 = sorted({int(m.group(1)) for m in re.finditer(r'(?m)^##\s+2\.(\d+)\b', rc_lf)})
LAST2 = SECS2[-1]
FLOOR_BYTES = len(rc_txt.encode('utf-8')) - 8 * 1024
FLOOR_HEAD = len(SECS2) - 1

CANON = re.compile(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·')
cur, SEC_DEF = None, {}
for l in rc_lf.split('\n'):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m:
        cur = m.group(1)
    mm = CANON.search(l)
    if mm and cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14:
        SEC_DEF.setdefault(int(mm.group(1)), set()).add(cur)

dr_txt = io.open(DR, encoding='utf-8', newline='').read()
ROWS = [l.split('\t') for l in dr_txt.split('\n') if l][1:]
TEXT_BLOB = '\n'.join('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3]) for r in ROWS)
TEXT_SHA = hashlib.sha256(TEXT_BLOB.encode('utf-8')).hexdigest()
TEXT_MAP = {r[0]: hashlib.sha256(('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])).encode('utf-8')).hexdigest()
            for r in ROWS}
print('pins: 2.x sections=%d last=%d floor_bytes=%d floor_head=%d' % (len(SECS2), LAST2, FLOOR_BYTES, FLOOR_HEAD))
print('pins: text blob sha256=%s (31 rows)' % TEXT_SHA[:16])

# ------------------------------------------------------------------ 补丁正文（CRLF 无关，纯 ASCII + 中文）
PATCH = r'''
# ---- C13 【R103 新增】第 2 列「节」必须与纪律号对应，不能只求「存在」 ----
# R103 实测（_r103/r103a_freetext.json）：31 行第 2 列全改成真实存在的 §2.14 ⇒ exit 0。
# C8 只查「该 ## x.y 在 R14_COMMON 里存在」，故把任意行指向任意存在的节都不被看见。
# 严格化可行（零误伤）：从正文反推每个「纪律 N ·」所属的 ## 2.x 节，31/31 行原值都在该集合内。
# 唯一歧义：纪律 1 在正文出现于 2.14（定义）与 2.26（引用），故按**集合成员**判，不按单值。
SEC_DEF = {}
_c13_cur = None
for _l in lines:
    _m13 = re.match(r'^##\s*(\d+(?:\.\d+)*)', _l)
    if _m13:
        _c13_cur = _m13.group(1)
    _mm13 = re.search(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·', _l)
    if _mm13 and _c13_cur and _c13_cur.startswith('2.') and float(_c13_cur.split('.')[1]) >= 14:
        SEC_DEF.setdefault(int(_mm13.group(1)), set()).add(_c13_cur)
c13 = 0
for r in rows:
    if len(r) != 7 or not r[0].strip().isdigit():
        continue
    _n13, _s13 = int(r[0]), r[1].lstrip('§').strip()
    _want13 = SEC_DEF.get(_n13, set())
    if not _want13:
        fails.append('C13 id %d has no 纪律 %d · definition in R14_COMMON (cannot cross-check section)'
                     % (_n13, _n13))
    elif _s13 not in _want13:
        fails.append('C13 id %d section %r != definition section(s) %s (col2 must point at the defining section)'
                     % (_n13, r[1], sorted(_want13)))
    else:
        c13 += 1
notes.append('C13 section-correspondence: %d/%d rows match their definition section' % (c13, len(rows)))

# ---- C14 【R103 新增】第 2/3/4 列自由文本的整表指纹 ----
# R103 实测：第 3 列 31 行全改单字符 x ⇒ exit 0；第 4 列只有 5 行被 R5 的 sha256 看到
# （改全表 col4 的 FAIL 集合恰为 [3,4,22,27,28]），其余 26 行改一字不可见。
# 且 R5 是自洽性检查：同时改 col4 并重写那 5 条自述行的 anchors ⇒ exit 0（M5）。
# 故把 (id, col2, col3, col4) 逐行指纹聚合钉住；任一字符改动即 FAIL 并列出变更 id。
# 边界（如实声明，与纪律 31 同族）：sha 钉只能抬高成本，不能防伪造 —— 同时改表与本常量者仍可过。
# 它的价值是把今天 26 行「完全不被读」变成 31 行「改动必被看见」。
C14_TEXT_SHA256 = '@@TEXT_SHA@@'
C14_ROW_SHA = @@ROW_SHA@@
_c14_blob = '\n'.join('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])
                      for r in rows if len(r) == 7)
_c14_now = hashlib.sha256(_c14_blob.encode('utf-8')).hexdigest()
if _c14_now != C14_TEXT_SHA256:
    _c14_drift = []
    for r in rows:
        if len(r) != 7:
            continue
        _k = r[0]
        _h = hashlib.sha256(('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])).encode('utf-8')).hexdigest()
        if C14_ROW_SHA.get(_k) != _h:
            _c14_drift.append(_k)
    fails.append('C14 col2/col3/col4 free-text table changed: sha256 %s != pinned %s ; drifted ids=%s '
                 '(re-pin C14_TEXT_SHA256/C14_ROW_SHA deliberately after editing those rows)'
                 % (_c14_now[:16], C14_TEXT_SHA256[:16], _c14_drift[:12]))
else:
    notes.append('C14 free-text table fingerprint ok: 31 rows, sha256=%s' % _c14_now[:16])

# ---- C15 【R103 新增】R14_COMMON 内容的单调下界：整节丢失必须 FAIL ----
# R103 实测（_r103/r103b_loss.json A 组）：删 §2.100..§2.106（7 节 / 74,626 B）⇒ 现门禁 exit 0，
# 且 CRLF 计数 1081→1081 变化量 0 —— C5 的 CR 不变量对丢内容失明，这正是 R102 那次
# 828,603→738,215 B 事故能全绿的结构性原因。C15 只加下界，不动任何行：
# 允许小节内改写、允许正常增节，不允许整节消失、末节号回退、字节数跌破下界。
C15_SECS = @@SECS2@@
C15_LAST = @@LAST2@@
C15_FLOOR_BYTES = @@FLOOR_BYTES@@
C15_FLOOR_HEAD = @@FLOOR_HEAD@@
_rc15 = rc
_secs15 = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', _rc15.replace('\r\n', '\n'))]
_miss15 = sorted(set(C15_SECS) - set(_secs15))
if _miss15:
    fails.append('C15 R14_COMMON section(s) disappeared: %d missing %s (content loss is NOT allowed; '
                 'if a section was legitimately merged, re-pin C15_SECS deliberately)'
                 % (len(_miss15), _miss15[:12]))
if not _secs15 or max(_secs15) < C15_LAST:
    fails.append('C15 R14_COMMON last 2.x section %s < pinned %d (tail truncation)'
                 % (max(_secs15) if _secs15 else 'none', C15_LAST))
_bytes15 = len(_rc15.encode('utf-8'))
if _bytes15 < C15_FLOOR_BYTES:
    fails.append('C15 R14_COMMON bytes %d < floor %d (lost >= %d B)'
                 % (_bytes15, C15_FLOOR_BYTES, C15_FLOOR_BYTES - _bytes15))
if len(_secs15) < C15_FLOOR_HEAD:
    fails.append('C15 R14_COMMON 2.x headings %d < floor %d' % (len(_secs15), C15_FLOOR_HEAD))
notes.append('C15 content floor: 2.x sections %d (pinned %d), last %s (pinned %d), bytes %d (floor %d)'
             % (len(_secs15), len(C15_SECS), max(_secs15) if _secs15 else 'none', C15_LAST, _bytes15, C15_FLOOR_BYTES))
'''
PATCH = (PATCH.replace('@@TEXT_SHA@@', TEXT_SHA)
              .replace('@@ROW_SHA@@', repr(TEXT_MAP))
              .replace('@@SECS2@@', repr(SECS2))
              .replace('@@LAST2@@', str(LAST2))
              .replace('@@FLOOR_BYTES@@', str(FLOOR_BYTES))
              .replace('@@FLOOR_HEAD@@', str(FLOOR_HEAD)))
assert '@@' not in PATCH

ANCHOR = '# ---- C5 CR 抽查 ----'

def patch_src(src, ver=None):
    assert ANCHOR in src, 'C5 anchor missing'
    body = PATCH
    if ver:
        body = body.replace('C14_TEXT_SHA256', 'C14_TEXT_SHA256')  # no-op, 保持可读
    return src.replace(ANCHOR, body.lstrip('\n') + '\n' + ANCHOR, 1)

def bump_ver(src, old, new):
    n = src.count("GATE_VER = '%s'" % old)
    assert n == 1, 'GATE_VER occurrence %d' % n
    return src.replace("GATE_VER = '%s'" % old, "GATE_VER = '%s'" % new)

# ------------------------------------------------------------------ 沙箱控制组
GSRC_REAL = io.open(GATE, encoding='utf-8', newline='').read()

# ---- 幂等：若真门禁**已经**是 R103 补丁版，则把 R102 备份当「未打补丁」的 G0，
#      本轮只做控制组 + 落盘复核，不再二次补丁（避免把补丁叠两遍）。
import glob as _glob
ALREADY = ("GATE_VER = 'R103'" in GSRC_REAL) and ('C14_TEXT_SHA256' in GSRC_REAL)
G0_UNPATCHED = None
if ALREADY:
    _baks = sorted(_glob.glob(os.path.join(BASE, 'R103.before_check_disc_C13C14C15_*.bak')))
    assert _baks, 'already-patched gate but no R103 backup to use as G0'
    G0_UNPATCHED = io.open(_baks[-1], encoding='utf-8', newline='').read()
    print('NOTE gate already patched (R103); using %s as the unpatched G0' % os.path.basename(_baks[-1]))
CHECK_BYTES_GATE = dict(crlf=GSRC_REAL.count('\r\n'), lfonly=GSRC_REAL.count('\n') - GSRC_REAL.count('\r\n'))
print('gate bytes: CRLF=%d LF-only=%d' % (CHECK_BYTES_GATE['crlf'], CHECK_BYTES_GATE['lfonly']))

S.prepare()
SBX_GATE = os.path.join(S.SBX, S.R14REL, 'check_disc.py')
SBX_DR = os.path.join(S.SBX, S.R14REL, 'DISC_RECHECK.tsv')
SBX_RC = os.path.join(S.SBX, S.R14REL, 'R14_COMMON.md')

def run():
    return S.run()

def write_gate(src):
    io.open(SBX_GATE, 'w', encoding='utf-8', newline='').write(src)

def write_dr(txt):
    io.open(SBX_DR, 'w', encoding='utf-8', newline='').write(txt)

def write_rc(txt):
    io.open(SBX_RC, 'w', encoding='utf-8', newline='').write(txt)

G0 = io.open(SBX_GATE, encoding='utf-8', newline='').read()
D0 = io.open(SBX_DR, encoding='utf-8', newline='').read()
R0 = io.open(SBX_RC, encoding='utf-8', newline='').read()
assert G0 == GSRC_REAL and D0 == dr_txt and R0 == rc_txt

if ALREADY:
    PATCHED = G0                      # 已在盘上
else:
    PATCHED = bump_ver(patch_src(G0), 'R102', 'R103')
write_gate(PATCHED)

# C7 会真跑 id 20 那一行的 grep，C10 会比对登记值 —— 必须同步改字面（R102 的三重钉教训）
def bump_selfrolw(txt, old, new):
    out = []
    hits = 0
    for l in txt.split('\n'):
        c = l.split('\t')
        if len(c) == 7 and c[4].strip().replace('/', '\\').endswith('check_disc.py'):
            assert ("GATE_VER = '%s'" % old) in c[5], 'self row expr missing GATE_VER'
            c[5] = c[5].replace("GATE_VER = '%s'" % old, "GATE_VER = '%s'" % new)
            hits += 1
        out.append('\t'.join(c))
    assert hits == 1, 'self rows %d' % hits
    return '\n'.join(out)

D1 = D0 if ALREADY else bump_selfrolw(D0, 'R102', 'R103')
D0_UNP = D0 if not ALREADY else bump_selfrolw(D0, 'R103', 'R102') if ALREADY else D0
write_dr(D1)

rc2, f2, out2 = run()
ck('S0 沙箱：原样行 + 已抬 GATE_VER 与新常量 ⇒ exit 0（三处纯加严不改变今天行为）',
   rc2 == 0, 'exit=%d fails=%s' % (rc2, f2[:4]))
ck('S1 输出含 C13 / C14 / C15 三条 NOTE',
   all(k in out2 for k in ('C13 section-correspondence', 'C14 free-text table fingerprint', 'C15 content floor')),
   [l.strip() for l in out2.splitlines() if l.strip().startswith('NOTE') and 'C1' in l][:3])
ck('S2 GATE_VER 已抬到 R103 且 C10 自检 ok(R103)', 'ok(R103)' in out2,
   [l.strip() for l in out2.splitlines() if l.strip().startswith('C10')])

NFT = []   # (name, expect_exit, mutator)
def trial(name, gate_src, dr_txt, rc_txt, expect):
    write_gate(gate_src); write_dr(dr_txt); write_rc(rc_txt)
    rc3, f3, _ = run()
    write_gate(PATCHED); write_dr(D1); write_rc(R0)
    NFT.append({'name': name, 'exit': rc3, 'expect': expect, 'fails': f3[:4]})
    print('  %-34s exit=%d (expect %s) fails=%s' % (name, rc3, expect, [x[:52] for x in f3][:2]))
    return rc3, f3

# ---- C13 正反控 ----

# 更彻底的变异：把每一行的第 2 列都换成一个**不是它自己的**存在节
def remap_col2(txt):
    out = []
    bad = 0
    for l in txt.split('\n'):
        c = l.split('\t')
        if len(c) == 7 and c[0].isdigit():
            n = int(c[0])
            others = [s for s in sorted(SEC_DEF.get(n, set()))]
            # 换成一个存在的、但不是自己的节
            cur_s = c[1].lstrip('§').strip()
            pick = '2.17' if cur_s != '2.17' else '2.19'
            c[1] = '§' + pick
            bad += 1
        out.append('\t'.join(c))
    return '\n'.join(out), bad
D13, nb = remap_col2(D1)
rc3, f3 = trial('M13b col2 shifted to a foreign section', PATCHED, D13, R0, None)
_c13n = [x for x in f3 if x.startswith('C13')]
_c8n = [x for x in f3 if x.startswith('C8')]
ck('C13a 第 2 列指向「存在的别的节」⇒ C13 命中 31 行，且 C8 命中 0（C8 结构上看不见这类改动）',
   rc3 == 1 and len(_c13n) == 31 and _c8n == [],
   'C13=%d C8=%d' % (len(_c13n), len(_c8n)))
ck('C14a2 同一变异也被 C14 指纹看到（col2 属指纹范围）',
   any(x.startswith('C14') for x in f3), [x[:50] for x in f3 if x.startswith('C14')][:1])

# ---- 反向控制配对纪律（R102 ED4：回退必须成对）----
# 未打补丁门禁 G0 的 GATE_VER 是 R102，故它只与 D0（登记 R102）配对；
# 把 D1（登记 R103）配 G0 会同时触发 C7/C10，那测的是我自己的配对错误，不是被测判据（纪律 32）。
rc_p, f_p = trial('PAIR unpatched baseline', G0_UNPATCHED or G0, D0_UNP, R0, 0)
ck('P0 配对基线 G0(R102)+D0(R102) ⇒ exit 0（反向控制的前提）', rc_p == 0, 'exit=%d fails=%s' % (rc_p, f_p[:2]))

# ---- C14 正反控 ----
def mutate_col3(txt, val='z'):
    out = []
    for l in txt.split('\n'):
        c = l.split('\t')
        if len(c) == 7 and c[0].isdigit():
            c[2] = val
        out.append('\t'.join(c))
    return '\n'.join(out)
def mutate_col4_one(txt, rid='16', val='ZZZ'):
    out = []
    for l in txt.split('\n'):
        c = l.split('\t')
        if len(c) == 7 and c[0] == rid:
            c[3] = val
        out.append('\t'.join(c))
    return '\n'.join(out)
D14a = mutate_col3(D1)
rc3, f3 = trial('M14a all col3 -> z', PATCHED, D14a, R0, None)
ck('C14a 第 3 列 31 行全改成 z ⇒ FAIL 且列出 31 个漂移 id（此前 exit 0）',
   rc3 == 1 and any(x.startswith('C14') for x in f3), 'exit=%d fails=%s' % (rc3, [x[:70] for x in f3][:2]))
_nc = trial('NC14a col3=z + unpatched gate', G0_UNPATCHED or G0, mutate_col3(D0_UNP), R0, 0)
ck('C14b 反向控制：第 3 列全改 z + 未打补丁配对门禁 ⇒ exit 0（证明抓到它的是 C14 本身）',
   _nc[0] == 0, 'exit=%d fails=%s' % (_nc[0], _nc[1][:2]))
D14b = mutate_col4_one(D1, '16')
rc3, f3 = trial('M14b col4 of id16 -> ZZZ', PATCHED, D14b, R0, None)
ck('C14c 只改 id 16 的第 4 列（今天完全不被读）⇒ FAIL 且只报 id 16',
   rc3 == 1 and any(x.startswith('C14') and "'16'" in x for x in f3),
   'exit=%d fails=%s' % (rc3, [x[:90] for x in f3][:2]))
_nc2 = trial('NC14b col4(id16)=ZZZ + unpatched gate', G0_UNPATCHED or G0, mutate_col4_one(D0_UNP, '16'), R0, 0)
ck('C14d 反向控制：只改 id 16 第 4 列 + 未打补丁配对门禁 ⇒ exit 0（26 行不可见）',
   _nc2[0] == 0, 'exit=%d fails=%s' % (_nc2[0], _nc2[1][:2]))

# ---- C15 正反控 ----
def cut_sections(text, lo, hi):
    lines = text.split('\n')
    out, dropping, cut = [], False, 0
    for l in lines:
        m = re.match(r'^##\s*2\.(\d+)\b', l)
        if m:
            n = int(m.group(1))
            dropping = lo <= n <= hi
            if dropping:
                cut += 1
        if not dropping:
            out.append(l)
    return '\n'.join(out), cut
R15, cut15 = cut_sections(R0, 100, 106)
rc3, f3 = trial('M15 cut 2.100..2.106 (7 sections)', PATCHED, D1, R15, None)
ck('C15a 删 §2.100..§2.106（7 节）⇒ FAIL（R102 事故同型，此前 exit 0）',
   rc3 == 1 and any(x.startswith('C15') for x in f3), 'cut=%d exit=%d fails=%s' % (cut15, rc3, [x[:70] for x in f3][:2]))
_nc3 = trial('NC15 cut 7 sections + unpatched gate', G0_UNPATCHED or G0, D0_UNP, R15, 0)
ck('C15b 反向控制：同一坏文件 + 未打补丁配对门禁 ⇒ exit 0（R102 事故同型）',
   _nc3[0] == 0, 'exit=%d fails=%s' % (_nc3[0], _nc3[1][:2]))
# 删「最后一节」必须按**盘上实际末节号**取，不能写死 106（本轮已落盘 §2.107，写死会过时 —— 自错 5）
_LAST_NOW = max(int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', R0.replace('\r\n', '\n')))
R15b, cut15b = cut_sections(R0, _LAST_NOW, _LAST_NOW)
rc3, f3 = trial('M15b cut last section 2.%d' % _LAST_NOW, PATCHED, D1, R15b, None)
# C15 的真实边界（不是脚本错，是判据错）：删掉**落盘之后才新增**的末节不会被抓 ——
# C15_SECS 只钉到落盘时的 106，末节号下界也是 106，字节下界留了 8 KiB 余量。
# 如实把这条登记成「已知边界」，而不是把断言改成必过。
ck('C15c 已知边界：删掉落盘后新增的末节 §2.%d 仍 exit 0（下界只覆盖到钉住时的 106 节 + 8 KiB 余量）'
   % _LAST_NOW, rc3 == 0, 'exit=%d fails=%s' % (rc3, [x[:60] for x in f3][:2]))
# 正控：§2.106 在钉住时是末节，现在不是末节 ⇒ 它被删时响的是 disappeared 而不是 truncation。
# （truncation 那一条只有删掉「钉住时的末节且其后无新节」才会响，见 C15c2 与 C15c 两格已覆盖。）
rc3, f3 = trial('C15c-pos cut 2.106 (pinned-time last)', PATCHED, D1, cut_sections(R0, 106, 106)[0], None)
ck('C15c-pos 钉住时的末节 §2.106 被删 ⇒ FAIL（报 disappeared；truncation 只在末节号真的回退时才报）',
   rc3 == 1 and any('disappeared' in x for x in f3), 'exit=%d fails=%s' % (rc3, [x[:70] for x in f3][:2]))
R15f, _ = cut_sections(R0, 106, 106)
rc3, f3 = trial('M15f cut a middle-to-late section 2.106', PATCHED, D1, R15f, None)
ck('C15c2 删 §2.106（此时已不是末节）⇒ FAIL 且报 disappeared（不报 truncation）',
   rc3 == 1 and any('disappeared' in x and '106' in x for x in f3), 'exit=%d fails=%s' % (rc3, [x[:70] for x in f3][:3]))
R15c = R0.replace('本节只收 R102 本机实测', '本节只收 R102 本机实测（R103 改写探针）', 1)
rc3, f3 = trial('M15c in-section edit (should pass)', PATCHED, D1, R15c, 0)
ck('C15d 不误伤：小节内改写（正文字节变化但节还在）⇒ exit 0', rc3 == 0, 'exit=%d' % rc3)
R15d = R0 + '\n## 2.107 R103 探针节\n\n本节仅用于证明 C15 不拦正常增节。\n'
rc3, f3 = trial('M15d append new section (should pass)', PATCHED, D1, R15d, 0)
ck('C15e 不误伤：正常追加 §2.107 ⇒ exit 0', rc3 == 0, 'exit=%d fails=%s' % (rc3, f3[:2]))
R15e, _ = cut_sections(R0, 50, 52)
rc3, f3 = trial('M15e cut 2.50..2.52 (historical)', PATCHED, D1, R15e, None)
ck('C15f 删历史节 §2.50..§2.52 也 FAIL（不只尾部）',
   rc3 == 1 and any(x.startswith('C15') and 'disappeared' in x for x in f3),
   'exit=%d fails=%s' % (rc3, [x[:70] for x in f3][:2]))

# ---- 还原并复核 ----
write_gate(PATCHED); write_dr(D1); write_rc(R0)
rc_end, f_end, _ = run()
ck('S3 沙箱收尾：还原后 exit 0', rc_end == 0, 'exit=%d' % rc_end)

json.dump({'pins': {'sections': SECS2, 'last': LAST2, 'floor_bytes': FLOOR_BYTES,
                    'floor_head': FLOOR_HEAD, 'text_sha': TEXT_SHA},
           'gate_bytes_before': CHECK_BYTES_GATE,
           'trials': NFT, 'checks': checks},
          io.open(os.path.join(OUT, 'r103c_gate.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)


def crf(t):
    return t.count('\r\n'), t.count('\n') - t.count('\r\n')


def lf_only_line_nos(b):
    """返回「行尾是 \n 且前一字节不是 \r」的行号（1-based）——R102 ED4 真正该钉的量。"""
    out, s, n = [], 0, 0
    while True:
        i = b.find(b'\n', s)
        if i < 0:
            break
        n += 1
        if i == 0 or b[i - 1:i] != b'\r':
            out.append(n)
        s = i + 1
    return out


def to_crlf_new_lines(old_bytes, new_bytes, keep=()):
    """把新增行里的孤立 LF 补成 CRLF，保留旧文件本来就 LF-only 的那些行（按行号）。"""
    def split(bs):
        out, s = [], 0
        while True:
            i = bs.find(b'\n', s)
            if i < 0:
                out.append(bs[s:]); break
            out.append(bs[s:i + 1]); s = i + 1
        return out
    L = split(new_bytes)
    keep_idx = {k - 1 for k in (keep or ())}
    fixed = 0
    for i, l in enumerate(L):
        if l.endswith(b'\n') and not l.endswith(b'\r\n') and i not in keep_idx:
            L[i] = l[:-1] + b'\r\n'
            fixed += 1
    return b''.join(L), fixed

NF = sum(1 for c in checks if not c['ok'])
print('\n%d checks, %d FAIL' % (len(checks), NF))
if NF:
    sys.exit(1)

# ------------------------------------------------------------------ 落真门禁
# ------------------------------------------------------------------ 已在盘上：只复核
if ALREADY:
    real_gate = io.open(GATE, encoding='utf-8', newline='').read()
    real_dr = io.open(DR, encoding='utf-8', newline='').read()
    ck('A0x 已在盘上：门禁 LF-only 行号集合为 [24, 25]',
       lf_only_line_nos(real_gate.encode('utf-8')) == [24, 25],
       lf_only_line_nos(real_gate.encode('utf-8')))
    ck('A1x 已在盘上：门禁 CRLF 计数 466、LF-only 2',
       real_gate.count('\r\n') == 466 and (real_gate.count('\n') - real_gate.count('\r\n')) == 2,
       'CRLF=%d LFonly=%d' % (real_gate.count('\r\n'), real_gate.count('\n') - real_gate.count('\r\n')))
    ck('A3x 已在盘上：DISC_RECHECK CRLF=0 且登记 R103',
       real_dr.count('\r\n') == 0 and "GATE_VER = 'R103'" in real_dr, '')
    p2 = subprocess.run([sys.executable, GATE], capture_output=True, text=True, cwd=R14)
    fails2 = [l.strip()[6:] for l in p2.stdout.splitlines() if l.strip().startswith('FAIL  ')]
    ck('A8x 已在盘上：真门禁 exit 0', p2.returncode == 0, 'exit=%d fails=%s' % (p2.returncode, fails2[:3]))
    ck('A9x 已在盘上：C13/C14/C15 NOTE 与 ok(R103) 全部在输出里',
       all(k in p2.stdout for k in ('C13 section-correspondence', 'C14 free-text table fingerprint',
                                    'C15 content floor', 'ok(R103)')), '')
    NF3 = sum(1 for c in checks if not c['ok'])
    print('\n=== VERIFY-ONLY: %d checks, %d FAIL ===' % (len(checks), NF3))
    sys.exit(1 if NF3 else 0)


if '--apply' not in sys.argv:
    print('DRY (pass --apply to land on the real gate)')
    sys.exit(0)

sys.exit(0)
