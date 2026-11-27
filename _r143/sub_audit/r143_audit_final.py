#!/usr/bin/env python3
"""R143 跨家族只读复核（deepseek，role=audit）：单条命令跑完 8 项复算，写 sub_audit/audit_result.json。

独立实现（不 import _r143/r143lib.py，避免同错复现）：
  * 自解析 PE 段表；chunk=32768 流式 disasm_lite（md.detail=False，不常驻指令对象）
  * 自写操作数解析器：接受十进制/十六进制/负位移，显式识别 [base+index*scale]
  * 单趟扫描同时产出：指令数 / 间接 call,jmp / slot0 装表 / dword 装载 / 每个装载的使用分类
  * 另做基本块内（分支截断）构造装表 -> 同寄存器装载 -> 派发 的严格链接计数（第 8 项第 4 条证据）
"""
import re, json, struct, hashlib, subprocess, collections, bisect, random

P = 'ra2bench/gamemd.exe'
CHUNK = 32768
OUT = '_r143/sub_audit/audit_result.json'
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

DATA = open(P, 'rb').read(); N = len(DATA)
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [dict(n=s.Name.decode().rstrip('\x00'), va=s.VirtualAddress, vs=s.Misc_VirtualSize,
             raw=s.PointerToRawData, rs=s.SizeOfRawData) for s in pe.sections]
TEXT = [s for s in SECS if s['n'] == '.text'][0]

def va2off(va):
    for s in SECS:
        lo = IB + s['va']
        if lo <= va < lo + max(s['vs'], s['rs']):
            d = va - lo
            return s['raw'] + d if d < s['rs'] else None

def rd(va, l):
    o = va2off(va)
    return None if o is None or o + l > N else DATA[o:o + l]

