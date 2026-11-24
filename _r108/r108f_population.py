#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108f_population.py —— 把 owner 判据从 19 张表推广到全 .text 的**所有** switch 分派表

19 张只是 R105 抽出的样本。若判据只在这 19 张上成立、在全量上崩，那它是过拟合。
本脚本对 .text 里全部「jmp [reg*4 + 表基址]」站点做同样处理：
  Q1 全量分派表基数（站点数 / distinct 表基址数 / 与 R107 exec 的 354 张关系）
  Q2 每张表按 E = CALLT ∪ VSLOT ∪ IMMPTR ∪ HB 定 owner；统计 owner 去重数、
     tables-per-owner 分布（1 个函数拥有多张表 = 嵌套 switch）
  Q3 对比：R107 判据（最近 call 目标）与 E 判据在**全量**上的分歧率
  Q4 一致性：E 判据给出的 owner 到 H 的直线体是否真的能走到 H（第一个 ret 不得早于 H）；
     反过来，R107 判据给出的 S 有多少比例连 H 都走不到
  Q5 交叉核验子代理 hy4 #182 的三条反例（C1 0x5657a0 / C2 0x4068f0 / C3 0x48d080）
     与其 misfire 分布（它报 E=5904 / 5713 对 / ret0 仅 144）
内存纪律：不一次性 detail=True 解全段；本脚本只读 branchmap2.bin + 局部解码。
"""
import array, bisect, hashlib, json, os, re, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
def fo(va):
    return va - IB

D = {}
f = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k = f.read(kl).decode()
    a = array.array('I'); a.frombytes(f.read(n * isz)); D[k] = a
starts = D['starts']; SSET = set(starts)
RETS = sorted(D['rets'])
CALLT = set(x for x in D['call_t'] if TS <= x < TE)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True

def d1(a, n=1):
    return [(g[0], g[1], g[2], g[3]) for g in md.disasm_lite(raw[fo(a):fo(a) + 16], a)][:n]

# ---- Q1 全量分派表 ----
SITES = []       # (insn_va, table_va)
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'jmp' and '[' in o and '*4' in o:
            m2 = re.findall(r'0x[0-9a-f]+', o)
            if m2:
                t = int(m2[-1], 16)
                SITES.append((a, t))
    if last <= pos:
        last = pos + 1
    pos = last
TB = sorted(set(t for _, t in SITES))
ck('Q1 全量「jmp [reg*4+表]」站点 %d 个 / distinct 表基址 %d 个（R107 exec 报 346 张，为其子集）'
   % (len(SITES), len(TB)), len(SITES) > 300 and len(TB) > 300, (len(SITES), len(TB)))
jt_prev = json.load(open('_r107/_exec/cfg_jt.json'))
prev = set(int(x['table'], 16) for x in jt_prev)
ck('Q1b 本轮 %d 张表覆盖 R107-exec 的 %d 张中的 %d 张（差集应为 0）'
   % (len(TB), len(prev), len(set(TB) & prev)),
   len(prev - set(TB)) == 0, [hex(x) for x in sorted(prev - set(TB))[:5]])

def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in RETS:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
VSLOT = set()
for cn, c in json.load(open('out/reverse/symbols.json'))['classes'].items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16)
    for i in range(400):
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE):
            break
        VSLOT.add(x)
IMMPTR = set()
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m in ('jmp', 'call') or (m[0] == 'j' and m != 'jmp'):
            continue
        o = re.sub(r'\[[^\]]*\]', ' ', o)
        for tok in o.replace(',', ' ').split():
            if tok.startswith('0x'):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if TS <= v < TE and v in SSET:
                    IMMPTR.add(v)
    if last <= pos:
        last = pos + 1
    pos = last
E = sorted(CALLT | VSLOT | IMMPTR | HB)
ck('Q1c |E| = %d（call %d / vslot %d / immptr %d / HB %d）'
   % (len(E), len(CALLT), len(VSLOT), len(IMMPTR), len(HB)), len(E) > 15000,
   (len(CALLT), len(VSLOT), len(IMMPTR), len(HB)))

def owner_of(S, H, Es=E):
    i = bisect.bisect_right(Es, H)
    if i and Es[i - 1] >= S:
        return Es[i - 1]
    return None

def first_ret_from(S, limit=20000):
    a = S; n = 0
    while a < TE and n < limit:
        g = d1(a, 1)[0]
        if g[2].startswith('ret'):
            return a, n + 1
        a = g[0] + g[1]; n += 1
    return None, n

# ---- Q2/Q3/Q4 全量处理 ----
ROWS = []
for site, tab in SITES:
    H = site
    # R107 判据：<= H 且是 call 目标的最大地址（>0 且在 0x8000 内）
    i = bisect.bisect_right(sorted(CALLT), H)
    cts = sorted(CALLT)
    S_r107 = cts[i - 1] if i and H - cts[i - 1] <= 0x8000 else None
    O = owner_of(S_r107 if S_r107 is not None else TS, H)
    ROWS.append({'site': hex(site), 'table': hex(tab), 'S_r107': hex(S_r107) if S_r107 else None,
                 'owner': hex(O) if O else None,
                 'differs': (O is not None and O != S_r107)})
n_owner = len(set(r['owner'] for r in ROWS if r['owner']))
from collections import Counter
c = Counter(r['owner'] for r in ROWS if r['owner'])
ck('Q2 全量 %d 个分派站点归到 %d 个不同 owner 函数（19 张样本上是 18 个）'
   % (len(ROWS), n_owner), n_owner > 100, n_owner)
dist = Counter(c.values())
ck('Q2b tables-per-owner 分布（1 表 / 2 表 / >=3 表 的函数个数）',
   True, {k: dist[k] for k in sorted(dist)})
top = c.most_common(6)
ck('Q2c 拥有最多表的 6 个函数（(owner, 表数)）', True, top)
nd = sum(1 for r in ROWS if r['differs'])
ck('Q3 R107 判据（最近 call 目标）与 E 判据在全量上的分歧率 = %d/%d = %.1f%%'
   % (nd, len(ROWS), 100.0 * nd / len(ROWS)), True, '%.1f%%' % (100.0 * nd / len(ROWS)))
# Q4 三条口径全部实测，逐条如实登记（只有第三条被判为可用）
#
# 口径 A（作废，E-y2）「从 O 线性解码，首条 ret 是否早于 H」：
#   0x417fe0 第 25 条指令就是 0x418030 的 ret，而其后的 0x418031 仍是同一函数（ret 后无填充，
#   紧接下一个 case 体），site 0x418345 就在其后 —— early-return 使该口径把正确 owner 判成到不了 H。
#
# 口径 B（作废，E-y3）「从 O 做 jmp/jcc BFS，call 不跟入、ret 终止」：
#   47/387 站点不可达，但抽查 0x418345 证明原因是我方 CFG **不跟跳转表边**：
#   0x417fff 是 jmp *0x418d58(,%eax,4)，case 体全在表后，BFS 在间接 jmp 处终止，
#   经其它 case 体再进第二张表的路径整段丢失。故「不可达」不能证明「不是本函数」，不作反证。
#
# 口径 C（可用）「帧配对 + 排他性」：
#   (i) O = max(E ∩ [S,H])，且 (O,H] 内无其它 E 成员（排他性，构造保证）；
#   (ii) O 处解析出帧常量 sub esp,N（或 and esp,-8 形态），(O,H] 内每条 ret 的前一条
#        清理指令必须是 add esp,N（同值）或 pop 序列；不配对即说明 O 不是含 H 的函数。
def frame_of(va):
    for a, sz, m, o in d1(va, 8):
        mm = re.fullmatch(r'esp, (0x[0-9a-f]+)', o)
        if m == 'sub' and mm:
            return int(mm.group(1), 16)
    for a, sz, m, o in d1(va, 8):
        if m == 'and' and o.startswith('esp,'):
            return 'and-align'
    return None

def prev_insn(a):
    i = bisect.bisect_left(starts, a)
    return starts[i - 1] if i > 0 else None

def pair_stats(O, H):
    fr = frame_of(O)
    i = bisect.bisect_right(RETS, O); j = bisect.bisect_right(RETS, H)
    rs = RETS[i:j]
    ok = 0
    for r in rs:
        p = prev_insn(r)
        if p is None:
            continue
        g = d1(p, 1)[0]
        mm = re.fullmatch(r'esp, (0x[0-9a-f]+)', g[3])
        if g[2] == 'pop' or g[2] == 'ret':
            ok += 1
        elif g[2] == 'add' and mm and isinstance(fr, int) and int(mm.group(1), 16) == fr:
            ok += 1
    return fr, len(rs), ok

bad_owner = []; unk_owner = 0; pair_pass = 0; pair_unknown = []; pair_fail = []
for r in ROWS:
    if not r['owner']:
        continue
    O = int(r['owner'], 16); H = int(r['site'], 16)
    fr, nret, nok = pair_stats(O, H)
    if nret == 0 or nok == nret:
        pair_pass += 1
    elif fr is None:
        # E-y4：首稿把「帧常量解析不出」与「帧配对失败」混成一类记为不通过。
        # 实测 0x617250 等函数用 push 型帧（无 sub esp,N），解析不到帧常量，
        # 此时该判据**不可判**而不是判负；如实单列。
        pair_unknown.append((r['site'], r['owner'], nret, nok))
    else:
        pair_fail.append((r['site'], r['owner'], fr, nret, nok))
ck('Q4a 口径 C：owner 排他性（(O,H] 内无其它 E 成员）违反数应为 0（构造保证，自检用）',
   all(len([x for x in E if O < x <= H]) == 0
       for r in ROWS if r['owner']
       for O, H in [(int(r['owner'], 16), int(r['site'], 16))]), True)
ck('Q4b 口径 C 三分类：通过 %d / 不可判（帧常量解析不出）%d / 判负（帧已知但不配对）%d'
   % (pair_pass, len(pair_unknown), len(pair_fail)), True,
   'unknown %s ; fail %s' % (pair_unknown[:5], pair_fail[:5]))
# 口径 B 的不可达量如实报（不作反证）
UJ = {a: t for a, t in zip(D['uj_s'], D['uj_t'])}
CJ = {a: t for a, t in zip(D['cj_s'], D['cj_t'])}
def reach(S, target, cap=200000):
    if S not in SSET:
        return None
    seen = {S}; dq = [S]; n = 0
    while dq:
        a = dq.pop()
        while True:
            if a == target:
                return True
            if a not in SSET:
                break
            g = d1(a, 1)[0]
            n += 1
            if n > cap:
                return None
            m = g[2]
            if m.startswith('ret'):
                break
            if m == 'jmp':
                t = UJ.get(a, 0)
                if t and t not in seen:
                    seen.add(t); dq.append(t)
                break
            if m[0] == 'j' and a in CJ:
                t = CJ[a]
                if t not in seen:
                    seen.add(t); dq.append(t)
            a = g[0] + g[1]
    return False
nour = 0; nunreach = []
for r in ROWS:
    if not r['owner']:
        continue
    res = reach(int(r['owner'], 16), int(r['site'], 16))
    if res is None:
        nour += 1
    elif res is False:
        nunreach.append(r['site'])
ck('Q4c 口径 B（不作反证，仅量化盲区）：owner 经 jmp/jcc BFS 到不了站点 = %d/%d，超上限 %d'
   % (len(nunreach), len(ROWS), nour), True, nunreach[:8])
# 口径 C 对 R107 的 S 的判别力（这才是它与 R107 判据的差别）
s_fail_but_o_pass = []
for r in ROWS:
    if not r['differs'] or not r['S_r107'] or not r['owner']:
        continue
    S = int(r['S_r107'], 16); O = int(r['owner'], 16); H = int(r['site'], 16)
    frS, nS, okS = pair_stats(S, H)
    frO, nO, okO = pair_stats(O, H)
    if (nS > 0 and okS != nS) and (nO == 0 or okO == nO):
        s_fail_but_o_pass.append((r['site'], r['S_r107'], nS, okS, r['owner'], nO, okO))
ck('Q4d 口径 C 的判别力：在 %d 个分歧站点里，R107 的 S 帧配对失败而 E 的 owner 通过的 = %d（%.1f%%）'
   % (nd, len(s_fail_but_o_pass), 100.0 * len(s_fail_but_o_pass) / max(1, nd)),
   len(s_fail_but_o_pass) > 0, '%.1f%%' % (100.0 * len(s_fail_but_o_pass) / max(1, nd)))

# ---- Q5 复核审计员 #182 的三条反例 ----
AUD = [('C1', 0x5657a0, 0x5657d5), ('C2', 0x4068f0, 0x406917), ('C3', 0x48d080, 0x48d1c2)]
aud = []
for cid, e, ret in AUD:
    fr, n = first_ret_from(e)
    ins = []
    a = e
    while a <= ret + 16:
        g = d1(a, 1)[0]
        ins.append((hex(a), g[2], g[3]))
        a = g[0] + g[1]
        if len(ins) > 400:
            break
    # 该函数的第一个分派站点（若有）
    site = next((s for s, t in SITES if e <= s <= (ret + 0x40)), None)
    aud.append({'id': cid, 'entry': hex(e), 'first_ret': hex(fr) if fr else None,
                'first_ret_matches_claim': (fr == ret), 'n_insn_to_first_ret': n,
                'dispatch_site_in_body': hex(site) if site else None,
                'ret_before_any_dispatch': (site is None or (fr is not None and fr < site))})
ck('Q5 审计员 3 条反例：其声称的首条 ret 与我方自算一致',
   all(x['first_ret_matches_claim'] for x in aud),
   [(x['id'], x['first_ret'], hex(AUD[0][2])) for x in aud if not x['first_ret_matches_claim']])
ck('Q5b 这 3 条反例的体内**没有**任何 switch 分派站点（故对本轮 19 张表的 owner 判定不构成反例）',
   all(x['dispatch_site_in_body'] is None for x in aud),
   [(x['id'], x['dispatch_site_in_body']) for x in aud])
# 审计员的 E 与 pairs 数
ck('Q5c 审计员报 E=5904 唯一 call 目标 / 5713 对；我方 .text 内 call 目标 %d、%d 个站点'
   % (len(CALLT), len(SITES)), True,
   'diff E=%d' % (len(CALLT) - 5904))

json.dump({'checks': checks, 'n_sites': len(SITES), 'n_tables': len(TB),
           'n_owner': n_owner, 'tables_per_owner': {k: dist[k] for k in sorted(dist)},
           'top_owners': [[k, v] for k, v in top],
           'differs': nd, 'pair_pass': pair_pass, 'pair_fail': pair_fail[:40],
           'pair_unknown': pair_unknown[:40],
           'n_unreach_owner': len(nunreach), 's_fail_but_o_pass': s_fail_but_o_pass[:40],
           'audit_counterex': aud,
           'rows_sample': ROWS[:20]},
          open('_r108/r108f_population.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
