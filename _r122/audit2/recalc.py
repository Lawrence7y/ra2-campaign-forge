#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R122 hy4 独立审计复算。

只读审计对象；只在本目录写 recalc.out。内存纪律：Capstone disasm_lite，detail=False，
不把全量 detail 对象常驻；边界集合只用 set/list 标量。
"""
import collections
import hashlib
import json
import os
import struct

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/audit2/recalc.out'
LINES = []


def P(tag, s=''):
    line = '[%s] %s' % (tag, s)
    print(line)
    LINES.append(line)


def ck(name, cond, detail=''):
    P('SELFTEST', '%s :: %s :: %s' % ('PASS' if bool(cond) else 'FAIL', name, detail))
    return bool(cond)


with open(EXE, 'rb') as f:
    DATA = f.read()
SHA = hashlib.sha256(DATA).hexdigest()
P('SHA256', SHA)

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm, va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
for x in SECS:
    P('SECTION', '%s va=0x%08x vs=0x%x pr=0x%x rs=0x%x end=0x%08x'
      % (x['name'], x['va'], x['vs'], x['pr'], x['rs'], x['va'] + x['rs']))
P('CAPSTONE', 'version=%s' % capstone.__version__)


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    x = sec_of(va)
    if x is None or va - x['va'] + n > x['rs']:
        return None
    off = x['pr'] + (va - x['va'])
    if off + n > len(DATA):
        return None
    return DATA[off:off + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


DS = [x for x in SECS if x['name'] == '.data'][0]
BSS_LO, BSS_HI = DS['va'] + DS['rs'], DS['va'] + DS['vs']
TXT = [x for x in SECS if x['name'] == '.text'][0]
TDATA = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TBASE = TXT['va']
TEXT_END = TBASE + len(TDATA)
P('TEXT', 'base=0x%08x bytes=%d end=0x%08x' % (TBASE, len(TDATA), TEXT_END))
P('BSS', 'lo=0x%08x hi=0x%08x' % (BSS_LO, BSS_HI))


# ---------- A1: 两种线性扫描模式 ----------
def scan(skipdata):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    md.skipdata = bool(skipdata)
    n = 0
    nbyte = 0
    last_end = None
    bounds = set()
    first_stop = None
    prev_end = None
    for off, size, mnem, ops in md.disasm_lite(TDATA, TBASE):
        n += 1
        last_end = off + size
        if mnem == '.byte':
            nbyte += 1
        else:
            bounds.add(off)
        if prev_end is not None and off != prev_end and first_stop is None:
            first_stop = (prev_end, off)
        prev_end = last_end
    return dict(n=n, last_end=last_end, nbyte=nbyte, bounds=bounds,
                gap=first_stop, covered=0 if last_end is None else last_end - TBASE)


S_OFF = scan(False)
S_ON = scan(True)
P('A1_OFF', 'insns=%d last_end=%s covered=%d reached_end=%s dotbyte=%d bounds=%d gap=%s'
  % (S_OFF['n'], hex(S_OFF['last_end']) if S_OFF['last_end'] else None, S_OFF['covered'],
     S_OFF['last_end'] == TEXT_END, S_OFF['nbyte'], len(S_OFF['bounds']),
     tuple(hex(x) for x in S_OFF['gap']) if S_OFF['gap'] else None))
P('A1_ON', 'insns=%d last_end=%s covered=%d reached_end=%s dotbyte=%d bounds=%d gap=%s'
  % (S_ON['n'], hex(S_ON['last_end']) if S_ON['last_end'] else None, S_ON['covered'],
     S_ON['last_end'] == TEXT_END, S_ON['nbyte'], len(S_ON['bounds']),
     tuple(hex(x) for x in S_ON['gap']) if S_ON['gap'] else None))
for t in (0x46f5a0, 0x7e1000):
    P('A1_PROBE', '0x%08x in OFF_BOUNDS=%s in ON_BOUNDS=%s'
      % (t, t in S_OFF['bounds'], t in S_ON['bounds']))


# ---------- RTTI helper ----------
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


# ---------- 原始 c7 05 命中 ----------
RAW = collections.defaultdict(list)
RAW_ALL = 0
for i in range(len(TDATA) - 10):
    if TDATA[i] == 0xc7 and TDATA[i + 1] == 0x05:
        RAW_ALL += 1
        t = struct.unpack_from('<I', TDATA, i + 2)[0]
        if BSS_LO <= t < BSS_HI:
            RAW[t].append(TBASE + i)
P('RAW', 'c705_bytes=%d targets=%d sites=%d' % (RAW_ALL, len(RAW), sum(len(v) for v in RAW.values())))


def with_bounds(bounds):
    out = {}
    for t, ss in RAW.items():
        ok = [s for s in ss if s in bounds]
        if len(ok) == len(ss):
            out[t] = ss
    dropped = {t: ss for t, ss in RAW.items() if t not in out}
    return out, dropped


def names_of(container, tab):
    out = []
    for s in sorted(tab.get(0, [])):
        pass
    return out


def names_t(t, tab):
    out = []
    for s in sorted(tab.get(t, [])):
        b = rd(s, 10)
        if b is None:
            continue
        nm = vtable_name(struct.unpack_from('<I', b, 6)[0])
        if nm:
            out.append(nm)
    return out


def vec_targets(tab):
    return [t for t in tab if any('VectorClass@' in x for x in names_t(t, tab))]


def elem_of(nm):
    head = '.?AV?$DynamicVectorClass@' if nm.startswith('.?AV?$DynamicVectorClass@') else '.?AV?$VectorClass@'
    return nm[len(head):].split('@@@')[0]


def strict_dual(tab, t):
    """严格定义：恰 2 次写入，且 1 Dynamic + 1 Vector，且元素类型相同。"""
    sites = sorted(tab.get(t, []))
    if len(sites) != 2:
        return None
    nms = []
    for s in sites:
        b = rd(s, 10)
        if b is None:
            return None
        nm = vtable_name(struct.unpack_from('<I', b, 6)[0])
        if nm is None:
            return None
        nms.append(nm)
    dyn = [x for x in nms if x.startswith('.?AV?$DynamicVectorClass@')]
    vec = [x for x in nms if x.startswith('.?AV?$VectorClass@') and not x.startswith('.?AV?$DynamicVectorClass@')]
    if len(dyn) != 1 or len(vec) != 1 or elem_of(dyn[0]) != elem_of(vec[0]):
        return None
    return elem_of(vec[0])


# ---------- 35 个对象（独立重扫 call rel32） ----------
calls = collections.defaultdict(list)
for i in range(len(TDATA) - 5):
    if TDATA[i] != 0xe8:
        continue
    rel = struct.unpack_from('<i', TDATA, i + 1)[0]
    va = TBASE + i
    tgt = va + 5 + rel
    if 0x67fdf0 <= tgt <= 0x680f80:
        calls[tgt].append(va)
TW = sorted(s for ss in calls.values() for s in ss if s not in (0x67d193, 0x67e62b))
CTR35 = []
for s in TW:
    b = rd(s - 7, 7)
    if b is None or b[0] != 0xba or b[5:7] != b'\x8b\xce':
        P('A3_WARN', 'bad call preamble at %s' % hex(s))
        continue
    CTR35.append(struct.unpack_from('<I', b, 1)[0])
CTR35 = sorted(set(CTR35))
P('OBJ35', 'call_targets=%d sites=%d twins=%d distinct_edx=%d'
  % (len(calls), sum(len(v) for v in calls.values()), len(TW), len(CTR35)))


# ---------- A2/A3: 正确边界（ON）与错误边界（OFF）两套口径 ----------
def loose_dual(tab, t):
    """主会话 r122f.dual_form 的实际口径：所有站点名字里恰各一个 Dynamic/Vector。
    不检查写入次数，也不保证两个 vptr 属于同一次构造。"""
    ns = names_t(t, tab)
    dyn = [x for x in ns if x.startswith('.?AV?$DynamicVectorClass@')]
    vec = [x for x in ns if x.startswith('.?AV?$VectorClass@') and not x.startswith('.?AV?$DynamicVectorClass@')]
    if len(dyn) != 1 or len(vec) != 1 or elem_of(dyn[0]) != elem_of(vec[0]):
        return None
    return elem_of(vec[0])


def census(tag, bounds):
    clean, dropped = with_bounds(bounds)
    vt = set(vec_targets(clean))
    dual = {t: strict_dual(clean, t) for t in clean}
    dual = {t: e for t, e in dual.items() if e}
    inside = {t for t in dual if t in CTR35}
    outside = set(dual) - inside
    loose_outside = set()
    for t in clean:
        if t in CTR35:
            continue
        ns = names_t(t, clean)
        if any(x.startswith('.?AV?$DynamicVectorClass@') for x in ns) and \
           any(x.startswith('.?AV?$VectorClass@') and not x.startswith('.?AV?$DynamicVectorClass@')
               for x in ns):
            loose_outside.add(t)
    loose2 = {t: loose_dual(clean, t) for t in clean}
    loose2 = {t: e for t, e in loose2.items() if e}
    loose2_outside = {t for t in loose2 if t not in CTR35}
    P(tag, 'clean_targets=%d clean_sites=%d dropped_targets=%d dropped_sites=%d vec=%d vec35=%d vecOutside35=%d dual_total=%d dual35=%d dualOutside35=%d looseOutside35=%d loose2Outside35=%d'
      % (len(clean), sum(len(v) for v in clean.values()), len(dropped),
         sum(len(v) for v in dropped.values()), len(vt), len(vt & set(CTR35)),
         len(vt - set(CTR35)), len(dual), len(inside), len(outside), len(loose_outside),
         len(loose2_outside)))
    return dict(clean=clean, dropped=dropped, vec=vt, dual=dual, inside=inside, outside=outside,
                loose_outside=loose_outside, loose2_outside=loose2_outside)


RES_ON = census('A2_A3_ON', S_ON['bounds'])
RES_OFF = census('A2_A3_OFF', S_OFF['bounds'])

# A2 明确打印 raw / clean 各数字
P('A2_RAW', 'raw_targets=%d raw_sites=%d clean_ON_targets=%d clean_ON_sites=%d dropped_targets=%d dropped_sites=%d'
  % (len(RAW), sum(len(v) for v in RAW.values()), len(RES_ON['clean']),
     sum(len(v) for v in RES_ON['clean'].values()), len(RES_ON['dropped']),
     sum(len(v) for v in RES_ON['dropped'].values())))

# ---------- A4: 0x00abfda0 ----------
TARGET = 0x00abfda0
P('A4_HEADER', 'target=0x%08x raw_sites=%s on_clean_sites=%s off_clean_sites=%s'
  % (TARGET, [hex(x) for x in sorted(RAW.get(TARGET, []))],
     [hex(x) for x in sorted(RES_ON['clean'].get(TARGET, []))],
     [hex(x) for x in sorted(RES_OFF['clean'].get(TARGET, []))]))
for s in sorted(RAW.get(TARGET, [])):
    b = rd(s, 10)
    vt = struct.unpack_from('<I', b, 6)[0] if b else None
    P('A4_SITE', 'site=0x%08x raw10=%s in_ON_BOUNDS=%s in_OFF_BOUNDS=%s vptr=%s rtti=%s'
      % (s, b.hex() if b else None, s in S_ON['bounds'], s in S_OFF['bounds'],
         hex(vt) if vt is not None else None, vtable_name(vt) if vt is not None else None))
P('A4_VERDICT', 'strict_2writes=%s loose_ge1each=%s r122f_dual_form_helper=%s'
  % (strict_dual(RES_ON['clean'], TARGET) is not None,
     any(x.startswith('.?AV?$DynamicVectorClass@') for x in names_t(TARGET, RES_ON['clean'])) and
     any(x.startswith('.?AV?$VectorClass@') and not x.startswith('.?AV?$DynamicVectorClass@')
         for x in names_t(TARGET, RES_ON['clean'])),
     loose_dual(RES_ON['clean'], TARGET) is not None))
P('A4_DUAL_HELPER_DIFF', 'strict_outside=%d r122f_helper_outside=%d only_r122f_helper=%s'
  % (len(RES_ON['outside']), len(RES_ON['loose2_outside']),
     [hex(x) for x in sorted(RES_ON['loose2_outside'] - RES_ON['outside'])]))

# A4 的 103-vs-104 差异：严格定义下 outside 集合对称差
sym = RES_ON['outside'] ^ {t for t in RAW if strict_dual(RAW, t) and t not in CTR35}
P('A4_SYMDIFF_STRICT', 'n=%d addrs=%s'
  % (len(sym), [hex(x) for x in sorted(sym)]))
for t in sorted(sym):
    P('A4_SYM_SITE', 'obj=0x%08x sites=%s' % (t, [hex(x) for x in sorted(RAW.get(t, []))]))

# ---------- 自测 ----------
ck('positive: 手工构造 c7 05 命中',
   DATA[TXT['pr']:TXT['pr'] + 6] != b'' and RAW_ALL > 0,
   'raw_hits=%d' % RAW_ALL)
ck('negative: 空边界集 clean 必须为 0',
   len(with_bounds(set())[0]) == 0, 'clean=%d' % len(with_bounds(set())[0]))
ck('negative: skipdata 关闭能复现扫描中断',
   S_OFF['last_end'] != TEXT_END and S_OFF['last_end'] == 0x46f5a0 and S_ON['last_end'] == TEXT_END,
   'off_end=%s on_end=%s' % (hex(S_OFF['last_end']), hex(S_ON['last_end'])))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    f.write('\n'.join(LINES) + '\n')
P('OUTPUT', OUT)
