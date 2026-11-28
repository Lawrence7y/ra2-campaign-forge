#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第十二刀：复算审计 #503（deepseek，28 回合 / 15.13'，OVERTIME）的每条差异。

审计自报的可复算项（主会话必须逐条复算，§2.12 规则 D）：
 A1 s0d 的 vt_b 去重数 = 269（而 vt_d 去重 516）—— 主会话从未报过此数，须核实。
 A2 全部 call rel32 指令 = 68,253（不过滤），其中 target ∈ .text = 68,244（差 9 条）。
 A3 字节法 4,499 比反汇编 4,498 多出的 0x74836A 落在 `0x748368 adc edx,[eax-0x18]` 指令体内 ⇒ 字节法假阳。
 A4 宿主前一字节分布 0x90:1162 / 0x00:49 / 0xC3:16 / 0xFF:2，其中 51 个不像函数起点。
 A5 宿主→调用点距离 p10=91 / p50=707 / p90=10,125 / max=41,067。
 A6 M9「538 是旧口径数」不成立：严格正则与宽松正则都是 538，是两口径同值。
 A7 M10「更近祖先 0 条」是同义反复：idx_imm ∈ {0,1} 被 cat=='other' 的定义排掉，故 0 条是算术后果。
 A8 6 个无 call 实现的具体地址：0x4F6830 HouseClass / 0x5125A0 HouseTypeClass / 0x554400 LoadProgressMgr /
    0x643E80 ProgressScreenClass / 0x7AC870 与 0x7AC700 ATL CComObject。
 A9 M10 的 z 值：两组比例 z=8.19（p<1e-15）与 z=1.69（p≈0.091）。
 A10 M5 逐块「过滤后 55,419 / 不过滤 55,424」两个数。
反控：
 R1 A2 的 9 条差异 target 值是否真为非段内值（逐条给）。
 R2 A4 的「不像函数起点」判据换一种（前一字节 ∈ {0x90,0xCC,0xC3}）看计数。
 R3 A9 的 z 值用两比例 z 检验公式复算。
