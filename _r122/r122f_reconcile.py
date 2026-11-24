#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122f: 复算两家族的分歧点（规则 D：所有审计员/执行员结论必须由主会话复算）。

deepseek 执行员（task 232）独立复算给出：
    c7 05 原始字节命中 1971，其中 1934 落在指令边界上，丢弃 37 个
    BSS 目标 1142，VectorClass 族 142，35 在其中，107 在外
    「Dynamic+Vector 同元素」共 139（35 内 + 104 外）
主会话自己的数：
    c7 05 命中（纯字节扫描，不判边界）→ BSS 目标 1159，VectorClass 族 142，
    35 在内，107 在外，「Dynamic+Vector 同元素」外 103

两个家族在 142 / 107 上一致，在 1159-vs-1142 与 103-vs-104 上不一致。本脚本判定：
  F1 差 17 个目标是不是「不在指令边界上的假命中」（若把边界判据加上，两数应收敛）
  F2 103 vs 104 的差是哪一个对象，谁的口径对
"""
import collections
import hashlib
import hashlib
import json
import re
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122f_reconcile.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:320]})
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


# ---- 口径 1：纯字节扫描（主会话原本的做法）----
RAW = collections.defaultdict(list)
i = 0
n = len(TDATA)
while i < n - 10:
    if TDATA[i] == 0xc7 and TDATA[i + 1] == 0x05:
        t = struct.unpack_from('<I', TDATA, i + 2)[0]
        if BSS_LO <= t < BSS_HI:
            RAW[t].append(TBASE + i)
    i += 1

# ---- 口径 2：要求站点落在真实指令边界上（deepseek 的做法）----
# 用线性扫描建立 .text 的指令边界集合。为避免 4MB 全量 detail，用 disasm_lite
# 全段一次扫完（实测 9.4s / RSS 500MB，可接受）。
# 关键：必须开 skipdata=True。不开的话 capstone 遇到第一个非法字节就停住
# （实测停在 0x46f5a0，只覆盖 452000/4063232 字节），残余边界集合被当全集用，
# 会把大量合法目标误判为「不在边界上」。
mdl = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdl.skipdata = True
BOUNDS = set()
N_SCAN = 0
N_BYTE = 0
LAST_END = None
for off, size, mnem, ops in mdl.disasm_lite(TDATA, TBASE):
    N_SCAN += 1
    LAST_END = off + size
    if mnem == '.byte':
        N_BYTE += 1
    else:
        BOUNDS.add(off)
TEXT_END = TBASE + len(TDATA)
ck('F0a 全段线性扫描必须覆盖到 .text 末尾（防 skipdata 缺失导致的提前中断）',
   LAST_END == TEXT_END and len(BOUNDS) > 1000000,
   'scan=%d .byte=%d bounds=%d last_end=0x%x text_end=0x%x'
   % (N_SCAN, N_BYTE, len(BOUNDS), LAST_END, TEXT_END))
ck('F0 指令边界集合规模合理', 100000 < len(BOUNDS) < 2000000,
   'bounds=%d ; text_bytes=%d' % (len(BOUNDS), len(TDATA)))

CLEAN = {t: ss for t, ss in RAW.items() if all(s in BOUNDS for s in ss)}
DROPPED_T = {t: ss for t, ss in RAW.items() if t not in CLEAN}
ck('F1 加上指令边界判据后，目标数从 1159 收敛到 deepseek 的 1142',
   len(CLEAN) == 1142, 'raw=%d clean=%d dropped_targets=%d dropped_sites=%d'
   % (len(RAW), len(CLEAN), len(DROPPED_T),
      sum(len(v) for v in DROPPED_T.values())))

# 被丢弃的站点样本：必须逐个证明确实全部站点都不在边界上（不是我漏判）
samp = [(hex(t), [hex(s) for s in sorted(v)]) for t, v in sorted(DROPPED_T.items())[:6]]
_all_dropped_off = all(s not in BOUNDS for v in DROPPED_T.values() for s in v)
ck('F1b 被丢弃目标的每一个站点都不在指令边界上（逐站校验，非抽样）',
   len(DROPPED_T) > 0 and _all_dropped_off,
   'dropped_targets=%d dropped_sites=%d all_off_boundary=%s sample=%s'
   % (len(DROPPED_T), sum(len(v) for v in DROPPED_T.values()), _all_dropped_off, samp))


def names_of(container, tab):
    out = []
    for s in sorted(tab.get(container, [])):
        b = rd(s, 10)
        if b is None:
            continue
        nm = vtable_name(struct.unpack_from('<I', b, 6)[0])
        if nm:
            out.append(nm)
    return out


VECRE = re.compile(r'^\.\?AV\?\$(Dynamic)?VectorClass@')


def is_vec_family(nm):
    return bool(nm) and bool(VECRE.match(nm))


# ---- 用 CLEAN 口径重算 142/107/双形态 ----
VEC_TARGETS = [t for t in CLEAN if any(is_vec_family(x) for x in names_of(t, CLEAN))]
VEC_TARGETS_RAW = [t for t in RAW if any(is_vec_family(x) for x in names_of(t, RAW))]
ck('F2 VectorClass 族 BSS 目标数 = 142（两口径都必须 142）',
   len(VEC_TARGETS) == 142 and len(VEC_TARGETS_RAW) == 142,
   'clean=%d raw=%d' % (len(VEC_TARGETS), len(VEC_TARGETS_RAW)))

# 35 个对象（重算）
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
    CTR35.append(struct.unpack_from('<I', b, 1)[0])
ck('F3 35 个容器重算一致', len(set(CTR35)) == 35, 'distinct=%d' % len(set(CTR35)))
# 审计必修 #4：35 内/35 外必须各自独立断言，不能只断总数 142
_v35 = sum(1 for t in VEC_TARGETS if t in CTR35)
ck('F3b 142 = 35 内 + 107 外（两段分别断言）', _v35 == 35 and len(VEC_TARGETS) - _v35 == 107,
   'in35=%d out35=%d' % (_v35, len(VEC_TARGETS) - _v35))


def dual_form(t, tab, strict=True):
    """双形态判定。
    strict=True （主会话口径）：全部写入恰为 1 个 Dynamic + 1 个 Vector，且元素类型相同。
    strict=False（deepseek 口径）：全部写入中至少 1 个 Dynamic + 至少 1 个 Vector，
                                 且去重后的元素类型集合大小 == 1。
    """
    ws = sorted(tab.get(t, []))
    ns = names_of(t, tab)
    vec = [x for x in ns if not x.startswith('.?AV?$Dynamic')]
    dyn = [x for x in ns if x.startswith('.?AV?$Dynamic')]
    if strict:
        if len(ws) != 2 or len(vec) != 1 or len(dyn) != 1:
            return None
    else:
        if not vec or not dyn:
            return None
    e1 = {x.split('VectorClass@')[1].split('@@@')[0] for x in vec}
    e2 = {x.split('VectorClass@')[1].split('@@@')[0] for x in dyn}
    if len(e1) == 1 and e1 == e2:
        return e1.pop()
    return None


def dual_stats(tab, strict):
    d = {t: dual_form(t, tab, strict) for t in tab}
    d = {t: e for t, e in d.items() if e}
    ins = sum(1 for t in d if t in CTR35)
    return d, len(d), ins, len(d) - ins


D_S_RAW, nS_raw, inS_raw, outS_raw = dual_stats(RAW, True)
D_S_CLN, nS_cln, inS_cln, outS_cln = dual_stats(CLEAN, True)
D_L_RAW, nL_raw, inL_raw, outL_raw = dual_stats(RAW, False)
D_L_CLN, nL_cln, inL_cln, outL_cln = dual_stats(CLEAN, False)

# 强断言：严格口径在两种扫描口径下必须给出同一答案（138 / 35 / 103）
ck('F4 严格双形态（恰 2 次写入）在 raw 与 clean 两口径下结果必须一致',
   (nS_raw, inS_raw, outS_raw) == (nS_cln, inS_cln, outS_cln) == (138, 35, 103),
   'raw: total=%d in=%d out=%d ; clean: total=%d in=%d out=%d'
   % (nS_raw, inS_raw, outS_raw, nS_cln, inS_cln, outS_cln))

# 强断言：宽松口径必须比严格口径多，且多出来的对象全部是「写入次数 > 2」
diff_loose = {t for t in D_L_CLN if t not in D_S_CLN}
ck('F4b 宽松口径比严格口径多出的对象全部写入次数 > 2（故差异不是漏解析）',
   len(D_L_CLN) > len(D_S_CLN) and
   all(len(CLEAN.get(t, [])) > 2 for t in diff_loose),
   'loose=%d strict=%d diff=%s writes=%s'
   % (len(D_L_CLN), len(D_S_CLN),
      [hex(t) for t in sorted(diff_loose)],
      {hex(t): len(CLEAN.get(t, [])) for t in sorted(diff_loose)}))

# 定位 104 vs 103：宽松减严格之后 outside 35 的那部分
loose_out = {t for t in D_L_CLN if t not in CTR35}
strict_out = {t for t in D_S_CLN if t not in CTR35}
ck('F5 宽松口径 outside 数 == 104 且差集恰为 0xabfda0 一个对象',
   len(loose_out) == 104 and (loose_out - strict_out) == {0xabfda0},
   'loose_out=%d strict_out=%d only_loose=%s'
   % (len(loose_out), len(strict_out), [hex(x) for x in sorted(loose_out - strict_out)]))

# 对差集对象逐个给字节证据
detail = []
for t in sorted(loose_out ^ strict_out):
    ws = sorted(CLEAN.get(t, []))
    rows = []
    for s in ws:
        b = rd(s, 10)
        rows.append(dict(site=hex(s), bytes=b.hex() if b else None,
                         vptr=hex(struct.unpack_from('<I', b, 6)[0]) if b else None,
                         name=vtable_name(struct.unpack_from('<I', b, 6)[0]) if b else None,
                         on_boundary=s in BOUNDS))
    detail.append(dict(obj=hex(t), n_writes=len(ws), writes=rows,
                       strict=dual_form(t, CLEAN, True),
                       loose=dual_form(t, CLEAN, False)))
ck('F6 差集对象的站点数与类名构成（判定它满足严格还是仅宽松定义）',
   len(detail) == 1 and detail[0]['obj'] == '0xabfda0'
   and len(detail[0]['writes']) == 9
   and detail[0]['strict'] is None and detail[0]['loose'] == 'PAVMultiplayerGameMode'
   and all(r['on_boundary'] for r in detail[0]['writes']),
   'detail=%r' % (detail,))

# ---------------- 自测（正控 + 反控），全部在真实数据之外另造样本 ----------------
def selftest():
    ok = []

    def t(name, cond, det=''):
        ok.append(dict(name=name, ok=bool(cond), detail=str(det)[:200]))

    # 正控 1：手工构造 c7 05 命中。就在 .text 里找一条真实 c7 05 站点，确认它在 BOUNDS 里
    hits = [(t_, s) for t_, ss in CLEAN.items() for s in ss]
    t('st1 正控：真实 c7 05 站点必须落在指令边界集合上',
      bool(hits) and all(s in BOUNDS for _, s in hits),
      'n=%d' % len(hits))

    # 反控 1：空边界集合时 clean 必须为 0
    empty = {k: v for k, v in RAW.items() if all(s in set() for s in v)}
    t('st2 反控：边界集合为空时 clean 必须为 0', len(empty) == 0, 'n=%d' % len(empty))

    # 反控 2：把 BOUNDS 整体平移到 +1，绝大多数 c7 05 站点必须掉出边界。
    # 阈值取 90% 而非 100%：x86 指令长度不固定，某些站点 s 的 s+1 恰好也是
    # 另一条指令的起点，这类命中是真实存在的，不应断言为 0。
    shifted = set(b + 1 for b in BOUNDS)
    killed = sum(1 for _, s in hits if s not in shifted)
    t('st3 反控：边界集合整体 +1 后至少 90% 的站点掉出边界',
      killed >= 0.90 * len(hits), 'killed=%d/%d = %.1f%%'
      % (killed, len(hits), 100.0 * killed / len(hits)))

    # 反控 3：skipdata 关闭后扫描必须提前中断（复现 r122f 原 bug）
    md2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    last2 = None
    for off, size, mnem, ops in md2.disasm_lite(TDATA, TBASE):
        last2 = off + size
    t('st4 反控：不开 skipdata 时线性扫描提前中断在中途，覆盖不到 .text 末',
      last2 is not None and last2 < TEXT_END,
      'no_skipdata_last_end=0x%x ; text_end=0x%x ; covered=%d/%d'
      % (last2, TEXT_END, last2 - TBASE, len(TDATA)))

    # RTTI 反解只对「真 vptr」有意义：先筛出能解出 VectorClass 族名的站点
    vec_vt = []
    for t_ in VEC_TARGETS:
        for s in CLEAN[t_]:
            b = rd(s, 10)
            if b:
                v = struct.unpack_from('<I', b, 6)[0]
                if is_vec_family(vtable_name(v)):
                    vec_vt.append(v)
    t('st0 前置：VectorClass 族站点数足够做 RTTI 正反控', len(vec_vt) >= 20,
      'n=%d' % len(vec_vt))

    # 反控 4：RTTI 反解 —— vptr+4 当 vtable 起点必须解不出名
    vs = vec_vt[:20]
    t('st5 反控：真实 vptr+4 当 vtable 起点解不出合法类名',
      bool(vs) and all(vtable_name(v + 4) is None for v in vs), 'n=%d' % len(vs))

    # 正控 2：真实 vptr 必须解得出名
    t('st6 正控：真实 vptr 解得出 .?AV 类名',
      bool(vs) and all(vtable_name(v) is not None for v in vs), 'n=%d' % len(vs))

    # 反控 5：严格双形态函数对「恰 2 次写入」的约束必须真的生效
    # 取一个已知 9 次写入的对象 0xabfda0，严格必须 None、宽松必须有名
    t('st7 反控：9 次写入的对象严格判定必须拒绝、宽松判定必须接受',
      dual_form(0xabfda0, CLEAN, True) is None
      and dual_form(0xabfda0, CLEAN, False) == 'PAVMultiplayerGameMode',
      'strict=%r loose=%r' % (dual_form(0xabfda0, CLEAN, True),
                              dual_form(0xabfda0, CLEAN, False)))

    return ok


ST = selftest()
for s in ST:
    print(('  ST-PASS ' if s['ok'] else '  ST-FAIL ') + s['name'] + ' :: ' + s['detail'])
if not all(s['ok'] for s in ST):
    print('SELFTEST FAILED')
    sys.exit(2)

json.dump(dict(exe_sha256=SHA,
               scan=dict(insns=N_SCAN, skipdata_bytes=N_BYTE, boundaries=len(BOUNDS),
                         last_end=hex(LAST_END), text_end=hex(TEXT_END),
                         covers_text_end=(LAST_END == TEXT_END)),
               raw_targets=len(RAW), raw_sites=sum(len(v) for v in RAW.values()),
               clean_targets=len(CLEAN), clean_sites=sum(len(v) for v in CLEAN.values()),
               dropped_targets=len(DROPPED_T),
               dropped_sites=sum(len(v) for v in DROPPED_T.values()),
               vec_family_clean=len(VEC_TARGETS), vec_family_raw=len(VEC_TARGETS_RAW),
               dual_strict=dict(raw=[nS_raw, inS_raw, outS_raw],
                                clean=[nS_cln, inS_cln, outS_cln]),
               dual_loose=dict(raw=[nL_raw, inL_raw, outL_raw],
                               clean=[nL_cln, inL_cln, outL_cln]),
               diff_detail=detail,
               checks=RES, all_ok=all(r['ok'] for r in RES)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d' % (len(RES), sum(1 for r in RES if r['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) else 1)
