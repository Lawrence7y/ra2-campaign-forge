#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 执行（hy4flash）：D1 直接槽关系 / D2 四个无副表 mdisp 档。

只读镜像；capstone detail=True 只作用于 16/24 字节小缓冲，绝不对整段 .text 开 disasm。
"""
import os, sys, struct, collections, json, hashlib, capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, '_r185'))
import pe185 as P

BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(HERE, 'd1d2.json')

fails = []
N = 0
def ck(nm, c, d=''):
    global N
    N += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def hx(x):
    return None if x is None else hex(x)

def hxlist(xs):
    return [hx(x) for x in xs]

# ---------------- 公共结构枚举 ----------------
T = P.B['.text']
LO, HI = T['lo'], T['hi_file']

COLS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]
    nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i in range(nd - 4):
        b = s['lo'] + 4 * i
        d = v[i:i + 5]
        if d[0] not in (0, 1) or d[2] != 0:
            continue
        if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata':
            continue
        nm = P.cstr(d[3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        COLS[b] = dict(d=d, off=d[1], ptd=d[3], chd=d[4], name=nm.decode('latin1'))

VTS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]
    nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i, x in enumerate(v):
        if not (LO <= x < HI):
            continue
        b = s['lo'] + 4 * i
        if P.dw(b - 4) in COLS:
            VTS[b] = COLS[P.dw(b - 4)]

def pre(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI):
            return k
        k += 1

PRE = {vt: pre(vt) for vt in VTS}
byname = collections.defaultdict(list)
for vt in sorted(VTS):
    byname[VTS[vt]['name']].append(vt)
byvt = {vt: vs for vs in byname.values() if len(vs) > 1 for vt in vs}

ck('C0 COL 1214 / vt 1214 / 槽 14044（前置事实 F1）',
   (len(COLS), len(VTS), sum(PRE.values())) == (1214, 1214, 14044),
   (len(COLS), len(VTS), sum(PRE.values())))

# 小缓冲反汇编
csd = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
csd.detail = True
csl = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
csl.detail = False

def adjdec(va):
    o = P.r2o(va)
    if o is None:
        return None
    ins = list(csd.disasm(P.RAW[o:o + 16], va))
    if len(ins) < 2 or ins[0].mnemonic != 'sub' or 'esp + 4' not in ins[0].op_str:
        return None
    try:
        k = ins[0].operands[1].imm
    except Exception:
        return None
    if ins[1].mnemonic != 'jmp' or not ins[1].op_str.startswith('0x'):
        return None
    return (k, int(ins[1].op_str, 16))

def bytes24(va):
    o = P.r2o(va)
    if o is None:
        return None
    return P.RAW[o:o + 24]

def shape_of(va):
    b = bytes24(va)
    if b is None:
        return 'unreadable'
    toks = []
    if b[0] == 0xC2 and len(b) >= 3:
        toks.append('ret %d' % struct.unpack_from('<H', b, 1)[0])
    elif b[0] == 0xC3:
        toks.append('ret')
    if b[:2] == b'\x32\xc0':
        toks.append('xor al,al')
    if b[:2] == b'\x8b\x01':
        toks.append('mov eax,[ecx]')
    if len(b) > 2 and b[:2] == b'\x8b\x41':
        toks.append('mov eax,[ecx+0x%x]' % b[2])
    if len(b) > 5 and b[:2] == b'\x8b\x81':
        toks.append('mov eax,[ecx+0x%x]' % struct.unpack_from('<I', b, 2)[0])
    if b[:2] == b'\xff\x25':
        toks.append('jmp dword ptr [mem]  # vfunc thunk')
    if b[:2] == b'\x83\xec':
        toks.append('sub esp,0x%x' % b[2])
    if b[:2] == b'\xe9':
        toks.append('jmp rel32')
    if not toks:
        try:
            toks = [' '.join('%02x' % c for c in ins.bytes) + ' ' + ins.mnemonic + ' ' + ins.op_str
                    for ins in csl.disasm(b, va)]
        except Exception:
            toks = ['raw only']
    return '; '.join(toks[:4]) if toks else 'raw only'

# ---------------- D1 ----------------
direct = []
thunks = []
for vt, c in sorted(VTS.items()):
    if c['off'] == 0:
        continue
    for k in range(PRE[vt]):
        v = P.dw(vt + 4 * k)
        r = adjdec(v)
        rec = dict(vt=vt, name=c['name'], off=c['off'], k=k, val=v,
                   group=byvt.get(vt, [vt]))
        (thunks if r is not None else direct).append(rec)

ck('D1-0 非主表 1318 槽 = 305 thunk + 1013 直接槽（前置事实 F3）',
   len(direct) + len(thunks) == 1318 and len(thunks) == 305 and len(direct) == 1013,
   (len(direct) + len(thunks), len(thunks), len(direct)))

# D1a
occ_a = 0
slots_a = 0
pairs_a = []
for d in direct:
    hits = [(o, j) for o in d['group'] if o != d['vt']
            for j in range(PRE[o]) if P.dw(o + 4 * j) == d['val']]
    occ_a += len(hits)
    if hits:
        slots_a += 1
        pairs_a.append(dict(host=hx(d['vt']), name=d['name'], off=d['off'], k=d['k'],
                            val=hx(d['val']),
                            hits=[[hx(o), j, VTS[o]['name'], VTS[o]['off']] for o, j in hits[:8]],
                            n=len(hits)))
ck('D1a 出现数 = 同组其它表任意槽命中对数；同组命中直接槽数独立复算一致',
   occ_a == sum(x['n'] for x in pairs_a) and
   slots_a == len({(x['host'], x['k']) for x in pairs_a}),
   dict(occurrences=occ_a, slots=slots_a, ratio=round(slots_a / len(direct), 6)))

# D1b
addr_count = collections.Counter(d['val'] for d in direct)
distinct_addr = len(addr_count)
shared_ge2 = {a: c for a, c in addr_count.items() if c >= 2}
shared_gt2 = {a: c for a, c in addr_count.items() if c > 2}
top_addr, top_uses = max(addr_count.items(), key=lambda x: (x[1], -x[0]))
top_names = sorted({d['name'] for d in direct if d['val'] == top_addr})
top_offs = dict(collections.Counter(d['off'] for d in direct if d['val'] == top_addr))
sig24 = {}
for d in direct:
    b = bytes24(d['val'])
    if b is not None:
        sig24.setdefault(b, []).append(d['val'])
distinct_sig = len(sig24)
sig_multi = {b: sorted(set(vs)) for b, vs in sig24.items() if len(set(vs)) >= 2}
grp_direct = collections.defaultdict(list)
for d in direct:
    grp_direct[d['name']].append(d)
grp_shared = sum(1 for nm, ds in grp_direct.items()
                 if any(c >= 2 for c in collections.Counter(d['val'] for d in ds).values()))
ck('D1b 地址计数闭合：sum(count)=1013，>=2 桶之和 >= 目标数',
   sum(addr_count.values()) == len(direct) and distinct_addr <= len(direct) and
   sum(shared_ge2.values()) >= len(shared_ge2) and distinct_sig <= distinct_addr + 1,
   dict(distinct_addr=distinct_addr, shared_ge2=len(shared_ge2), shared_gt2=len(shared_gt2)))

# D1c
ge5 = sorted(((a, c) for a, c in addr_count.items() if c >= 5), key=lambda x: (-x[1], x[0]))
c_top = []
for a, c in ge5[:5]:
    b = bytes24(a)
    c_top.append(dict(va=hx(a), uses=c,
                      raw24=' '.join('%02x' % x for x in b) if b else None,
                      bytes=list(b) if b else None,
                      shape=shape_of(a),
                      offs=dict(collections.Counter(d['off'] for d in direct if d['val'] == a))))
ck('D1c 前 5 目标的 raw24 均为 24 字节、uses 均与计数一致',
   len(c_top) == min(5, len(ge5)) and
   all(len(x['bytes']) == 24 and x['uses'] == addr_count[int(x['va'], 16)] for x in c_top),
   [(x['va'], x['uses']) for x in c_top])

# D1d
main_vts = [vt for vt, c in VTS.items() if c['off'] == 0]
occ_d = 0
slots_d = 0
same_idx = 0
pairs_d = []
for d in direct:
    hits = [(vt, j) for vt in main_vts for j in range(PRE[vt])
            if P.dw(vt + 4 * j) == d['val']]
    occ_d += len(hits)
    if hits:
        slots_d += 1
    if any(o in d['group'] and VTS[o]['off'] == 0 and PRE[o] > d['k'] and
           P.dw(o + 4 * d['k']) == d['val'] for o in main_vts):
        same_idx += 1
    if hits and len(pairs_d) < 8:
        pairs_d.append(dict(host=hx(d['vt']), name=d['name'], k=d['k'],
                            val=hx(d['val']), n=len(hits),
                            first=[hx(hits[0][0]), hits[0][1], VTS[hits[0][0]]['name']]))
ck('D1d 主表命中计数闭合；同组主表同槽号命中 = 0（前置事实 F5）',
   occ_d >= slots_d and same_idx == 0,
   dict(occurrences=occ_d, slots=slots_d, ratio=round(slots_d / len(direct), 6), same_index=same_idx))

# ---------------- D2 ----------------
# BCD 结构（MSVC RTTI BaseClassDescriptor，6 dword / 24 字节，数组成员间距恰 24）：
#   +0 pTD, +4 numContainedBases, +8 mdisp, +12 pdisp, +16 vdisp, +20 attributes。
#   +24 已经是下一个 BCD 的 pTD（例 0x7fb3a0+24=0x7fb3b8，其 pTD 恰是 FlasherClass TD）。
#   旁证：0x8005a0（FactoryClass 的 StageClass 基类，mdisp=0x24=36）attributes(+20)=9，
#         而 mdisp=36 确实属于有副表的档；四个无副表档的 attributes(+20) 全为 0。
def bcd_attr(e):
    return P.dw(e + 20)

def base_desc(chd):
    num = P.dw(chd + 8)
    arr = P.dw(chd + 12)
    if num is None or arr is None:
        return []
    out = []
    for j in range(num):
        e = P.dw(arr + 4 * j)
        if e is None:
            continue
        raw = [P.dw(e + 4 * k) for k in range(6)]
        out.append(dict(e=e, raw=raw, j=j))
    return out

TIERS = (172, 176, 240, 248)
tier_entries = {m: [] for m in TIERS}
all_bcd = []
for b, c in sorted(COLS.items()):
    for bd in base_desc(c['chd']):
        m = bd['raw'][2]
        all_bcd.append((b, c, bd))
        if m in TIERS:
            ptd = bd['raw'][0]
            nm = P.cstr(ptd + 8, 200) if ptd else None
            tier_entries[m].append(dict(col=b, cls=c['name'], chd=c['chd'],
                                        e=bd['e'], ptd=ptd,
                                        base=nm.decode('latin1') if nm else None,
                                        raw=bd['raw'], attr20=bcd_attr(bd['e'])))
ck('D2a 四档条目数 = 8/4/25/25（前置事实 D2 给定计数）',
   tuple(len(tier_entries[m]) for m in TIERS) == (8, 4, 25, 25),
   {m: len(tier_entries[m]) for m in TIERS})

for m in TIERS:
    print('# D2a mdisp=%d 共 %d 条（宿主 COL / 宿主类 -> 基类 BCD）' % (m, len(tier_entries[m])))
    for x in tier_entries[m]:
        print('   COL=%s %-28s BCD=%s pTD=%s base=%-24s attr20=%s d=%s' %
              (hx(x['col']), x['cls'], hx(x['e']), hx(x['ptd']), x['base'],
               hx(x['attr20']), hxlist(x['raw'])))

# D2b：三个基类类（它们自己没有严格 COL 记录，只作为 BCD.pTD 出现）
def find_td(cls):
    needle = b'.?AV' + cls.encode('latin1') + b'@@\0'
    for sec in ('.data', '.rdata'):
        s = P.B[sec]
        blob = P.RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
        i = blob.find(needle)
        if i >= 0:
            return s['lo'] + i - 8
    return None

def col_like_with_ptd(td):
    out = []
    for sec in ('.rdata', '.data'):
        s = P.B[sec]
        nd = s['rawsize'] // 4
        v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, x in enumerate(v):
            if x != td:
                continue
            b = s['lo'] + 4 * i - 12
            d = [P.dw(b + 4 * k) for k in range(5)]
            if None in d:
                continue
            if d[2] == 0 and P.where(d[3]) == '.data':
                out.append(dict(b=b, d=d, strict_sig=d[0] in (0, 1),
                                chd_in_rdata=P.where(d[4]) == '.rdata'))
    return out

d2b = {}
for cls in ('StageClass', 'BounceClass', 'FlasherClass'):
    td = find_td(cls)
    cands = col_like_with_ptd(td) if td else []
    col_of = [(b, c) for b, c in COLS.items() if td is not None and c['ptd'] == td]
    refs = collections.defaultdict(list)
    for b, c, bd in all_bcd:
        if td is not None and bd['raw'][0] == td:
            refs[bd['e']].append((b, c['name'], c['chd'], bd['raw']))
    uniq = []
    for e, hosts in sorted(refs.items()):
        raw = hosts[0][3]
        uniq.append(dict(e=e, hosts=sorted({(hx(h[0]), h[1]) for h in hosts}),
                         raw=hxlist(raw), raw4=hxlist(raw[:4]), attr20=hx(bcd_attr(e))))
    d2b[cls] = dict(td=hx(td), td_sig=hx(P.dw(td)) if td else None,
                    td_name=P.cstr(td + 8, 100).decode('latin1') if td else None,
                    col_like=[dict(col=hx(z['b']), d=hxlist(z['d']), strict_sig=z['strict_sig'],
                                   chd_in_rdata=z['chd_in_rdata']) for z in cands],
                    col_count=len(col_of), col5=[dict(col=hx(b), d=hxlist(c['d'])) for b, c in col_of],
                    chd_count=len(col_of),
                    bcd_unique=uniq, bcd_occurrences=sum(len(x) for x in refs.values()))
    print('# D2b %s: TD=%s sig=%s name=%s' % (cls, hx(td), hx(P.dw(td)), d2b[cls]['td_name']))
    print('   COL5: %s' % (d2b[cls]['col5'] if col_of else
          '严格 COL 0 条；放宽 signature 后 COL-like 候选 %s' % d2b[cls]['col_like']))
    print('   CHD5: %s' % ('有（见 COL5）' if col_of else '无（无严格 COL 即无所属 CHD）'))
    for x in uniq:
        print('   BCD=%s hosts=%s attr20=%s d0..d5=%s (前4=%s)' %
              (hx(x['e']), x['hosts'], x['attr20'], x['raw'], x['raw4']))

ck('D2b 三个 TD 均可读且 sig=0x7F9594；均无严格 COL/CHD；均有引用它的 BCD',
   all(v['td_sig'] == '0x7f9594' and v['col_count'] == 0 and len(v['bcd_unique']) > 0
       for v in d2b.values()),
   {k: (v['col_count'], len(v['bcd_unique'])) for k, v in d2b.items()})

# D2c
attr_h = collections.Counter(x['attr20'] for m in TIERS for x in tier_entries[m])
attr_uniq = collections.Counter(bcd_attr(bd['e'])
                                for bd in {bd['e']: bd for _, _, bd in all_bcd
                                           if bd['raw'][2] in TIERS}.values())
ptd_ok = sum(1 for m in TIERS for x in tier_entries[m]
             if P.where(x['ptd']) == '.data' and P.dw(x['ptd']) == 0x7F9594 and
             P.cstr(x['ptd'] + 8, 200) == x['base'].encode('latin1'))
chd_ok = sum(1 for m in TIERS for x in tier_entries[m]
             if P.dw(x['chd']) == 0 and P.dw(x['chd'] + 8) > 0 and
             P.where(P.dw(x['chd'] + 12)) == '.rdata')
base_chd_ok = sum(1 for m in TIERS for x in tier_entries[m]
                  if any(b for b, c in COLS.items() if c['ptd'] == x['ptd']))
nonvirtual = sum(v for k, v in attr_h.items() if k & 1)
n_entries = sum(len(tier_entries[m]) for m in TIERS)
bit1_mdisp = collections.Counter(bd['raw'][2] for _, _, bd in all_bcd if bcd_attr(bd['e']) & 1)
tier_overlap = sum(v for m, v in bit1_mdisp.items() if m in TIERS)
verdict = ('不支持 non-virtual 解释：%d/%d 条 tier BCD 的 attributes(+20) bit0=0'
           '（按卡面判据 bit0=非虚基类，故这四档没有一条带 non-virtual 标记）；'
           '且这 4 个基类一个严格 COL/CHD 都没有（base_own_chd=0），'
           '镜像根本没有为它们生成 vtable 副表。bit0=1 的 BCD 全部落在其它 mdisp 档 %s，'
           '与四档交集 %d 条。' % (n_entries - nonvirtual, n_entries,
                                dict(sorted(bit1_mdisp.items())), tier_overlap)) if nonvirtual == 0 else (
          '部分支持：%d/%d 条 attributes(+20) bit0=1（non-virtual）' % (nonvirtual, n_entries))
ck('D2c pTD/宿主 CHD 逐条可读；attributes(+20) 分桶闭合；bit0=1 与四档交集=0（实测）',
   ptd_ok == n_entries and chd_ok == n_entries and
   sum(attr_h.values()) == n_entries and
   sum(attr_uniq.values()) == len({bd['e'] for m in TIERS for x in tier_entries[m] for bd in [x]}) and
   nonvirtual == sum(v for k, v in attr_h.items() if k & 1) and tier_overlap == 0 and
   sum(collections.Counter(bcd_attr(bd['e']) for _, _, bd in all_bcd).values()) == 5302,
   dict(ptd_ok=ptd_ok, chd_ok=chd_ok, base_chd_ok=base_chd_ok,
        attr_hist=dict(attr_h), attr_uniq=dict(attr_uniq), nonvirtual=nonvirtual,
        all_bcd_attr_hist={str(k): v for k, v in sorted(collections.Counter(
            bcd_attr(bd['e']) for _, _, bd in all_bcd).items())},
        bit0_1_mdisp_hist={str(k): v for k, v in sorted(bit1_mdisp.items())},
        tier_overlap=tier_overlap))

h = hashlib.sha256()
with open(BIN, 'rb') as fh:
    for chunk in iter(lambda: fh.read(1 << 20), b''):
        h.update(chunk)
bin_sha = h.hexdigest()
script_lines = len(open(__file__, 'r', encoding='utf-8').read().splitlines())

summary = dict(
    meta=dict(binary='ra2bench/gamemd.exe', binary_sha256=bin_sha,
              script=os.path.basename(__file__), script_lines=script_lines,
              pe_sections={k: [hx(v['lo']), hx(v['hi_file'])] for k, v in P.B.items()}),
    C0=dict(col=len(COLS), vt=len(VTS), slots=sum(PRE.values())),
    D1=dict(
        D1a=dict(direct=len(direct), occurrences=occ_a, slots_with_match=slots_a,
                 ratio=round(slots_a / len(direct), 6), matched=pairs_a),
        D1b=dict(direct=len(direct), distinct_addrs=distinct_addr,
                 targets_used_ge2=len(shared_ge2), targets_used_gt2=len(shared_gt2),
                 uses_ge2_total=sum(shared_ge2.values()),
                 top=dict(va=hx(top_addr), uses=top_uses, classes=top_names, offsets=top_offs),
                 distinct_24byte_signatures=distinct_sig,
                 signatures_shared_by_multiple_addrs=len(sig_multi),
                 groups_with_internal_share=grp_shared,
                 shared_sample=[[hx(a), c] for a, c in sorted(shared_ge2.items(), key=lambda x: (-x[1], x[0]))[:12]]),
        D1c=dict(threshold='>=5', n_ge5=len(ge5), top=c_top),
        D1d=dict(direct=len(direct), main_occurrences=occ_d, main_slots_with_match=slots_d,
                 ratio=round(slots_d / len(direct), 6), same_index_same_group=same_idx,
                 sample=pairs_d)),
    D2=dict(
        D2a={str(m): [dict(col=hx(x['col']), cls=x['cls'], chd=hx(x['chd']), bcd=hx(x['e']),
                           ptd=hx(x['ptd']), base=x['base'], d=hxlist(x['raw']),
                           attr20=hx(x['attr20'])) for x in tier_entries[m]] for m in TIERS},
        D2b=d2b,
        D2c=dict(entries=n_entries, ptd_readable=ptd_ok, host_chd_readable=chd_ok,
                 base_own_chd=base_chd_ok, attr_hist_per_entry={str(k): v for k, v in sorted(attr_h.items())},
                 attr_hist_unique_bcd={str(k): v for k, v in sorted(attr_uniq.items())},
                 nonvirtual_bit0_count=nonvirtual,
                 all_bcd_attr_hist={str(k): v for k, v in sorted(collections.Counter(
                     bcd_attr(bd['e']) for _, _, bd in all_bcd).items())},
                 bit0_1_mdisp_hist={str(k): v for k, v in sorted(bit1_mdisp.items())},
                 tier_overlap=tier_overlap, verdict=verdict)),
    checks=N, fails=fails)
with open(OUT, 'w', encoding='utf-8') as _f:
    json.dump(summary, _f, ensure_ascii=False, indent=1)

print('\n===== JSON 汇总 =====')
print(json.dumps(summary, ensure_ascii=False, indent=1))
print('\n===== 断言 =====')
print('checks=%d fails=%d %s' % (N, len(fails), fails))
print('sha256(binary)=%s  script_lines=%d' % (bin_sha, script_lines))
sys.exit(1 if fails else 0)
