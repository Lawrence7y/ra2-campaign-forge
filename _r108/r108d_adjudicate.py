#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108d_adjudicate.py —— 19 张 switch 表所属函数的最终裁定（含 R107 判据 P 的误判率量化）

r108c 的两处自错（保留痕迹）：
  E-x1 owner_in() 用 strict '>' 判 S，导致「S 本身已是窗口内最大 E 成员」时返回 None，
       13 张 R107-OWNER 被误记成「拿不到 owner」，A1 断言 FAIL；改为 max(E ∩ [S,H])，空则取 S。
  E-x2 «排他性» 判据按当前定义在随机窗口上发火率 100%（HB 密度 1/235 B，短窗口内几乎必有 HB），
       故它**没有鉴别力**，不能当独立证据。本脚本改用它只作一致性自检，不作判据。

本脚本交四条可机械核验的量：
  Q1  HB / IMMPTR / CALLT / VSLOT 四类入口各自对「已知函数入口」（call 目标、vtable 槽值）的召回；
  Q2  ret 清理约定一致性（同函数内所有 ret / ret imm16 的 imm 必须相同）作为**独立**判据的鉴别力，
      含随机窗口负控（若随机窗口也大量一致，则该判据无鉴别力，如实记）；
  Q3  19 张逐张最终裁定 + 每张 owner 的证据类别；
  Q4  R107 判据 P（S→H 间 ret 必须为 0）在**正确 owner** 上的误拒率 —— 量化它为什么错。
