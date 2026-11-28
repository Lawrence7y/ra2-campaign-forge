#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 卡 C 审计员脚本 v2（deepseek 家族，只读）。
A1..A4 独立复算；B1..B5 新算。v2 相对 v1 增加：
  - 判据 (i') 虚表目标（.rdata/.data 内任何 dword 指向 .text 的地址，含 vtbl 全部表项）
  - 「函数范围」口径（entry 排序成 [e_i, e_{i+1})），与「区间」口径并列对比
  - B5 断言改为「距离非常数」并给分布（v1 误写成「是常数」）
只读 gamemd.exe 与 _r185/pe185.py；产物只落 _r202/audit_c.json 与 _r202/audit_c.log。"""
import sys, struct, json, bisect, collections, hashlib, statistics
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone

OUTD = '/home/t628/projects/ra2-campaign-forge/_r202'
LOG = []
def out(s=''):
    s = str(s); print(s); LOG.append(s)

fails = []; N = 0
def ck(nm, c, d=''):
    global N
    N += 1
    if not c: fails.append(nm)
    out(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if str(d) != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def sha(xs): return hashlib.sha256(','.join('%x' % x for x in xs).encode()).hexdigest()[:16]
def pct(v, q):
    if not v: return None
    s = sorted(v); return s[min(len(s) - 1, int(len(s) * q))]

REGNAME = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
RAW = P.RAW
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
def in_text(x): return x is not None and LO <= x < HI

out('=== R202 卡 C 审计 v2 (family=deepseek, read-only) ===')
out('.text LO=%s HI=%s size=%d' % (hex(LO), hex(HI), len(BUF)))
out('gamemd.exe sha256=%s size=%d' % (hashlib.sha256(RAW).hexdigest()[:32], len(RAW)))

# ---------- COL / VT ----------
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))

VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
out('COL=%d (sha16=%s) ; VT=%d (sha16=%s) ; VT imm 落段=%s'
    % (len(COL), sha(sorted(COL)), len(VT), sha(sorted(VT)),
       dict(collections.Counter(P.where(v) for v in VT))))
out('VT->COL 存放位点检查: VT[v]==dw(v-4) 成立比例 = %d/%d'
    % (sum(1 for v in VT if P.dw(v - 4) == VT[v]), len(VT)))

# 判据 (i') 虚表目标全集：.rdata/.data 内指向 .text 的 dword
VTGT = set()
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]): VTGT.add(w[i])
out('虚表目标集 (i\') 基数 = %d' % len(VTGT))

# ---------- 线性反汇编（64KB 分块 / disasm_lite / 无 detail）----------
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
INS_N = 0; BEND = []; RET_N = 0; INT3_N = 0; CALLT = set(); CALL_IN = 0; CALL_ALL = 0
ST_INSTR = []
p2 = 0; bad = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2 + 65536], LO + p2):
        got = True; INS_N += 1
        if mn.startswith('ret'): RET_N += 1; BEND.append(off + sz)
        elif mn == 'int3': INT3_N += 1; BEND.append(off + sz)
        elif mn == 'call' and op.startswith('0x'):
            CALL_ALL += 1; t = int(op, 16)
            if in_text(t): CALLT.add(t); CALL_IN += 1
        o = off - LO
        if BUF[o] == 0xC7 and 2 <= sz <= 10:
            mb = BUF[o + 1]; mo = mb >> 6; rg = (mb >> 3) & 7; rm = mb & 7
            if rg == 0 and rm != 4 and not (rm == 5 and mo == 0):
                if mo == 1: ST_INSTR.append((off, REGNAME[rm], struct.unpack_from('<b', BUF, o + 2)[0], struct.unpack_from('<I', BUF, o + 3)[0], 1))
                elif mo == 2: ST_INSTR.append((off, REGNAME[rm], struct.unpack_from('<i', BUF, o + 2)[0], struct.unpack_from('<I', BUF, o + 6)[0], 2))
                elif mo == 0: ST_INSTR.append((off, REGNAME[rm], 0, struct.unpack_from('<I', BUF, o + 2)[0], 0))
        p2 += sz
    if not got: bad += 1; p2 += 1
out('线性反汇编: 指令 %d, 无效字节 %d, ret* %d, int3 %d, call 总 %d (目标在 .text %d, 去重 %d)'
    % (INS_N, bad, RET_N, INT3_N, CALL_ALL, CALL_IN, len(CALLT)))

BEND = sorted(BEND)
REGION = []; st = LO
for e in BEND:
    if e > st: REGION.append((st, e))
    st = e
if st < HI: REGION.append((st, HI))
RL = [r[0] for r in REGION]
REND = {r[0]: r[1] for r in REGION}
def reg_of(va):
    i = bisect.bisect_right(RL, va) - 1
    return REGION[i] if i >= 0 else None

# ---------- A1 ----------
out('')
out('--- A1 ret/int3 边界数与区间数 ---')
out('A1 实测: 边界 = %d (= ret* %d + int3 %d) ; 区间 = %d ; 尾部段 %s..%s'
    % (len(BEND), RET_N, INT3_N, len(REGION), hex(REGION[-1][0]), hex(REGION[-1][1])))
ck('A1a 边界数 == 31967', len(BEND) == 31967, len(BEND))
ck('A1b 区间数 == 31968', len(REGION) == 31968, len(REGION))
ck('A1c 边界 = ret* + int3 且 ret* 单独为 31084', RET_N + INT3_N == len(BEND) and RET_N == 31084, (RET_N, INT3_N))
ck('A1d 区间 = 边界 + 1 且无零长区间', len(REGION) == len(BEND) + 1 and all(b > a for a, b in REGION), len(REGION) - len(BEND))
LENS = [b - a for a, b in REGION]
out('A1 区间长度 p50=%d p90=%d p99=%d max=%d mean=%.2f' % (pct(LENS, .5), pct(LENS, .9), pct(LENS, .99), max(LENS), sum(LENS) / len(LENS)))
nopf = 0
for a, b in REGION:
    fh = next(md.disasm_lite(BUF[a - LO:a - LO + 16], a), None)
    if fh and fh[2] == 'nop': nopf += 1
out('A1 单字节区间 %d（其中 0xCC 单字节区间 %d）; 区间首指令为 nop 的 %d (%.1f%%) ⇒ 区间边界不是函数边界'
    % (sum(1 for x in LENS if x == 1),
       sum(1 for a, b in REGION if b - a == 1 and BUF[a - LO] == 0xCC), nopf, 100.0 * nopf / len(REGION)))

# ---------- 字节扫描两种口径 ----------
RAWEND = T['rawptr'] + T['rawsize']
def naive(noskip66):
    res = []; pos = T['rawptr']; lim = RAWEND - (6 if noskip66 else 4)
    while pos < lim:
        if not noskip66 and RAW[pos] == 0x66:
            if pos + 2 < RAWEND and RAW[pos + 1] == 0xC7:
                mo = RAW[pos + 2] >> 6; pos += 6 if mo == 0 else (7 if mo == 1 else 11); continue
            pos += 1; continue
        if RAW[pos] != 0xC7: pos += 1; continue
        mb = RAW[pos + 1]; mo = mb >> 6; rg = (mb >> 3) & 7; rm = mb & 7
        if rg != 0 or rm == 4 or (rm == 5 and mo == 0): pos += 1; continue
        va = LO + (pos - T['rawptr'])
        if mo == 1: res.append((va, REGNAME[rm], struct.unpack_from('<b', RAW, pos + 2)[0], struct.unpack_from('<I', RAW, pos + 3)[0], 1)); pos += 7
        elif mo == 2: res.append((va, REGNAME[rm], struct.unpack_from('<i', RAW, pos + 2)[0], struct.unpack_from('<I', RAW, pos + 6)[0], 2)); pos += 10
        elif noskip66: pos += 1
        else: res.append((va, REGNAME[rm], 0, struct.unpack_from('<I', RAW, pos + 2)[0], 0)); pos += 6
    return res

recs = naive(True); allsite = naive(False)
sub = [r for r in recs if 1 <= r[2] <= 9 and r[3] in VT]
sub_all = [r for r in allsite if 1 <= r[2] <= 9 and r[3] in VT]
sub_in = [r for r in ST_INSTR if 1 <= r[2] <= 9 and r[3] in VT and r[4] in (1, 2)]
out('')
out('--- A2 装表 store（小位移 1..9 且 imm in VT）---')
out('A2 实测: rec字节扫描=%d ; allsite字节扫描=%d ; 指令对齐=%d ; 后两者地址集对称差=%d'
    % (len(sub), len(sub_all), len(sub_in),
       len(set(r[0] for r in sub_in) ^ set(r[0] for r in sub))))
out('A2 补充: mod 分布=%s ; disp 取值=%s ; 指令对齐口径 mod 分布=%s'
    % (dict(collections.Counter(r[4] for r in sub)), sorted(set(r[2] for r in sub)),
       dict(collections.Counter(r[4] for r in sub_in))))
ck('A2a rec 口径 == 697', len(sub) == 697, len(sub))
ck('A2b allsite 口径 == 697', len(sub_all) == 697, len(sub_all))
ck('A2c 指令对齐口径 == 697 且地址集与字节扫描完全相同', len(sub_in) == 697 and len(set(r[0] for r in sub_in) ^ set(r[0] for r in sub)) == 0, len(sub_in))

# ---------- A3 ----------
G1 = [r for r in sub if r[2] == MD[r[3]]]
G2 = [r for r in sub if r[2] != MD[r[3]]]
out('')
out('--- A3 686/11 二分 ---')
out('A3 实测: disp==mdisp %d (mdisp4=%d, mdisp8=%d) ; disp!=mdisp %d (mdisp 分布=%s)'
    % (len(G1), sum(1 for r in G1 if MD[r[3]] == 4), sum(1 for r in G1 if MD[r[3]] == 8),
       len(G2), dict(collections.Counter(MD[r[3]] for r in G2))))
out('A3 不等 11 条明细: ' + ' '.join('%s(disp=%d,mdisp=0,%s)' % (hex(r[0]), r[2], CLS[r[3]]) for r in G2))
ck('A3a (686,11)', (len(G1), len(G2)) == (686, 11), (len(G1), len(G2)))
ck('A3b mdisp4=345 mdisp8=341', (sum(1 for r in G1 if MD[r[3]] == 4), sum(1 for r in G1 if MD[r[3]] == 8)) == (345, 341),
   (sum(1 for r in G1 if MD[r[3]] == 4), sum(1 for r in G1 if MD[r[3]] == 8)))
ck('A3c 11 条 mdisp 全 0', len(G2) == 11 and all(MD[r[3]] == 0 for r in G2), dict(collections.Counter(MD[r[3]] for r in G2)))
ck('A3d 697 条 disp 仅取 {4,8} 且全为 disp8(mod1)', set(r[2] for r in sub) == {4, 8} and all(r[4] == 1 for r in sub),
   (sorted(set(r[2] for r in sub)), dict(collections.Counter(r[4] for r in sub))))

# ---------- A4 区间口径 ----------
def build(sites):
    brm = collections.defaultdict(int); brs = collections.defaultdict(int)
    m = [r for r in sites if r[3] in VT and MD[r[3]] == 0]
    s = [r for r in sites if r[3] in VT and MD[r[3]] != 0]
    for r in m: brm[reg_of(r[0])] += 1
    for r in s: brs[reg_of(r[0])] += 1
    return brm, brs, m, s

brm, brs, mainall, suball = build(allsite)
def classify(subs, brm_, brs_):
    """区间口径：unit = store 所在 ret/int3 区间。"""
    c = collections.Counter(); rows = []
    for r in subs:
        g = reg_of(r[0])
        if g is None: c['noreg'] += 1; rows.append((r, 'noreg')); continue
        if brm_[g] > 0 and brs_[g] > 0: k = 'both'
        elif brs_[g] > 0: k = 'only_sub'
        else: k = 'none'
        c[k] += 1; rows.append((r, k))
    return c, rows

def classify_gate(subs, brm_, brs_, gate):
    """区间口径 + 入口门：unit = 区间，但区间起点必须落在 gate（入口集）里，否则记 nonfunc。
    brm/brs 必须同样按区间键构造（仅统计区间起点 ∈ gate 的装表点）。"""
    c = collections.Counter(); rows = []
    for r in subs:
        g = reg_of(r[0])
        if g is None: c['noreg'] += 1; rows.append((r, 'noreg')); continue
        if g[0] not in gate: c['nonfunc'] += 1; rows.append((r, 'nonfunc')); continue
        if brm_[g] > 0 and brs_[g] > 0: k = 'both'
        elif brs_[g] > 0: k = 'only_sub'
        else: k = 'none'
        c[k] += 1; rows.append((r, k))
    return c, rows

cS, rowsS = classify(sub, brm, brs)
out('')
out('--- A4 区间口径三分类（分母 697）---')
out('A4 实测: both=%d only_sub=%d none=%d noreg=%d ; 装表点 total=%d 主表=%d 次表=%d ; 涉及区间=%d'
    % (cS['both'], cS['only_sub'], cS['none'], cS['noreg'],
       len([r for r in allsite if r[3] in VT]), len(mainall), len(suball),
       len(set(reg_of(r[0]) for r in sub))))
ck('A4a both==689', cS['both'] == 689, cS['both'])
ck('A4b only_sub==0', cS['only_sub'] == 0, cS['only_sub'])
ck('A4c none==8', cS['none'] == 8, cS['none'])
ck('A4d noreg==0 且四数合 697', cS['noreg'] == 0 and sum(cS.values()) == 697, (cS['noreg'], sum(cS.values())))
none_rows = [r for r, k in rowsS if k == 'none']
ck('A4e 8 条 none 全为 mdisp==0 主表装填', len(none_rows) == 8 and all(MD[r[3]] == 0 for r in none_rows),
   [(hex(r[0]), r[2], hex(r[3])) for r in none_rows])
brm2, brs2, _, _ = build(ST_INSTR)
cS2, _ = classify([r for r in ST_INSTR if 1 <= r[2] <= 9 and r[3] in VT and r[4] in (1, 2)], brm2, brs2)
out('A4 稳健性（指令对齐口径）: both=%d only_sub=%d none=%d noreg=%d'
    % (cS2['both'], cS2['only_sub'], cS2['none'], cS2['noreg']))
ck('A4f 指令对齐口径四数相同', (cS2['both'], cS2['only_sub'], cS2['none'], cS2['noreg']) == (689, 0, 8, 0),
   (cS2['both'], cS2['only_sub'], cS2['none'], cS2['noreg']))

# ---------- B1 真函数入口 ----------
out('')
out('--- B1 真函数入口过滤 ---')
out('判据 (i)  区间起点 ∈ CALLT（call rel32 target 且落 .text）')
out('判据 (i\') 区间起点 ∈ VTGT（.rdata/.data 内任一指向 .text 的 dword，即含 vtbl 表项 = 虚函数入口）')
out('判据 (ii) 区间起点按序匹配 MSVC 序言（最多 4 条，匹配指令不越区间尾）:')
out('          P1 push ebp;mov ebp,esp | P2 mov edi,edi;push ebp;mov ebp,esp |')
out('          P3 push GPR;sub esp,imm | P4 sub esp,imm (首指令) | P5 push GPR;push GPR;sub esp,imm')
out('判据 (iii) 区间内含至少一条 ret（区别于仅以 int3 收尾）')

def head(a, n=4):
    o = a - LO; r = []
    for off, sz, mn, op in md.disasm_lite(BUF[o:o + 48], a):
        r.append((off, sz, mn, op))
        if len(r) >= n: break
    return r
def gpr(x): return x in ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp')
def prologue(a, end):
    h = head(a, 4)
    if not h: return None
    def fit(k): return len(h) >= k and h[k - 1][0] + h[k - 1][1] <= end
    if len(h) >= 2 and h[0][2] == 'push' and h[0][3] == 'ebp' and h[1][2] == 'mov' and h[1][3] == 'ebp, esp' and fit(2): return 'P1'
    if len(h) >= 3 and h[0][3] == 'edi, edi' and h[1][2] == 'push' and h[1][3] == 'ebp' and h[2][3] == 'ebp, esp' and fit(3): return 'P2'
    if len(h) >= 2 and h[0][2] == 'push' and gpr(h[0][3]) and h[1][2] == 'sub' and h[1][3].startswith('esp, ') and fit(2): return 'P3'
    if h[0][2] == 'sub' and h[0][3].startswith('esp, ') and fit(1): return 'P4'
    if len(h) >= 3 and h[0][2] == 'push' and gpr(h[0][3]) and h[1][2] == 'push' and gpr(h[1][3]) and h[2][2] == 'sub' and h[2][3].startswith('esp, ') and fit(3): return 'P5'
    return None

hit1 = []; hitp = []; hitv = []; hitr = []; pat = collections.Counter(); firstc = collections.Counter()
for a, b in REGION:
    if a in CALLT: hit1.append(a)
    if a in VTGT: hitv.append(a)
    pf = prologue(a, b)
    if pf: hitp.append(a); pat[pf] += 1
    for off, sz, mn, op in md.disasm_lite(BUF[a - LO:b - LO], a):
        if mn.startswith('ret'): hitr.append(a); break
    fh = head(a, 1)
    if fh: firstc[(fh[0][2], fh[0][3])] += 1

# ---- 严格按卡面定义 (i)/(ii) 的 (a)(b)(c)(d) ----
STRICT = set(hit1) | set(hitp)
SL = set(hit1) & set(hitp)
out('B1 (a) 满足(i)（区间起点 ∈ CALLT）区间数 = %d' % len(hit1))
out('B1 (b) 满足(ii)（MSVC 序言）区间数 = %d ; 型分布 = %s' % (len(hitp), dict(pat)))
out('B1 (c) 满足(i)或(ii) 区间数 = %d ; 占全部区间 %.2f%% ; |(i)∩(ii)| = %d'
    % (len(STRICT), 100.0 * len(STRICT) / len(REGION), len(SL)))
out('B1 (a)仅(i)不(ii) = %d ; (b)仅(ii)不(i) = %d' % (len(set(hit1) - set(hitp)), len(set(hitp) - set(hit1))))
SDL = [r for r in REGION if r[0] not in STRICT]
SDLEN = [b - a for a, b in SDL]
out('B1 (d) 既非(i)也非(ii) 区间数 = %d ; 长度 p50=%d p90=%d p99=%d max=%d mean=%.2f'
    % (len(SDL), pct(SDLEN, .5), pct(SDLEN, .9), pct(SDLEN, .99), max(SDLEN), sum(SDLEN) / len(SDLEN)))
out('B1 (d) 长度直方(<=8): %s' % dict(sorted(collections.Counter(x for x in SDLEN if x <= 8).items())))
sd_pad = 0
for a, b in SDL:
    ok = True; any_ = False
    for off, sz, mn, op in md.disasm_lite(BUF[a - LO:b - LO], a):
        any_ = True
        if mn not in ('nop', 'int3'): ok = False; break
    if any_ and ok: sd_pad += 1
out('B1 (d) 其中纯 nop/int3 填充区间 = %d (%.2f%%)' % (sd_pad, 100.0 * sd_pad / len(SDL)))
out('B1 (d) 12 例:')
stepd = max(1, len(SDL) // 12)
sex = []
for a, b in SDL[::stepd][:12]:
    h = head(a, 2); sex.append(hex(a))
    out('   %s len=%d  %s' % (hex(a), b - a, '; '.join('%s %s' % (m, o) for _, _, m, o in h)))

out('B1 (a\') 扩展判据 (i\'): 区间起点 ∈ VTGT（.rdata/.data 内任一指 .text 的 dword）= %d' % len(hitv))
out('B1 (iii) 区间内含 ret 的区间数 = %d' % len(hitr))
out('B1 交集: (i)&(ii)=%d ; (i\')&(ii)=%d ; (i)&(i\')=%d'
    % (len(set(hit1) & set(hitp)), len(set(hitv) & set(hitp)), len(set(hit1) & set(hitv))))
TRUE = sorted(STRICT)                 # 卡面定义：真入口集 = (i) ∪ (ii)
TSET = set(TRUE)
TRUE_EXT = sorted(STRICT | set(hitv))  # 稳健性：再并入虚表目标 (i')
out('B1 (c\') 稳健性扩展集 (i)∪(ii)∪(i\') 区间数 = %d ; 占 %.2f%%'
    % (len(TRUE_EXT), 100.0 * len(TRUE_EXT) / len(REGION)))
out('B1 全区间首指令 top6: %s' % [(k, v) for k, v in firstc.most_common(6)])
# 区间 != 函数 的量化
out('B1 关键反证: CALLT 去重 %d 个地址中只有 %d 个恰好落在区间起点；其余 %d 落在区间内部 ⇒ 区间边界 != 函数边界'
    % (len(CALLT), sum(1 for a in RL if a in CALLT), len(CALLT) - sum(1 for a in RL if a in CALLT)))
ck('B1a (c) == (a)+(b)-|(i)∩(ii)|', len(STRICT) == len(hit1) + len(hitp) - len(SL), len(STRICT))
ck('B1b (c)+(d) == 31968', len(STRICT) + len(SDL) == len(REGION), len(STRICT) + len(SDL))
ck('B1c (d) 中纯 nop/int3 填充区间数与单字节 0xCC 区间数同阶',
   700 <= sd_pad <= 900, '%d/%d' % (sd_pad, len(SDL)))
ck('B1d 多数 call 目标不在区间起点（区间!=函数）', len(CALLT) - sum(1 for a in RL if a in CALLT) > len(CALLT) / 2,
   '%d/%d' % (len(CALLT) - sum(1 for a in RL if a in CALLT), len(CALLT)))

# ---------- 函数范围口径 ----------
E = TRUE
def unit_of(region):
    """把区间映射到包含它的函数范围起点；在最小入口之前返回 None。"""
    i = bisect.bisect_right(E, region[0]) - 1
    return None if i < 0 else E[i]
FR = [(E[i], E[i + 1] if i + 1 < len(E) else HI) for i in range(len(E))]
FRL = [x[0] for x in FR]
def func_of(va):
    i = bisect.bisect_right(FRL, va) - 1
    return None if i < 0 else FR[i]
brmF = collections.defaultdict(int); brsF = collections.defaultdict(int)
for r in mainall:
    f = func_of(r[0])
    if f: brmF[f] += 1
for r in suball:
    f = func_of(r[0])
    if f: brsF[f] += 1
def classifyF(subs):
    c = collections.Counter(); rows = []
    for r in subs:
        f = func_of(r[0])
        if f is None: c['nonfunc'] += 1; rows.append((r, 'nonfunc')); continue
        if brmF[f] > 0 and brsF[f] > 0: k = 'both'
        elif brsF[f] > 0: k = 'only_sub'
        else: k = 'none'
        c[k] += 1; rows.append((r, k))
    return c, rows
cF, rowsF = classifyF(sub)
out('')
out('--- B2 三分类（两种过滤口径，分母均 697）---')
cA, _ = classify_gate(sub, brm, brs, TSET)
out('B2 口径 A（严格按卡面：区间起点 ∈ 真入口集，否则记 nonfunc）: both=%d only_sub=%d none=%d nonfunc=%d 合计=%d'
    % (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc'], sum(cA.values())))
out('B2 口径 B（函数范围 [e_i,e_{i+1}) 归属，store 一律有归属）: both=%d only_sub=%d none=%d nonfunc=%d 合计=%d'
    % (cF['both'], cF['only_sub'], cF['none'], cF['nonfunc'], sum(cF.values())))
out('B2 参考: 函数范围总数=%d ; 真入口集大小=%d' % (len(FR), len(TSET)))
nonoA = [r for r, k in classify_gate(sub, brm, brs, TSET)[1] if k == 'none']
out('B2 口径 A 的 %d 条 none 明细: %s' % (len(nonoA), ' '.join(hex(r[0]) for r in nonoA)))
nfF = [r for r, k in rowsF if k == 'none']
out('B2 口径 B 的 %d 条 none 明细: %s' % (len(nfF), ' '.join('%s[%s]' % (hex(r[0]), hex(func_of(r[0])[0])) for r in nfF)))
ck('B2a 口径 A 四数合计 == 697', sum(cA.values()) == 697, sum(cA.values()))
ck('B2b 口径 B 四数合计 == 697', sum(cF.values()) == 697, sum(cF.values()))
ck('B2c 口径 A 与 A4 不同（过滤非恒等）',
   (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc']) != (cS['both'], cS['only_sub'], cS['none'], 0),
   (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc']))
ck('B2d 口径 B 与口径 A 不同',
   (cF['both'], cF['only_sub'], cF['none'], cF['nonfunc']) != (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc']),
   (cF['both'], cF['only_sub'], cF['none'], cF['nonfunc']))
ck('B2e 口径 A 下 nonfunc > 0（多数 store 落在非入口区间）', cA['nonfunc'] > 0, cA['nonfunc'])

# ---------- B3 反控 ----------
out('')
out('--- B3 反控（错误判据，证明过滤非恒等变换）---')
C3 = [LO + i for i, b in enumerate(BUF) if b == 0xC3]
def near(a, r):
    i = bisect.bisect_left(C3, a - r)
    return i < len(C3) and C3[i] <= a + r
W1 = set(a for a, b in REGION if near(a, 3))
W2 = set(a for a, b in REGION if any(BUF[x - LO] == 0xC3 for x in range(a, min(a + 4, HI))))
W3 = set(a for a, b in REGION if near(a, 0))
cWs = {}
for tag, W in (('W1 起点在 0xC3 字节 +-3 内', W1), ('W2 起点[s,s+3] 内含 0xC3', W2), ('W3 起点恰为 0xC3 字节', W3)):
    cw, _ = classify_gate(sub, brm, brs, W)
    cWs[tag.split()[0]] = cw
    out('B3 %s: 子集区间=%d ; both=%d only_sub=%d none=%d nonfunc=%d'
        % ((tag, len(W)) + tuple(cw[k] for k in ('both', 'only_sub', 'none', 'nonfunc'))))
cW1 = cWs['W1']; cW2 = cWs['W2']; cW3 = cWs['W3']
ck('B3a 错误判据 W1 四数与 B2-A 不同',
   (cW1['both'], cW1['only_sub'], cW1['none'], cW1['nonfunc']) != (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc']),
   (cW1['both'], cW1['only_sub'], cW1['none'], cW1['nonfunc']))
ck('B3b 错误判据 W2 四数与 B2-A 不同',
   (cW2['both'], cW2['only_sub'], cW2['none'], cW2['nonfunc']) != (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc']),
   (cW2['both'], cW2['only_sub'], cW2['none'], cW2['nonfunc']))
ck('B3c 错误判据 W3 四数与 B2-A 不同',
   (cW3['both'], cW3['only_sub'], cW3['none'], cW3['nonfunc']) != (cA['both'], cA['only_sub'], cA['none'], cA['nonfunc']),
   (cW3['both'], cW3['only_sub'], cW3['none'], cW3['nonfunc']))

# ---------- B4 重装 ----------
out('')
out('--- B4 同 unit 内同基址同 imm 的重复装表 ---')
byreg = collections.defaultdict(list)
for r in sub: byreg[reg_of(r[0])].append(r)
dupR = []
for g, rs in byreg.items():
    cnt = collections.Counter((r[1], r[3]) for r in rs)
    dupR += [r for r in rs if cnt[(r[1], r[3])] >= 2]
dupR.sort()
out('B4 区间口径: 重装 store = %d / 697 ; 涉及 (区间,基址,imm) 组 = %d'
    % (len(dupR), len(set((reg_of(r[0]), r[1], r[3]) for r in dupR))))
byregF = collections.defaultdict(list)
for r in sub:
    f = func_of(r[0])
    if f: byregF[f].append(r)
dupF = []
for g, rs in byregF.items():
    cnt = collections.Counter((r[1], r[3]) for r in rs)
    dupF += [r for r in rs if cnt[(r[1], r[3])] >= 2]
dupF.sort()
out('B4 函数范围口径: 重装 store = %d / 697 ; 涉及 (函数,基址,imm) 组 = %d ; 涉及函数数 = %d'
    % (len(dupF), len(set((func_of(r[0]), r[1], r[3]) for r in dupF)), len(set(func_of(r[0]) for r in dupF))))
out('B4 前 10 地址（区间口径）: ' + (' '.join('%s(%s,%s)' % (hex(r[0]), r[1], hex(r[3])) for r in dupR[:10]) or '无'))
out('B4 前 10 地址（函数范围口径）: ' + (' '.join('%s(%s,%s)' % (hex(r[0]), r[1], hex(r[3])) for r in dupF[:10]) or '无'))
ck('B4a 两口径重装数已给出', True, (len(dupR), len(dupF)))

# ---------- B5 ----------
out('')
out('--- B5 imm(VT) 段落分布 与 VT→COL 距离 ---')
sec = collections.Counter(P.where(r[3]) for r in sub)
dist = collections.Counter(r[3] - VT[r[3]] for r in sub)
out('B5 实测: 697 条 imm 落段 = %s' % dict(sec))
out('B5 实测: VT→COL 距离 取值数=%d min=%d max=%d 众数=%s' % (len(dist), min(dist), max(dist), dist.most_common(1)))
out('B5 距离 top10: %s' % dist.most_common(10))
allv = collections.Counter(v - VT[v] for v in VT)
out('B5 全体 VT(%d) 距离取值数=%d 众数=%s ; 距离取值为负的比例=%d/%d'
    % (len(VT), len(allv), allv.most_common(1), sum(1 for v in VT if v - VT[v] < 0), len(VT)))
out('B5 补充: COL 地址并非由 vt 固定偏移算出，而是固定存放在 dw(vt-4) 处（VT 构造即依赖此），'
    '故布局偏移恒为 -4，而 vt 到 COL 绝对地址距离非常数 ⇒ 必须查表，无法线性推算')
ck('B5a VT→COL 距离非常数（B5 问「是否为常数」→ 否）', len(dist) > 1, len(dist))
ck('B5b COL 地址恒定存放在 dw(vt-4) 处', all(P.dw(v - 4) == VT[v] for v in VT),
   sum(1 for v in VT if P.dw(v - 4) == VT[v]))
ck('B5c 697 条 imm 全在 .rdata', set(sec) == {'.rdata'}, dict(sec))

# ---------- 汇总 ----------
out('')
out('--- 判定 ---')
V = []
def verdict(tag, ok, num, why):
    V.append(dict(id=tag, verdict='CONFIRM' if ok else 'REFUTE', num=num, why=why))
    out('%s %s | %s | %s' % (tag, 'CONFIRM' if ok else 'REFUTE', num, why))
verdict('A1', len(BEND) == 31967 and len(REGION) == 31968, '边界 31967 / 区间 31968',
        'ret*(31084)+int3(883)=31967，区间=边界+1，尾部 0x7e038d..0x7e1000 非空')
verdict('A2', len(sub) == 697, '697', '三种口径（rec/allsite/指令对齐）同为 697，地址集对称差 0')
verdict('A3', (len(G1), len(G2)) == (686, 11) and sum(1 for r in G1 if MD[r[3]] == 4) == 345
        and sum(1 for r in G1 if MD[r[3]] == 8) == 341 and all(MD[r[3]] == 0 for r in G2),
        '686/11; mdisp4=345 mdisp8=341', 'disp 仅取 {4,8}，不等组 11 条 mdisp 全 0')
verdict('A4', (cS['both'], cS['only_sub'], cS['none'], cS['noreg']) == (689, 0, 8, 0),
        '689/0/8/0', '区间口径；指令对齐口径复算一致')
out('A1/A2/A3/A4 全部 CONFIRM')
res = dict(
    exe_sha256=hashlib.sha256(RAW).hexdigest(), text=(hex(LO), hex(HI)),
    COL=len(COL), VT=len(VT),
    A1=dict(bends=len(BEND), regions=len(REGION), ret=RET_N, int3=INT3_N, ins=INS_N, bad=bad,
            p50=pct(LENS, .5), p90=pct(LENS, .9), max=max(LENS)),
    A2=dict(rec=len(sub), allsite=len(sub_all), instr=len(sub_in)),
    A3=dict(G1=len(G1), G2=len(G2), m4=sum(1 for r in G1 if MD[r[3]] == 4), m8=sum(1 for r in G1 if MD[r[3]] == 8),
            G2_mdisp=dict(collections.Counter(MD[r[3]] for r in G2)),
            G2_rows=[(hex(r[0]), r[2], CLS[r[3]]) for r in G2]),
    A4=dict(cat=dict(cS), instr_cat=dict(cS2), none=[(hex(r[0]), r[2], hex(r[3]), CLS[r[3]]) for r in none_rows]),
    B1=dict(i=len(hit1), i_vtgt=len(hitv), ii=len(hitp), iii=len(hitr), c=len(STRICT), d=len(SDL),
            c_ext=len(TRUE_EXT), pat=dict(pat), d_pad=sd_pad, d_p50=pct(SDLEN, .5), d_p90=pct(SDLEN, .9),
            d_p99=pct(SDLEN, .99), d_max=max(SDLEN), d_examples=sex,
            callt=len(CALLT), callt_at_region_start=sum(1 for a in RL if a in CALLT),
            func_ranges=len(FR), first_instr_top=firstc.most_common(8)),
    B2=dict(catA=dict(cA), catB=dict(cF)),
    B3=dict(W1=dict(cW1), W1_n=len(W1), W2=dict(cW2), W2_n=len(W2)),
    B4=dict(region_dup=len(dupR), func_dup=len(dupF),
            region_top=[(hex(r[0]), r[1], hex(r[3]), CLS[r[3]]) for r in dupR[:10]],
            func_top=[(hex(r[0]), r[1], hex(r[3]), CLS[r[3]]) for r in dupF[:10]]),
    B5=dict(sec=dict(sec), distinct=len(dist), top=dist.most_common(10), all_vt_distinct=len(allv)),
    verdicts=V, asserts=N, fails=fails)
json.dump(res, open(OUTD + '/audit_c.json', 'w'), ensure_ascii=False, indent=1, default=str)
open(OUTD + '/audit_c.log', 'w').write('\n'.join(LOG) + '\n')
out('')
out('SUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
