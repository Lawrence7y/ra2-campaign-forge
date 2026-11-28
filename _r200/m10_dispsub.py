#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第十刀（本轮第二交付）：全 .text 的「小位移装表」699 条是什么。

m9 的反控意外打开一面新镜：全 .text 里 C7 /0（mov r/m32, imm32）且 disp8 ∈ 1..9 的指令
共 2,404 条（位移分布 4:1482 / 8:913 / 1:3 / 2:3 / 3:2 / 5:1），其中 imm 落 .rdata/.data 的 **699** 条。
R199 与 R200 前九刀的 store 正则只认 0x 位移，对这 699 条**零覆盖**（但它们不在 516 个槽 0 实现体内，
所以 R199 的 538 不受影响）。本刀把这 699 条定性。

判据（全字节）：
 T1 扫全 .text 的 C7 /0，取 mod==01（disp8），记录 (指令地址, 基址寄存器, disp8, imm32)。
 T2 对 imm 落 .rdata/.data 的，判 imm 是否虚表头：imm 在 VT 内、且 dword[imm-4] 在 COL 内。
 T3 对命中的，给该 COL 的 mdisp（4/8/12 = 子表，0 = 主表）与 disp8 的交叉。
 T4 宿主函数：该指令往前最近的一个「被任何 call 引用的地址」= 宿主入口；
    再取宿主体首条 `mov esi, ecx` / `mov edi, ecx`（this 搬移）是否存在。
 T5 三组「类名关系」：宿主若能从「同一函数内前一条 disp8==0 的装表指令」取到主表，
    则比较主表类名与子表类名（应相同 = 同类的子表）。
反控：
 R1 把 disp8 范围放宽到 1..127，看总数与结构变化。
 R2 只统计 disp==4 与 disp==8 两档，看 imm 的 mdisp 分布。
"""
import sys, struct, collections, json, re, bisect
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
ck('T0a COL/VT', (len(COL), len(VT)) == (1214, 1214), (len(COL), len(VT)))

REGNAME = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
# ---- T1 ----
recs = []; dist = collections.Counter(); tot_c7 = 0
pos = T['rawptr']; end = T['rawptr'] + T['rawsize']
while pos < end - 6:
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos + 1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4: pos += 1; continue
    if rm == 5 and mod == 0: pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        disp = struct.unpack_from('<b', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 3)[0]
        tot_c7 += 1; dist[disp] += 1
        recs.append((va, REGNAME[rm], disp, imm))
        pos += 7
    elif mod == 2:
        disp = struct.unpack_from('<i', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 6)[0]
        tot_c7 += 1; dist[disp] += 1
        recs.append((va, REGNAME[rm], disp, imm))
        pos += 10
    else:
        pos += 1
small = [r for r in recs if 1 <= r[2] <= 9]
svt = [r for r in small if P.where(r[3]) in ('.rdata', '.data')]
ck('T1a C7 /0 总数', True, tot_c7)
ck('T1b disp8 ∈ 1..9 的 C7 /0 == 2,404', len(small) == 2404, len(small))
ck('T1c 其中 imm 落 .rdata/.data == 699', len(svt) == 699, len(svt))

# ---- T2/T3 ----
isvt = [r for r in svt if r[3] in VT]
print('   T2 imm 在 VT 内（虚表头）%d / %d' % (len(isvt), len(svt)))
md_cross = collections.Counter((r[2], MD[r[3]]) for r in isvt)
print('   T3 (disp8, mdisp) 交叉: %s' % dict(sorted(md_cross.items())))
ck('T3a 全部命中 imm 的 mdisp 都是 4/8/12（子表，非主表）',
   all(MD[r[3]] != 0 for r in isvt), collections.Counter(MD[r[3]] for r in isvt))
disp4_8 = [r for r in isvt if r[2] in (4, 8)]
ck('T3b disp8 只取 4 与 8 两档', all(r[2] in (4, 8) for r in isvt), collections.Counter(r[2] for r in isvt))
ck('T3c disp8 == mdisp 的条数（偏移对齐）',
   sum(1 for r in isvt if r[2] == MD[r[3]]), (sum(1 for r in isvt if r[2] == MD[r[3]]), len(isvt)))
# 基址寄存器
print('   T3d 基址寄存器: %s' % dict(collections.Counter(r[1] for r in isvt).most_common()))

# ---- T4 宿主 ----
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
CALLAT = []; p2 = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2 + 65536], LO + p2):
        got = True
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
        p2 += sz
    if not got: p2 += 1
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c):
    i = bisect.bisect_left(SORT, c) - 1
    return SORT[i] if i >= 0 else None
hosts = collections.Counter(host_of(r[0]) for r in isvt)
print('   T4 宿主去重数 %d ；每个宿主承载条数 Top10: %s' % (len(hosts), [(hex(h), c) for h, c in hosts.most_common(10)]))
ck('T4a 宿主数 > 50', len(hosts) > 50, len(hosts))

# ---- T5 同类子表判定：同一函数内是否有 disp==0 的主表装表，类名是否相同 ----
# 用宿主入口 + 宿主后继入口界定函数体
entries = SORT
def next_entry(c):
    i = bisect.bisect_right(entries, c)
    return entries[i] if i < len(entries) else HI
byhost = collections.defaultdict(list)
for r in isvt: byhost[host_of(r[0])].append(r)
same_cls = 0; diff_cls = 0; no_main = 0; unread = 0
samples = []
for h, rs in byhost.items():
    if h is None: no_main += len(rs); continue
    hi = min(next_entry(h), h + 4096)
    o = P.r2o(h)
    if o is None: unread += len(rs); continue
    mains = []
    for i in md.disasm(RAW[o:o + (hi - h)], h):
        if i.mnemonic == 'mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv = int(i.op_str.rsplit(', ', 1)[1], 16)
            except Exception: continue
            if iv in VT and MD[iv] == 0: mains.append(iv)
    for r in rs:
        sub_cls = CLS[r[3]]
        if not mains: no_main += 1; samples.append((hex(h), sub_cls, hex(r[3]), None, 'no_main')); continue
        if any(CLS[m] == sub_cls for m in mains):
            same_cls += 1
        else:
            diff_cls += 1
            if len(samples) < 12: samples.append((hex(h), sub_cls, hex(r[3]), CLS[mains[0]], 'diff'))
print('   T5 同类子表 %d / 类名不同 %d / 同函数无主表装表 %d / 不可读 %d' % (same_cls, diff_cls, no_main, unread))
for s in samples[:12]: print('        T5s host=%s sub=%-46s vt=%s main=%s %s' % s)
ck('T5a 同类子表占多数（>= 60%%）', same_cls >= 0.6 * (same_cls + diff_cls + no_main), (same_cls, diff_cls, no_main))

# ---- R1/R2 ----
wide = [r for r in recs if 1 <= r[2] <= 127 and P.where(r[3]) in ('.rdata', '.data')]
ck('R1a disp8 放宽到 1..127 的装表条数', True, len(wide))
ck('R2a disp 4/8 两档的 imm mdisp 分布', True,
   dict(collections.Counter(MD[r[3]] for r in disp4_8)))

json.dump(dict(c7_total=tot_c7, small=len(small), svt=len(svt), isvt=len(isvt),
               md_cross={'%d|%d' % k: v for k, v in md_cross.items()},
               regs=dict(collections.Counter(r[1] for r in isvt)),
               same_cls=same_cls, diff_cls=diff_cls, no_main=no_main, unread=unread,
               hosts=len(hosts), wide=len(wide), samples=samples,
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m10_dispsub.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