内存纪律：全部只用 branchmap2.bin 与 disasm_lite 分块，不一次性 detail=True 解全段。
"""
import array, bisect, hashlib, json, os, random, struct, sys
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
RETS = sorted(D['rets']); CALLT = set(D['call_t'])
ck('S1 载入：指令 %d / ret %d / call 目标 %d' % (len(starts), len(RETS), len(CALLT)),
   len(starts) == 1392592 and len(RETS) == 31084 and len(CALLT) == 6728,
   (len(starts), len(RETS), len(CALLT)))

# E-x3：ret 前缀 0x67（地址大小前缀）曾被漏判 —— 全段 2 处（0x7dcc34 / 0x7dcc58），
# 其真实字节是 67 cb 7d 00（retf imm16，属数据区误入），必须给确定值而不是 None，
# 否则排序 set 会 TypeError（本轮实测崩在 Q2a 负控上）。
def _rbytes(r):
    q = fo(r); b = []
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return q, raw[q]
def ret_imm(r):
    q, b = _rbytes(r)
    if b == 0xc3: return 0
    if b == 0xc2: return struct.unpack_from('<H', raw, q + 1)[0]
    if b == 0xcb: return -1000
    if b == 0xca: return -1000 - struct.unpack_from('<H', raw, q + 1)[0]
    return -9999
def ret_size(r):
    q, b = _rbytes(r)
    return (q - fo(r)) + (3 if b in (0xc2, 0xca) else 1)

HB = set()
for r in RETS:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
ck('Q0 ret 形态普查：ret %d / ret imm16 %d / 带前缀怪异 %d（后者必须是少数）'
   % (sum(1 for r in RETS if ret_imm(r) == 0),
      sum(1 for r in RETS if ret_imm(r) > 0),
      sum(1 for r in RETS if ret_imm(r) < 0)),
   sum(1 for r in RETS if ret_imm(r) < 0) < 100,
   (sum(1 for r in RETS if ret_imm(r) == 0), sum(1 for r in RETS if ret_imm(r) > 0),
    sum(1 for r in RETS if ret_imm(r) < 0)))

sym = json.load(open('out/reverse/symbols.json'))['classes']
VSLOT = set()
for cn, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16)
    for i in range(400):
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE):
            break
        VSLOT.add(x)

# IMMPTR v3：只取**立即数操作数**里的 .text 地址。
# v2 事故（E-x4）：把内存操作数的 displacement 也当立即数 —— 0x71f2be 的
#   add byte ptr [eax + 0x71ef01], dl 被读成「0x71ef01 是函数指针」，
#   而 0x71ef01 其实是 0x71f2c0 这张表的 case 体首地址（表项 0），
#   导致 0x71f328 的 owner 被错改判成 0x71ef01。必须先剥掉方括号内内容再取 token。
import re as _re
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
IMMPTR = set(); n_imm_raw = 0
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
        o = _re.sub(r'\[[^\]]*\]', ' ', o)     # 剥掉内存操作数
        for tok in o.replace(',', ' ').split():
            if tok.startswith('0x'):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                n_imm_raw += 1
                if TS <= v < TE and v in SSET:
                    IMMPTR.add(v)
    if last <= pos:
        last = pos + 1
    pos = last
ck('I1 IMMPTR v3（非分支指令的**立即数**操作数里的 .text 地址）= %d 个 distinct；扫描 %d 个 token'
   % (len(IMMPTR), n_imm_raw), len(IMMPTR) > 500, len(IMMPTR))

# ---- Q1 召回 ----
def recall(known, name):
    hit = sum(1 for x in known if x in HB)
    return hit, len(known)
h_call, n_call = recall(CALLT, 'call')
h_slot, n_slot = recall(VSLOT, 'slot')
ck('Q1a HB 对 call 目标（已知函数入口）的召回 = %d/%d = %.1f%%'
   % (h_call, n_call, 100.0 * h_call / n_call), h_call / n_call > 0.5,
   '%.1f%%' % (100.0 * h_call / n_call))
ck('Q1b HB 对 vtable 槽值（已知函数入口）的召回 = %d/%d = %.1f%%'
   % (h_slot, n_slot, 100.0 * h_slot / n_slot), h_slot / n_slot > 0.5,
   '%.1f%%' % (100.0 * h_slot / n_slot))
# HB 的精确度代理：HB 中同时也是 call 目标 / 槽值 / IMMPTR 的比例
h_ev = sum(1 for x in HB if x in CALLT or x in VSLOT or x in IMMPTR)
ck('Q1c HB 里带独立外部证据（call∪slot∪immptr）的比例 = %d/%d = %.1f%%'
   % (h_ev, len(HB), 100.0 * h_ev / len(HB)), True,
   '%.1f%%' % (100.0 * h_ev / len(HB)))
random.seed(20261124)
samp = random.sample(range(len(starts)), 20000)
n1 = sum(1 for i in samp if starts[i] in HB)
ck('Q1d 反控：随机 20000 个指令起点里是 HB 的比例（判据基线密度）',
   n1 / 20000 < 0.03, '%.2f%% (%d/20000)' % (100.0 * n1 / 20000, n1))

# ---- Q2 ret 清理约定 ----
def rets_in(a, b):
    i = bisect.bisect_right(RETS, a); j = bisect.bisect_right(RETS, b)
    return RETS[i:j]
def imms(a, b):
    return sorted(set(ret_imm(r) for r in rets_in(a, b)))
# 负控：随机相邻 call 目标窗口（长度 <= 0x800），看 imm 一致（<=1 种）的比例
ct = sorted(CALLT)
wins = []
for i in range(len(ct) - 1):
    a, b = ct[i], ct[i + 1]
    if 0 < b - a <= 0x800:
        wins.append((a, b))
random.shuffle(wins)
wins = wins[:3000]
uni = sum(1 for a, b in wins if len(imms(a, b)) <= 1)
ck('Q2a 负控：%d 个随机相邻-call-目标短窗口里 ret imm 一致（<=1 种）的比例 = %.1f%%'
   % (len(wins), 100.0 * uni / len(wins)), len(wins) > 1000,
   '%.1f%%' % (100.0 * uni / len(wins)))
# 正控：单函数内提前返回的真实例子（人工已核的 0x46dfd0 体）
ck('Q2b 正控：0x46dfd0..0x46e4be 内 ret imm 集合 = %s（单函数多 ret 且 imm 全同 16）' % imms(0x46dfd0, 0x46e4be),
   imms(0x46dfd0, 0x46e4be) == [16], imms(0x46dfd0, 0x46e4be))

# ---- Q3/Q4 逐张裁定 ----
E = sorted(CALLT | VSLOT | IMMPTR | HB)
def owner_of(S, H, Esorted):
    i = bisect.bisect_right(Esorted, H)
    if i and Esorted[i - 1] >= S:
        return Esorted[i - 1]
    return S
def cls(x):
    t = []
    if x in HB: t.append('HB')
    if x in CALLT: t.append('CALL')
    if x in VSLOT: t.append('VSLOT')
    if x in IMMPTR: t.append('IMM')
    return t

R107 = json.load(open('_r107/r107g_owner.json'))['rows']
ROWS = []
for r107 in R107:
    S0 = int(r107['owner'], 16); H = int(r107['holder'], 16)
    O = owner_of(S0, H, E)
    rows_im = imms(O, H)
    ROWS.append({
        'table': r107['table'], 'holder': r107['holder'],
        'R107_owner': r107['owner'], 'R107_status': r107['owner_status'],
        'owner_new': hex(O), 'evidence': cls(O),
        'changed': O != S0,
        'n_ret_owner_to_holder': len(rets_in(O, H)),
        'ret_imm_owner_to_holder': rows_im,
        'ret_imm_consistent': len(rows_im) <= 1,
        'R107_would_reject': len(rets_in(O, H)) > 0,
        'verdict': ('OWNER' if len(rows_im) <= 1 else 'AMBIGUOUS'),
    })
    print('%-10s H=%-10s R107=%-10s(%s) owner=%-10s ev=%-18s changed=%-5s nret=%-2d imm=%s'
          % (r107['table'], r107['holder'], r107['owner'], r107['owner_status'],
             ROWS[-1]['owner_new'], ','.join(ROWS[-1]['evidence']), ROWS[-1]['changed'],
             ROWS[-1]['n_ret_owner_to_holder'], rows_im), flush=True)

ck('A1 19 张全部有 owner（含「S 本身即最大 E 成员」的退化情形）', all(r['owner_new'] for r in ROWS), 19)
vac = [r['table'] for r in ROWS if not r['evidence']]
ck('A2 有 owner 却四类外部证据全无的张数（应为 0 —— 否则该 owner 只是退化取 S）', not vac, vac)
own13 = [r for r in ROWS if r['R107_status'] == 'OWNER']
ch13 = [(r['table'], r['R107_owner'], r['owner_new']) for r in own13 if r['changed']]
ck('P1 正控：13 张 R107-OWNER 上 owner 与 R107 一致', not ch13, ch13)
amb6 = [r for r in ROWS if r['R107_status'] == 'AMBIGUOUS']
chg = [(r['table'], r['R107_owner'], r['owner_new']) for r in amb6 if r['changed']]
keep = [r['table'] for r in amb6 if not r['changed']]
ck('A3 6 张 AMBIGUOUS：改判 %d 张 / 保持 %d 张' % (len(chg), len(keep)), True,
   '改判 %s ; 保持 %s' % (chg, keep))
rej = [r['table'] for r in ROWS if r['R107_would_reject']]
ck('Q4 R107 判据 P 对「按 HD/证据定出的正确 owner」的误拒张数 = %d/19 = %.1f%%'
   % (len(rej), 100.0 * len(rej) / 19), True, rej)
mixed = [(r['table'], r['ret_imm_owner_to_holder']) for r in ROWS if not r['ret_imm_consistent']]
ck('A4 按 ret imm 一致性仍判不出（imm 混用）的张数', not mixed, mixed)

json.dump({'checks': checks, 'rows': ROWS,
           'n_HB': len(HB), 'n_IMMPTR': len(IMMPTR), 'n_CALLT': len(CALLT),
           'n_VSLOT': len(VSLOT),
           'recall_HB_on_call': [h_call, n_call], 'recall_HB_on_slot': [h_slot, n_slot],
           'HB_with_external_evidence': [h_ev, len(HB)],
           'negctl_imm_uniform': [uni, len(wins)]},
          open('_r108/r108d_adjudicate.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
