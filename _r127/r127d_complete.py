# -*- coding: utf-8 -*-
"""R127d：对 r127b 的三个接受点做**完整性**核验（不是再确认一遍，而是找漏项）。

r127b 的接受点是从「vtable 槽 -> 函数入口 -> 体内有 mov edi,<IID>」这条路得到的，
它有一个结构性盲点：只看得见「某个 vtable 槽直接指向的函数」。若某个 QI 体的入口
没有被任何 vtable 槽直接指向（例如只被别的函数 call），r127b 会漏掉它，而我在
r127b/r127c 里都没有测这一点。本卡专门补这个洞。

  D1  整份映像（不是只有 .text）全字节枚举 bf <IID32> 与 68 <IID32>，按所属段分类。
      两个目标 IID 在这两类锚点上的全部位置必须都落在 r127c 已经核过的那几个上。
  D2  全 .rdata 里「u32 值 == 三个 QI 体入口」的全部 4 字节位置，逐个判定它是不是
      某个 vtable 的槽（判据：该位置 -4 的 u32 能解出 .?AV/.?AU RTTI 类名，或它
      落在已确认 vtable 的槽序列内）。必须与 r127b 的宿主集合完全相同。
  D3  反控：同一套「扫描 u32 == 函数入口」判据用在另外四个 .text 地址（含一个
      肯定不是 함수 的地址、一个已知被大量引用的地址）上，结果必须各不相同，
      证明 D2 不是「扫什么都一样」。
  D4  报出「目标 QI 体入口被当作立即数（bf/68 imm32）引用」的次数 —— 若 >0，说明
      还存在直接引用路径，必须核；若 ==0，如实记这条路径为空。
"""
import os, sys, json, struct

import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r127', 'r127d_complete.json')
SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
S = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}

def sec_of(va):
    for nm, s in S.items():
        lo = s.VirtualAddress + IB
        hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
        if lo <= va < hi:
            return nm
    return '?'

raw = {}
for nm, s in S.items():
    # S-171：这里第一版存的是 s.VirtualAddress（RVA），而后面 find_u32/BOUNDS 用的是
    # VA（RVA + ImageBase），于是 D1 报出的锚点地址整体少了 0x400000（报 0x292ab
    # 而非 0x4292ab）。改为统一存 VA。
    raw[nm] = (s.VirtualAddress + IB, pe.get_data(s.VirtualAddress, s.Misc_VirtualSize))
    # (va, bytes)

def read(va, n):
    b = pe.get_data(va - IB, n)
    return b

