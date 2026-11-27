#!/usr/bin/env python3
"""R143 A：用字节独立证「对象偏移 0 处的 dword 是 vptr」（vt == [obj]）这条对象模型判读。

方法（全部机械，不读源码、不做语义臆测）：
  A1 装表存储：.text 内 mov dword ptr [rX (+d)], imm32，imm32 属于「已知虚表地址集合」，
     统计装表点数、d 的分布、覆盖的 distinct 虚表数。若 d==0 占绝对多数且覆盖全部 1218 张表
     => 构造器把虚表地址写到对象偏移 0。
  A2 消费端：全部间接 call/jmp [rX+4k] 的基址寄存器，回溯其最近一次定义；
     只认「由内存装载」并保守失效（任何写该寄存器的指令、call 对 eax/ecx/edx 的隐式破坏都算打断）。
     统计「装载位移 == 0」的比例，与「全部内存装载位移 == 0」的基线比 => 富集倍数。
  A3 若 A1 的 d==0 与 A2 的装载位移==0 同时成立，则在同一条 .text 内，
     派发寄存器 = [对象+0]，而 [对象+0] 是构造器写入的虚表地址 => 偏移 0 即 vptr。
  A4 反控：① 随机 .data/.rdata dword 命中虚表集合的假阳性率；② 把「偏移 0」换成 4/8/0xc
     富集应消失；③ 位移分布整表（看 4k 槽位是否只有 0 号位出现派发）。

禁止：不对整段 .text 开 detail=True；只用 disasm_lite 流式（64KB 分块）。
"""
import struct, json, subprocess, re, collections, random
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

P = 'ra2bench/gamemd.exe'
data = open(P, 'rb').read(); N = len(data)
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
T = [s for s in secs if s[0] == '.text'][0]
TEXT_LO = IB + T[1]; TEXT_RAW = T[3]; TEXT_RSZ = T[4]; TEXT_HI = TEXT_LO + T[2]

def va2off(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs):
            d = va - lo
            return raw + d if d < rs else None
    return None

def rd(va, l):
    o = va2off(va)
    if o is None or o + l > N: return None
    return data[o:o + l]

def dw(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def sec_of(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs): return nm
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')
# 会写第一操作数的助记符（保守白名单）。其余一律不动记账。
W_MN = {'mov', 'movzx', 'movsx', 'lea', 'add', 'sub', 'adc', 'sbb', 'and', 'or', 'xor',
        'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'imul',
        'pop', 'xchg', 'bswap', 'mul', 'div', 'idiv', 'cdq'}

def sweep():
    off = TEXT_RAW; end = TEXT_RAW + TEXT_RSZ
    while off < end:
        chunk = data[off:min(off + 65536, end)]
        base = IB + (T[1] + (off - TEXT_RAW))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(chunk, base):
            if a - base + sz > len(chunk): break
            consumed = a - base + sz
            yield a, sz, mn, re.sub(r'\s*([+,*])\s*', r'\1', op or '')
        off += consumed if consumed else 1

# ---- 已知虚表 / COL 集合（R140/r140n 同法重算）----
pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
TDs = {}
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        for m in pat.finditer(data[raw:raw + rs]):
            s = IB + ava + m.start()
            if dw(s - 8) is not None and dw(s - 4) == 0 and sec_of(dw(s - 8)) in ('.data', '.rdata'):
                TDs[s - 8] = m.group()
tdset = set(TDs)
COL = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in tdset:
                c = IB + ava + i * 4 - 12
                if dw(c) == 0 and dw(c + 12) == v and dw(c + 16) != 0:
                    COL.add(c)
VTS = set(); vt_occ = 0
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in COL:
                vt = IB + ava + i * 4 + 4
                if dw(vt - 4) == v:
                    VTS.add(vt); vt_occ += 1

# ---- 单遍扫描 ----
imm_stores = []       # (va, base, disp, imm)
mem_stores = []       # (va, base, disp, src)   src 为寄存器名或 None(立即数)
loads = []            # (va, dst, base, disp)
calls = []            # (va, mn, base, disp)
lastdef = {}
n_ins = 0
RE_STORE = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\](?:,([^,]+))?$')
RE_LOAD = re.compile(r'^([a-z0-9]+),dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')
RE_CALL = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')

def disp_of(s):
    if s is None: return 0
    return int(s[3:], 16) if s.startswith('+0x') else -int(s[1:])

for a, sz, mn, op in sweep():
    n_ins += 1
    if op:
        m = RE_STORE.match(op)
        if m and mn in ('mov', 'movl'):
            d = disp_of(m.group(2)); tgt = m.group(3)
            if tgt is not None and re.match(r'^(0x[0-9a-f]+|\d+)$', tgt):
                imm = int(tgt, 16) if tgt.startswith('0x') else int(tgt)
                imm_stores.append((a, m.group(1), d, imm & 0xFFFFFFFF))
                mem_stores.append((a, m.group(1), d, None))
            else:
                mem_stores.append((a, m.group(1), d, tgt))
                if tgt in GEN:
                    lastdef[tgt] = None   # 值被搬到内存，寄存器本身不变，记账保持
        else:
            ml = RE_LOAD.match(op)
            if ml and mn == 'mov':
                dst, base, d = ml.group(1), ml.group(2), disp_of(ml.group(3))
                loads.append((a, dst, base, d))
                if dst in GEN:
                    lastdef[dst] = ('load', d, a)
            elif mn == 'lea' and ',' in op:
                dst = op.partition(',')[0]
                if dst in GEN: lastdef[dst] = ('other', None, a)
            elif mn == 'pop' and op in GEN:
                lastdef[op] = ('other', None, a)
            elif mn == 'call':
                for r in ('eax', 'ecx', 'edx'):
                    lastdef[r] = ('clobber', None, a)
            elif mn in W_MN:
                dst = op.partition(',')[0]
                if dst in GEN:
                    lastdef[dst] = ('other', None, a)
        mc = RE_CALL.match(op)
        if mc and mn in ('call', 'jmp'):
            calls.append((a, mn, mc.group(1), disp_of(mc.group(2))))

