#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203-VDISP-EXEC hy4 独立重算：虚表/槽位/间接调用四分类。
只读主会话产物当线索，不读取其 json。方法自行实现。
防 OOM：仅 disasm_lite 64KB 分块线性扫描；detail 仅对极少数地址使用（本脚本未用）。
"""
import os, sys, re, json, struct, hashlib, collections, random, bisect
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
import capstone
from capstone import x86

EXE = ROOT + '/ra2bench/gamemd.exe'
SHA_EXPECT = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
with open(EXE, 'rb') as fh:
    blob = fh.read()
sha = hashlib.sha256(blob).hexdigest()
assert sha == SHA_EXPECT, ('SHA mismatch', sha)

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
TXT = P.B['.text']
LO, HI, RP = TXT['lo'], TXT['hi_file'], TXT['rawptr']
RAW = blob  # 与 P.RAW 同一份内容，但由本脚本自己读取并校验

LOGS = []
def log(s=''):
    LOGS.append(str(s)); print(s)
N = 0
FAILS = []
def ck(name, cond, detail=''):
    global N
    N += 1
    if not cond:
        FAILS.append(name)
    log(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''))

def u32(va):
    o = P.r2o(va)
    if o is None or o + 4 > len(RAW):
        return None
    return struct.unpack_from('<I', RAW, o)[0]

def signed32(v):
    return v - 0x100000000 if v & 0x80000000 else v

def sect(va):
    return P.where(va)

def in_text(va):
    return va is not None and LO <= va < HI

def dwords_of(section_name):
    s = P.B[section_name]
    lo, n = s['lo'], s['rawsize'] // 4
    return lo, struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n

# ============ 1. COL ============
COL = {}          # va -> mdisp
COL_NAME = {}     # va -> name bytes
for sn in ('.rdata', '.data'):
    base, arr, n = dwords_of(sn)
    for i in range(n - 4):
        sig, mdisp, pdisp, ptd, pcd = arr[i:i + 5]
        if sig not in (0, 1, 2) or pdisp != 0:
            continue
        if sect(ptd) != '.data' or sect(pcd) != '.rdata':
            continue
        nm = P.cstr(ptd + 8, 400)
        if not nm or not nm.startswith(b'.?A') or not nm.endswith(b'@@'):
            continue
        va = base + 4 * i
        COL[va] = signed32(mdisp)
        COL_NAME[va] = nm
COLADDRS = set(COL)
log('=== 7 项独立重算 ===')
log('[1] COL 记录总数 = %d' % len(COL))
log('    签名分布 = %s' % dict(collections.Counter(COL[a] for a in COL).most_common(6)))

# ============ 2. vtable ============
VT = {}           # vtable_va -> COL va
COLSET = set(COL)
for sn in ('.rdata', '.data'):
    base, arr, n = dwords_of(sn)
    for i in range(1, n):
        va = base + 4 * i
        prev = u32(va - 4)
        if prev in COLSET and in_text(arr[i]):
            VT[va] = prev
log('[2] vtable 总数 = %d ; 全部 vt-4 属于 COL = %s' % (len(VT), all(u32(v - 4) in COLSET for v in VT)))
ck('2a vtable 数 > 0 且 vt-4 全为 COL', len(VT) > 0 and all(u32(v - 4) in COLSET for v in VT),
   (len(VT), sum(1 for v in VT if u32(v - 4) not in COLSET)))

# ============ 3. 槽位 ============
SLOT = {}         # (vt, off) -> target
PER = {}          # vt -> count
for vt in VT:
    k = 0
    while k <= 400:
        t = u32(vt + 4 * k)
        if not in_text(t):
            break
        SLOT[(vt, 4 * k)] = t
        k += 1
    PER[vt] = k
TGTS = set(SLOT.values())
TGTLIST = sorted(TGTS)
hist = collections.Counter(PER.values())
log('[3] 槽位总数 = %d ; 去重目标 = %d ; 每表槽数直方图前三 = %s' %
    (len(SLOT), len(TGTS), hist.most_common(3)))
ck('3a 每个 vtable 至少 1 槽', len(PER) == len(VT) and min(PER.values()) >= 1,
   (len(PER), min(PER.values()) if PER else None))

# ============ 4. 槽位切分正确性 ============
sample = sorted(SLOT)
random.seed(203)
picks = random.sample(sample, min(200, len(sample)))
# k=0 时 vt+0 就是本表起始，不是「另一个 vtable」，须排除
overlap = [p for p in picks if p[1] > 0 and (p[0] + p[1]) in VT]
selfstart = [p for p in picks if p[1] == 0]
alloverlap = [(vt, off) for (vt, off) in SLOT if off > 0 and (vt + off) in VT]
allself = [(vt, off) for (vt, off) in SLOT if off == 0]
log('[4] 随机 200 槽: 自表起始(k=0)=%d(平凡) ; 落在另一个 vtable 起始次数 = %d' %
    (len(selfstart), len(overlap)))
log('    全量: 自表起始(k=0)=%d ; 跨表重叠 = %d' % (len(allself), len(alloverlap)))
ck('4a 200 样本槽位不落在另一个 vtable 起始', len(overlap) == 0, len(overlap))
ck('4b 全量槽位位置无一为另一个 vtable 起始', len(alloverlap) == 0, len(alloverlap))

# ============ 线性扫描（指令流） ============
BUF = RAW[RP:RP + (HI - LO)]
INS = []
p = 0
L = len(BUF)
while p < L:
    got = False
    for (off, sz, mn, op) in MD.disasm_lite(BUF[p:p + 65536], LO + p):
        got = True
        INS.append((off, sz, mn, op))
        p += sz
    if not got:
        p += 1
INS.sort()
log('   线性扫描指令数 = %d' % len(INS))
ASET = set(a for a, _, _, _ in INS)

# ============ 5. 间接调用四分类 ============
CALLS = [(a, op) for a, sz, mn, op in INS if mn == 'call']
RE_PREF = re.compile(r'^(?:dword ptr |word ptr |byte ptr )?')
RE_ABS = re.compile(r'^(?:dword ptr )?\[(0x[0-9a-f]+|\d+)\]$')
RE_BASE = re.compile(r'^(?:dword ptr |word ptr |byte ptr )?\[([a-z]{3})(?: \+ (0x[0-9a-f]+|-0x[0-9a-f]+|\d+))?\]$')
RE_REG = re.compile(r'^(?:dword ptr )?([a-z]{3})$')
REGSET = {'eax','ebx','ecx','edx','esi','edi','ebp','esp'}

def num(s):
    return int(s, 16) if s.startswith('0x') else int(s, 10)

DIR = []
IND = []
ABS = []      # (a, target) 绝对寻址 [0x...]
BASED = []    # (a, reg, disp)
REGIND = []   # (a, op)
OTHER = []    # (a, op)
for a, op in CALLS:
    if op.startswith('0x') or (op and op[0].isdigit()):
        DIR.append((a, num(op)))
        continue
    IND.append((a, op))
    m = RE_ABS.match(op)
    if m:
        ABS.append((a, num(m.group(1))))
        continue
    m = RE_BASE.match(op)
    if m and m.group(1) in REGSET:
        BASED.append((a, m.group(1), num(m.group(2)) if m.group(2) else 0))
        continue
    m = RE_REG.match(op)
    if m and m.group(1) in REGSET:
        REGIND.append((a, op))
        continue
    OTHER.append((a, op))
DIRIN = [(a, t) for a, t in DIR if in_text(t)]
log('[5] call 总数 = %d ; 直接 = %d ; 间接 = %d' % (len(CALLS), len(DIR), len(IND)))
log('    间接四类: (a)绝对IAT=%d (b)基址+disp=%d (c)纯寄存器=%d (d)其它=%d' %
    (len(ABS), len(BASED), len(REGIND), len(OTHER)))
log('    (d)其它全部地址与文本: %s' % [(hex(a), o) for a, o in OTHER])
ck('5a call=直接+间接', len(CALLS) == len(DIR) + len(IND), (len(CALLS), len(DIR), len(IND)))
ck('5b 四类之和=间接', len(ABS) + len(BASED) + len(REGIND) + len(OTHER) == len(IND),
   (len(ABS), len(BASED), len(REGIND), len(OTHER)))

# ============ 6. 位移普查 ============
DISP = collections.Counter(d for _, _, d in BASED)
REGS = collections.Counter(r for _, r, _ in BASED)
log('[6] 位移取值个数 = %d ; 全为 4 倍数 = %s' %
    (len(DISP), all(d % 4 == 0 for _, _, d in BASED)))
log('    前10 (disp,次数) = %s' % [(hex(d), c) for d, c in DISP.most_common(10)])
log('    基址寄存器分布 = %s' % REGS.most_common())
ck('6a 位移全为 4 的倍数', all(d % 4 == 0 for _, _, d in BASED),
   sum(1 for _, _, d in BASED if d % 4))

# ============ 7. 交叉 ============
DIRT = set(t for _, t in DIRIN)
INTER = TGTS & DIRT
ONLY_V = TGTS - DIRT
ONLY_D = DIRT - TGTS
NOTINS = sorted(t for t in TGTS if t not in ASET)
log('[7] 直接调用落 .text 去重目标 = %d ; 槽位去重目标 = %d' % (len(DIRT), len(TGTS)))
log('    交集 = %d ; 仅槽位 = %d ; 仅直接 = %d' % (len(INTER), len(ONLY_V), len(ONLY_D)))
log('    槽位目标不在线性扫描指令起点 = %d ; 清单 = %s' % (len(NOTINS), [hex(x) for x in NOTINS]))
ck('7a 交集/差集自洽', len(INTER) + len(ONLY_V) == len(TGTS) and len(INTER) + len(ONLY_D) == len(DIRT),
   (len(INTER), len(ONLY_V), len(ONLY_D)))

# ============ 正反控 ============
# 反控①：去掉 vt-4 是 COL 条件，只要求 dword 落 .text 且前一 dword 是「任意非 0 值」等宽松条件。
VT_LOOSE = set()
for sn in ('.rdata', '.data'):
    base, arr, n = dwords_of(sn)
    for i in range(1, n):
        va = base + 4 * i
        if in_text(arr[i]) and arr[i - 1] is not None and arr[i - 1] != 0:
            VT_LOOSE.add(va)
log('=== 正反控 ===')
log('CTRL1 去掉 vt-4 COL 约束后 vtable 候选 = %d (原 %d, 变化 %+d)' %
    (len(VT_LOOSE), len(VT), len(VT_LOOSE) - len(VT)))
ck('CTRL1 去掉 COL 约束后数量显著改变', abs(len(VT_LOOSE) - len(VT)) > len(VT) // 2,
   (len(VT), len(VT_LOOSE)))
# 同时验证：以「dword 落 .text 即算表头」为最宽松条件
VT_LOOSE2 = set()
for sn in ('.rdata', '.data'):
    base, arr, n = dwords_of(sn)
    for i in range(n):
        if in_text(arr[i]):
            VT_LOOSE2.add(base + 4 * i)
log('CTRL1b 仅要求 dword 落 .text 的表头候选 = %d (原 %d)' % (len(VT_LOOSE2), len(VT)))
ck('CTRL1b 全宽松条件数量显著改变', abs(len(VT_LOOSE2) - len(VT)) > len(VT),
   (len(VT), len(VT_LOOSE2)))

# 反控②：把「读到不落 .text 即停」改为「最多读 3 槽」
SLOT3 = {}
for vt in VT:
    for k in range(3):
        t = u32(vt + 4 * k)
        if not in_text(t):
            break
        SLOT3[(vt, 4 * k)] = t
log('CTRL2 最多读 3 槽时槽位总数 = %d (原 %d, 减少 %d)' %
    (len(SLOT3), len(SLOT), len(SLOT) - len(SLOT3)))
ck('CTRL2 限 3 槽后槽位总数显著减少', len(SLOT3) < len(SLOT) // 2,
   (len(SLOT), len(SLOT3)))
# 正控：COL 名字模式自洽（全部以 .?A 开头 @@ 结尾）
ck('POS1 全部 COL 名字以 .?A 开头且 @@ 结尾',
   all(n.startswith(b'.?A') and n.endswith(b'@@') for n in COL_NAME.values()), len(COL_NAME))
# 正控：COL 四点组结构自洽（重读一遍验证 signature/pdisp）
ok = 0
for va in COL:
    o = P.r2o(va)
    if o is None: continue
    sig, mdsp, pdsp, ptd, pcd = struct.unpack_from('<IIIII', RAW, o)
    if sig in (0, 1, 2) and pdsp == 0 and sect(ptd) == '.data' and sect(pcd) == '.rdata':
        ok += 1
ck('POS2 COL 四点组结构复核', ok == len(COL), (ok, len(COL)))

OUT = {
 'sha256': sha,
 'section_text': [hex(LO), hex(HI)],
 'item1_col': len(COL),
 'item1_disp': dict(collections.Counter(COL.values()).most_common(10)),
 'item2_vtable': len(VT),
 'item2_all_prev_is_col': all(u32(v - 4) in COLSET for v in VT),
 'item3_slots': len(SLOT),
 'item3_unique_targets': len(TGTS),
 'item3_hist_top3': [[str(k), v] for k, v in hist.most_common(3)],
 'item4_sample200_overlap': len(overlap),
 'item4_all_overlap': len(alloverlap),
 'item4_sample_selfstart': len(selfstart),
 'item4_all_selfstart': len(allself),
 'item5_call_total': len(CALLS),
 'item5_direct': len(DIR),
 'item5_indirect': len(IND),
 'item5_abs_iat': len(ABS),
 'item5_based': len(BASED),
 'item5_reg': len(REGIND),
 'item5_other': len(OTHER),
 'item5_other_list': [[hex(a), o] for a, o in OTHER],
 'item6_disp_kinds': len(DISP),
 'item6_all_mult4': all(d % 4 == 0 for _, _, d in BASED),
 'item6_disp_top10': [[hex(d), c] for d, c in DISP.most_common(10)],
 'item6_regs': REGS.most_common(),
 'item7_direct_text_targets': len(DIRT),
 'item7_inter': len(INTER),
 'item7_only_slot': len(ONLY_V),
 'item7_only_direct': len(ONLY_D),
 'item7_slot_not_in_insn_start_count': len(NOTINS),
 'item7_slot_not_in_insn_start_list': [hex(x) for x in NOTINS],
 'ctrl1_loose_prev': len(VT_LOOSE),
 'ctrl1_loose_any_text': len(VT_LOOSE2),
 'ctrl2_slots_max3': len(SLOT3),
 'asserts': N,
 'fails': FAILS,
}
with open(ROOT + '/_r203/hy4_vdisp.json', 'w') as fh:
    json.dump(OUT, fh, ensure_ascii=False, indent=1)
with open(ROOT + '/_r203/hy4_vdisp.log', 'w') as fh:
    fh.write('\n'.join(LOGS) + '\n')
log('')
log('SUMMARY asserts=%d fails=%d %s' % (N, len(FAILS), FAILS))
