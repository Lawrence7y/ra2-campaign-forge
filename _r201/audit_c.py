#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 卡 C（审计员 deepseek，只读）：独立复算 A1..A8。
口径声明：
 W-CALLAT   = R200 m11_subfill.py 原口径（宿主=CALLAT 目标集合中 <= store 的最大者；
              窗口 hi=min(下一个 CALLAT 目标, 宿主+4096)）。
 BODY-RET   = 从宿主 h 线性反汇编到第一条 ret 的真实函数体。
 BODY-BOUND = 以 ret/int3 指令结束位置为边界，把 store 所在区间 [prev_bound, next_bound) 当函数体。
本脚本不写任何托管文件，只打印。"""
import sys, struct, json, bisect, collections
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
print('text lo=%s hi_file=%s size=%d' % (hex(LO), hex(HI), HI - LO))
print('gamemd sha256 见命令末尾 sha256sum 输出（同命令内一并打印）')
def in_text(x): return x is not None and LO <= x < HI

# ---------- 共享底座：COL / VT / MD / CLS（与 R200 m11 完全同式） ----------
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
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
print('COL=%d VT=%d' % (len(COL), len(VT)))

# ---------- C7 装表 store 记录（imm 为 dword ptr [reg+disp], imm） ----------
REGNAME = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
recs = []
pos = T['rawptr']; end = T['rawptr'] + T['rawsize']
while pos < end - 6:
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos + 1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        disp = struct.unpack_from('<b', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 3)[0]
        recs.append((va, REGNAME[rm], disp, imm)); pos += 7
    elif mod == 2:
        disp = struct.unpack_from('<i', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 6)[0]
        recs.append((va, REGNAME[rm], disp, imm)); pos += 10
    else:
        pos += 1
sub = [r for r in recs if 1 <= r[2] <= 9 and r[3] in VT]
ck('C0a 小位移(1..9)装表 store 697 条', len(sub) == 697, len(sub))
main11 = [r for r in sub if MD[r[3]] == 0]
ck('C0b 其中 imm 为 mdisp==0 主表类 11 条', len(main11) == 11, len(main11))

# ---------- 单次流式全段扫描：CALLAT 目标 + ret/int3 边界 ----------
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
CALLAT = []; BOUND = []
p2 = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2 + 65536], LO + p2):
        got = True
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
        if mn.startswith('ret') or mn == 'int3':
            BOUND.append(off + sz)
        p2 += sz
    if not got: p2 += 1
SORT = sorted(set(t for _, t in CALLAT))
BOUND.sort()
ck('C0c CALLAT 目标去重 > 1000', len(SORT) > 1000, len(SORT))
print('   ret/int3 边界数=%d  CALLAT 边=%d' % (len(BOUND), len(CALLAT)))

def host_of(c):
    i = bisect.bisect_left(SORT, c) - 1
    return SORT[i] if i >= 0 else None
def next_entry(c):
    i = bisect.bisect_right(SORT, c)
    return SORT[i] if i < len(SORT) else HI
def is_bound(x):
    i = bisect.bisect_left(BOUND, x)
    return i < len(BOUND) and BOUND[i] == x

byhost = collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)
om_h = sorted({host_of(r[0]) for r in main11})

STORE_RE_HIT = lambda op: op.startswith('dword ptr [') and ', 0x' in op

DISP_RE = __import__('re').compile(r'dword ptr \[(e[a-z]{2})(?: ([+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
def parse_store(op):
    """返回 (reg, disp, imm) 或 None"""
    m = DISP_RE.match(op)
    if not m: return None
    d = 0
    if m.group(3) is not None:
        d = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
        if m.group(2) == '-': d = -d
    return m.group(1), d, int(m.group(4), 16)

def scan_ins(ins):
    """ins 元素为 (address, size, mnemonic, op_str)；返回 (has_main, has_sub, 明细[(ad,disp,imm,kind)])"""
    hm = hs = False; det = []
    for ad, _sz, mn, op in ins:
        if mn != 'mov' or not op.startswith('dword ptr ['): continue
        ps = parse_store(op)
        if ps is None: continue
        _reg, dsp, iv = ps
        if iv not in VT: continue
        k = 'main' if MD[iv] == 0 else 'sub'
        det.append((ad, dsp, iv, k))
        if k == 'main': hm = True
        else: hs = True
    return hm, hs, det

def win_ins(h):
    hi = min(next_entry(h), h + 4096); o = P.r2o(h)
    return hi, [(i.address, i.size, i.mnemonic, i.op_str) for i in md.disasm(RAW[o:o + (hi - h)], h)]

def body_ret_ins(h, cap=65536, stop='retint3'):
    """BODY-RET：从宿主线性反汇编，遇到第一条 ret/int3 即止（卡面口径）。
    stop='retjmp' 为 m2_retbody.py 的变体口径，仅作对照。"""
    o = P.r2o(h)
    if o is None: return []
    out = []
    for i in md.disasm(RAW[o:o + cap], h):
        out.append((i.address, i.size, i.mnemonic, i.op_str))
        if stop == 'retjmp':
            if i.mnemonic.startswith('ret') or i.mnemonic == 'jmp': break
        else:
            if i.mnemonic.startswith('ret') or i.mnemonic == 'int3': break
        if len(out) > 20000: break
    return out

# ---------- A2：R200 口径复现 ----------
both = only_sub = only_main = 0; om = []
for h, rs in byhost.items():
    if h is None: continue
    hi, ins = win_ins(h)
    hm, hs, det = scan_ins(ins)
    if hm and hs: both += 1
    elif hs: only_sub += 1
    else: only_main += 1; om.append((h, hi, hm, hs, det))
print('\n[A2] R200 口径: 宿主=%d both=%d only_sub=%d only_main=%d  sub=%d main11=%d'
      % (len(byhost), both, only_sub, only_main, len(sub), len(main11)))
ck('A2 复现 (251,0,11) 且宿主 262 / sub 697 / main11 11',
   (both, only_sub, only_main, len(byhost), len(sub), len(main11)) == (251, 0, 11, 262, 697, 11),
   (both, only_sub, only_main, len(byhost), len(sub), len(main11)))
print('   only_main 宿主数=%d, main11 的宿主去重数=%d(set 相等=%s)'
      % (len(om), len(om_h), set(h for h, *_ in om) == set(om_h)))
print('   main11 逐条->宿主: %s' % [(hex(r[0]), hex(host_of(r[0]))) for r in main11])
print('   only_main 宿主集与 main11 宿主集差集: only=%s main11only=%s'
      % ([hex(x) for x in sorted(set(h for h, *_ in om) - set(om_h))],
         [hex(x) for x in sorted(set(om_h) - set(h for h, *_ in om))]))
ck('A2b only_main 宿主集合 == main11 的去重宿主集合', set(h for h, *_ in om) == set(om_h),
   (len(om), len(om_h)))

# 窗口是否真的覆盖了挂在其下的 store（宿主归组的关键有效性自检）
noutside = 0
for r in sub:
    h = host_of(r[0]); hi = min(next_entry(h), h + 4096)
    if not (h <= r[0] < hi):
        noutside += 1
outdet=[]
for r in sub:
    h = host_of(r[0]); hi = min(next_entry(h), h + 4096)
    if not (h <= r[0] < hi): outdet.append((hex(r[0]), hex(h), hex(hi)))
print('   sub store 落在其宿主 CALLAT 窗口之外（窗口只扫到前段、store 在窗口右边）的条数 = %d / 697 : %s'
      % (noutside, outdet))
om_out = []
for h, hi, hm, hs, det in om:
    rs = byhost[h]
    out = [x for x in rs if not (h <= x[0] < hi)]
    om_out.append(len(out))
print('   11 个 only_main 宿主: 其名下 sub store 落在窗口外的条数 %s（合计 %d）'
      % (om_out, sum(om_out)))
ck('A2c 697 条中无一落在宿主窗口外', noutside == 0, noutside)

# ---------- A3：11 个 only_main 宿主窗口内 vs 真实体内 ----------
print('\n[A3] 11 个 only_main 宿主：CALLAT 窗口 / 16KB 宽松窗口 / BODY-RET 三口径')
a3_win_main = 0; a3_win_zero = 0; a3_body_main = 0; a3_body_zero = 0
a3_body_main_in_host = 0; a3_body_main_out_host = 0
a3_rows = []
for h, hi, hm, hs, det in sorted(om):
    _, ins2 = win_ins(h)
    loose = [(i.address, i.size, i.mnemonic, i.op_str) for i in md.disasm(RAW[P.r2o(h):P.r2o(h) + 16384], h)]
    lm, ls, ldet = scan_ins(loose)
    bi = body_ret_ins(h)
    bend = (bi[-1][0] + bi[-1][1]) if bi else h
    bm, bs, bdet = scan_ins(bi)
    hitwin = len(det)
    if hm: a3_win_main += 1
    if hitwin == 0: a3_win_zero += 1
    if bm: a3_body_main += 1
    if len(bdet) == 0: a3_body_zero += 1
    a3_rows.append(dict(h=h, hi=hi, nwin=hitwin, hm=hm, hs=hs, nloose=len(ldet), lm=lm, ls=ls,
                        bodylen=len(bi), bodyend=bend, nbody=len(bdet), bm=bm, bs=bs))
    print('   host=%s hi=%s wlen=%4d nwin=%d has_main_win=%s | loose16k=%d(m=%s,s=%s) | bodylen=%d bodyend=%s nbody=%d(m=%s,s=%s)'
          % (hex(h), hex(hi), hi - h, hitwin, hm, len(ldet), lm, ls, len(bi),
             hex(bend), len(bdet), bm, bs))
    print('        win_det=%s' % [(hex(a), d, hex(v)) for a, d, v, k in det])
    inbody = [x for x in det if h <= x[0] < bend]
    outbody = [x for x in det if not (h <= x[0] < bend)]
    MAIN_IN = sum(1 for a, d, v, k in inbody if k == 'main')
    MAIN_OUT = sum(1 for a, d, v, k in outbody if k == 'main')
    a3_body_main_in_host += (MAIN_IN > 0)
    a3_body_main_out_host += (MAIN_IN == 0 and MAIN_OUT > 0)
    print('        窗口内主表: 在宿主体内=%d 在体末之后(跨函数)=%d' % (MAIN_IN, MAIN_OUT))
print('   11 个 only_main 宿主的前一字节/首字节(是否为函数入口的粗检):')
for h, hi, hm, hs, det in sorted(om):
    o = P.r2o(h)
    print('     %s prev=%s head=%s' % (hex(h), hex(RAW[o-1]) if o and o > 0 else None, RAW[o:o+10].hex()))
ck('A3a CALLAT 窗口内 has_main=True 的 only_main 宿主数 == 6', a3_win_main == 6, a3_win_main)
ck('A3b CALLAT 窗口内零装表(无任何 imm-in-VT store)者 == 5', a3_win_zero == 5, a3_win_zero)
print('   >> 6 个窗口内有主表的宿主里：主表落在宿主体内(同函数)=%d，主表仅在体末之后(跨函数)=%d'
      % (a3_body_main_in_host, a3_body_main_out_host))
ck('A3d 主表落在宿主自身 ret 体内者 <= 6', a3_body_main_in_host <= 6, a3_body_main_in_host)
ck('A3c 6+5 == 11 个 only_main 宿主全部覆盖', a3_win_main + a3_win_zero == 11, (a3_win_main, a3_win_zero))
print('   >> 窗口口径(与主张一致): has_main=True 者=%d, 零装表者=%d' % (a3_win_main, a3_win_zero))
print('   >> BODY-RET 口径(对照, 独立事实): 体内有主表=%d, 体内零装表=%d' % (a3_body_main, a3_body_zero))

# ---------- A4：窗口终点是否落在 ret/int3 边界 ----------
print('\n[A4] 11 个 only_main 宿主的窗口终点 hi 是否为 ret/int3 边界')
notb = 0; eq_end = 0; rows4 = []; ECUT = []
for r in a3_rows:
    h = r['h']; hi = r['hi']
    b = is_bound(hi)
    pb = is_bound(hi - 1); pb2 = RAW[P.r2o(hi) - 1] if P.r2o(hi) and P.r2o(hi) > 0 else None
    e = r['bodyend']
    if not b and not pb: notb += 1
    same = (e == hi)
    if same: eq_end += 1
    rows4.append((h, hi, b, pb, pb2, e, same))
    cap = (hi - h) == 4096
    # 窗口是否在一条指令中间被切断：从 h 反汇编，累计尺寸是否恰等于窗口长
    tot = 0; nins = 0
    for i in md.disasm(RAW[P.r2o(h):P.r2o(h) + (hi - h)], h):
        tot += i.size; nins += 1
    IN_CUT = (tot != (hi - h))
    ECUT.append((h, IN_CUT, tot, hi - h))
    print('   host=%s hi=%s hi_is_bound=%s hi-1_is_bound=%s prevbyte=%s bodyret_end=%s hi==bodyret_end=%s hi=h+4096=%s'
          % (hex(h), hex(hi), b, pb, hex(pb2) if pb2 is not None else None, hex(e), same, cap))
ck('A4a 窗口终点不是 ret/int3 边界的宿主数', True, notb)
print('   >> 字面判据(hi 既非 ret/int3 指令结束地址、hi-1 也不是)满足者 = %d / 11' % notb)
midf = sum(1 for r in a3_rows if r['bodyend'] > r['hi'])
ck('A4e hi 恰等于宿主体 ret 指令结束地址者', eq_end > 0, eq_end)
print('   >> 严格中间截断(hi < 宿主体 ret 结束地址)者 = %d / 11' % midf)
ck('A4b 存在中间截断的宿主（>0）', midf > 0, midf)
ck('A4c hi 恰等于宿主体 ret 结束地址者统计', True, eq_end)
print('   >> 三者明细: hi 非边界=%d, 严格中间截断=%d, hi==体末=%d' % (notb, midf, eq_end))
nc = sum(1 for _, c, _, _ in ECUT if c)
print('   >> 窗口终点落在指令中间(反汇编覆盖不足窗口长)者 = %d / 11 : %s'
      % (nc, [(hex(h), tot, ln) for h, c, tot, ln in ECUT if c]))
ck('A4d 存在窗口在指令中间被切断的宿主', nc > 0, nc)
print('   >> hi 来源: hi=下一个 CALLAT 目标者=%d, hi=h+4096 上限者=%d'
      % (sum(1 for r in a3_rows if not (r['hi'] - r['h'] == 4096)), sum(1 for r in a3_rows if r['hi'] - r['h'] == 4096)))
over = [(r['h'], r['hi'], r['bodyend']) for r in a3_rows if r['bodyend'] < r['hi']]
print('   >> 窗口越过函数体末(ret 之后)的宿主: %s' % [(hex(a), hex(b), hex(c)) for a, b, c in over])

# ---------- A5：BODY-RET 口径下 262 宿主三分类 ----------
print('\n[A5] BODY-RET 口径 262 宿主三分类')
cats = collections.Counter(); rows5 = []
trunc = 0
for h, rs in sorted(byhost.items()):
    bi = body_ret_ins(h)
    hm, hs, det = scan_ins(bi)
    k = 'both' if (hm and hs) else ('only_sub' if hs else ('only_main' if hm else 'none'))
    cats[k] += 1
    bend = (bi[-1][0] + bi[-1][1]) if bi else h
    last_store = max(r[0] for r in rs)
    bad = last_store >= bend
    if bad: trunc += 1
    rows5.append((h, k, len(bi), len(det), bend, last_store, bad))
print('   BODY-RET: both=%d only_sub=%d only_main=%d none=%d 合计=%d'
      % (cats['both'], cats['only_sub'], cats['only_main'], cats['none'], sum(cats.values())))
ck('A5a BODY-RET 三分类不是 251/0/11', not (cats['both'], cats['only_sub'], cats['only_main']) == (251, 0, 11),
   dict(cats))
ck('A5b BODY-RET both 显著小于 251（<251）', cats['both'] < 251, cats['both'])
print('   自检：宿主体在自身 sub store 之前就终止（体截断）的宿主数=%d / 262' % trunc)
ck('A5c 无体截断（每条 sub store 都落在其宿主体内）', trunc == 0, trunc)
# 稳健性变体：停到 ret 或 jmp
cats_rj = collections.Counter()
for h, rs in sorted(byhost.items()):
    hm, hs, det = scan_ins(body_ret_ins(h, stop='retjmp'))
    k = 'both' if (hm and hs) else ('only_sub' if hs else ('only_main' if hm else 'none'))
    cats_rj[k] += 1
print('   变体(停到 ret/jmp): both=%d only_sub=%d only_main=%d none=%d'
      % (cats_rj['both'], cats_rj['only_sub'], cats_rj['only_main'], cats_rj['none']))
# 变体二：宿主落在 [prev ret/int3 结束, next ret/int3 结束) 区间的整体扫描（不受首 ret 截断影响）
def span_of_pre(va):
    k = bisect.bisect_right(BOUND, va) - 1
    lo = BOUND[k] if k >= 0 else LO
    j = bisect.bisect_right(BOUND, va)
    hi = BOUND[j] if j < len(BOUND) else HI
    return lo, hi
cats_sp = collections.Counter()
for h, rs in sorted(byhost.items()):
    lo, hi = span_of_pre(h)
    o = P.r2o(lo)
    ins = [(i.address, i.size, i.mnemonic, i.op_str) for i in md.disasm(RAW[o:o + (hi - lo)], lo)]
    hm, hs, det = scan_ins(ins)
    k = 'both' if (hm and hs) else ('only_sub' if hs else ('only_main' if hm else 'none'))
    cats_sp[k] += 1
print('   变体(宿主所在 ret/int3 区间整体): both=%d only_sub=%d only_main=%d none=%d'
      % (cats_sp['both'], cats_sp['only_sub'], cats_sp['only_main'], cats_sp['none']))
ck('A5d 三口径下 both 全部 < 251', max(cats['both'], cats_rj['both'], cats_sp['both']) < 251,
   (cats['both'], cats_rj['both'], cats_sp['both']))
ck('A5e 三口径下都不等于 251/0/11', all((c['both'], c['only_sub'], c['only_main']) != (251, 0, 11)
   for c in (cats, cats_rj, cats_sp)),
   (dict(cats), dict(cats_rj), dict(cats_sp)))
for k in ('only_main', 'none'):
    for h, kk, bl, nd, bend, ls, bad in rows5:
        if kk == k: print('     %s %s bodylen=%d ndet=%d bodyend=%s laststore=%s' % (hex(h), kk, bl, nd, hex(bend), hex(ls)))

# 函数级去重（函数体 = ret/int3 边界区间，以「含至少一条子表 store 的区间」为分母）
funcs = collections.defaultdict(lambda: [0, 0])
__ma = [r for r in recs if r[3] in VT and MD[r[3]] == 0]
__su = [r for r in recs if r[3] in VT and MD[r[3]] != 0]
for r in sub:
    lo, hi = span_of_pre(r[0]); funcs[(lo, hi)][1] += 1
for r in __ma:
    lo, hi = span_of_pre(r[0])
    if (lo, hi) in funcs: funcs[(lo, hi)][0] += 1
nfunc = len(funcs)
fboth = sum(1 for k, v in funcs.items() if v[0] > 0 and v[1] > 0)
fonly = sum(1 for k, v in funcs.items() if v[0] == 0 and v[1] > 0)
print('   函数级去重: 含子表 store 的函数体=%d, 其中同函数内另有主表 store=%d, 仅子表=%d'
      % (nfunc, fboth, fonly))
# 变体三：BODY-RET-PLUS（从宿主线性反汇编，直到「该宿主名下最后一条 sub store 之后的第一条 ret」）
cats_bp = collections.Counter()
for h, rs in sorted(byhost.items()):
    last = max(x[0] for x in rs)
    o = P.r2o(h); ins = []; ended = False
    lim = max(0, last - h) + 8192
    for i in md.disasm(RAW[o:o + lim], h):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret') or i.mnemonic == 'int3':
            if i.address + i.size > last: ended = True; break
        if len(ins) > 8000: break
    hm2, hs2, _ = scan_ins(ins)
    k = 'both' if (hm2 and hs2) else ('only_sub' if hs2 else ('only_main' if hm2 else 'none'))
    cats_bp[k] += 1
print('   变体(体=到名下最后一条 sub store 之后的首个 ret): both=%d only_sub=%d only_main=%d none=%d'
      % (cats_bp['both'], cats_bp['only_sub'], cats_bp['only_main'], cats_bp['none']))
ck('A5g 该变体 both 亦 < 251', cats_bp['both'] < 251, dict(cats_bp))
ck('A5f 函数级 both 亦 < 251', fboth < 251, (nfunc, fboth, fonly))

# ---------- A6：store 级（分母 697）BODY-BOUND 口径 ----------
print('\n[A6] store 级三分类（分母 697，函数体=[上一 ret/int3 结束, 下一 ret/int3 结束)）')
mainall = [r for r in recs if r[3] in VT and MD[r[3]] == 0]
suball = [r for r in recs if r[3] in VT and MD[r[3]] != 0]
print('   任意位移装表: main=%d sub=%d total=%d' % (len(mainall), len(suball), len(mainall) + len(suball)))
def span_of(va):
    return span_of_pre(va)
def in_span(lo, hi, arr):
    return [r for r in arr if lo <= r[0] < hi]
cat6 = collections.Counter(); spans = []; rows6 = []
for r in sub:
    lo, hi = span_of(r[0])
    ma = in_span(lo, hi, mainall); su = in_span(lo, hi, suball)
    k = 'both' if (ma and su) else ('only_sub' if su else 'none')
    cat6[k] += 1; spans.append(hi - lo)
    rows6.append((r[0], r[2], r[3], lo, hi, len(ma), len(su), k))
print('   store 级: both=%d only_sub=%d none=%d 合计=%d' % (cat6['both'], cat6['only_sub'], cat6['none'], sum(cat6.values())))
spans.sort()
print('   span 中位=%d p90=%d max=%d' % (spans[len(spans) // 2], spans[int(len(spans) * 0.9)], spans[-1]))
ck('A6a 697 条 store 三分类合计为 697', sum(cat6.values()) == 697, sum(cat6.values()))
nc6 = collections.Counter(r[5] for r in rows6)
print('   每条 sub store 所属函数体内主表 store 条数分布 (n_main: 条数) = %s' % dict(sorted(nc6.items())))
ck('A6d none 的 8 条其函数体内主表条数不为 0（说明 none 非零装表）', True, 'see rows above')
ck('A6b 复算 (152,537,8)', (cat6['both'], cat6['only_sub'], cat6['none']) == (152, 537, 8),
   (cat6['both'], cat6['only_sub'], cat6['none']))
print('   >> 我的复算: both=%d only_sub=%d none=%d；主会话称 152/537/8 差异=%s'
      % (cat6['both'], cat6['only_sub'], cat6['none'],
         '无' if (cat6['both'], cat6['only_sub'], cat6['none']) == (152, 537, 8) else '有'))
for row in rows6:
    if row[7] != 'both':
        print('     %s disp=%d imm=%s k=%s span=%s..%s n_main=%d n_sub=%d'
              % (hex(row[0]), row[1], hex(row[2]), row[7], hex(row[3]), hex(row[4]), row[5], row[6]))

# ---------- A7：251 表述在真实函数体口径下 ----------
print('\n[A7] both 口径对比')
ok7 = cats['both'] < 251
print('   CALLAT 宿主级 both=%d vs BODY-RET 宿主级 both=%d vs store 级 both=%d'
      % (both, cats['both'], cat6['both']))
ck('A7a BODY-RET 宿主级 both < 251（251 表述不成立）', ok7, cats['both'])
ck('A7b store 级 both 亦 < 251', cat6['both'] < 251, cat6['both'])

# ---------- A8：disp8 vs imm 的 COL mdisp ----------
print('\n[A8] 697 条子表 store 的 disp8 与 imm 的 COL mdisp 比对')
eq = [r for r in sub if r[2] == MD[r[3]]]
ne = [r for r in sub if r[2] != MD[r[3]]]
print('   相等=%d 不等=%d' % (len(eq), len(ne)))
ck('A8a 相等 686 / 不等 11', (len(eq), len(ne)) == (686, 11), (len(eq), len(ne)))
ne_m0 = all(MD[r[3]] == 0 for r in ne)
ck('A8b 不等 11 条全部满足 mdisp==0', ne_m0, [(hex(r[0]), r[2], hex(r[3]), MD[r[3]]) for r in ne])
ck('A8c 不等集 == main11 集', set(x[0] for x in ne) == set(x[0] for x in main11), len(ne))
ck('A8d 不等集位移仅 {4,8}', set(r[2] for r in ne) <= {4, 8}, sorted(set(r[2] for r in ne)))
for r in ne:
    print('     ne at=%s reg=%s disp=%d imm=%s mdisp=%d cls=%s' % (hex(r[0]), r[1], r[2], hex(r[3]), MD[r[3]], CLS[r[3]]))
sd = collections.Counter(r[2] for r in sub)
md_ok = collections.Counter(MD[r[3]] for r in sub)
print('   子表 store 位移分布=%s ; imm 的 mdisp 分布=%s' % (dict(sorted(sd.items())), dict(sorted(md_ok.items()))))
eq11 = [r for r in eq if MD[r[3]] == 0]
print('   另注：disp8==mdisp 的 686 条里 imm 为 mdisp==0 的条数=%d' % len(eq11))

print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
