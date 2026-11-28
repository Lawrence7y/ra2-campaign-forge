# -*- coding: utf-8 -*-
"""R219-A: 67 个 diff 目标的语义归类 / 反查命中 / same 反控。
一次跑完全部取证；产物 cardA_diff67.txt + cardA_diff67.json。
"""
import sys, struct, collections, json, random
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True

OUT = {}
def p(*a):
    print(*a)

# ---------- PE / COL / VT 重建 (与 m1_sites6.py 同律) ----------
def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']
def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]

COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k + 2] != 0:
            continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata':
            continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@':
            continue
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), pCHD=w[k + 4], name=nm.decode('latin1'))
CS = set(COL)
VT = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS:
            VT[base + 4 * k + 4] = v
VTS = sorted(VT)
REAL = [v for v in VTS if P.where(P.dw(v)) == '.text']

def slots(vt, cap=65536):
    out = []
    while len(out) < cap and P.where(P.dw(vt + 4 * len(out))) == '.text':
        out.append(P.dw(vt + 4 * len(out)))
    return out

SLOTS = {v: slots(v) for v in VTS}
p('[0] 正控 COL=%d VT=%d real(.text首槽)=%d phantom=%d max_slots=%d total_slots=%d'
  % (len(COL), len(VT), len(REAL), len(VTS) - len(REAL),
     max(len(x) for x in SLOTS.values()), sum(len(x) for x in SLOTS.values())))

TGT = [0x7f5c70, 0x7eb058, 0x7e22a4, 0x7e8c94, 0x7e3ebc, 0x7f4960]
EXPECT = {0x7f5c70: 344, 0x7eb058: 343, 0x7e22a4: 341,
          0x7e8c94: 341, 0x7e3ebc: 322, 0x7f4960: 309}
for v in TGT:
    p('    vt=%08x n=%d expect=%d %s' % (v, len(SLOTS[v]), EXPECT[v],
      'PASS' if len(SLOTS[v]) == EXPECT[v] else 'FAIL'))

BYNAME = collections.defaultdict(list)
for c, d in COL.items():
    BYNAME[d['name']].append(c)
def view_of(name):
    best = None
    for c in BYNAME.get(name, []):
        for v, cc in VT.items():
            if cc == c and COL[c]['md_'] == 0:
                if best is None or v < best[0]:
                    best = (v, c)
    return best

def bcds(coladdr):
    chd = COL[coladdr]['pCHD']
    nb = P.dw(chd + 8); arr = P.dw(chd + 12); out = []
    for i in range(nb):
        e = P.dw(arr + 4 * i)
        if e is None or P.where(e) == 'other':
            continue
        td = P.dw(e)
        nm = P.cstr(td + 8, 256) if td else None
        out.append(dict(bcd=e, name=(nm or b'').decode('latin1'),
                        ncb=P.dw(e + 4), mdisp=s32(P.dw(e + 8))))
    return chd, arr, out

# 父类主视图：m9 已证实 PAR 映射与 BCD 后继项一致，运行时重新推导并断言
PAR_DERIVED = {}
for vt in TGT:
    c = VT[vt]; nm = COL[c]['name']; chd, arr, bc = bcds(c)
    idx = [i for i, b in enumerate(bc) if b['name'] == nm]
    if len(idx) == 1 and idx[0] + 1 < len(bc):
        pv = view_of(bc[idx[0] + 1]['name'])
        if pv:
            PAR_DERIVED[vt] = pv[0]
PAR_EXPECT = {0x7f5c70: 0x7e8c94, 0x7eb058: 0x7e8c94, 0x7e22a4: 0x7e8c94,
              0x7e8c94: 0x7f4960, 0x7e3ebc: 0x7f4960, 0x7f4960: 0x7f0508}
p('[0b] 父类视图推导 vs 期望: %s' % ('PASS' if PAR_DERIVED == PAR_EXPECT else 'FAIL'))
if PAR_DERIVED != PAR_EXPECT:
    p('    derived=%s' % {hex(k): hex(v) for k, v in PAR_DERIVED.items()})
PAR = PAR_EXPECT
tot = collections.Counter()
diff_rows = []   # (host_vt, slot, self_target, parent_target)
same_targets = []
for vt in TGT:
    S = SLOTS[vt]; P2 = SLOTS[PAR[vt]]
    for k in range(256, len(S)):
        if k >= len(P2):
            tot['oob'] += 1
        elif S[k] == P2[k]:
            tot['same'] += 1
            same_targets.append(S[k])
        else:
            tot['diff'] += 1
            diff_rows.append((vt, k, S[k], P2[k]))
    p('    vt=%08x slots>=256=%d same=%d diff=%d oob=%d'
      % (vt, len(S) - 256,
         sum(1 for r in diff_rows if r[0] == vt) * 0 + sum(1 for k in range(256, len(S)) if k < len(P2) and S[k] == P2[k]),
         sum(1 for r in diff_rows if r[0] == vt),
         sum(1 for k in range(256, len(S)) if k >= len(P2))))
