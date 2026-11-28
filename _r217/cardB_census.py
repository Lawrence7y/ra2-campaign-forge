# -*- coding: utf-8 -*-
"""R217 card B：全部虚表槽语义普查（一次运行输出 B1..B4 全部证据）。
只读 _r185/pe185.py；capstone disasm_lite 小块流式（每函数 <=64B），不开 detail。
"""
import sys, struct, collections, json, hashlib
sys.path.insert(0, '_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

RAW = P.RAW
md = Cs(CS_ARCH_X86, CS_MODE_32)  # detail=False (默认)

def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), RAW, s['rawptr']), s['lo']

def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]

def rawhex(va, n):
    o = P.r2o(va)
    return None if o is None else RAW[o:o+n].hex()

# ---------- COL / vtable 枚举（沿用 R217-m1 已确认定位法） ----------
COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k+2] != 0:
            continue
        if P.where(w[k+3]) != '.data' or P.where(w[k+4]) != '.rdata':
            continue
        nm = P.cstr(w[k+3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@':
            continue
        COL[base + 4*k] = dict(mdisp=s32(w[k+1]), pTD=w[k+3], pCHD=w[k+4],
                               sig=w[k], name=nm.decode('latin1'))
CS = set(COL)
VT = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS:
            VT[base + 4*k + 4] = v
VTS = sorted(VT)

t = P.B['.text']; TLO = t['lo']; THI = TLO + t['rawsize']
def slots(vt, cap=4096):  # 指令要求上限256；此处延伸扫描只为识别 cap 截断并给真值，统计仍按256
    out = []
    for i in range(cap):
        v = P.dw(vt + 4*i)
        if v is None or not (TLO <= v < THI):
            break
        out.append(v)
    return out
SL_ALL = {v: slots(v) for v in VTS}
SL = {v: arr[:256] for v, arr in SL_ALL.items()}  # 正式统计只用前256槽（遵守卡面上限）
TRUE_MAX = max(len(a) for a in SL_ALL.values())

# ---------- 全表槽频次 ----------
cnt = collections.Counter()
tbls = collections.defaultdict(set)
slotidx = collections.defaultdict(set)
pairs = []
for vt in VTS:
    for i, f in enumerate(SL[vt]):
        cnt[f] += 1
        tbls[f].add(vt)
        slotidx[f].add(i)
        pairs.append((vt, i, f))
TOP = cnt.most_common(25)
rank_all = {f: r for r, (f, _) in enumerate(cnt.most_common(), 1)}

# ---------- 函数体形状（小块 disasm_lite） ----------
def body(va, maxb=64):
    o = P.r2o(va)
    if o is None:
        return dict(ins=[], length=0, nore=True)
    ins = list(md.disasm_lite(RAW[o:o+maxb], va))
    for j, (a, sz, mn, op) in enumerate(ins):
        if mn in ('ret', 'retf'):
            return dict(ins=ins[:j+1], length=(a - va) + sz, nore=False)
    return dict(ins=ins, length=sum(x[1] for x in ins), nore=True)

def immval(op, tail):
    x = op.split(',', 1)[-1].strip() if ',' in op else op.strip()
    try:
        v = int(x, 0)
    except ValueError:
        return None
    return v if x == tail else None

def classify(bi):
    ins = bi['ins']
    if bi['nore'] or not ins:
        return ('v_other', None)
    ops = [(mn, op) for _, _, mn, op in ins if mn not in ('nop', 'int3')]
    if not ops:
        return ('v_other', None)
    m0, o0 = ops[0]
    m1, o1 = ops[1] if len(ops) > 1 else ('', '')
    # (i) mov eax,imm ; ret imm  （正控 b801000000c20400）
    if (len(ops) >= 2 and m0 == 'mov' and o0.startswith('eax, ')
            and m1 == 'ret' and o1.strip().isdigit()):
        v = immval(o0, o0.split(',', 1)[-1].strip())
        if v is not None:
            return ('i_const', v)
    # (ii) xor eax,eax ; ret  （正控 33c0c3）
    if m0 == 'xor' and o0.replace(' ', '') == 'eax,eax' and m1 == 'ret':
        return ('ii_zero', None)
    # (iii) 直接 ret（ret imm 也算；后续填充忽略）
    if m0 == 'ret':
        return ('iii_ret', None)
    # (iv) mov/or eax,-1 ; ret[ imm]
    if m0 in ('mov', 'or') and o0.startswith('eax, ') and m1 == 'ret':
        x = o0.split(',', 1)[-1].strip()
        try:
            if int(x, 0) in (-1, 0xffffffff):
                return ('iv_minus1', None)
        except ValueError:
            pass
    return ('v_other', None)

CLS = {}
for f, _ in TOP:
    bi = body(f)
    k, v = classify(bi)
    CLS[f] = dict(body=bi, cls=k, imm=v)
cls_names = {'i_const': '(i) mov eax,imm ; ret imm', 'ii_zero': '(ii) xor eax,eax ; ret',
             'iii_ret': '(iii) 直接 ret', 'iv_minus1': '(iv) 返回 -1', 'v_other': '(v) 其他'}

# ---------- B3 ----------
g0 = [v for v in VTS if SL[v] and SL[v][0] == 0x410260]
g0_mdisps = sorted({COL[VT[v]]['mdisp'] for v in g0})
g0_names = [COL[VT[v]]['name'] for v in g0]
internal_dups = []
for vt in VTS:
    c = collections.Counter(SL[vt])
    for f, n in c.items():
        if n >= 2:
            idx = [i for i, x in enumerate(SL[vt]) if x == f]
            internal_dups.append((vt, idx[:2], f, n))
internal_dups.sort(key=lambda x: (x[0], x[1]))
slen = collections.Counter(len(SL[v]) for v in VTS)
eq64 = [v for v in VTS if len(SL[v]) == 64]
gt64 = [v for v in VTS if len(SL[v]) > 64]
trunc = [v for v in VTS if len(SL[v]) == 256 and len(SL_ALL[v]) > 256]
maxn = max(len(SL[v]) for v in VTS)
maxvts = [v for v in VTS if len(SL[v]) == maxn]
trunc_true = {hex(v): len(SL_ALL[v]) for v in trunc}

# ---------- B4 ----------
F_FAMILY = 'b801000000c20400'
fam = sorted(f for f in cnt if (rawhex(f, 8) or '') == F_FAMILY)
fam_tables = set().union(*(tbls[f] for f in fam)) if fam else set()
fam_slots = sum(cnt[f] for f in fam)
fam_idx = collections.Counter(i for vt, i, f in pairs if f in set(fam))
exact = 0x410300
exact_tbl = tbls[exact]
exact_idx = collections.Counter(i for vt, i, f in pairs if f == exact)

# ---------- 异常收集 ----------
anoms = []
b1 = {hex(f): rank_all[f] for f in (0x4c9150, 0x410300) if f in rank_all}
for f, exp in ((0x4c9150, '33c0c3'), (0x410300, F_FAMILY)):
    got = rawhex(f, len(exp)//2)
    if got is None or not got.startswith(exp):
        anoms.append('正控字节不符 %#x 期望 %s 实测 %s' % (f, exp, got))
if b1.get(hex(0x4c9150)) is None or b1.get(hex(0x410300)) is None:
    anoms.append('正控未进全表前25：ranks=%s' % b1)
if trunc:
    anoms.append('达到 cap=256 且下一个 dword 仍在 .text 的表 %d 张（可能真槽数>256）' % len(trunc))
if any(COL[VT[v]]['mdisp'] != 0 for v in g0):
    anoms.append('slot0=0x410260 的表中存在 mdisp!=0')
empty = [v for v in VTS if not SL[v]]
if empty:
    anoms.append('零槽表 %d 张，样例 %s' % (len(empty), [hex(x) for x in empty[:10]]))
nore = [f for f, _ in TOP if CLS[f]['body']['nore']]
if nore:
    anoms.append('前25中 64B 内未见 ret 的函数 %d 个：%s' % (len(nore), [hex(x) for x in nore]))
weird_sig = sorted({d['sig'] for d in COL.values()})
if weird_sig != [0, 1, 2]:
    anoms.append('COL.sig 取值异常：%s' % weird_sig)

# ---------- 输出 ----------
out = []
def P2(s=''):
    out.append(str(s))
    print(s)

P2('=== 骨架 ===')
P2('COL=%d vtable=%d 槽引用总数=%d 不同槽目标=%d COL.sig=%s' %
   (len(COL), len(VTS), sum(cnt.values()), len(cnt), weird_sig))
P2('正控字节: 0x4c9150[0:3]=%s  0x410300[0:8]=%s' %
   (rawhex(0x4c9150, 3), rawhex(0x410300, 8)))
P2()
P2('=== B1 高频槽目标 TOP25（频次降序）===')
P2('| rank | 函数地址 | 前8字节 | 频次 | 引用表数 | 不同槽序号数 | 槽序号样例 | 类 | 体长 |')
P2('|---|---|---|---|---|---|---|---|---|')
for r, (f, n) in enumerate(TOP, 1):
    b = CLS[f]
    P2('| %d | 0x%08x | %s | %d | %d | %d | %s | %s | %dB |' %
       (r, f, rawhex(f, 8), n, len(tbls[f]), len(slotidx[f]),
        ','.join(str(x) for x in sorted(slotidx[f])[:12]),
        b['cls'], b['body']['length']))
P2()
for f in (0x4c9150, 0x410300):
    P2('正控 0x%08x: bytes=%s 频次=%d 引用表数=%d 不同槽序号数=%d 全表排名=%s 前25排名=%s' %
       (f, rawhex(f, 8), cnt[f], len(tbls[f]), len(slotidx[f]), rank_all.get(f),
        next((r for r, (x, _) in enumerate(TOP, 1) if x == f), None)))
P2()
P2('=== B2 前25桩族归类 ===')
for key, label in cls_names.items():
    fs = [f for f, _ in TOP if CLS[f]['cls'] == key]
    refs = sum(cnt[f] for f in fs)
    P2('%s: 函数数=%d 总引用数=%d 地址=%s' %
       (label, len(fs), refs, [hex(x) for x in fs]))
consts = collections.Counter(CLS[f]['imm'] for f, _ in TOP if CLS[f]['cls'] == 'i_const')
P2('(i) 立即数分布(立即数->函数个数): %s' %
   {hex(k): v for k, v in sorted(consts.items())})
P2('(i) 明细: %s' % [(hex(f), hex(CLS[f]['imm']), cnt[f], rawhex(f, 8))
                     for f, _ in TOP if CLS[f]['cls'] == 'i_const'])
P2()
P2('=== B3 共享结构 ===')
P2('slot0==0x410260 表数=%d mdisp取值=%s 全为0=%s' %
   (len(g0), g0_mdisps, g0_mdisps == [0]))
P2('类名清单(%d):' % len(g0_names))
for i in range(0, len(g0_names), 6):
    P2('  ' + ' | '.join(g0_names[i:i+6]))
P2('内部重复表数=%d；前10例(表地址, 槽序号对, 函数地址, 重复次数):' %
   len({x[0] for x in internal_dups}))
for vt, idx, f, n in internal_dups[:10]:
    P2('  0x%08x (slot %d,%d) -> 0x%08x x%d' % (vt, idx[0], idx[1], f, n))
P2('槽数分布: ==64: %d 张, >64: %d 张, 最大=%d (表数=%d)' %
   (len(eq64), len(gt64), maxn, len(maxvts)))
P2('最大槽表(卡面上限256口径): %s' % [(hex(v), COL[VT[v]]['name']) for v in maxvts])
if trunc_true:
    P2('延伸扫描真槽数(仅诊断, 正式统计仍用256): %s' % trunc_true)
    P2('延伸后最大真槽数=%d' % TRUE_MAX)
P2('cap=256 截断嫌疑表=%d %s' % (len(trunc), [hex(x) for x in trunc[:20]]))
P2('槽数>64 表清单(前20): %s' % [hex(x) for x in gt64[:20]])
P2()
P2('=== B4 TClassFactory 桩族 ===')
P2('正控 0x410300: 频次(槽位总数)=%d 引用表数=%d 不同表数=%d 槽序号分布=%s' %
   (cnt[exact], len(exact_tbl), len(exact_tbl),
    dict(sorted(exact_idx.items()))))
P2('全族(前8字节==%s): 函数地址=%s' % (F_FAMILY, [hex(x) for x in fam]))
P2('全族: 函数个数=%d 槽位总数=%d 引用表数=%d 不同表数=%d' %
   (len(fam), fam_slots, len(fam_tables), len(fam_tables)))
P2('全族槽序号分布: %s' % dict(sorted(fam_idx.items())))
P2('逐地址: %s' % [(hex(f), cnt[f], len(tbls[f])) for f in fam])
P2()
P2('=== 复核异常 ===')
P2('共 %d 条' % len(anoms))
for a in anoms:
    P2('  - ' + a)

res = dict(
    col=len(COL), vt=len(VTS), total_refs=sum(cnt.values()), distinct_targets=len(cnt),
    top25=[dict(rank=r, addr=hex(f), bytes=rawhex(f, 8), freq=n, tables=len(tbls[f]),
                slotnum=len(slotidx[f]), cls=CLS[f]['cls'], body=CLS[f]['body']['length'])
           for r, (f, n) in enumerate(TOP, 1)],
    controls={hex(f): dict(bytes=rawhex(f, 8), freq=cnt[f], tables=len(tbls[f]),
                           rank=rank_all.get(f)) for f in (0x4c9150, 0x410300)},
    b2={k: dict(n=sum(1 for f, _ in TOP if CLS[f]['cls'] == k),
                refs=sum(cnt[f] for f, _ in TOP if CLS[f]['cls'] == k),
                addrs=[hex(f) for f, _ in TOP if CLS[f]['cls'] == k]) for k in cls_names},
    b2_consts={hex(k): v for k, v in consts.items()},
    b3=dict(g0_n=len(g0), g0_mdisp=g0_mdisps, g0_names=g0_names,
            internal_dups_n=len({x[0] for x in internal_dups}),
            internal_dups_head=[[hex(v), i, hex(f), n] for v, i, f, n in internal_dups[:10]],
            eq64=len(eq64), gt64=len(gt64), maxn=maxn,
            maxvts=[[hex(v), COL[VT[v]]['name']] for v in maxvts], trunc=[hex(x) for x in trunc],
            trunc_true=trunc_true, true_max_slot=TRUE_MAX),
    b4=dict(exact=dict(freq=cnt[exact], tables=len(exact_tbl),
                       idx={str(k): v for k, v in sorted(exact_idx.items())}),
            family=dict(addrs=[hex(x) for x in fam], n=len(fam), slots=fam_slots,
                        tables=len(fam_tables), idx={str(k): v for k, v in sorted(fam_idx.items())})),
    anomalies=anoms,
)
with open('_r217/cardB_census.json', 'w') as fh:
    json.dump(res, fh, indent=1, ensure_ascii=False)
with open('_r217/cardB_report.txt', 'w') as fh:
    fh.write('\n'.join(out) + '\n')
print('\n[落盘] _r217/cardB_census.json bytes=%d sha256=%s' %
      (len(open('_r217/cardB_census.json','rb').read()),
       hashlib.sha256(open('_r217/cardB_census.json','rb').read()).hexdigest()))
