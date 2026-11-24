#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r103a_freetext.py —— 门禁第 2/3/4 列是不是自由文本（行为级取证）

动机：DISC_RECHECK.tsv 表头把第 3 列叫「可执行判据（逐字截取）」、第 4 列叫「必查的
现有数据锚」、第 2 列叫「节」。名字暗示它们与 R14_COMMON 正文有绑定关系。
R102 只做了第 7 列（C11）与冻结档第 4 列（C12）的取证，这三列**从未被行为级测过**。

本脚本只做测量 + 反控，不改真门禁。全部在 /tmp/r103_sbx 里跑（sbxlib 建）。

**重要的量测对象声明（R103 落盘后补记）**：本脚本量的是 **R103 落盘前**（GATE_VER=R102）的门禁，
即「问题存在时的行为」。落盘 C13/C14 之后同一个变异已会被抓住 —— 所以本脚本用
`S.prepare(gate='unpatched')` 把被测对象钉在备份门禁上，而不是钉在「盘上当前门禁」。
两次都跑完：unpatched 给出问题存在时的行为，patched 给出收紧后的行为（见 PAT-* 组）。

四组变异（每组改完立刻还原，逐组独立）：
  M1  31 行第 3 列全改成单字符 x                  → 若 exit 0，第 3 列在多数行上不被读
  M1b 只改 id 3 的第 3 列（该行今天真被 C11 读） → 若 exit 1，说明读点在 C11 路径上
  M2  31 行第 4 列全改成任意非占位串               → 与 M2b（只改 id 3）对照
  M3  31 行第 2 列全改成真实存在的 §2.14           → 若 exit 0，第 2 列只校验「存在」
  M3b 31 行第 2 列全改成不存在的 §2.999            → 必须 exit 1（证明 C8 真在跑）