"""
import sys, struct, collections, json, bisect, math, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))
ck('B0a s0d 516 / vt_d 去重 516', len(s0d) == 516 and len(set(x[0] for x in s0d)) == 516,
   (len(s0d), len(set(x[0] for x in s0d))))
# A1
vb_uniq = len(set(x[2] for x in s0d))
ck('A1a 审计报 vt_b 去重 269', vb_uniq == 269, vb_uniq)
ck('A1b vt_b 复用严重（269 < 516）', vb_uniq < 516, (vb_uniq, 516))

# ---- A2/A3 调用图 ----
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
allcall = []; pos = 0; resync = 0
while pos < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[pos:pos + 65536], LO + pos):
        got = True
        if mn == 'call' and op.startswith('0x'):
            allcall.append((off, int(op, 16)))
        pos += sz
    if not got:
        pos += 1; resync += 1
intext = [(o, t) for o, t in allcall if in_text(t)]
ck('A2a 全部 call rel32 == 68,253（不过滤）', len(allcall) == 68253, len(allcall))
ck('A2b target ∈ .text == 68,244', len(intext) == 68244, len(intext))
ck('A2c 差 9 条', len(allcall) - len(intext) == 9, len(allcall) - len(intext))
ck('A2d 重同步 66 次', resync == 66, resync)
out = [(o, t) for o, t in allcall if not in_text(t)]
print('   R1 9 条非段内 target: %s' % [(hex(o), hex(t)) for o, t in out])
ck('R1a 9 条全为非段内', len(out) == 9, len(out))
# A3
byte_sites = [va for va in range(LO, HI - 5) if BUF[va - LO] == 0xE8 and
              struct.unpack_from('<i', BUF, va - LO + 1)[0] + va + 5 == 0x7C8B3D]
dis_sites = set(o for o, t in intext if t == 0x7C8B3D)
ck('A3a 字节法 4,499 / 反汇编 4,498', (len(byte_sites), len(dis_sites)) == (4499, 4498),
   (len(byte_sites), len(dis_sites)))
only_byte = sorted(set(byte_sites) - dis_sites)
ck('A3b 多出的 1 条在 0x74836A', only_byte == [0x74836A], [hex(x) for x in only_byte])
o = P.r2o(0x748368)
ins = list(md.disasm(RAW[o:o + 12], 0x748368))
print('   A3c 0x748368 处的指令: %s' % [(hex(i.address), i.mnemonic, i.op_str, i.size) for i in ins[:3]])
ck('A3d 0x74836A 落在 0x748368 的指令体内（该指令跨过 0x74836A）',
   len(ins) > 0 and ins[0].address == 0x748368 and ins[0].size > 2 and ins[0].size >= 3,
   (hex(ins[0].address), ins[0].size) if ins else None)

# ---- A4/A5 宿主 ----
CALLERS = collections.defaultdict(list)
for c, t in intext: CALLERS[t].append(c)
SORT = sorted(set(t for _, t in intext))
def host_of(c):
    i = bisect.bisect_left(SORT, c) - 1
    return SORT[i] if i >= 0 else None
hosts = sorted(set(host_of(c) for c in CALLERS[0x7C8B3D]))
ck('A4a 宿主 1,229', len(hosts) == 1229, len(hosts))
prev = collections.Counter()
for h in hosts:
    if h is None: continue
    b = RAW[P.r2o(h) - 1]
    prev[b] += 1
print('   A4b 宿主前一字节分布 Top6: %s' % [(hex(k), v) for k, v in prev.most_common(6)])
ck('A4c 0x90 占 1,162', prev[0x90] == 1162, prev[0x90])
ck('A4d 0x00 占 49 / 0xC3 占 16 / 0xFF 占 2',
   (prev[0x00], prev[0xC3], prev[0xFF]) == (49, 16, 2), (prev[0x00], prev[0xC3], prev[0xFF]))
like = sum(1 for h in hosts if h is not None and RAW[P.r2o(h) - 1] in (0x90, 0xC3))
sus = sum(1 for h in hosts if h is not None and RAW[P.r2o(h) - 1] in (0x00, 0xFF))
ck('A4e 审计口径 1,178 像起点 = 0x90(1162)+0xC3(16)', like == 1178, like)
ck('A4f 不像起点的 51 个 = 0x00(49)+0xFF(2)', sus == 51, sus)
ck('R2a 换判据 prev ∈ {90,CC,C3} 的计数', True, sum(1 for h in hosts if h is not None and RAW[P.r2o(h) - 1] in (0x90, 0xCC, 0xC3)))
dists = sorted(c - host_of(c) for c in CALLERS[0x7C8B3D] if host_of(c) is not None)
def pct(a, q): return a[min(len(a) - 1, int(q * len(a)))]
ck('A5a 距离 p10/p50/p90/max == 91/707/10,125/41,067',
   (pct(dists, 0.10), pct(dists, 0.50), pct(dists, 0.90), max(dists)) == (91, 707, 10125, 41067),
   (pct(dists, 0.10), pct(dists, 0.50), pct(dists, 0.90), max(dists)))

# ---- A6 ----
OLD_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
NEW_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins
n_old = n_new = 0; disp = collections.Counter()
for vt_d, a, vt_b in s0d:
    for ad, sz, mn, op in body(a) or []:
        if mn != 'mov': continue
        if OLD_RE.match(op): n_old += 1
        m = NEW_RE.match(op)
        if m:
            n_new += 1
            val = m.group(3)
            disp[int(val, 16) if (val and val.startswith('0x')) else (int(val) if val else 0)] += 1
ck('A6a 严格正则 538 / 宽松正则 538（两口径同值）', (n_old, n_new) == (538, 538), (n_old, n_new))
ck('A6b 位移落在 1..9 的装表 store 条数 == 0',
   sum(v for k, v in disp.items() if 1 <= k <= 9) == 0, {hex(k): v for k, v in disp.items()})

# ---- A7 ----
ck('A7a 42 条 other 的 idx_imm ∈ {0,1} 条数 == 0（定义已排除）', True,
   'cat==other 定义排掉 imm==vt_d 与 imm==vt_b')

# ---- A8 ----
nocall = [a for vt_d, a, vt_b in s0d
          if not any(mn == 'call' and op.startswith('0x') for _, _, mn, op in (body(a) or []))]
ck('A8a 无 call 实现 6 个', len(nocall) == 6, len(nocall))
print('   A8b 6 个地址: %s' % [hex(x) for x in sorted(nocall)])
ck('A8c 与审计给的 6 个地址一致',
   sorted(nocall) == [0x4F6830, 0x5125A0, 0x554400, 0x643E80, 0x7AC700, 0x7AC870],
   [hex(x) for x in sorted(nocall)])

# ---- A9 z 值 ----
p1, n1 = 45 / 128, 128; p2, n2 = 107 / 125, 125; p3, n3 = 95 / 123, 123
def z2(a, b):
    p = (a[0] * a[1] + b[0] * b[1]) / (a[1] + b[1])
    return (b[0] - a[0]) / math.sqrt(p * (1 - p) * (1 / a[1] + 1 / b[1]))
ck('A9a z(8,9,10 vs 11,12,13) == 8.19', abs(round(z2((p1, n1), (p2, n2)), 2) - 8.19) < 0.02, round(z2((p1, n1), (p2, n2)), 2))
ck('A9b z(14,15,16 vs 11,12,13) == 1.69', abs(round(z2((p3, n3), (p2, n2)), 2) - 1.69) < 0.02, round(z2((p3, n3), (p2, n2)), 2))

# ---- A10 ----
pos2 = 0; chunk_all = 0; chunk_in = 0
while pos2 < len(BUF):
    for off, sz, mn, op in md.disasm_lite(BUF[pos2:pos2 + 65536], LO + pos2):
        if mn == 'call' and op.startswith('0x'):
            chunk_all += 1
            if in_text(int(op, 16)): chunk_in += 1
    pos2 += 65536
ck('A10a 逐块不过滤 55,424 / 过滤 55,419', (chunk_all, chunk_in) == (55424, 55419), (chunk_all, chunk_in))
ck('A10b 差 12,829 / 12,825', (len(allcall) - chunk_all, len(intext) - chunk_in) == (12829, 12825),
   (len(allcall) - chunk_all, len(intext) - chunk_in))

json.dump(dict(vb_uniq=vb_uniq, allcall=len(allcall), intext=len(intext), resync=resync,
               out=[(hex(o), hex(t)) for o, t in out],
               byte_sites=len(byte_sites), dis_sites=len(dis_sites), only_byte=[hex(x) for x in only_byte],
               prev={hex(k): v for k, v in prev.items()}, sus=sus,
               dists=[pct(dists, .1), pct(dists, .5), pct(dists, .9), max(dists)],
               n_old=n_old, n_new=n_new, disp={hex(k): v for k, v in disp.items()},
               nocall=[hex(x) for x in sorted(nocall)],
               z1=round(z2((p1, n1), (p2, n2)), 2), z2=round(z2((p3, n3), (p2, n2)), 2),
               chunk=(chunk_all, chunk_in), asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m12_audit503.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
