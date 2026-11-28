#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 卡 B：槽 0 首 call 的另外 50 个目标身份定性。

口径：
  S0 集合完全按 R200 m8_final.py / exec_b/callgraph.py：603 对 pairs，min(nslot(vt_d),nslot(vt_b))>=1
  且 dw(vt_d)!=dw(vt_b)，得 516 条 store / 516 个唯一实现。
  首 call = 实现体起始反汇编（600 字节 / 300 条，遇 ret 停）中的第一条 mn=='call' 且 operand 为
  0x 十六进制的目标。这是 R200 得到 51 目标 / 510 记录 / 0x7C8B3D 360 条的原始口径；
  卡面文字所给的「CALLAT 窗口」口径会得 53/514/362（见 §8 反控与脚本输出）。
  全部扫描用 disasm_lite/detail=False；不把全量 detail 对象常驻。
"""
import sys, struct, json, bisect, collections, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []
N = 0
def ck(nm, c, d=''):
    global N
    N += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def hx(x):
    return hex(x) if x is not None else 'None'

RAW = P.RAW
T = P.B['.text']
LO, HI = T['lo'], T['hi_file']
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
def in_text(x):
    return x is not None and LO <= x < HI

def wv(sn):
    s = P.B[sn]
    n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n

# ---------- RTTI / vtable 重建（与 R200 完全一致） ----------
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0:
            continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata':
            continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        COL[base + 4 * i] = dict(mdisp=struct.unpack('<i', struct.pack('<I', w[i + 1]))[0],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS:
        return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)):
            break
        k += 1
    NS[vt] = k
    return k
ck('C0a COL/VT == 1214/1214', (len(COL), len(VT)) == (1214, 1214), (len(COL), len(VT)))

# ---------- 槽 0 实现集合 ----------
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
ck('C0b pairs == 603', len(pairs) == 603, len(pairs))
s0 = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1:
        continue
    a, b = P.dw(vt_d), P.dw(vt_b)
    if a != b:
        s0.append((vt_d, a, vt_b))
impls = sorted(set(a for _, a, _ in s0))
ck('C0c 516 store / 516 实现', (len(s0), len(impls)) == (516, 516), (len(s0), len(impls)))

# ---------- 全段 call rel32 扫描（单次迭代 + 1 字节重同步，detail=False） ----------
CALLAT = []
resync = 0
pos = 0
while pos < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[pos:pos + 65536], LO + pos):
        got = True
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t):
                CALLAT.append((off, t))
        pos += sz
    if not got:
        pos += 1
        resync += 1
ck('C0d CALLAT 单次迭代 == 68,244', len(CALLAT) == 68244, len(CALLAT))
CALLERS = collections.defaultdict(list)
for c, t in CALLAT:
    CALLERS[t].append(c)
SORT = sorted(set(t for _, t in CALLAT))

# ---------- 首 call 的两套口径 ----------
def first_body(a, maxb=600, maxi=300):
    o = P.r2o(a)
    if o is None:
        return None
    for i in md.disasm(RAW[o:o + maxb], a):
        if i.mnemonic == 'call' and i.op_str.startswith('0x'):
            return int(i.op_str, 16)
        if i.mnemonic.startswith('ret'):
            return None
    return None

def next_entry(c):
    i = bisect.bisect_right(SORT, c)
    return SORT[i] if i < len(SORT) else HI

def first_window(a, cap=4096, in_filter=True):
    end = min(next_entry(a), a + cap)
    o = P.r2o(a)
    if o is None or end <= a:
        return None
    for j in md.disasm(RAW[o:o + (end - a)], a):
        if j.mnemonic == 'call' and j.op_str.startswith('0x'):
            t = int(j.op_str, 16)
            if not in_filter or in_text(t):
                return t
    return None

# ---------- 虚表槽反查 ----------
ALLREF = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        ALLREF[P.dw(vt + 4 * k)].add((vt, k))

# ---------- 1. 复现校验（R200 原生 body 口径） ----------
recs = []
for a in impls:
    t = first_body(a)
    if t is not None:
        recs.append((a, t))
cnt = collections.Counter(t for _, t in recs)
tgts = sorted(cnt)
inv_t = sorted(t for t in tgts if t in ALLREF)
inv_r = [(a, t) for a, t in recs if t in ALLREF]
ck('C1a 去重目标 51 / 记录 510', (len(tgts), len(recs)) == (51, 510), (len(tgts), len(recs)))
ck('C1b 0x7C8B3D 记录 360', cnt[0x7C8B3D] == 360, cnt[0x7C8B3D])
ck('C1c 虚表槽内目标 4 / 记录 9', (len(inv_t), len(inv_r)) == (4, 9), (len(inv_t), len(inv_r)))
ck('C1d 四个槽目标与 R200 一致',
   inv_t == [0x40B270, 0x410260, 0x557AC0, 0x55A9B0], [hx(t) for t in inv_t])
if fails:
    print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
    sys.exit(1)
print('   复现基线 | targets=%d recs=%d 7c8b3d=%d invt=%d invr=%d' %
      (len(tgts), len(recs), cnt[0x7C8B3D], len(inv_t), len(inv_r)))

FIFTY = [t for t in tgts if t != 0x7C8B3D]
ck('C1e 另外 50 个目标', len(FIFTY) == 50, len(FIFTY))
ck('C1f 另外 50 个目标记录数合计 150',
   sum(cnt[t] for t in FIFTY) == 150, sum(cnt[t] for t in FIFTY))

# ---------- 2/4/6. 每个目标：字节、字符串、call 出边 ----------
def prevbyte(va):
    o = P.r2o(va)
    return RAW[o - 1] if o and o > 0 else None

def headbytes(va, n=24):
    o = P.r2o(va)
    return RAW[o:o + n].hex() if o is not None else None

PRINTABLE = set(range(0x20, 0x7f))
def str_samples(va, lim=512, maxn=2):
    """目标起始后 lim 字节内找 push imm32 / mov reg,imm32，imm 处取 P.cstr。"""
    o = P.r2o(va)
    if o is None:
        return []
    out = []
    for i in md.disasm(RAW[o:o + lim], va):
        imm = None
        if i.mnemonic == 'push' and i.op_str.startswith('0x'):
            imm = int(i.op_str, 16)
        elif i.mnemonic == 'mov' and ', 0x' in i.op_str:
            try:
                imm = int(i.op_str.rsplit(', ', 1)[1], 16)
            except Exception:
                pass
        if imm is None or P.sec_of(imm) not in ('.rdata', '.data'):
            continue
        s = P.cstr(imm, 120)
        if not s or not (8 <= len(s) <= 120):
            continue
        ratio = sum(1 for c in s if c in PRINTABLE) / len(s)
        if ratio > 0.9:
            sample = s.decode('latin1').replace('\n', '\\n').replace('\r', '\\r')
            if sample not in [x[1] for x in out]:
                out.append((hx(imm), sample))
            if len(out) >= maxn:
                break
    return out

def call_out(va, lim=512):
    o = P.r2o(va)
    if o is None:
        return []
    seen = set()
    for i in md.disasm(RAW[o:o + lim], va):
        if i.mnemonic == 'call' and i.op_str.startswith('0x'):
            seen.add(int(i.op_str, 16))
    return sorted(seen)

ROWS = []
print('\n=== §2 50 个目标逐项（地址/记录/头24字节/段/前一字节/in_text） ===')
print('target     recs head24                                    sec      prev in_text')
for t in FIFTY:
    r = dict(target=hx(t), recs=cnt[t], head24=headbytes(t), sec=P.where(t),
             prev=hx(prevbyte(t)) if prevbyte(t) is not None else None, in_text=in_text(t))
    ROWS.append(r)
    print('%-9s %-4d %-46s %-8s %-5s %s' %
          (r['target'], r['recs'], r['head24'], r['sec'], r['prev'], r['in_text']))
ck('C2a 50 项全部 in_text', all(r['in_text'] for r in ROWS),
   sum(1 for r in ROWS if r['in_text']))

# ---------- 3. CALLERS 独立口径 ----------
print('\n=== §3 CALLERS 反查（全 .text call rel32 命中数 vs 记录数） ===')
print('target     recs callers ratio(records/callers)')
for r in ROWS:
    t = int(r['target'], 16)
    nc = len(CALLERS.get(t, []))
    r['callers'] = nc
    r['ratio'] = round(r['recs'] / nc, 4) if nc else None
    print('%-9s %-4d %-7d %s' % (r['target'], r['recs'], nc, r['ratio']))

# ---------- 4. 字符串样本 ----------
print('\n=== §4 目标体内 512 字节 ASCII 字符串引用 ===')
for r in ROWS:
    r['strings'] = str_samples(int(r['target'], 16))
    print('%-9s %s' % (r['target'], r['strings'] if r['strings'] else None))

# ---------- 5. 虚表出现 ----------
print('\n=== §5 目标是否出现在虚表槽 ===')
for r in ROWS:
    refs = ALLREF.get(int(r['target'], 16), set())
    r['in_vt'] = bool(refs)
    r['vt_refs'] = [(hx(v), k) for v, k in sorted(refs)]
    print('%-9s %-4s %s' % (r['target'], 'yes' if r['in_vt'] else 'no', r['vt_refs'] if r['vt_refs'] else ''))

# ---------- 6. 出边调用与成簇 ----------
print('\n=== §6 目标体内前 512 字节 call 出边 ===')
OUT = {}
for r in ROWS:
    outs = call_out(int(r['target'], 16))
    OUT[int(r['target'], 16)] = outs
    r['outs'] = [hx(x) for x in outs]
    print('%-9s n=%-2d %s' % (r['target'], len(outs), r['outs'] if outs else ''))
FSET = set(FIFTY)
clusters = []
for t, outs in OUT.items():
    peers = sorted(x for x in outs if x in FSET)
    if peers:
        clusters.append((hx(t), [hx(x) for x in peers]))
print('   50 目标内互相调用边: %s' % (clusters if clusters else 'None'))
ck('C6a 出边扫描覆盖全部 50 目标', len(OUT) == 50, len(OUT))

# ---------- 7. 汇总定性 ----------
print('\n=== §7 汇总定性（在虚表 / 有字符串 / 有出边） ===')
groups = collections.defaultdict(list)
for r in ROWS:
    key = (r['in_vt'], bool(r['strings']), bool(r['outs']))
    groups[key].append(r['target'])
for key in sorted(groups, key=lambda x: (not x[0], not x[1], not x[2])):
    print('   in_vt=%-5s str=%-5s out=%-5s size=%-2d reps=%s' %
          (key[0], key[1], key[2], len(groups[key]), groups[key][:5]))
ck('C7a 分组覆盖 50', sum(len(v) for v in groups.values()) == 50,
   sum(len(v) for v in groups.values()))

# ---------- 8. 反控 ----------
print('\n=== §8 反控 ===')
for cap in (2048, 8192):
    w = []
    for a in impls:
        t = first_window(a, cap, True)
        if t is not None:
            w.append(t)
    c = collections.Counter(w)
    print('   cap=%-5d targets=%-3d recs=%-3d 7c8b3d=%d' % (cap, len(c), len(w), c[0x7C8B3D]))
    ck('C8a window cap=%d 已记录' % cap, len(c) > 0, (len(c), len(w)))
w = []
for a in impls:
    t = first_window(a, 4096, False)
    if t is not None:
        w.append(t)
print('   4096 不过滤 in_text: targets=%d recs=%d' % (len(set(w)), len(w)))
ck('C8b 4096 不过滤 in_text 已记录', len(set(w)) > 0, len(set(w)))
w2 = []
for a in impls:
    t = first_window(a, 4096, True)
    if t is not None:
        w2.append(t)
print('   卡面窗口口径 4096 + in_text: targets=%d recs=%d 7c8b3d=%d（R200 的 body 口径是 51/510/360）' %
      (len(set(w2)), len(w2), collections.Counter(w2)[0x7C8B3D]))
ck('C8c 两套口径差异已明示', True, 'body=51/510/360 window=53/514/362')

json.dump(dict(repro=dict(targets=len(tgts), recs=len(recs), c7c8b3d=cnt[0x7C8B3D],
                          invt=[hx(t) for t in inv_t], invrec=len(inv_r)),
               rows=ROWS, clusters=clusters,
               groups={'|'.join(str(x) for x in k): v for k, v in groups.items()},
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/b_firstcall50.json', 'w'),
          ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
