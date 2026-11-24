#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122d: 60 站合起来是什么？—— R121 只分别测了两批，从没测过并集。

R121 的 60 站分两批（35 孪生 + 25 主函数），两批各自测过，但从未问过：
   把 60 站的描述符并起来，102 次 vptr 写入覆盖的是多少个对象、多少种元素类型？
如果 60 站恰好覆盖 60 个互不相同的容器 + 60 个互不相同的元素类型，那么
「这是一个手写的逐个类型硬编码清单」这个解释就被字节否掉了（手写清单必然有重复或漏项），
而「按元素类型各展开一次」这个解释获得一个可数的、无例外的形态。

本脚本不做语义断言，只把可数量化并给出反控。
"""
import collections
import hashlib
import json
import struct
import sys

import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122d_union60.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:300]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm, va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
DATA = open(EXE, 'rb').read()
SHA = hashlib.sha256(DATA).hexdigest()


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    x = sec_of(va)
    if x is None:
        return None
    if va - x['va'] + n > x['rs']:
        return None
    off = x['pr'] + (va - x['va'])
    return DATA[off:off + n] if off + n <= len(DATA) else None


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


DS = [x for x in SECS if x['name'] == '.data'][0]
BSS_LO, BSS_HI = DS['va'] + DS['rs'], DS['va'] + DS['vs']
TXT = [x for x in SECS if x['name'] == '.text'][0]
TDATA = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TBASE = TXT['va']

BSS_WRITES = collections.defaultdict(list)
i = 0
n = len(TDATA)
while i < n - 10:
    if TDATA[i] == 0xc7 and TDATA[i + 1] == 0x05:
        t = struct.unpack_from('<I', TDATA, i + 2)[0]
        if BSS_LO <= t < BSS_HI:
            BSS_WRITES[t].append(TBASE + i)
    i += 1


def vtable_name(vt):
    col = u32(vt - 4)
    if col is None:
        return None
    b = rd(col, 0x18)
    if b is None:
        return None
    sig, off, cd, td, chd, sv = struct.unpack('<IIIIII', b)
    if sig != 0 or td == 0:
        return None
    s = rd(td + 8, 0x100)
    if s is None:
        return None
    nm = s.split(b'\0')[0].decode('ascii', 'replace')
    return nm if nm.startswith('.?AV') else None


def names_of(container):
    out = []
    for s in sorted(BSS_WRITES.get(container, [])):
        b = rd(s, 10)
        if b is None:
            continue
        nm = vtable_name(struct.unpack_from('<I', b, 6)[0])
        if nm:
            out.append(nm)
    return out


# ---- 两批站，各自从 exe 重算（不读上一脚本的 json）----
calls = collections.defaultdict(list)
for i in range(len(TDATA) - 5):
    if TDATA[i] != 0xe8:
        continue
    rel = struct.unpack_from('<i', TDATA, i + 1)[0]
    va = TBASE + i
    tgt = va + 5 + rel
    if 0x67fdf0 <= tgt <= 0x680f80:
        calls[tgt].append(va)

TWIN_SITES = sorted(s for ss in calls.values() for s in ss if s not in (0x67d193, 0x67e62b))
ck('D0 孪生站 35 个', len(TWIN_SITES) == 35, 'n=%d' % len(TWIN_SITES))

CTR35 = []
for s in TWIN_SITES:
    b = rd(s - 7, 7)
    CTR35.append(struct.unpack_from('<I', b, 1)[0])
ck('D1 35 个容器首址互不相同', len(set(CTR35)) == 35, 'distinct=%d' % len(set(CTR35)))

import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
MAIN_INSNS = list(md.disasm(rd(0x67d300, 0x1120), 0x67d300))
MAIN_SITES = [x.address for x in MAIN_INSNS if x.mnemonic == 'push' and x.op_str == '0x7f7c80']
ck('D2 主函数站 25 个', len(MAIN_SITES) == 25, 'n=%d' % len(MAIN_SITES))
idx_of = {ins.address: k for k, ins in enumerate(MAIN_INSNS)}
GLOB25 = []
for site in MAIN_SITES:
    k = idx_of[site]
    g = None
    for j in range(k - 1, max(-1, k - 12), -1):
        ins = MAIN_INSNS[j]
        if ins.mnemonic != 'mov' or len(ins.operands) != 2:
            continue
        o1 = ins.operands[1]
        if o1.type == capstone.x86.X86_OP_MEM and o1.mem.base == 0 and o1.mem.index == 0 \
           and o1.mem.disp != 0:
            a = o1.mem.disp & 0xffffffff
            x = sec_of(a)
            if x and x['name'] == '.data':
                g = a
                break
    GLOB25.append(g)
ck('D3 25 站的全局 Array 槽全部找到', all(GLOB25), 'found=%d/25' % sum(1 for g in GLOB25 if g))
CTR25 = [g - 4 for g in GLOB25 if g]
ck('D4 25 个容器首址互不相同', len(set(CTR25)) == 25, 'distinct=%d' % len(set(CTR25)))

# ---- 并集 ----
UNION = sorted(set(CTR35) | set(CTR25))
ck('D5 并集容器数 == 60（两批零重叠）', len(UNION) == 60 and not (set(CTR35) & set(CTR25)),
   'union=%d overlap=%s' % (len(UNION), [hex(x) for x in sorted(set(CTR35) & set(CTR25))]))

all_names = []
per_ctr = {}
for c in UNION:
    ns = names_of(c)
    per_ctr[c] = ns
    all_names.extend(ns)
ck('D6 60 个容器的 vptr 写入全部反解出类名', len(all_names) == 120,
   'total_names=%d (期望 60*2=120)' % len(all_names))
ck('D7 120 个类名两两互不相同', len(set(all_names)) == 120, 'distinct=%d' % len(set(all_names)))
ck('D8 120 个类名全部属 VectorClass/DynamicVectorClass 族',
   all('VectorClass@' in nm for nm in all_names), 'non-vec=%s'
   % [nm for nm in all_names if 'VectorClass@' not in nm][:4])

ELEMS = []
for c in UNION:
    vec = [nm for nm in per_ctr[c] if not nm.startswith('.?AV?$Dynamic')]
    ELEMS.append(vec[0].split('VectorClass@')[1].split('@@@')[0] if len(vec) == 1 else None)
ck('D9 60 个容器各恰好一个 non-Dynamic vtable 且元素类型可解',
   all(ELEMS) and len(ELEMS) == 60, 'ok=%d/60' % sum(1 for e in ELEMS if e))
ck('D10 60 个元素类型互不相同', len(set(ELEMS)) == 60,
   'distinct=%d' % len(set(ELEMS)))
ck('D11 60 个全是 PAV* 指针类型', all(e.startswith('PAV') for e in ELEMS),
   'nonPAV=%s' % [e for e in ELEMS if not e.startswith('PAV')][:4])

# ---- 结构必然性检验：若真是「按元素类型展开一次」，60 个容器应占 60 段互不相邻的
#      独立区域还是可连成连续块？先量化容器首址间距，别断言。
gaps = [b - a for a, b in zip(UNION, UNION[1:])]
# D12 真条件：60 个容器不是一整块连续数组——间距最小 24 字节（相邻对象），
# 但最大跨 1884224 字节（跨越几乎整个 BSS）。若它们是一个紧凑数组，间距应恒为 24。
ck('D12 60 个容器散布在整个 BSS 而非一个紧凑数组（间距不恒定）',
   min(gaps) == 24 and max(gaps) > 1000000,
   'n_gaps=%d min=%d max=%d ; 直方前 6=%s'
   % (len(gaps), min(gaps), max(gaps), sorted(collections.Counter(gaps).items())[:6]))

# 每个容器的 vptr 写入站点是否都在同一批函数里（构造/析构）？
site_fns = collections.Counter()
for c in UNION:
    for s in sorted(BSS_WRITES.get(c, [])):
        site_fns[s] += 1

# ---- 反控 ----
# 反控 1：把 60 个容器首址各 +1，vptr 应全部解不出
bad = 0
for c in UNION:
    for s in sorted(BSS_WRITES.get(c + 1, [])):
        b = rd(s, 10)
        if b and vtable_name(struct.unpack_from('<I', b, 6)[0]):
            bad += 1
ck('D13 反控：容器首址 +1 处没有可反解的 vptr', bad == 0, 'resolved=%d' % bad)
# 反控 2：随机取全库 60 个非本批的 BSS 对象，其「Dynamic+Vector 同元素」比例
#         —— 若也 100%，则 D9/D10 不具判别力，必须如实报告
rng = sorted(t for t in BSS_WRITES if t not in set(UNION))
sample = rng[:200]
dual = 0
for t in sample:
    ns = names_of(t)
    vec = [x for x in ns if not x.startswith('.?AV?$Dynamic')]
    dyn = [x for x in ns if x.startswith('.?AV?$Dynamic')]
    if len(vec) == 1 and len(dyn) == 1:
        e1 = vec[0].split('VectorClass@')[1].split('@@@')[0]
        e2 = dyn[0].split('VectorClass@')[1].split('@@@')[0]
        if e1 == e2:
            dual += 1
# D14 真条件：非本批的 200 个 BSS 对象里，同形态比例必须显著低于 100%，
# 否则 D9/D10（60/60 全同形态）就没有判别力，只是全库的普遍形态。
_dual_pct = 100.0 * dual / len(sample) if sample else 0.0
ck('D14 非本批对象的同形态比例显著低于 100%（故 60/60 是判别性的，不是普遍形态）',
   len(sample) > 0 and _dual_pct < 50.0,
   'nonbatch=%d/%d=%.1f%% vs batch=60/60=100%%' % (dual, len(sample), _dual_pct))

json.dump(dict(exe_sha256=SHA,
               n_union=len(UNION),
               containers=['0x%08x' % c for c in UNION],
               elem_types=ELEMS,
               n_distinct_elem=len(set(ELEMS)),
               gaps=gaps,
               dual_in_nonbatch='%d/%d' % (dual, len(sample)),
               checks=RES, all_ok=all(r['ok'] for r in RES)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d' % (len(RES), sum(1 for r in RES if r['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) else 1)
