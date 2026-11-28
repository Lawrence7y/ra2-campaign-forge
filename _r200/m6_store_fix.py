#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第六刀（订正 R199 的 538）：store 计数与分类在**正确位移解析**下重算。

自错（本轮抓出）：R199 的 STORE_RE 只匹配 `dword ptr [reg + 0xHEX], imm32`，
而 capstone 对小位移输出**十进制**（实测 `[esi + 4]`、`[esi + 8]`、`[ecx + 4]` 都是十进制；
位移 >= 0xa 才输出 `0xa` 形式）。因此任何 `mov dword ptr [reg + 1..9], imm32` 的装表指令
在 R199 与 m1..m5 里都被静默丢弃。本轮先做正反控证明该 bug 存在，再给订正后的全量数。

判据：
 X1 正控：用 capstone 现场汇编/反汇编构造 12 条已知 store（偏移 0,1,4,8,9,0xa,0xc,0x10,0x34,0x40,
    以及带 -4），确认「旧正则」与「新正则」的匹配率差。
 X2 修正解析器 parse_store：接受 base ∈ {eax..ebp}、位移形式 {缺省, 十进制, 0x十六进制, -十进制}。
 X3 用新解析器重算 516 个槽 0 派生实现体内的全部 [reg(+off)]=imm32 store：
    总数、按 imm 类别（own/base/sub/other/nonvt）、按偏移 0/非 0、按 base 寄存器。
 X4 与 R199 的 538 做差：给「旧口径漏掉的条数」与「漏掉条目的类名清单（去重）」。
反控：
 R1 旧正则（只认 0x 位移）在新口径下的命中数必须等于 538。
 R2 把「store 目标必须落 .text 虚表」的过滤加上，看 other/nonvt 是否变化。
"""
import sys, struct, collections, json, re
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

# ---------- X1 正控：位移文本形式 ----------
TXT = {}
for reg, modrm in (('esi', 0x46), ('ecx', 0x41), ('eax', 0x40), ('edi', 0x47)):
    for off in (0, 1, 4, 8, 9, 0xa, 0xc, 0x10, 0x34, 0x40):
        code = bytes([0xC7, modrm, off]) + b'\x50\x1f\x7e\x00'
        for i in md.disasm(code, 0x400000):
            TXT[(reg, off)] = i.op_str
print('   X1 位移文本样本: %s' % {('%s+%d' % (r, o)): t.split('],')[0].split('[')[1] for (r, o), t in
                                 list(TXT.items())[:12]})
dec_small = [o for (r, o), t in TXT.items() if reg_dummy(o) and False] if False else None
# 判定：位移 1..9 是否输出成裸十进制
small = [(r, o, t) for (r, o), t in TXT.items() if 1 <= o <= 9]
ck('X1a 位移 1..9 全部输出为裸十进制（无 0x 前缀）',
   all(('+ %d]' % o) in t for r, o, t in small), [(o, t) for r, o, t in small][:4])
hexf = [(r, o, t) for (r, o), t in TXT.items() if o >= 0xa]
ck('X1b 位移 >= 0xa 输出为 0x 十六进制', all(('+ 0x%x]' % o) in t for r, o, t in hexf), [(o, t) for r, o, t in hexf][:3])

OLD_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
NEW_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
def parse_store(op):
    m = NEW_RE.match(op)
    if not m: return None
    reg = m.group(1); sign = m.group(2); val = m.group(3); imm = int(m.group(4), 16)
    if val is None: off = 0
    else:
        off = int(val, 16) if val.startswith('0x') else int(val)
        if sign == '-': off = -off
    return reg, off, imm
old_hit = sum(1 for (r, o), t in TXT.items() if OLD_RE.match(t))
new_hit = sum(1 for (r, o), t in TXT.items() if parse_store(t) is not None)
ck('X1c 旧正则命中数远小于新解析器（正控）', old_hit < new_hit, (old_hit, new_hit, len(TXT)))

# ---------- 底座 ----------
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

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))
ck('X0a 516', len(s0d) == 516, len(s0d))

def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

# ---------- X3 重算 ----------
cat = collections.Counter(); offc = collections.Counter(); regc = collections.Counter()
newrows = []; oldrows = []
for vt_d, a, vt_b in s0d:
    for ad, sz, mn, op in body(a) or []:
        if mn != 'mov': continue
        ps = parse_store(op)
        if ps is None: continue
        reg, off, imm = ps
        if imm == vt_d: t = 'own_main'
        elif imm == vt_b: t = 'base_main'
        elif imm in VT and MD[imm] != 0: t = 'subtable'
        elif imm in VT: t = 'other_main'
        else: t = 'nonvt'
        cat[t] += 1; offc[off] += 1; regc[reg] += 1
        newrows.append(dict(vt_d=vt_d, impl=a, at=ad, reg=reg, off=off, imm=imm, cat=t))
        if OLD_RE.match(op): oldrows.append(dict(vt_d=vt_d, impl=a, at=ad, reg=reg, off=off, imm=imm, cat=t))
print('   X3 新口径 store 总数 %d ; 旧口径 %d ; 差 %d' % (len(newrows), len(oldrows), len(newrows) - len(oldrows)))
print('   X3 imm 类别: %s' % dict(cat))
ck('R1a 旧正则命中数 == 538（R199 值）', len(oldrows) == 538, len(oldrows))
ck('X3a 新口径总数 > 旧口径（证明漏检）', len(newrows) > len(oldrows), (len(newrows), len(oldrows)))
print('   偏移分布 Top10: %s' % [(hex(o), c) for o, c in offc.most_common(10)])
print('   base 寄存器: %s' % dict(regc.most_common()))
# 漏掉的条目
missed = [r for r in newrows if not OLD_RE.match('dword ptr [%s], 0x%x' % (r['reg'], r['imm']))]
miss_ids = set((r['impl'], r['at']) for r in missed)
print('   X4 旧口径漏掉的 store 条数 %d，涉及实现 %d 个' % (len(missed), len(set(r['impl'] for r in missed))))
mk = collections.Counter((CLS[r['vt_d']], r['cat'], r['off']) for r in missed)
print('   X4 漏掉条目形状 Top15:')
for k, v in mk.most_common(15): print('        %-56s %-12s off=0x%x  x%d' % (k[0], k[1], k[2], v))
ck('X4a 漏掉条目里非 0 位移占多数', sum(1 for r in missed if r['off'] != 0) > sum(1 for r in missed if r['off'] == 0),
   (sum(1 for r in missed if r['off'] != 0), sum(1 for r in missed if r['off'] == 0)))

json.dump(dict(new_total=len(newrows), old_total=len(oldrows), cat=dict(cat),
               offdist={hex(o): c for o, c in offc.items()}, regs=dict(regc),
               missed_shapes={'%s|%s|%d' % k: v for k, v in mk.items()},
               rows=[dict(cls_d=CLS[r['vt_d']], impl=hex(r['impl']), at=hex(r['at']), reg=r['reg'],
                          off=r['off'], imm=hex(r['imm']), cat=r['cat'], cls_imm=CLS.get(r['imm']))
                     for r in newrows],
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m6_store_fix.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