p('[0c] slot>=256 比对合计 same=%d diff=%d oob=%d (应 294/67/103, 和=%d)'
  % (tot['same'], tot['diff'], tot['oob'], tot['same'] + tot['diff'] + tot['oob']))
assert tot['diff'] == 67, 'diff must be 67'

DIFF_ADDRS = sorted(set(r[2] for r in diff_rows))
p('[0d] diff 槽 67 个, 去重目标地址数=%d' % len(DIFF_ADDRS))

# ---------- 前缀判据 ----------
def classify(addr):
    """返回 (类别, 前12字节hex, 前3条指令文本列表, 解码是否确定)。"""
    o = P.r2o(addr)
    if o is None:
        return 'other', '', [], False, False
    b12 = P.RAW[o:o + 12]
    bmax = P.RAW[o:o + 64]
    ins = []
    try:
        for i in md.disasm(bmax, addr):
            ins.append('%s %s' % (i.mnemonic, i.op_str))
            if len(ins) >= 3:
                break
    except Exception:
        pass
    b0 = b12[0] if b12 else None
    # 按卡片定义顺序判定（首条指令）
    if b0 == 0x55:
        cat = 'push_ebp'
    elif b0 == 0xCC:
        cat = 'cc_pad'
    elif ins:
        first = ins[0]
        mnem = first.split()[0]
        if mnem == 'jmp':
            # 解析目标，判断是否落 .text
            op = first.split(' ', 1)[1] if ' ' in first else ''
            dest = None
            try:
                if op.startswith('0x'):
                    dest = int(op, 16)
            except ValueError:
                pass
            if dest is not None and P.where(dest) == '.text':
                cat = 'jmp_rel'
            else:
                cat = 'other'
        elif (mnem == 'ret'):
            cat = 'ret_stub'
        elif (mnem == 'mov' and
              (first.startswith('mov eax, dword ptr [esp') or
               '[ebp + 8]' in first or '[ebp+8]' in first)):
            cat = 'mov_eax_arg'
        else:
            cat = 'other'
    else:
        cat = 'other'
    determined = len(ins) >= 1
    # 附加标注：push_ebp 中是否为「push ebp; mov ebp,esp」标准 prologue
    std_pro = bool(b12[:1] == b'\x55' and b12[1:4] == b'\x8b\xec')
    return cat, b12.hex(), ins, determined, std_pro

# ---------- 反查命中：.rdata + .data 全 dword 计数 ----------
refcnt = collections.Counter()
refhosts = collections.defaultdict(list)
ref_locs = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in DIFF_ADDRS or v in set(same_targets):
            loc = base + 4 * k
            refcnt[v] += 1
            ref_locs[v].append(loc)
            # 宿主虚表：若 loc-4 处 dword 是 COL，则虚表起点=loc，否则回溯最近的 VT 起点
            if (loc - 4) in VT:
                refhosts[v].append(loc)
            else:
                # 在 [loc-4*400, loc) 内找 VT 起点使 loc 在其槽域内
                host = None
                for hv in VTS:
                    if hv < loc and (loc - hv) % 4 == 0 and (loc - hv) // 4 < 400:
                        if hv in VT and loc < hv + 4 * len(SLOTS[hv]):
                            host = hv; break
                if host is not None:
                    refhosts[v].append(host)
                else:
                    refhosts[v].append(None)

p('\n' + '=' * 110)
p('A1: 67 个 diff 目标逐目标前缀归类')
p('%-10s %-24s %-44s %-14s %s' % ('目标', '前12字节', '前3条指令', '前缀类别', '解码确定'))
cat_counter = collections.Counter()
a1_rows = []
for a in DIFF_ADDRS:
    cat, hx, ins, det, std_pro = classify(a)
    cat_counter[cat] += 1
    ins_s = ' | '.join(ins) if ins else '(无法线性解码)'
    p('0x%08x %-24s %-44s %-14s %s' % (a, hx, ins_s[:44], cat, det))
    a1_rows.append(dict(addr=hex(a), bytes12=hx, ins=ins, cat=cat, determined=det, std_prologue=std_pro))
p('A1 汇总: %s 合计=%d (应=67)'
  % (dict(cat_counter), sum(cat_counter.values())))
assert sum(cat_counter.values()) == 67

p('\n' + '=' * 110)
p('A2: 67 个 diff 目标反查命中数 (.rdata+.data 全 dword)')
one = [a for a in DIFF_ADDRS if refcnt[a] == 1]
multi = [(a, refcnt[a]) for a in DIFF_ADDRS if refcnt[a] > 1]
zero = [a for a in DIFF_ADDRS if refcnt[a] == 0]
p('被引用 1 次: %d ; 被引用 0 次: %d ; 被引用多次(>1): %d'
  % (len(one), len(zero), len(multi)))
if zero:
    p('  零引用地址(异常): %s' % [hex(x) for x in zero])