def dw(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def sec_of(va):
    for s in SECS:
        lo = IB + s['va']
        if lo <= va < lo + max(s['vs'], s['rs']):
            return s['n']

def build_vtset():
    pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@'); TDs = {}
    for s in SECS:
        if s['n'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw'] + s['rs']]
            for m in pat.finditer(blob):
                S = IB + s['va'] + m.start(); v = dw(S - 8)
                if v is not None and dw(S - 4) == 0 and sec_of(v) in ('.data', '.rdata'):
                    TDs.setdefault(S - 8, m.group().decode('latin1'))
    td = set(TDs); COL = set()
    for s in SECS:
        if s['n'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw'] + s['rs']]
            for i in range(len(blob) // 4):
                v = struct.unpack_from('<I', blob, i * 4)[0]
                if v in td:
                    c = IB + s['va'] + i * 4 - 12
                    if dw(c) == 0 and dw(c + 12) == v and dw(c + 16) != 0:
                        COL.add(c)
    V = set()
    for s in SECS:
        if s['n'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw'] + s['rs']]
            for i in range(len(blob) // 4):
                v = struct.unpack_from('<I', blob, i * 4)[0]
                if v in COL:
                    vt = IB + s['va'] + i * 4 + 4
                    if dw(vt - 4) == v:
                        V.add(vt)
    return TDs, COL, V

TDs, COL, VTS = build_vtset()

GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi'); STK = ('esp', 'ebp')
SZ = ('byte', 'word', 'dword', 'qword', 'fword', 'tbyte', 'oword', 'xmmword')
MEM = re.compile(r'^(?:(%s) ptr )?\[(.+)\]$' % '|'.join(SZ))
def pm(s):
    m = MEM.match(s or '')
    if not m:
        return None
    inner = re.sub(r'\s+', '', m.group(2))
    toks = [t for t in inner.replace('-', '+-').split('+') if t]
    b = i = None; sc = 1; d = 0
    for t in toks:
        if '*' in t:
            r, c = t.split('*'); i, sc = r, int(c, 0)
        elif re.fullmatch(r'[a-z]{2,3}', t):
            if b is None:
                b = t
            else:
                i, sc = t, 1
        else:
            try:
                d += int(t, 0)
            except ValueError:
                return None
    return m.group(1), b, i, sc, d

IMM = re.compile(r'^-?(?:0x[0-9a-f]+|\d+)$')
def iv(t):
    return (int(t, 16) if t.lstrip('-').startswith('0x') else int(t)) & 0xFFFFFFFF

def norm_main(op):
    """主会话 r143lib.norm 的逐字复刻（用于检验其副作用）。"""
    if not op:
        return ''
    op = re.sub(r'\s*([+,*])\s*', r'\1', op)
    op = re.sub(r'([+-])(\d+)(?![\dx])', lambda m: '%s0x%x' % (m.group(1), int(m.group(2))), op)
    return op
RE_MAIN_CALL = re.compile(r'^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\]$')

KILL = {'mov', 'movzx', 'movsx', 'lea', 'pop', 'bswap', 'lods'}
RMW = {'add', 'sub', 'adc', 'sbb', 'and', 'or', 'xor', 'inc', 'dec', 'neg', 'not',
       'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'imul', 'mul', 'div', 'idiv', 'test', 'cmp', 'xchg'}
ALLW = KILL | RMW
JCC = {'ja','jae','jb','jbe','jc','je','jg','jge','jl','jle','jna','jnae','jnb','jnbe','jnc',
       'jne','jng','jnge','jnl','jnle','jno','jnp','jns','jnz','jo','jp','jpe','jpo','js','jz',
       'loop','loope','loopne','jecxz'}
RETM = {'ret', 'retn', 'iret', 'iretd', 'leave'}

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
def sweep():
    off = TEXT['raw']; end = TEXT['raw'] + TEXT['rs']
    while off < end:
        blob = DATA[off:min(off + CHUNK, end)]
        base = IB + (TEXT['va'] + (off - TEXT['raw'])); cons = 0
        for a, sz, mn, op in md.disasm_lite(blob, base):
            d = a - base
            if d + sz > len(blob):
                break
            cons = d + sz
            yield a, sz, mn, op
        off += cons if cons else 1

text_vend = IB + TEXT['va'] + TEXT['vs']; text_rend = IB + TEXT['va'] + TEXT['rs']

n_ins = 0; n_beyond = 0; last_end = 0
hist = collections.Counter(); sites = []; excl = collections.Counter(); excl_s = collections.defaultdict(list)
abs_base = collections.Counter()
c1 = 0; c1_vt = set(); c1_addrs = []; c1_scaled = []; c1_stackbase = []
store0_any = 0
loads = []; fed = []; memo = {}; pending = {}
n1 = {'scaled': [], 'push': [], 'neg': [], 'negdec': []}
nm_regbase_chk = 0; nm_regbase_mis = 0; nm_all_chk = 0; nm_all_drop = 0; nm_bad = []
negload_total = 0; negload_hist = collections.Counter(); negload_ex = []
negdec_dispatch = 0
scaled_memops = 0
branch_targets = set()
# 基本块内链接：block 内 reg -> ('vt',vt) / ('obj',vt)
blk = {}; links = 0; link_ex = []; block_epoch = 0
idx = 0
for a, sz, mn, op in sweep():
    if a >= text_rend:
        break
    if a >= text_vend:
        n_beyond += 1
    n_ins += 1; last_end = a + sz
    ops = [x.strip() for x in re.split(r',(?![^\[]*\])', op)] if op else []
    mems = [m for m in (pm(o) for o in ops) if m]
    if '[' in (op or ''):
        scaled_memops += 1

    # ---- 使用分类（第 6 项“机会分母”） ----
    ment = set(re.findall(r'\b(eax|ebx|ecx|edx|esi|edi)\b', op or ''))
    for r in list(pending.keys()):
        if r not in ment:
            continue
        rec = pending.pop(r)
        if mn in ('call', 'jmp') and len(mems) == 1 and mems[0][1] == r:
            k = 'fed'
        elif any(m[1] == r or m[2] == r for m in mems):
            k = 'ptr_base'
        elif ops and ops[0] == r and mn in KILL:
            k = 'dead'
        elif ops and ops[0] == r and mn in RMW:
            k = 'val_rmw'
        else:
            k = 'val_read'
        rec['cls'] = k; rec['gap'] = idx - rec['idx']; rec['use_addr'] = a

    # ---- 第 1 项：norm 副作用抽样 ----
    if op:
        if len(n1['scaled']) < 4 and '[' in op and re.search(r'\[\s*[a-z0-9]+\s*[+-]\s*[a-z0-9]+\s*\*', op):
            n1['scaled'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm_main(op)])
        if len(n1['push']) < 4 and mn == 'push' and IMM.match(op):
            n1['push'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm_main(op)])
        if len(n1['neg']) < 4 and re.search(r'\[\s*[a-z0-9]+\s*-\s*0x', op):
            n1['neg'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm_main(op),
                              bool(RE_MAIN_CALL.match(norm_main(op)))])
        if len(n1['negdec']) < 4 and re.search(r'\[\s*[a-z0-9]+\s*-\s*\d+\s*\]', op):
            n1['negdec'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm_main(op),
                                 bool(RE_MAIN_CALL.match(norm_main(op)))])

    # ---- 分支目标收集（用于链接的块边界） ----
    if mn in JCC or mn == 'jmp':
        m = re.fullmatch(r'(0x[0-9a-f]+)', op or '')
        if m:
            branch_targets.add(int(m.group(1), 16))

    is_branch = mn in JCC or mn in RETM or mn == 'call' or mn == 'jmp'

    # ---- 间接 call/jmp ----
    if mn in ('call', 'jmp'):
        if len(ops) == 1:
            mm = pm(ops[0])
            if mm:
                size, b, i, sc, d = mm
                if size == 'dword':
                    if d < 0:
                        negdec_dispatch += 1
                    if i is None and b in GEN:
                        hist[d] += 1; sites.append((a, mn, b, d))
                        l = memo.get(b)
                        if l and l[0] == 'load':
                            fed.append((a, mn, b, d, l[3], l[1], l[2], idx - l[4]))
                        # 第 8 项：块内链接
                        e = blk.get(b)
                        if e and e[0] == 'obj' and e[2] == block_epoch:
                            links += 1
                            if len(link_ex) < 10:
                                link_ex.append([hex(a), op, hex(e[1]), b, d, 'blk'])
                    elif i is not None:
                        excl['scaled_index'] += 1
                        if len(excl_s['scaled_index']) < 6:
                            excl_s['scaled_index'].append([hex(a), op])
                    elif isinstance(b, int) or b is None:
                        abs_base[b if isinstance(b, int) else -1] += 1; excl['absolute'] += 1
                        if len(excl_s['absolute']) < 6:
                            excl_s['absolute'].append([hex(a), op])
                    elif b in STK:
                        excl['stack_base'] += 1
                        if len(excl_s['stack_base']) < 6:
                            excl_s['stack_base'].append([hex(a), op])
                    else:
                        excl['other_reg'] += 1
            # norm 一致性
            nm_all_chk += 1
            nom = norm_main(ops[0]); m2 = RE_MAIN_CALL.match(nom)
            if m2 is None:
                nm_all_drop += 1
                if len(nm_bad) < 8:
                    nm_bad.append([hex(a), ops[0], nom, 'regex_drop'])
            elif mm and mm[1] in GEN and mm[2] is None:
                nm_regbase_chk += 1
                g = m2.group(2); dn = int(g, 16) if g else 0
                if (mm[4] & 0xFFFFFFFF) != (dn & 0xFFFFFFFF):
                    nm_regbase_mis += 1
                    if len(nm_bad) < 8:
                        nm_bad.append([hex(a), ops[0], nom, mm[4], dn])
        for x in ('eax', 'ecx', 'edx'):
            memo[x] = ('clobber', None, None, None, idx)
            pending.pop(x, None); blk.pop(x, None)
        idx += 1
        continue

    if mn == 'mov' and len(ops) == 2:
        m1 = pm(ops[0]); m2 = pm(ops[1])
        if m1 and m2 is None and m1[0] == 'dword' and IMM.match(ops[1]):
            size, b, i, sc, d = m1; v = iv(ops[1])
            if b in GEN and i is None and d == 0:
                store0_any += 1
                if v in VTS:
                    c1 += 1; c1_vt.add(v); c1_addrs.append(a)
                    blk[b] = ('vt', v, block_epoch)   # 块内：b 里装着 vt
            elif i is not None and v in VTS:
                c1_scaled.append([hex(a), ops[0], hex(v)])
            elif v in VTS and d == 0:
                c1_stackbase.append([hex(a), ops[0], hex(v)])
        if m2 and m1 is None and m2[0] == 'dword':
            size, b, i, sc, d = m2
            dst = ops[0]
            if d < 0:
                negload_total += 1
                negload_hist[(b, d)] += 1
                if len(negload_ex) < 5:
                    negload_ex.append([hex(a), op])
            rec = dict(addr=a, dst=dst, base=b, index=i, disp=d, idx=idx, cls=None, gap=None, use_addr=None)
            loads.append(rec)
            if dst in GEN:
                memo[dst] = ('load', b, d, a, idx)
                if i is None and b is not None:
                    pending[dst] = rec
                else:
                    pending.pop(dst, None)
                # 块内：从“装着 vt 的寄存器”disp0 装载 -> dst 是对象
                src = blk.get(b)
                if src and src[0] == 'vt' and src[2] == block_epoch and i is None and d == 0:
                    blk[dst] = ('obj', src[1], block_epoch)
                else:
                    blk.pop(dst, None)
        idx += 1
        continue

    if ops and ops[0] in GEN and mn in ALLW:
        memo[ops[0]] = ('other', None, None, None, idx)
        pending.pop(ops[0], None); blk.pop(ops[0], None)
    if is_branch:
        blk.clear(); block_epoch += 1
    elif a in branch_targets:
        blk.clear(); block_epoch += 1
    idx += 1

# ---------------- 汇总 ----------------
fed_addrs = set(r[4] for r in fed)
obj_tot = collections.Counter(); obj_fed = collections.Counter()
obj_cls = collections.defaultdict(collections.Counter); obj_gap = collections.defaultdict(collections.Counter)
obj_dst = collections.defaultdict(collections.Counter)
stk_tot = collections.Counter(); stk_fed = collections.Counter()
for L in loads:
    if L['index'] is not None:
        continue
    if L['base'] in GEN:
        obj_tot[L['disp']] += 1; obj_dst[L['disp']][L['dst']] += 1
        if L['addr'] in fed_addrs:
            obj_fed[L['disp']] += 1
        if L['cls']:
            obj_cls[L['disp']][L['cls']] += 1
        if L['gap'] is not None:
            obj_gap[L['disp']][min(L['gap'], 9)] += 1
    elif L['base'] in STK:
        stk_tot[L['disp']] += 1
        if L['addr'] in fed_addrs:
            stk_fed[L['disp']] += 1

fcls = collections.Counter(); fcls0 = collections.Counter(); fcls_disp = collections.defaultdict(collections.Counter)
for (a, mn, reg, d, la, lb, ld, gap) in fed:
    k = 'obj' if lb in GEN else ('stack' if lb in STK else 'absolute')
    fcls[k] += 1
    fcls_disp[k][d] += 1
    if d == 0:
        fcls0[k] += 1

def rate(f, t):
    return round(f / t, 4) if t else None
def ptrden(k):
    c = obj_cls.get(k, {})
    return c.get('fed', 0), c.get('ptr_base', 0) + c.get('fed', 0)

disp0 = [s[0] for s in sites if s[3] == 0]
c1s = sorted(c1_addrs)
def near(addrs, ws, pts):
    n = 0
    for sa in pts:
        i = bisect.bisect_left(addrs, sa - ws)
        if i < len(addrs) and addrs[i] <= sa + ws:
            n += 1
    return n
random.seed(143)
rand_txt = sorted(random.randint(IB + TEXT['va'], IB + TEXT['va'] + TEXT['vs']) for _ in range(len(disp0)))
PRO = [b'\x55\x8b\xec', b'\x53', b'\x56', b'\x57', b'\x83\xec', b'\x8b\xff\x55', b'\x6a\xff', b'\x51',
       b'\x8b\xc1', b'\xb8', b'\xe9', b'\x8b\x44\x24']
def is_pro(va):
    b = rd(va, 4)
    return bool(b) and any(b.startswith(p) for p in PRO)
vtslot = {}
for k in (0, 4, 8, 0xc, 0x10, 0x44, 0x48):
    t = [dw(vt + k) for vt in VTS]
    t = [v for v in t if v is not None and sec_of(v) == '.text']
    vtslot[k] = dict(n=len(t), pro=sum(1 for v in t if is_pro(v)))
rand_pro = sum(1 for v in rand_txt if is_pro(v))

def objdump_at(va, n=8):
    out = subprocess.run(['i686-w64-mingw32-objdump', '-d', '--start-address=0x%x' % va,
                          '--stop-address=0x%x' % (va + n), P], capture_output=True, text=True).stdout
    rows = []
    for ln in out.splitlines():
        m = re.match(r'^\s+([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$', ln)
        if m:
            rows.append([int(m.group(1), 16), m.group(2).strip(), m.group(3).strip()])
    return rows

fix = {}
for va in (0x47C437, 0x47C440):
    o = va2off(va); cs = []
    for i in md.disasm(DATA[o:o + 8], va):
        cs.append([i.address, i.bytes.hex(), i.mnemonic, i.op_str]); break
    fix[hex(va)] = dict(raw=DATA[o:o + 8].hex(), capstone=cs, objdump=objdump_at(va)[:1])
between = []
for i in md.disasm(DATA[va2off(0x47C437):va2off(0x47C437) + 0x20], 0x47C437):
    if 0x47C437 < i.address < 0x47C440:
        between.append([i.address, i.bytes.hex(), i.mnemonic, i.op_str])
edx_w = [x for x in between if x[2] in ALLW and x[3].split(',')[0].strip() == 'edx']
tail = DATA[TEXT['raw'] + TEXT['vs']:TEXT['raw'] + TEXT['rs']]

res = {
 'meta': {'auditor': 'deepseek work/cn:deepseek-v4.1-flash role=audit (只读)',
          'exe': P, 'bytes': N, 'sha256': hashlib.sha256(DATA).hexdigest(), 'imagebase': hex(IB),
          'chunk': CHUNK,
          'segments': [{'n': s['n'], 'va': hex(IB + s['va']), 'vs': s['vs'], 'rs': s['rs']} for s in SECS]},
 'I1_norm': {
   'scaled_two_reg_sample': n1['scaled'], 'push_imm_sample': n1['push'],
   'neg_hex_sample': n1['neg'], 'neg_dec_sample': n1['negdec'],
   'scaled_mem_ops_in_text': scaled_memops,
   'call_mem_total_checked': nm_all_chk, 'call_mem_dropped_by_norm_regex': nm_all_drop,
   'regbase_checked': nm_regbase_chk, 'regbase_value_corrupted': nm_regbase_mis,
   'bad_samples': nm_bad,
   'neg_disp_dword_loads_total': negload_total,
   'neg_disp_dword_load_top': [[k[0], k[1], v] for k, v in negload_hist.most_common(8)],
   'neg_disp_load_samples': negload_ex,
   'neg_disp_indirect_dispatch_sites': negdec_dispatch},
 'I2_insn': {'mine': n_ins, 'main': 1394120, 'in_padding_beyond_virtualsize': n_beyond,
             'text_va_vs_rs': [hex(IB + TEXT['va']), hex(text_vend), hex(text_rend)],
             'last_insn_end': hex(last_end), 'tail_bytes': len(tail),
             'tail_all_zero': len(set(tail)) == 1 and tail[:1] == b'\x00'},
 'I3_dispatch': {'mine': len(sites), 'main': 18803, 'hist_top8': hist.most_common(8),
                 'hist_sum': sum(hist.values()), 'disp0': hist.get(0, 0),
                 'excluded': dict(excl), 'excluded_samples': dict(excl_s),
                 'absolute_base_total': sum(abs_base.values())},
 'I4_install': {'slot0_sites': c1, 'slot0_distinct_vt': len(c1_vt), 'main_sites': 2741, 'main_vt': 838,
                'any_slot0_store': store0_any,
                'scaled_index_dropped': len(c1_scaled), 'scaled_index_samples': c1_scaled[:5],
                'nonobj_base_slot0': len(c1_stackbase), 'nonobj_base_samples': c1_stackbase[:5],
                'VTSET': {'td': len(TDs), 'col': len(COL), 'vt': len(VTS)}},
 'I5_datapath': {'fed_total': len(fed), 'sites': len(sites),
                 'base_class': dict(fcls), 'base_class_at_disp0': dict(fcls0),
                 'dispatch_disp_by_load_base_class': {k: dict(v.most_common(6)) for k, v in fcls_disp.items()},
                 'gap_hist': dict(collections.Counter(min(r[7], 9) for r in fed))},
 'I6_enrichment': {
   'obj_loads': {k: obj_tot.get(k, 0) for k in (0, 4, 8, 12)},
   'obj_fed': {k: obj_fed.get(k, 0) for k in (0, 4, 8, 12)},
   'rate': {k: rate(obj_fed.get(k, 0), obj_tot.get(k, 0)) for k in (0, 4, 8, 12)},
   'ratio0_over_4_raw': round((obj_fed.get(0, 0) / max(1, obj_tot.get(0, 0))) /
                              max(1e-9, obj_fed.get(4, 0) / max(1, obj_tot.get(4, 0))), 3),
   'use_class': {str(k): dict(obj_cls.get(k, {})) for k in (0, 4, 8)},
   'ptrlike_denominator': {str(k): ptrden(k) for k in (0, 4, 8)},
   'rate_given_ptrlike': {str(k): rate(ptrden(k)[0], ptrden(k)[1]) for k in (0, 4, 8)},
   'ratio0_over_4_ptrlike': round((ptrden(0)[0] / max(1, ptrden(0)[1])) / max(1e-9, ptrden(4)[0] / max(1, ptrden(4)[1])), 3),
   'gap_hist': {str(k): dict(obj_gap.get(k, {})) for k in (0, 4)},
   'dst_reg': {str(k): dict(obj_dst.get(k, {}).most_common(8)) for k in (0, 4)},
   'loads_total': sum(obj_tot.values()), 'fed_total': sum(obj_fed.values()),
   'stack_loads': {k: stk_tot.get(k, 0) for k in (0, 4, 8, 12)},
   'stack_fed': {k: stk_fed.get(k, 0) for k in (0, 4, 8, 12)},
   'stack_rate': {k: rate(stk_fed.get(k, 0), stk_tot.get(k, 0)) for k in (0, 4, 8, 12)},
   'stack_loads_total': sum(stk_tot.values()), 'stack_fed_total': sum(stk_fed.values())},
 'I7_fixed_bytes': {'sites': fix, 'between': between, 'edx_write_between': edx_w},
 'I8_extra_evidence': {
   'block_local_ctor_to_dispatch_links': links, 'samples': link_ex,
   'vt_slot_targets': {hex(k): v for k, v in vtslot.items()}, 'vt_total': len(VTS),
   'random_prologue_rate': round(rand_pro / len(rand_txt), 4),
   'disp0_sites_near_install_1k': near(c1s, 0x1000, disp0),
   'rand_baseline_near_install_1k': near(c1s, 0x1000, rand_txt),
   'disp0_sites_near_install_4k': near(c1s, 0x4000, disp0),
   'rand_baseline_near_install_4k': near(c1s, 0x4000, rand_txt)},
}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
print('WROTE', OUT)
