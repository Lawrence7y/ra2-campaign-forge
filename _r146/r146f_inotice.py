#!/usr/bin/env python3
"""R146 F：0x7E1FB4（TD .?AVINoticeSource@@）的活 vptr 归属（R145 下轮待办 #1）。

R145 已证：3 个装表站点（0x41017B / 0x4101C9 / 0x6E800F）全部被同块后续写覆盖 ⇒ 瞬态。
「瞬态」只证「块内该槽被再次写」，不证那个对象后来没被重新装回。本脚本换三个独立判据：

  P1 **写入者的完整上下文**：把三个站点各自所在基本块逐指令反汇编出来，看后续写的是
     同一 base 的**同一槽**还是**别的槽**（R145 是按 (base,disp) 匹配的，需复核 base
     在后续写里是否被改写 —— 若 base 被改写，则「覆盖」判定就是 S-318 那类错）。
  P2 **构造完成后有无虚调用落到该槽**：全 .text 扫 `call/jmp dword ptr [base+disp]`，
     若存在 disp 与之一致的调用，说明该槽确实是活 vptr 槽。
  P3 **该对象实例的实际装载**：找所有把 0x7E1FB4 或它前后虚表写进内存的站点，
     以及 `.data/.rdata` 里是否存在 0x7E1FB4 的 dword 初值（静态实例）。
反控：同样三问对一张**已知持久**的虚表（0x7E6060，R145 已证）跑一遍作对照。
纪律：disasm_lite 流式；上下文用 <=16KB 小窗口 disasm。
"""
import sys, re, json, collections, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coltd = {c: B.dw(c + 12) for c in COL}
coloff = {c: B.dw(c + 4) for c in COL}
TDname = {td: nm.decode('latin-1', 'replace') for td, nm in TDs.items()}
def name_of(vt):
    c = COLof.get(vt)
    return TDname.get(coltd.get(c)) if c else None
def off_of(vt): return coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)

TARGETS = {'0x7e1fb4': 0x7E1FB4, '0x7e6060': 0x7E6060}   # 前者=疑似无主，后者=已知持久（正控）

stores = collections.defaultdict(list)   # vt -> [(va, base, disp)]
vcalls = []                              # (va, base, disp, mn)
raw4 = {}                                # vt -> 原始 4 字节出现次数（含数据节）
for nm, ava, vs, raw, rs in B.secs:
    blob = B.data[raw:raw + rs]
    for vt in TARGETS.values():
        pat = vt.to_bytes(4, 'little')
        n = 0; i = blob.find(pat)
        while i >= 0:
            n += 1; i = blob.find(pat, i + 1)
        raw4.setdefault(hex(vt), {})[nm] = n

for a, sz, mn, op in B.sweep(md):
    if not op: continue
    mt = TOL.match(op)
    if mt:
        pm = parse_mem(mt.group(1))
        if pm:
            base, disp = pm
            tgt = (mt.group(2) or '').strip()
            if mn == 'mov' and L.RE_IMM.match(tgt):
                v = immv(tgt)
                if v in TARGETS.values(): stores[v].append((a, base, disp))
            if mn in ('call', 'jmp') and mt.group(2) is None:
                vcalls.append((a, base, disp, mn))

res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'raw4_all_sections': raw4, 'vcalls_total': len(vcalls)}

# ---- P1 站点上下文 ----
def ctx(va, before=0x30, after=0x60):
    lo = va - before; off = B.va2off(lo)
    if off is None: return []
    blob = B.data[off:off + before + after]
    out = []
    for insn in md.disasm(blob, lo):
        out.append('%08X  %-7s %s' % (insn.address, insn.mnemonic, insn.op_str))
    return out

detail = {}
for vt in TARGETS.values():
    ss = sorted(stores.get(vt, []))
    detail[hex(vt)] = {'name': name_of(vt), 'col_offset': off_of(vt),
                       'stores': [[hex(a), b, d] for a, b, d in ss],
                       'n_stores': len(ss),
                       'ctx': {hex(a): ctx(a) for a, b, d in ss[:6]}}
res['P1'] = detail

# ---- P2 该槽有无虚调用 ----
def p2(vt):
    d = off_of(vt)
    hit = [(a, b, dd, m) for a, b, dd, m in vcalls if d is not None and dd == d]
    hit0 = [(a, b, dd, m) for a, b, dd, m in vcalls if d == 0 and dd == 0]
    return {'col_offset': d, 'vcalls_same_disp': len(hit), 'vcalls_same_disp_d0': len(hit0),
            'samples': [[hex(a), b, dd, m] for a, b, dd, m in hit[:8]]}
res['P2'] = {hex(vt): p2(vt) for vt in TARGETS.values()}

# ---- P3 .data/.rdata 静态初值：上面 raw4 已给（按节分）----
res['P3_static_dword_init'] = {hex(vt): raw4.get(hex(vt), {}).get('.data', 0) + raw4.get(hex(vt), {}).get('.rdata', 0)
                               for vt in TARGETS.values()}

# ---- 附加：三个站点的 base 是否在块内被改写（复核 R145 的「同槽覆盖」判定）----
def base_rewritten(va, base, upto=0x60):
    lo = va; off = B.va2off(lo)
    blob = B.data[off:off + upto]
    for insn in md.disasm(blob, lo):
        if insn.address == va: continue
        head = (insn.op_str or '').partition(',')[0].strip()
        if head == base and insn.mnemonic not in ('push', 'cmp', 'test', 'call'):
            return True, '%08X %s %s' % (insn.address, insn.mnemonic, insn.op_str)
    return False, None
rw = {}
for vt in TARGETS.values():
    for a, b, d in sorted(stores.get(vt, [])):
        rw['%08X' % a] = base_rewritten(a, b)
res['base_rewritten_after_store'] = rw

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('0x7E1FB4 有 3 个装表站点（复现 R145）', len(stores.get(0x7E1FB4, [])) == 3, len(stores.get(0x7E1FB4, [])))
chk('0x7E6060 有 1 个装表站点（复现 R145）', len(stores.get(0x7E6060, [])) == 1, len(stores.get(0x7E6060, [])))
chk('两张表的 COL.offset 都是 0', off_of(0x7E1FB4) == 0 and off_of(0x7E6060) == 0, [off_of(0x7E1FB4), off_of(0x7E6060)])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146f_inotice.json', 'w'), indent=1)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