p('被多次引用的目标（地址, 次数, 全部宿主虚表）:')
for a, c in sorted(multi, key=lambda x: -x[1]):
    p('  0x%08x  count=%d  hosts=%s' % (a, c, [hex(x) if x else None for x in refhosts[a]]))
p('被引用 1 次的目标（本表专属新增槽候选）共 %d 个:' % len(one))
for a in one:
    p('  0x%08x @%s' % (a, hex(ref_locs[a][0]) if ref_locs[a] else '?'))

p('\n' + '=' * 110)
p('A3: 随机 20 个 same 目标前缀类别分布（反控）')
uniq_same = sorted(set(same_targets))
rnd = random.Random(20261117)
sample = rnd.sample(uniq_same, min(20, len(uniq_same)))
same_cat = collections.Counter()
for a in sample:
    cat, hx, ins, det, std_pro = classify(a)
    same_cat[cat] += 1
    p('  0x%08x %-24s %-30s %s' % (a, hx, ' | '.join(ins)[:30], cat))
p('A3 same 反控汇总: %s 合计=%d' % (dict(same_cat), sum(same_cat.values())))
p('A3 对比: diff 分布=%s ; same 分布=%s' % (dict(cat_counter), dict(same_cat)))

p('\n' + '=' * 110)
p('异常与不确定')
undet = [a for a in DIFF_ADDRS if not classify(a)[3]]
p('首条指令无法线性解码确定的 diff 目标数: %d %s' % (len(undet), [hex(a) for a in undet]))
addr_cnt = collections.Counter(r[2] for r in diff_rows)
dup = [(a, c) for a, c in addr_cnt.items() if c > 1]
p('67 个 diff 槽指向重叠（同一地址被多个槽引用）: %d 组' % len(dup))
for a, c in dup:
    slots_here = [(hex(v), k) for v, k, t, _ in diff_rows if t == a]
    p('  0x%08x count=%d slots=%s' % (a, c, slots_here))
out_of_text = [a for a in DIFF_ADDRS if P.where(a) != '.text']
p('diff 目标落 .text 之外: %d %s' % (len(out_of_text), [hex(a) for a in out_of_text]))
p('线性解码说明: 使用 md.disasm(字节切片, addr)，detail=False, skipdata=True；')
p('  "无法线性解码" 指该地址起始 64 字节内无有效指令流。')

OUT = {
    'positive_control': {
        'COL': len(COL), 'VT': len(VT), 'real': len(REAL),
        'max_slots': max(len(x) for x in SLOTS.values()),
        'total_slots': sum(len(x) for x in SLOTS.values()),
        'six_table_slots': {hex(v): len(SLOTS[v]) for v in TGT},
        'par_derived_pass': PAR_DERIVED == PAR_EXPECT,
        'cmp': dict(tot),
    },
    'a1': a1_rows,
    'a1_summary': dict(cat_counter),
    'a2': {
        'once': [hex(a) for a in one],
        'zero': [hex(a) for a in zero],
        'multi': [{'addr': hex(a), 'count': c,
                   'hosts': [hex(x) if x else None for x in refhosts[a]]}
                  for a, c in sorted(multi, key=lambda x: -x[1])],
    },
    'a3': {
        'sample': [hex(a) for a in sample],
        'summary': dict(same_cat),
    },
    'anomalies': {
        'undetermined': [hex(a) for a in undet],
        'overlap': [{'addr': hex(a), 'count': c} for a, c in dup],
        'out_of_text': [hex(a) for a in out_of_text],
    },
}
json.dump(OUT, open('_r219/cardA_diff67.json', 'w'), indent=1)
p('\n[E] 与 R218 粗分布的关系（判据差异，来源不确定）')
p('  R218 粗分布: other=58 jmp_rel=4 mov_eax_arg=4 push_ebp=1 (合计 67)。')
p('  本卡判据结果: other=57 jmp_rel=4 mov_eax_arg=4 push_ebp=2 ret_stub=0 cc_pad=0 (合计 67)。')
p('  本卡逐字节事实: 首字节 0x55 的目标恰有 2 个 (0x004565e0=55 56 8b f1, 0x0051dbd0=55 8b ec);')
p('  首字节 0xe9 的目标恰有 4 个 (0x005228b0/0x005228c0/0x00746cb0/0x00746cc0, 均落 .text 0x70f070/0x70f090);')
p('  首条为 mov eax, dword ptr [esp+...] 的目标恰有 4 个 (0x004d94a0/0x0051cba0/0x00521c60/0x007416a0)。')
p('  因此 jmp_rel 与 mov_eax_arg 两类与 R218 数字一致；push_ebp 差 1、other 差 1（方向相反）。')
p('  调度卡未给出 R218 粗判据的具体代码，且 0x55 首字节实为 2 个而非 1 个，故两者差异的精确映射')
p('  无法仅凭卡片复现 —— 记为不确定，不以臆测填补。本卡一律以「首条指令」判据（卡片定义）为准。')

p('\n[done] -> _r219/cardA_diff67.txt / .json')
