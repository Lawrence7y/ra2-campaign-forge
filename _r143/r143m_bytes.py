#!/usr/bin/env python3
"""R143 M：链式判据的定点字节旁证 + 非虚表命中的去向定性。

对 5 条命中链，逐条用 objdump（独立解码器）与 capstone 双解，抄出机器码，确认：
  1) 装表指令真的把 imm 写进 [base+0]
  2) 同一函数内真的从 [base+0] 读回
  3) 派发指令真的是 call/jmp [reg+4k]
  4) 槽目标地址真的在 .text 且 dword[vt-4] 真的回指 COL
并对「非虚表 imm 的 20 条结构命中」逐条报出它们的槽目标落在哪一节（预期：不进 .text）。
"""
import sys, json, subprocess, os, tempfile
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
TXT = B.T

def dis_range(va_lo, va_hi, tag):
    """用 objdump 独立解码一段（先按文件偏移切出字节）。"""
    n = va_hi - va_lo
    b = B.rd(va_lo, n)
    if b is None: return 'OOR'
    p = '/tmp/r143m_%s.bin' % tag
    open(p, 'wb').write(b)
    out = subprocess.run(['i686-w64-mingw32-objdump', '-D', '-b', 'binary', '-m', 'i386',
                          '--adjust-vma=0x%X' % va_lo, p],
                         capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        if ':\t' in line:
            rows.append(line.strip())
    os.unlink(p)
    return rows

CHAINS = [
    ('0x41b4e7', '0x7e2288', 16),
    ('0x431a8a', '0x7e3a2c', 4),
    ('0x4a082a', '0x7e5ca4', 0),
    ('0x4f3a76', '0x7ea690', 16),
    ('0x521a17', '0x7eb03c', 16),
]

out = []
for (iva_s, vt_s, sd) in CHAINS:
    iva = int(iva_s, 16); vt = int(vt_s, 16)
    lo = iva - 16; hi = iva + 0x60
    rows = dis_range(lo, hi, iva_s.replace('0x', ''))
    cap = []
    for a, sz, mn, op in md.disasm_lite(B.rd(lo, hi - lo), lo):
        cap.append('%08x: %-28s %s' % (a, mn, op))
    tgt = B.dw(vt + sd)
    out.append({
        'install': hex(iva), 'vt': hex(vt), 'slot': sd // 4,
        'vt_in_VTS': vt in VTS,
        'vt_minus4_in_COL': B.dw(vt - 4) in COL,
        'slot_target': (hex(tgt) if tgt else None),
        'slot_target_sec': (B.sec_of(tgt) if tgt else None),
        'objdump': rows,
        'capstone': cap,
    })

# 非虚表命中的去路
def parse(a, sz, mn, op):
    if not op: return ('nop', None)
    if mn in ('call', 'jmp'):
        m = L.RE_CALL.match(op)
        if m and m.group(1) in L.GEN: return ('disp', (m.group(1), L.disp_of(m.group(2)), mn))
        return ('nop', None)
    ms = L.RE_STORE.match(op)
    if ms and mn in ('mov', 'movl'):
        t = ms.group(3)
        if t is not None and L.RE_IMM.match(t):
            return ('store_imm', (ms.group(1), L.disp_of(ms.group(2)), L.immval(t)))
        return ('store', (ms.group(1), L.disp_of(ms.group(2)), t))
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov': return ('load', (m.group(1), m.group(2), L.disp_of(m.group(3))))
    if mn in L.W_MN: return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'): return ('ret', None)
    return ('other', None)

ins = list(B.sweep(md))
P = [parse(*x) for x in ins]
N = len(P)

def follow(i, disp, win=200):
    base = P[i][1][0]
    j = i + 1; end = min(N, i + 1 + win); loaded = None
    while j < end:
        k, d = P[j]
        if k == 'ret': return None
        if k in ('write', 'store', 'store_imm') and d[0] == base: return None
        if k == 'load' and d[1] == base and d[2] == disp: loaded = d[0]
        elif k == 'disp' and loaded and d[0] == loaded: return (ins[j][0], d[1])
        j += 1
    return None

non = []
for i, (k, d) in enumerate(P):
    if k != 'store_imm': continue
    base, ds, imm = d
    if base not in L.GEN or ds != 0 or imm in VTS: continue
    f = follow(i, 0)
    if not f: continue
    tgt = B.dw(imm + f[1])
    non.append({'install': hex(ins[i][0]), 'imm': hex(imm),
                'slot': f[1] // 4, 'target': (hex(tgt) if tgt else None),
                'target_sec': (B.sec_of(tgt) if tgt else None),
                'imm_sec': B.sec_of(imm)})
res = {'chains': out,
       'nonvts_hits': non,
       'nonvts_target_sec_hist': {},
       'nonvts_imm_sec_hist': {}}
for r in non:
    res['nonvts_target_sec_hist'][str(r['target_sec'])] = res['nonvts_target_sec_hist'].get(str(r['target_sec']), 0) + 1
    res['nonvts_imm_sec_hist'][str(r['imm_sec'])] = res['nonvts_imm_sec_hist'].get(str(r['imm_sec']), 0) + 1
json.dump(res, open('_r143/r143m_bytes.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'nonvts_count': len(non),
                  'nonvts_target_sec_hist': res['nonvts_target_sec_hist'],
                  'nonvts_imm_sec_hist': res['nonvts_imm_sec_hist'],
                  'chain0_objdump': out[0]['objdump'],
                  'chain0_meta': {k: v for k, v in out[0].items() if k not in ('objdump', 'capstone')},
                  'nonvts_sample': non[:8]}, ensure_ascii=False, indent=1))