另外做 C13 可行性测量（不改门禁，只算）：把「纪律 N ·」在 R14_COMMON 里所属的
## x.y 节反推出来，与本表第 2 列逐行比对，看严格化会不会误伤。
"""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbxlib as S

OUT = os.path.join(S.REAL, '_r103')
checks = []

def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

S.prepare(gate='unpatched')
rc0, f0, _ = S.run()
ck('S0 沙箱基线 exit 0', rc0 == 0, 'exit=%d fails=%s' % (rc0, f0[:2]))

rs, t = S.rows(S.SBX)
ck('S1 行数 31、列数全 7', len(rs) == 31 and all(len(r) == 7 for r in rs), 'rows=%d' % len(rs))

def mutate(col, val, only_id=None):
    out = []
    for r in rs:
        c = list(r)
        if (only_id is None) or (c[0] == only_id):
            if col == 'all3':
                c[1], c[2], c[3] = val[0], val[1], val[2]
            else:
                c[col] = val
        out.append(c)
    return out

def trial(name, rows):
    S.write_rows(rows, t, S.SBX)
    rc, f, _ = S.run()
    S.write_rows(rs, t, S.SBX)        # 立刻还原
    print('  %-28s exit=%d  fails=%s' % (name, rc, [x[:70] for x in f][:3]))
    return rc, f

RES = {}
# ---- M1 第 3 列（可执行判据）全改 x ----
rc, f = trial('M1 col3=all-x', mutate(2, 'x'))
RES['M1_col3_all_x'] = {'exit': rc, 'fails': f}
ck('M1: 第 3 列 31 行全改单字符 x ⇒ 门禁不 FAIL（第 3 列无内容级校验）', rc == 0, 'exit=%d' % rc)

rc, f = trial('M1b col3=id3-x', mutate(2, 'x', only_id='3'))
RES['M1b_col3_id3_x'] = {'exit': rc, 'fails': f}
ck('M1b: 只改 id 3 的第 3 列 ⇒ 与 M1 同结果（该行也不读第 3 列内容）',
   rc == RES['M1_col3_all_x']['exit'], 'M1=%d M1b=%d' % (RES['M1_col3_all_x']['exit'], rc))

# ---- M2 第 4 列（锚）全改任意非占位串 ----
rc, f = trial('M2 col4=ANCHOR-X', mutate(3, 'ANCHOR-X'))
RES['M2_col4_all'] = {'exit': rc, 'fails': f}
ck('M2: 第 4 列 31 行全改成 ANCHOR-X ⇒ exit 1，且 FAIL 全部来自 C11 的 R5（26 行不可见、5 行可见）',
   rc == 1 and all(x.startswith('C11') for x in f)
   and sorted(int(x.split()[2]) for x in f) == [3, 4, 22, 27, 28],
   'exit=%d fails=%s' % (rc, sorted(int(x.split()[2]) for x in f)))

rc, f = trial('M2b col4=id3', mutate(3, 'ANCHOR-X', only_id='3'))
RES['M2b_col4_id3'] = {'exit': rc, 'fails': f}
ck('M2b: 只改 id 3 的第 4 列 ⇒ exit 1 且报 R5 anchors mismatch（sha256 绑定真在跑）',
   rc == 1 and any('R5 anchors mismatch' in x for x in f), 'fails=%s' % [x[:60] for x in f][:2])

# ---- M3 第 2 列（节）全改成真实存在的 §2.14 ----
rc, f = trial('M3 col2=all-2.14', mutate(1, '§2.14'))
RES['M3_col2_existing'] = {'exit': rc, 'fails': f}
ck('M3: 第 2 列 31 行全改成 §2.14（真实存在）⇒ exit 0（只校验存在，不校验对应）', rc == 0, 'exit=%d' % rc)

rc, f = trial('M3b col2=all-2.999', mutate(1, '§2.999'))
RES['M3b_col2_missing'] = {'exit': rc, 'fails': f}
ck('M3b: 第 2 列全改成 §2.999（不存在）⇒ exit 1（C8 真在跑，M3 不是门禁失灵）',
   rc == 1 and any(x.startswith('C8') for x in f), 'fails=%s' % [x[:60] for x in f][:2])

# ---- M4 三列同时伪造（最坏情形）----
rc, f = trial('M4 col2/3/4 all forged',
              [[c[0], '§2.14', 'FORGED', 'FORGED-ANCHOR-%s' % c[0], c[4], c[5], c[6]] for c in rs])
RES['M4_triple_forgery'] = {'exit': rc, 'fails': f}
ck('M4: 第 2/3/4 列同时伪造 ⇒ 仍被 C11 的 R5 抓到（26 行不可见，5 行可见）',
   rc == 1 and any('R5 anchors mismatch' in x for x in f), 'fails=%s' % [x[:50] for x in f][:2])

# ---- C13 可行性：节号能否从正文反推 ----
rc_txt = io.open(os.path.join(S.REAL, S.R14REL, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
CANON = re.compile(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·')
cur, sec_of = None, {}
for l in rc_txt.replace('\r\n', '\n').split('\n'):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m:
        cur = m.group(1)
    mm = CANON.search(l)
    if mm and cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14:
        sec_of.setdefault(int(mm.group(1)), set()).add(cur)
mismatch = [(int(r[0]), r[1].lstrip('§').strip(), sorted(sec_of.get(int(r[0]), [])))
            for r in rs if r[1].lstrip('§').strip() not in sec_of.get(int(r[0]), set())]
multi = {n: sorted(s) for n, s in sec_of.items() if len(s) > 1}
RES['C13'] = {'defs': len(sec_of), 'mismatch': mismatch, 'ambiguous': multi}
ck('C13 可行性：31 行第 2 列全部等于「纪律 N」在正文里所属的节（严格化不会误伤）',
   mismatch == [], 'mismatch=%s' % mismatch[:5])
ck('C13 边界：有 1 个纪律号在正文里出现在两个节（歧义，严格化必须按集合而非单值）',
   multi == {1: ['2.14', '2.26']}, 'ambiguous=%s' % multi)

# ---- 第 3 列「逐字截取」逐行核 ----
doc = rc_txt.replace('\r\n', '\n')
v3 = []
for r in rs:
    c3 = r[2]
    v3.append({'id': int(r[0]), 'verbatim_in_doc': c3 in doc, 'stripped_verbatim':
               c3.lstrip('⇒ ').lstrip('*') in doc, 'len': len(c3)})
RES['col3_verbatim'] = v3
bad3 = [x['id'] for x in v3 if not x['verbatim_in_doc']]
ck('S2 第 3 列声称「逐字截取」：实测 28/31 逐字在正文，3 行不在（31/32/33）',
   bad3 == [31, 32, 33], 'bad=%s' % bad3)

# ---- 第 4 列锚在产物里的出现情况 ----
inprod, indoc = [], []
for r in rs:
    a = r[3].strip()
    pp = os.path.join(S.SBX, r[4].strip().replace('\\', '/'))
    pt = io.open(pp, encoding='utf-8', errors='replace').read().replace('\r\n', '\n') if os.path.isfile(pp) else ''
    if a in pt:
        inprod.append(int(r[0]))
    if a in doc:
        indoc.append(int(r[0]))
RES['anchor_occurrence'] = {'in_product': inprod, 'in_doc': indoc}
ck('S3 第 4 列锚在「自己那行的产物」里逐字出现的只有 1 行（id 14）', inprod == [14], 'in_product=%s' % inprod)
ck('S4 第 4 列锚在 R14_COMMON 正文里逐字出现的只有 2 行（id 14/32）', indoc == [14, 32], 'in_doc=%s' % indoc)

# ---- M5 完整伪造链：改第 4 列 + 同步重写 5 条自述行的 anchors ----
# C11 的 R5 把自述行 anchors 与第 4 列用 sha256 绑定；若同一行为者能同时改
# DISC_RECHECK.tsv 与产物里的自述行，这条绑定就只是自洽性检查，不是真实性检查。
import hashlib as _h
rs5 = [list(r) for r in rs]
chain = []
for c in rs5:
    if c[0] in ('3', '4', '22', '27', '28'):
        old_anchor = c[3]
        c[3] = 'FORGED-ANCHOR-' + c[0]
        newhash = 'sha256:' + _h.sha256(c[3].encode('utf-8')).hexdigest()
        pp = os.path.join(S.SBX, c[4].strip().replace('\\', '/'))
        pt = io.open(pp, encoding='utf-8', newline='').read()
        oldline = 'sha256:' + _h.sha256(old_anchor.encode('utf-8')).hexdigest()
        assert oldline in pt, 'self-desc line for %s not found' % c[0]
        io.open(pp, 'w', encoding='utf-8', newline='').write(pt.replace(oldline, newhash))
        chain.append(int(c[0]))
S.write_rows(rs5, t, S.SBX)
rc, f, _ = S.run()
S.write_rows(rs, t, S.SBX)
RES['M5_full_forgery_chain'] = {'exit': rc, 'fails': f, 'rewritten': chain}
print('  %-28s exit=%d  fails=%s' % ('M5 forge col4 + selfdesc', rc, [x[:70] for x in f][:3]))
ck('M5 完整伪造链可成功：改第 4 列锚 + 同步重写 5 条自述行的 anchors ⇒ exit 0'
   '（R5 是自洽性检查，不是真实性检查）', rc == 0 and chain == [3, 4, 22, 27, 28],
   'exit=%d rewritten=%s fails=%s' % (rc, chain, f[:2]))

# ================= PAT 组：落盘 C13/C14 之后，同一批变异必须被抓 =================
S.prepare(gate='patched')
rs_p, t_p = S.rows(S.SBX)
def mutp(fn):
    out = []
    for r in rs_p:
        c = list(r); fn(c); out.append(c)
    return out
def trialp(name, rows):
    S.write_rows(rows, t_p, S.SBX); rc, f, _ = S.run(); S.write_rows(rs_p, t_p, S.SBX)
    print('  %-30s exit=%d fails=%s' % (name, rc, [x[:60] for x in f][:2]))
    return rc, f
PAT = {}
rc, f = trialp('PAT1 col3 all x', mutp(lambda c: c.__setitem__(2, 'x')))
PAT['col3_all_x'] = {'exit': rc, 'fails': f[:2]}
ck('PAT1 落盘后：第 3 列全改 x ⇒ FAIL（C14 指纹，M1 的历史结论已被收紧）',
   rc == 1 and any(x.startswith('C14') for x in f), [x[:60] for x in f][:2])
rc, f = trialp('PAT2 col2 all 2.14', mutp(lambda c: c.__setitem__(1, '§2.14')))
PAT['col2_all_2_14'] = {'exit': rc, 'fails': f[:2]}
ck('PAT2 落盘后：第 2 列全指 §2.14 ⇒ FAIL（C13 + C14 双响，M3 的历史结论已被收紧）',
   rc == 1 and any(x.startswith('C13') for x in f), [x[:60] for x in f][:2])
rc, f = trialp('PAT3 col4 id16', mutp(lambda c: c.__setitem__(3, 'ZZZ') if c[0] == '16' else None))
PAT['col4_id16'] = {'exit': rc, 'fails': f[:2]}
ck('PAT3 落盘后：只改 id 16 的第 4 列 ⇒ FAIL（C14，此前 26 行完全不被读）',
   rc == 1 and any(x.startswith('C14') for x in f), [x[:60] for x in f][:2])
RES['PAT'] = PAT

json.dump({'checks': checks, 'results': RES},
          io.open(os.path.join(OUT, 'r103a_freetext.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n%d checks, %d FAIL' % (len(checks), nf))
sys.exit(1 if nf else 0)