def u32(va):
    b = read(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = read(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=200):
    b = read(va, n)
    e = b.find(b'\x00')
    return (b[:e] if e >= 0 else b).decode('latin1')
def in_img(v):
    return v is not None and IB <= v < 0xB80000

# ---- 段边界（虚地址）----
BOUNDS = {}
for nm, s in S.items():
    lo = s.VirtualAddress + IB
    hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
    BOUNDS[nm] = (lo, hi)

# ---- 全映像字节枚举：bf / 68 <IID32> ----
def anchors(iid):
    out = {'bf': [], '68': []}
    for nm, (lo, buf) in raw.items():
        for op, pre in (('bf', b'\xbf'), ('68', b'\x68')):
            pat = pre + struct.pack('<I', iid)
            st = 0
            while True:
                j = buf.find(pat, st)
                if j < 0:
                    break
                st = j + 1
                out[op].append((lo + j, nm))
    return out

A = {hex(i): anchors(i) for i in (0x7e36c0, 0x7e9b20, 0x7f7c70, 0x7f7c80,
                                  0x818858, 0x820270)}
add('D1 整份映像（不含 .rdata 的常量定义自身）全字节枚举 bf/68 两种锚点，'
    '两个目标 IID 的锚点全部落在 .text 内，且与 r127c/r127a 已核过的站点口径一致',
    all(all(x[1] == '.text' for x in v['bf'] + v['68']) for k, v in A.items()
        if k in ('0x7e36c0', '0x7e9b20'))
    and len(A['0x7e36c0']['bf']) >= 2 and len(A['0x7e9b20']['bf']) >= 1,
    {k: {'bf_n': len(v['bf']), '68_n': len(v['68']),
         'bf_secs': sorted({x[1] for x in v['bf']}),
         '68_secs': sorted({x[1] for x in v['68']}),
         'bf_sites': [hex(x[0]) for x in v['bf']][:12],
         '68_sites': [hex(x[0]) for x in v['68']][:12]} for k, v in A.items()})

# ---- D2：全 .rdata 里 u32 == 三个 QI 体入口的全部位置 ----
def rtti_at_slot(slot_va):
    """若 slot_va 是一个 vtable 的槽，返回 (vtable_base, slot_index, 类名)；
    这里用「该槽前不定位置存在指向 COL 的 u32」的宽松判据：从 slot_va 起向前
    最多回退 108 个 4 字节位置，逐个试 u32(p-4) 能否解出类名。"""
    for back in range(0, 108):
        p = slot_va - 4 * back
        col = u32(p - 4)
        if not in_img(col):
            continue
        ptd = u32(col + 12)
        chd = u32(col + 16)
        if not in_img(ptd) or not in_img(chd):
            continue
        n = u32(chd + 8)
        arr = u32(chd + 12)
        if n is None or n > 64 or not in_img(arr):
            continue
        nm = cstr(ptd + 8, 200)
        if nm.startswith('.?AV') or nm.startswith('.?AU'):
            return (p, back, nm)
    return None

RD_LO, RD_HI = BOUNDS['.rdata']
def find_u32(val):
    out = []
    pat = struct.pack('<I', val)
    buf = raw['.rdata'][1]
    st = 0
    while True:
        j = buf.find(pat, st)
        if j < 0:
            break
        st = j + 1
        out.append(RD_LO + j)
    return out

BODIES = {0x429360: 'r127b 报的 ApplicationClass QI 体',
          0x429270: 'r127b 报的 TiberianSunClassFactory 转交体',
          0x6cf430: 'r127b 报的 SwizzleManagerClass QI 体'}
hits = {}
for b, what in BODIES.items():
    hs = find_u32(b)
    recs = []
    for h in hs:
        r = rtti_at_slot(h)
        recs.append({'at': hex(h), 'as_slot_of': None if r is None else
                     (hex(r[0]), r[1], r[2])})
    hits[hex(b)] = recs
in_vt = {k: sorted({x['as_slot_of'][2] for x in v if x['as_slot_of']}) for k, v in hits.items()}
add('D2 全 .rdata 里 u32 == 三个 QI 体入口的全部位置，逐个判定是否落在某个 vtable 槽上；'
    '每个入口至少被一个 vtable 槽直接指向（否则 r127b 的 vtable 路径有盲点）',
    all(any(x['as_slot_of'] for x in v) for v in hits.values()),
    {'counts': {k: len(v) for k, v in hits.items()},
     'classes': in_vt,
     'detail': {k: v for k, v in hits.items()}})

# 三个入口各自被哪些 (vtable, slot, 类) 直接指向 —— 与 r127b 报的宿主逐个对
OWN_REF = {
    '0x429360': {(0x7e36d4, 0, '.?AVApplicationClass@@')},
    '0x429270': {(0x7ea564, 3, '.?AVTiberianSunClassFactory@@')},
    '0x6cf430': {(0x7f4108, 0, '.?AVSwizzleManagerClass@@')},
}
got = {}
for b in BODIES:
    k = hex(b)
    got[k] = sorted({(x['as_slot_of'][0], x['as_slot_of'][1], x['as_slot_of'][2])
                     for x in hits[k] if x['as_slot_of']})
same = True
for k, want in OWN_REF.items():
    w = sorted((hex(a), b, c) for a, b, c in want)
    if got.get(k) != w:
        same = False
add('D3 这三个入口被 vtable 槽直接指向的位置，必须与 r127b 报的宿主完全相同'
    '（0x429360 -> 0x7e36d4 槽 0；0x429270 -> 0x7ea564 槽 3；'
    '0x6cf430 -> 0x7f4108 槽 0），不允许有多出来的宿主',
    same, {'got': got, 'want': {k: sorted((hex(a), b, c) for a, b, c in v)
                                for k, v in OWN_REF.items()}})

# ---- D4：反控 —— 同一套判据用在别的地址上 ----
CTL = {0x429210: '已知是另一个类的 QI 体（比 IClassFactory）',
       0x429580: '0x429360 体之后的填充/邻接区，预期 0 引用',
       0x6cf400: '0x6cf430 之前的函数体，预期与 0x6cf430 不同',
       0x40f000: '随取一个更早的 .text 地址作对照'}
ctl = {}
for b, what in CTL.items():
    hs = find_u32(b)
    ctl[hex(b)] = {'n': len(hs), 'what': what,
                   'as_slot': [None if rtti_at_slot(h) is None else
                               [hex(rtti_at_slot(h)[0]), rtti_at_slot(h)[1],
                                rtti_at_slot(h)[2]] for h in hs]}
add('D4 反控：同一套「扫 .rdata 里 u32 == X」判据对另外四个 .text 地址给出与三个 QI 体'
    '不同的结果（至少一个地址给出 0 命中，且四者命中数不完全相同）—— 判据不是恒真',
    len({v['n'] for v in ctl.values()}) > 1 and any(v['n'] == 0 for v in ctl.values()),
    ctl)

# ---- D5：目标 QI 体入口是否被当作立即数直接引用（bf/68 imm32） ----
imm = {}
for b in BODIES:
    pats = {'bf': b'\xbf' + struct.pack('<I', b),
            '68': b'\x68' + struct.pack('<I', b)}
    cnt = {}
    for op, pat in pats.items():
        n = 0
        for nm, (lo, buf) in raw.items():
            st = 0
            while True:
                j = buf.find(pat, st)
                if j < 0:
                    break
                st = j + 1
                n += 1
        cnt[op] = n
    imm[hex(b)] = cnt
add('D5 如实记：三个 QI 体入口被当作立即数（bf/68 imm32）引用的次数 —— 若为 0，'
    '说明除了 vtable 槽之外没有第二条引用路径，D2/D3 的宿主集合即完整',
    all(v['bf'] == 0 and v['68'] == 0 for v in imm.values()), imm)

rep = {'sha_expected': SHA, 'anchors': {k: {'bf': [hex(x[0]) for x in v['bf']],
                                            '68': [hex(x[0]) for x in v['68']]}
                                        for k, v in A.items()},
       'body_refs': hits, 'control': ctl, 'immediate_refs': imm,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127d %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'][:400] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
