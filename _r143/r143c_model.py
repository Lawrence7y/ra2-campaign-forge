#!/usr/bin/env python3
"""R143 C：把「vt == [obj+0]」拆成三条可失败判据并逐条机械实测。

判据 C1（写入侧）：构造器把虚表地址写进对象偏移 0。
  实测 = .text 内 mov dword ptr [rX], imm32 且 imm32 是已知虚表地址的站点数与覆盖的 distinct 虚表数。
判据 C2（读取侧）：虚派发的基址寄存器由偏移 0 的内存装载得来。
  实测 = 间接 call/jmp [rX+4k] 中，rX 的最近一次定义是 mov rX,[rY+0] 的比例；
  同时给「全部内存装载中 disp==0 的比例」作基线 => 富集倍数。
判据 C3（互斥性）：若偏移 0 不是 vptr，则同样的「按偏移装载」在 4/8/0xc/0x10 上应当同样常见；
  实测各偏移在派发基址装载里的计数，看是否只有 0 位独占。
反控：① 伪虚表集合（随机 .data/.rdata dword 抽样等势）下 C1 计数应塌；② 装载偏移直方图整体；
     ③ objdump 起点集复核派发站点是否为合法指令起点。

禁用：不对整段 .text 开 detail=True；只用 disasm_lite 流式 64KB 分块。
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
TEXT_LO = IB + T[1]; TEXT_RAW = T[3]; TEXT_RSZ = T[4]

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
W_MN = {'mov', 'movzx', 'movsx', 'lea', 'add', 'sub', 'adc', 'sbb', 'and', 'or', 'xor',
        'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'imul',
        'pop', 'xchg', 'bswap', 'mul', 'div', 'idiv'}

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

# ---------------- 虚表集合 ----------------
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
VTS = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in COL:
                vt = IB + ava + i * 4 + 4
                if dw(vt - 4) == v:
                    VTS.add(vt)

RE_STORE = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\](?:,([^,]+))?$')
RE_LOAD = re.compile(r'^([a-z0-9]+),dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')
RE_CALL = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')

def disp_of(s):
    if s is None: return 0
    return int(s[3:], 16) if s.startswith('+0x') else -int(s[1:])

def run(vtset, want_dispatch=True):
    """单遍扫描；返回 (imm stores 按其 imm 是否属于 vtset, 派发基址来源记录, 装载直方图)。"""
    imm_vt = []
    rec = []
    load_disp = collections.Counter()
    lastdef = {}
    for a, sz, mn, op in sweep():
        if not op: continue
        if mn in ('call', 'jmp'):
            mc = RE_CALL.match(op)
            if mc:
                b, d = mc.group(1), disp_of(mc.group(2))
                if want_dispatch and b in GEN:
                    ld = lastdef.get(b)
                    rec.append((a, mn, b, d, ld[0] if ld else 'unknown',
                                ld[1] if ld else None, ld[2] if ld else None))
                for r in ('eax', 'ecx', 'edx'):
                    lastdef[r] = ('clobber', None, a)
                continue
        ms = RE_STORE.match(op)
        if ms and mn in ('mov', 'movl'):
            d = disp_of(ms.group(2)); tgt = ms.group(3)
            if tgt is not None and re.match(r'^(0x[0-9a-f]+|\d+)$', tgt):
                iv = (int(tgt, 16) if tgt.startswith('0x') else int(tgt)) & 0xFFFFFFFF
                if iv in vtset:
                    imm_vt.append((a, ms.group(1), d, iv))
            continue
        ml = RE_LOAD.match(op)
        if ml and mn == 'mov':
            dst, base, d = ml.group(1), ml.group(2), disp_of(ml.group(3))
            load_disp[d] += 1
            if dst in GEN:
                lastdef[dst] = ('load', d, a)
            continue
        if mn == 'lea' and ',' in op:
            dst = op.partition(',')[0]
            if dst in GEN: lastdef[dst] = ('other', None, a)
        elif mn in W_MN:
            dst = op.partition(',')[0]
            if dst in GEN: lastdef[dst] = ('other', None, a)
    return imm_vt, rec, load_disp

imm_vt, rec, load_disp = run(VTS)
d_hist = collections.Counter(s[2] for s in imm_vt)
regs_hit = {s[1] for s in imm_vt}

# C1 明细
vt_at_d0 = {s[3] for s in imm_vt if s[2] == 0}
vt_at_non0 = {s[3] for s in imm_vt if s[2] != 0}
# C2 明细
src_hist = collections.Counter(r[4] for r in rec)
bydisp = collections.Counter(r[6] for r in rec if r[4] == 'load')
# C3：0 位与 4/8/12 位比较
key_disp = {k: bydisp.get(k, 0) for k in (0, 4, 8, 12, 16, 0x10, 0x14)}
# 全部装载基线
base_all = len(load_disp); base0 = load_disp.get(0, 0)
# 反控 1：伪虚表集合（等势随机抽样自 .data/.rdata dword）
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(struct.unpack_from('<I', blob, i * 4)[0])
fake = set(random.sample(pool, len(VTS)))
imm_fake, _, _ = run(fake, want_dispatch=False)
# 反控 3：objdump 起点集
try:
    starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())
    SRC = '_r140/obj_starts.txt'
except Exception as e:
    starts = set(); SRC = 'UNAVAILABLE %s' % e
res = {
 'exe_sha256': subprocess.run(['sha256sum', P], capture_output=True, text=True).stdout.split()[0],
 'exe_bytes': N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'C1_sites': len(imm_vt), 'C1_distinct_vt': len(vt_at_d0 | vt_at_non0),
 'C1_sites_disp0': d_hist.get(0, 0), 'C1_distinct_vt_disp0': len(vt_at_d0),
 'C1_vt_coverage_disp0': round(len(vt_at_d0) / len(VTS), 4),
 'C1_sites_nonzero': len(imm_vt) - d_hist.get(0, 0),
 'C1_distinct_vt_nonzero': len(vt_at_non0),
 'C1_disp_hist': dict(sorted(d_hist.items())),
 'C1_regs': sorted(regs_hit),
 'C2_dispatch_total': len(rec),
 'C2_src': dict(src_hist),
 'C2_load_share': round(src_hist['load'] / max(1, len(rec)), 4),
 'C2_load_disp0': bydisp.get(0, 0),
 'C2_load_disp0_share': round(bydisp.get(0, 0) / max(1, sum(bydisp.values())), 4),
 'C2_all_loads': base_all, 'C2_all_loads_disp0': base0,
 'C2_all_loads_disp0_share': round(base0 / max(1, base_all), 4),
 'C2_enrichment': round((bydisp.get(0, 0) / max(1, sum(bydisp.values()))) / max(1e-9, base0 / max(1, base_all)), 3),
 'C3_key_disp': {str(k): v for k, v in key_disp.items()},
 'C3_load_disp_top': collections.Counter(bydisp).most_common(12),
 'NEG1_fake_vt_len': len(fake),
 'NEG1_fake_sites_disp0': sum(1 for s in imm_fake if s[2] == 0),
 'NEG1_fake_distinct': len({s[3] for s in imm_fake}),
 'NEG2_starts_src': SRC, 'NEG2_starts_n': len(starts),
 'NEG2_dispatch_in_starts': sum(1 for r in rec if r[0] in starts),
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143c_model.judg.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'imm_vt_head': [[hex(a), b, d, hex(v)] for a, b, d, v in imm_vt[:60]],
           'imm_vt_d0_head': [[hex(a), b, hex(v)] for a, b, d, v in imm_vt if d == 0][:40],
           'rec_head': [[hex(r[0]), r[1], r[2], r[3], r[4], r[5]] for r in rec[:40]]},
          open('_r143/r143c_samples.json', 'w'), ensure_ascii=False, indent=1)