# ---- A1 ----
st_vt = [s for s in imm_stores if s[3] in VTS]
st_col = [s for s in imm_stores if s[3] in COL]
d_vt = collections.Counter(s[2] for s in st_vt)
d_all_imm = collections.Counter(s[2] for s in imm_stores)
# 反控：把 imm 换成「.data/.rdata 里随机 dword」时假阳性
random.seed(143)
dv = []
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(0, len(blob) // 4, 61):
            dv.append(struct.unpack_from('<I', blob, i * 4)[0])
samp = random.sample(dv, min(5000, len(dv)))

# ---- A2 ----
call_reg = [c for c in calls if c[2] in GEN]
src_hist = collections.Counter()
disp_hist = collections.Counter()
for va, mn, base, disp in call_reg:
    ld = lastdef.get(base)   # 注意：这是「整段扫描结束」的快照，不能用于回溯
# 回溯必须在扫描中做：重扫一遍，边扫边判
rec = []
lastdef = {}
for a, sz, mn, op in sweep():
    if op:
        if mn in ('call', 'jmp'):
            mc = RE_CALL.match(op)
            if mc:
                base = mc.group(1); disp = disp_of(mc.group(2))
                if base in GEN:
                    ld = lastdef.get(base)
                    rec.append((a, mn, base, disp, ld[0] if ld else 'unknown',
                                ld[1] if ld else None, ld[2] if ld else None))
        mc = RE_CALL.match(op)
        if mc and mn in ('call', 'jmp'):
            pass
        ml = RE_LOAD.match(op)
        if ml and mn == 'mov':
            dst, base, d = ml.group(1), ml.group(2), disp_of(ml.group(3))
            if dst in GEN: lastdef[dst] = ('load', d, a)
        elif mn == 'lea' and ',' in op:
            dst = op.partition(',')[0]
            if dst in GEN: lastdef[dst] = ('other', None, a)
        elif mn == 'pop' and op in GEN:
            lastdef[op] = ('other', None, a)
        elif mn in W_MN:
            dst = op.partition(',')[0]
            if dst in GEN: lastdef[dst] = ('other', None, a)
        if mn == 'call':
            for r in ('eax', 'ecx', 'edx'):
                lastdef[r] = ('clobber', None, a)

for va, mn, base, disp, kind, ldisp, lva in rec:
    src_hist[kind] += 1
    if kind == 'load':
        disp_hist[ldisp] += 1

load_disp = collections.Counter(l[3] for l in loads)
res = {
 'exe_sha256': subprocess.run(['sha256sum', P], capture_output=True, text=True).stdout.split()[0],
 'exe_bytes': N, 'instructions': n_ins,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS), 'vt_occurrences': vt_occ,
 'A1_imm_stores': len(imm_stores),
 'A1_imm_stores_vt': len(st_vt),
 'A1_imm_stores_vt_distinct': len({s[3] for s in st_vt}),
 'A1_disp0': d_vt.get(0, 0),
 'A1_disp_hist': dict(sorted(d_vt.items())),
 'A1_all_imm_store_disp_hist_top': d_all_imm.most_common(8),
 'A1_col_imm_stores': len(st_col),
 'A2_calls_mem_indirect': len(calls),
 'A2_call_reg_base': len(call_reg),
 'A2_base_src_hist': dict(src_hist),
 'A2_load_disp_hist': dict(sorted((k, v) for k, v in disp_hist.items() if abs(k) < 0x8000)),
 'A2_load_disp0': disp_hist.get(0, 0),
 'A2_load_disp0_share': round(disp_hist.get(0, 0) / max(1, sum(disp_hist.values())), 4),
 'A2_all_loads': len(loads),
 'A2_all_loads_disp0': load_disp.get(0, 0),
 'A2_all_loads_disp0_share': round(load_disp.get(0, 0) / max(1, len(loads)), 4),
 'A2_enrichment': round((disp_hist.get(0, 0) / max(1, sum(disp_hist.values()))) /
                        max(1e-9, load_disp.get(0, 0) / max(1, len(loads))), 3),
 'A4_ctrl_sample': len(samp),
 'A4_ctrl_fp_vt': sum(1 for v in samp if v in VTS),
 'A4_ctrl_fp_col': sum(1 for v in samp if v in COL),
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143b_model.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'st_vt_head': [[hex(a), b, d, hex(v)] for a, b, d, v in st_vt[:60]],
           'st_vt_nonzero': [[hex(a), b, d, hex(v)] for a, b, d, v in st_vt if d != 0][:60],
           'rec_head': [[hex(a), mn, b, d, k, (ld if ld is None or ld < 0x8000 else hex(ld)), (hex(l) if l else None)] for a, mn, b, d, k, l, lv in rec[:40]]},
          open('_r143/r143b_samples.json', 'w'), ensure_ascii=False, indent=1)
