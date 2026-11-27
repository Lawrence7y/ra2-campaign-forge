#!/usr/bin/env python3
"""R143 跨家族只读复核（deepseek，role=audit）：8 项独立复算。只读二进制，产物只写 sub_audit/。

独立实现（不 import r143lib，避免同错复现）：
  - 自解析 PE 段表；chunk=32768 流式 disasm_lite（md.detail=False，不常驻指令对象）
  - 自写操作数解析器，同时接受十进制/十六进制/负位移，显式识别 [base+index*scale]
  - 单趟扫描同时收集：指令数 / 间接 call,jmp / slot0 装表 / 全部 dword 装载 / 每个装载的使用分类
"""
import sys, re, json, struct, hashlib, subprocess, collections, bisect

P = 'ra2bench/gamemd.exe'
CHUNK = 32768
OUT = '_r143/sub_audit/audit_result.json'

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

DATA = open(P, 'rb').read()
N = len(DATA)
pe = pefile.PE(P, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [dict(name=s.Name.decode().rstrip('\x00'), va=s.VirtualAddress, vs=s.Misc_VirtualSize,
             raw=s.PointerToRawData, rs=s.SizeOfRawData) for s in pe.sections]
TEXT = [s for s in SECS if s['name'] == '.text'][0]

def va2off(va):
    for s in SECS:
        lo = IB + s['va']
        if lo <= va < lo + max(s['vs'], s['rs']):
            d = va - lo
            return s['raw'] + d if d < s['rs'] else None
    return None

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
            return s['name']
    return None

def build_vtset():
    pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
    TDs = {}
    for s in SECS:
        if s['name'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw'] + s['rs']]
            for m in pat.finditer(blob):
                S = IB + s['va'] + m.start()
                v = dw(S - 8)
                if v is not None and dw(S - 4) == 0 and sec_of(v) in ('.data', '.rdata'):
                    TDs.setdefault(S - 8, m.group().decode('latin1'))
    tdset = set(TDs)
    COL = set()
    for s in SECS:
        if s['name'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw'] + s['rs']]
            for i in range(len(blob) // 4):
                v = struct.unpack_from('<I', blob, i * 4)[0]
                if v in tdset:
                    c = IB + s['va'] + i * 4 - 12
                    if dw(c) == 0 and dw(c + 12) == v and dw(c + 16) != 0:
                        COL.add(c)
    VTS = set()
    for s in SECS:
        if s['name'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw'] + s['rs']]
            for i in range(len(blob) // 4):
                v = struct.unpack_from('<I', blob, i * 4)[0]
                if v in COL:
                    vt = IB + s['va'] + i * 4 + 4
                    if dw(vt - 4) == v:
                        VTS.add(vt)
    return TDs, COL, VTS

TDs, COL, VTS = build_vtset()

GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')
STK = ('esp', 'ebp')
REG_ANY = set(GEN) | set(STK) | {'ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp',
                                 'al', 'bl', 'cl', 'dl', 'ah', 'bh', 'ch', 'dh'}
SZ = ('byte', 'word', 'dword', 'qword', 'fword', 'tbyte', 'oword', 'xmmword')
MEM_RE = re.compile(r'^(?:(%s) ptr )?\[(.+)\]$' % '|'.join(SZ))
# 纯 kill（不读旧值）
KILL = {'mov', 'movzx', 'movsx', 'lea', 'pop', 'bswap', 'lods'}
# 读-改-写（读过旧值）
RMW = {'add', 'sub', 'adc', 'sbb', 'and', 'or', 'xor', 'inc', 'dec', 'neg', 'not',
       'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'imul', 'mul', 'div', 'idiv',
       'test', 'cmp', 'xchg'}
ALLW = KILL | RMW

def split_ops(op):
    parts, cur, depth = [], '', 0
    for ch in op:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur.strip())
            cur = ''
        else:
            cur += ch
    parts.append(cur.strip())
    return parts

def parse_mem(s):
    if not s:
        return None
    m = MEM_RE.match(s)
    if not m:
        return None
    size = m.group(1)
    inner = re.sub(r'\s+', '', m.group(2))
    tokens = [t.strip() for t in re.split(r'\+', inner.replace('-', '+-')) if t.strip()]
    base = index = None
    scale = 1
    disp = 0
    for t in tokens:
        if '*' in t:
            r, sc = t.split('*')
            index, scale = r.strip(), int(sc, 0)
        elif re.fullmatch(r'[a-z]{2,3}', t) and t in REG_ANY:
            if base is None:
                base = t
            else:
                index, scale = t, 1
        else:
            try:
                disp += int(t, 0)
            except ValueError:
                return None
    return size, base, index, scale, disp

IMM_RE = re.compile(r'^-?(?:0x[0-9a-f]+|\d+)$')
def is_imm(t):
    return t is not None and IMM_RE.match(t) is not None

def immval(t):
    v = int(t, 16) if t.lstrip('-').startswith('0x') else int(t)
    return v & 0xFFFFFFFF

def norm(op):
    """主会话 r143lib.norm 的逐字等价实现，用于检验它是否篡改/丢弃操作数。"""
    if not op:
        return ''
    op = re.sub(r'\s*([+,*])\s*', r'\1', op)
    op = re.sub(r'([+-])(\d+)(?![\dx])', lambda m: '%s0x%x' % (m.group(1), int(m.group(2))), op)
    return op

RE_CALL_N = re.compile(r'^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\]$')

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def sweep():
    off = TEXT['raw']; end = TEXT['raw'] + TEXT['rs']
    while off < end:
        blob = DATA[off:min(off + CHUNK, end)]
        base = IB + (TEXT['va'] + (off - TEXT['raw']))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(blob, base):
            d = a - base
            if d + sz > len(blob):
                break
            consumed = d + sz
            yield a, sz, mn, op
        off += consumed if consumed else 1

text_vend = IB + TEXT['va'] + TEXT['vs']
text_rend = IB + TEXT['va'] + TEXT['rs']

n_ins = 0; n_ins_beyond_vs = 0; last_end = 0
disp_hist = collections.Counter()
sites = []
excl = collections.Counter(); excl_s = collections.defaultdict(list)
abs_call = collections.Counter()
c1 = 0; c1_vts = set(); c1_addrs = []; c1_scaled = []; c1_otherbase = []
store_slot0_any = 0
loads = []
fed = []            # (dispatch_addr, mn, reg, dispatch_disp, load_addr, load_base, load_disp, gap)
memo = {}
pending = {}
disp_regs = {'eax', 'ecx', 'edx'}
n1 = {'scaled': [], 'push': [], 'neg': [], 'neg_disp': []}
norm_checked = 0; norm_mismatch = 0; norm_bad = []
norm_checked_all = 0; norm_mismatch_all = 0
neload = collections.Counter()   # 负位移装载（主口径会丢）
neload_obj = collections.Counter()
nedispatch = 0
scaled_ops = 0
idx = 0

for a, sz, mn, op in sweep():
    if a >= text_rend:
        break
    if a >= text_vend:
        n_ins_beyond_vs += 1
    n_ins += 1
    last_end = a + sz
    ops = split_ops(op) if op else []
    mems = [m for m in (parse_mem(o) for o in ops) if m]
    if '[' in (op or ''):
        scaled_ops += 1

    # 使用分类（item 6 机会分析）
    ment = set(re.findall(r'\b(eax|ebx|ecx|edx|esi|edi)\b', op or ''))
    for reg in list(pending.keys()):
        if reg not in ment:
            continue
        rec = pending.pop(reg)
        if mn in ('call', 'jmp') and len(mems) == 1 and mems[0][1] == reg:
            k = 'fed'
        elif any(m[1] == reg or m[2] == reg for m in mems):
            k = 'ptr_base'
        elif ops and ops[0] == reg and mn in KILL:
            k = 'dead'
        elif ops and ops[0] == reg and mn in RMW:
            k = 'val_rmw'
        else:
            k = 'val_read'
        rec['cls'] = k
        rec['gap'] = idx - rec['idx']
        rec['use_addr'] = a

    # item 1 抽样
    if op:
        if '[' in op and re.search(r'\[\s*[a-z0-9]+\s*[+-]\s*[a-z0-9]+\s*\*', op) and len(n1['scaled']) < 4:
            n1['scaled'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm(op)])
        if mn == 'push' and IMM_RE.match(op) and len(n1['push']) < 4:
            n1['push'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm(op)])
        if re.search(r'\[\s*[a-z0-9]+\s*-\s*(?:\d+|0x[0-9a-f]+)\s*\]', op) and len(n1['neg']) < 4:
            n1['neg'].append([hex(a), DATA[va2off(a):va2off(a) + sz].hex(), op, norm(op)])

    if mn in ('call', 'jmp'):
        if len(ops) == 1:
            mm = parse_mem(ops[0])
            if mm:
                size, base, index, scale, disp = mm
                if size == 'dword':
                    if disp < 0:
                        nedispatch += 1
                    if index is None and base in GEN:
                        disp_hist[disp] += 1
                        sites.append((a, mn, base, disp))
                        l = memo.get(base)
                        if l and l[0] == 'load':
                            fed.append((a, mn, base, disp, l[3], l[1], l[2], idx - l[4]))
                    elif index is not None:
                        excl['scaled_index'] += 1
                        if len(excl_s['scaled_index']) < 6:
                            excl_s['scaled_index'].append([hex(a), op])
                    elif isinstance(base, int) or base is None:
                        abs_call[base if isinstance(base, int) else -1] += 1
                        excl['absolute'] += 1
                        if len(excl_s['absolute']) < 6:
                            excl_s['absolute'].append([hex(a), op])
                    elif base in STK:
                        excl['stack_base'] += 1
                        if len(excl_s['stack_base']) < 6:
                            excl_s['stack_base'].append([hex(a), op])
                    else:
                        excl['other_reg'] += 1
            # norm 值一致性（仅寄存器基址形态）
            nom = norm(ops[0])
            m2 = RE_CALL_N.match(nom)
            if mm:
                norm_checked_all += 1
                if m2 is None:
                    norm_mismatch_all += 1
                    if len(norm_bad) < 8:
                        norm_bad.append([hex(a), ops[0], nom, 'regex_drop'])
                elif mm[1] in GEN:
                    norm_checked += 1
                    g = m2.group(2)
                    dn = int(g, 16) if g else 0
                    if (mm[4] & 0xFFFFFFFF) != (dn & 0xFFFFFFFF):
                        norm_mismatch += 1
                        if len(norm_bad) < 8:
                            norm_bad.append([hex(a), ops[0], nom, mm[4], dn])
        for x in disp_regs:
            memo[x] = ('clobber', None, None, idx)
        for x in disp_regs:
            pending.pop(x, None)
        idx += 1
        continue

    if mn == 'mov' and len(ops) == 2:
        m1 = parse_mem(ops[0]); m2 = parse_mem(ops[1])
        if m1 and m2 is None and m1[0] == 'dword' and is_imm(ops[1]):
            size, base, index, scale, disp = m1
            v = immval(ops[1])
            if base in GEN and index is None and disp == 0:
                store_slot0_any += 1
                if v in VTS:
                    c1 += 1; c1_vts.add(v); c1_addrs.append(a)
            elif index is not None and v in VTS:
                c1_scaled.append([hex(a), ops[0], hex(v)])
            elif v in VTS and disp == 0:
                c1_otherbase.append([hex(a), ops[0], hex(v)])
        if m2 and m1 is None and m2[0] == 'dword':
            size, base, index, scale, disp = m2
            dst = ops[0]
            if disp < 0:
                neload['neg'] += 1
                if base in GEN:
                    neload_obj[disp] += 1
            rec = dict(addr=a, dst=dst, base=base, index=index, disp=disp, idx=idx,
                       cls=None, gap=None, use_addr=None)
            loads.append(rec)
            if dst in GEN:
                memo[dst] = ('load', base, disp, a, idx)
                if index is None and base is not None:
                    pending[dst] = rec
                else:
                    pending.pop(dst, None)
        idx += 1
        continue

    if mn in ALLW and ops:
        d = ops[0]
        if d in GEN:
            memo[d] = ('other', None, None, idx, idx)
            pending.pop(d, None)
    idx += 1

# ---------------- 汇总 ----------------
fed_addrs = set(r[4] for r in fed)
obj_tot = collections.Counter(); obj_fed = collections.Counter()
obj_cls = collections.defaultdict(collections.Counter)
obj_gap = collections.defaultdict(collections.Counter)
obj_dst = collections.defaultdict(collections.Counter)
stk_tot = collections.Counter(); stk_fed = collections.Counter()
for L in loads:
    if L['index'] is not None:
        continue
    tgt = obj_tot if L['base'] in GEN else (stk_tot if L['base'] in STK else None)
    if tgt is None:
        continue
    tgt[L['disp']] += 1
    hit = L['addr'] in fed_addrs
    if hit:
        (obj_fed if L['base'] in GEN else stk_fed)[L['disp']] += 1
    if L['base'] in GEN:
        obj_dst[L['disp']][L['dst']] += 1
        if L['cls']:
            obj_cls[L['disp']][L['cls']] += 1
        if L['gap'] is not None:
            obj_gap[L['disp']][min(L['gap'], 9)] += 1

fclass = collections.Counter(); fclass0 = collections.Counter()
joint = collections.Counter()
for (a, mn, reg, disp, la, lb, ld, gap) in fed:
    k = 'obj' if lb in GEN else ('stack' if lb in STK else 'absolute')
    fclass[k] += 1
    if disp == 0:
        fclass0[k] += 1
    joint[(ld, disp)] += 1

def rate(f, t):
    return round(f / t, 4) if t else None

# 机会归一化：只统计“装载值被当作内存基址用过”的（pointer-like）
def ptrden(disp):
    c = obj_cls.get(disp, {})
    return (c.get('fed', 0), c.get('ptr_base', 0) + c.get('fed', 0))

disp0 = [s[0] for s in sites if s[3] == 0]
def near(addrs, ws):
    n = 0
    for sa in disp0:
        i = bisect.bisect_left(addrs, sa - ws)
        if i < len(addrs) and addrs[i] <= sa + ws:
            n += 1
    return n

import random
random.seed(143)
rand_txt = sorted(random.randint(text_lo_i := IB + TEXT['va'], IB + TEXT['va'] + TEXT['vs']) for _ in range(len(disp0)))
c1s = sorted(c1_addrs)

# item 8 辅助：槽位合法性 + 目标是否函数序言
PRO = [b'\x55\x8b\xec', b'\x53', b'\x56', b'\x57', b'\x83\xec', b'\x8b\xff\x55', b'\x6a\xff',
       b'\x51', b'\x8b\xc1', b'\xb8', b'\xe9', b'\x8b\x44\x24']
def is_pro(va):
    b = rd(va, 4)
    if not b:
        return False
    return any(b.startswith(p) for p in PRO)

vt_pro = collections.Counter()
for vt in VTS:
    for k in (0, 4, 8, 0x48, 0x44, 0x0c, 0x10):
        v = dw(vt + k)
        if v is not None and sec_of(v) == '.text':
            vt_pro[k] += 1

vt48 = [dw(vt + 0x48) for vt in VTS]
vt48_txt = [v for v in vt48 if v is not None and sec_of(v) == '.text']
pro48 = sum(1 for v in vt48_txt if is_pro(v))
rand_pro = sum(1 for v in rand_txt if is_pro(v))

def objdump_at(va, n=8):
    out = subprocess.run(['i686-w64-mingw32-objdump', '-d', '--start-address=0x%x' % va,
                          '--stop-address=0x%x' % (va + n), P],
                         capture_output=True, text=True).stdout
    rows = []
    for ln in out.splitlines():
        m = re.match(r'^\s+([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$', ln)
        if m:
            rows.append([int(m.group(1), 16), m.group(2).strip(), m.group(3).strip()])
    return rows

fix = {}
for va in (0x47C437, 0x47C440):
    o = va2off(va)
    cs = []
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
 'auditor': 'deepseek work/cn:deepseek-v4.1-flash role=audit (read-only)',
 'exe': {'path': P, 'bytes': N, 'sha256': hashlib.sha256(DATA).hexdigest(), 'imagebase': hex(IB)},
 'segments': [{'n': s['name'], 'va': hex(IB + s['va']), 'vs': s['vs'], 'rs': s['rs']} for s in SECS],
 'chunk': CHUNK,
 'I2_insn_mine': n_ins, 'I2_insn_main': 1394120,
 'I2_insn_beyond_vs': n_ins_beyond_vs, 'I2_text_tail_len': len(tail),
 'I2_text_tail_allzero': len(set(tail)) == 1 and tail[:1] == b'\x00',
 'I2_text': [hex(IB + TEXT['va']), hex(text_vend), hex(text_rend)],
 'I2_last_insn_end': hex(last_end),
 'VTSET': {'td': len(TDs), 'col': len(COL), 'vt': len(VTS)},
 'I3_total_mine': len(sites), 'I3_total_main': 18803,
 'I3_hist_top8': disp_hist.most_common(8), 'I3_hist_sum': sum(disp_hist.values()),
 'I3_disp0': disp_hist.get(0, 0),
 'I3_excluded': dict(excl), 'I3_excluded_samples': dict(excl_s),
 'I3_absolute_base_total': sum(abs_call.values()),
 'I4_slot0_sites_mine': c1, 'I4_slot0_vt_mine': len(c1_vts),
 'I4_slot0_sites_main': 2741, 'I4_slot0_vt_main': 838,
 'I4_store_slot0_any': store_slot0_any,
 'I4_scaled_index_dropped': len(c1_scaled), 'I4_scaled_index_samples': c1_scaled[:5],
 'I4_stack_slot_dropped': len(c1_otherbase), 'I4_stack_slot_samples': c1_otherbase[:5],
 'I5_feed_total': len(fed), 'I5_feed_base_class': dict(fclass),
 'I5_feed_base_class_disp0': dict(fclass0),
 'I5_joint_loaddisp_dispatchdisp_top10': [[[x[0][0], x[0][1]], x[1]] for x in joint.most_common(10)],
 'I5_gap_hist': dict(collections.Counter(min(r[7], 9) for r in fed)),
 'I6': {
   'loads': {k: obj_tot.get(k, 0) for k in (0, 4, 8, 12)},
   'fed': {k: obj_fed.get(k, 0) for k in (0, 4, 8, 12)},
   'rate': {k: rate(obj_fed.get(k, 0), obj_tot.get(k, 0)) for k in (0, 4, 8, 12)},
   'ratio0_4_raw': round((obj_fed.get(0, 0) / max(1, obj_tot.get(0, 0))) /
                         max(1e-9, obj_fed.get(4, 0) / max(1, obj_tot.get(4, 0))), 3),
   'disp0_use': dict(obj_cls.get(0, {})),
   'disp4_use': dict(obj_cls.get(4, {})),
   'disp8_use': dict(obj_cls.get(8, {})),
   'disp0_gap': dict(obj_gap.get(0, {})),
   'disp4_gap': dict(obj_gap.get(4, {})),
   'disp0_dst': dict(obj_dst.get(0, {}).most_common(8)),
   'disp4_dst': dict(obj_dst.get(4, {}).most_common(8)),
   'ptrden0': ptrden(0), 'ptrden4': ptrden(4), 'ptrden8': ptrden(8),
   'rate_given_ptrlike0': rate(ptrden(0)[0], ptrden(0)[1]),
   'rate_given_ptrlike4': rate(ptrden(4)[0], ptrden(4)[1]),
   'loads_total': sum(obj_tot.values()), 'fed_total': sum(obj_fed.values()),
 },
 'I6_stk': {'loads': {k: stk_tot.get(k, 0) for k in (0, 4, 8, 12)},
            'fed': {k: stk_fed.get(k, 0) for k in (0, 4, 8, 12)},
            'rate': {k: rate(stk_fed.get(k, 0), stk_tot.get(k, 0)) for k in (0, 4, 8, 12)},
            'loads_total': sum(stk_tot.values()), 'fed_total': sum(stk_fed.values())},
 'I1': {'samples': n1, 'norm_regbase_checked': norm_checked, 'norm_regbase_mismatch': norm_mismatch,
        'norm_allcall_mem_checked': norm_checked_all, 'norm_allcall_mem_dropped': norm_mismatch_all,
        'norm_bad': norm_bad, 'scaled_mem_ops': scaled_ops,
        'negdisp_loads': neload.get('neg', 0), 'negdisp_loads_objbase': sum(neload_obj.values()),
        'negdisp_load_obj_hist': dict(neload_obj.most_common(6)),
        'negdisp_dispatch_sites': nedispatch},
 'I7_fixed': fix, 'I7_between': between, 'I7_edx_write_between': edx_w,
 'I8': {'c1_store_sites': len(c1_addrs), 'disp0_sites': len(disp0),
        'disp0_near_c1_1k': near(c1s, 0x1000), 'disp0_near_c1_4k': near(c1s, 0x4000),
        'rand_baseline_near_c1_1k': near(c1s, 0x1000) if False else None,
        'vt_slot_in_text': {hex(k): v for k, v in sorted(vt_pro.items())},
        'vt_total': len(VTS),
        'vt48_targets': len(vt48_txt), 'vt48_prologue': pro48,
        'rand_prologue_rate': round(rand_pro / len(rand_txt), 4)},
}
# 随机基线：用同样的 near() 逻辑，但派发点换成随机 .text 地址
def near_rand(addrs, ws, pts):
    n = 0
    for sa in pts:
        i = bisect.bisect_left(addrs, sa - ws)
        if i < len(addrs) and addrs[i] <= sa + ws:
            n += 1
    return n
res['I8']['rand_baseline_near_c1_1k'] = near_rand(c1s, 0x1000, rand_txt)
res['I8']['rand_baseline_near_c1_4k'] = near_rand(c1s, 0x4000, rand_txt)

json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
print('WROTE', OUT)
